# -*- coding: utf-8 -*-

import base64
import os
import random
from typing import List

from azure.storage.blob import BlobServiceClient, ContentSettings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from langchain_openai import ChatOpenAI
import requests
from sentence_transformers import SentenceTransformer

BASE_PATH = os.path.dirname(__file__)

PACKAGES = """
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-scripts": "^4.0.0",
    "react-icons": "3.11.0",
    "@chakra-ui/react": "latest",
    "@chakra-ui/icons": "latest",
    "@emotion/react": "^11.7.0",
    "@emotion/styled": "^11.6.0",
    "framer-motion": "^4.1.17"
"""

STORAGE_CONNECTION = os.getenv("AzureWebJobsStorage")
STORAGE_SERVICE = BlobServiceClient.from_connection_string(STORAGE_CONNECTION)

FILES_ALLOWED_EXTENSIONS = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/x-png",
    "webp": "image/webp",
}

MODEL_BASE_DIRECTORY = "models"
MODEL_ID = "all-MiniLM-L6-v2"
MODEL_DIRECTORY = os.path.join(BASE_PATH, MODEL_BASE_DIRECTORY, MODEL_ID)

_GENERATE_RANDOM_COLORS_DIRECTORY = os.path.join(BASE_PATH, "random_colors")
_GENERATE_RANDOM_COLORS = {}

# List was take from here: https://github.com/purry03/Username-Generator
_GENERATE_RANDOM_SLUG_NOUNS_DIRECTORY = os.path.join(BASE_PATH, "random_slug", "nouns.txt")
_GENERATE_RANDOM_SLUG_ADJECTIVES_DIRECTORY = os.path.join(BASE_PATH, "random_slug", "adjectives.txt")

_GENERATE_RANDOM_SLUG_NOUNS = []
_GENERATE_RANDOM_SLUG_ADJECTIVES = []


if all(
    [
        os.path.exists(MODEL_DIRECTORY),
        os.path.isdir(MODEL_DIRECTORY),
    ]
):
    model = SentenceTransformer(MODEL_DIRECTORY)
else:
    model = SentenceTransformer(MODEL_ID, trust_remote_code=True)
    model.save(MODEL_DIRECTORY)

model_dimensions = model.get_sentence_embedding_dimension()

LLM_ID = "gpt-4o"

llm = ChatOpenAI(model=LLM_ID)


def generate_embedding(file_content):
    return model.encode(file_content)


def generate_random_slug():
    global _GENERATE_RANDOM_SLUG_NOUNS
    global _GENERATE_RANDOM_SLUG_ADJECTIVES
    if _GENERATE_RANDOM_SLUG_NOUNS == []:
        with open(_GENERATE_RANDOM_SLUG_NOUNS_DIRECTORY, "r") as f:
            _GENERATE_RANDOM_SLUG_NOUNS = f.read().strip(" \n").split("\n")
    if _GENERATE_RANDOM_SLUG_ADJECTIVES == []:
        with open(_GENERATE_RANDOM_SLUG_ADJECTIVES_DIRECTORY, "r") as f:
            _GENERATE_RANDOM_SLUG_ADJECTIVES = f.read().strip(" \n").split("\n")
    return "{}-{}-{}".format(
        random.choice(_GENERATE_RANDOM_SLUG_ADJECTIVES),
        random.choice(_GENERATE_RANDOM_SLUG_NOUNS),
        random.randint(1, 1000),
    ).lower()


def generate_random_color():
    global _GENERATE_RANDOM_COLORS
    if _GENERATE_RANDOM_COLORS == {}:
        for f in os.listdir(_GENERATE_RANDOM_COLORS_DIRECTORY):
            if f.endswith(".txt"):
                f_path = os.path.join(_GENERATE_RANDOM_COLORS_DIRECTORY, f)
                with open(f_path, "r", encoding="utf-8") as f_instance:
                    _GENERATE_RANDOM_COLORS[f_path] = f_instance.read()
    return random.choice(list(_GENERATE_RANDOM_COLORS.values())).strip(" \n").replace("\n", ",")


def file_upload_to_blob(CONTAINER_NAME, file_name, file_extension_descriptive, file_content, overwrite=True):
    blob_client = STORAGE_SERVICE.get_blob_client(
        container=CONTAINER_NAME,
        blob=file_name,
    )
    blob_client.upload_blob(
        file_content,
        overwrite=overwrite,
        content_settings=ContentSettings(
            content_type=file_extension_descriptive,
        ),
    )
    return blob_client.url


def get_closest_matches(session, reference, search_vector, number=1):
    search_distance = reference.embedding.cosine_distance(search_vector).label("distance")
    search_items = (
        session.query(
            reference,
            search_distance,
        )
        .order_by(search_distance)
        .limit(number)
        .all()
    )
    results = []
    for search_item, search_item_distance in search_items:
        results.append(search_item.url)
    return results


def get_close_match_with_threshold(session, reference, search_vector, search_threshold):
    search_distance = reference.embedding.cosine_distance(search_vector).label("distance")
    return (
        session.query(
            reference,
            search_distance,
        )
        .filter(
            search_distance < search_threshold,
        )
        .order_by(search_distance)
        .limit(1)
        .first()
    )


def generate_images_from_urls(urls):
    images = []
    for image_url in urls[:1]:
        _, image_extension = os.path.splitext(image_url)
        image_extension = image_extension[1:]
        try:
            image_raw = requests.get(image_url)
            image_content = image_raw.content
            image_base64 = base64.b64encode(image_content).decode("utf-8")
        except:
            continue
        images.append(
            {
                "url": image_url,
                "base64": image_base64,
                "extension": image_extension,
            }
        )
    return images


class SkeletonElement(BaseModel):
    x: int
    y: int
    width: int
    height: int
    category: str
    type: str
    src: str


def generate_skeleton_for_app(search, references):
    llm_structured = llm.with_structured_output(List[SkeletonElement], method="json_mode")
    response = llm_structured.invoke(
        [
            SystemMessage(
                content=(
                    f'I have these designs as reference, please create an app mockup in json format for an app about "{search}". '
                    "Use provided screenshot apps for style reference and structure. "
                    "For each element use this reference: {src, category, type, x, y, width, height}."
                    "For text elements, include the some'text' attribute with relevant content."
                )
            ),
            HumanMessage(
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:{file_extension_descriptive};base64,{file_base64}".format(
                                file_extension_descriptive=FILES_ALLOWED_EXTENSIONS[reference["extension"]],
                                file_base64=reference["base64"],
                            ),
                        },
                    }
                    for reference in references
                ]
            ),
        ]
    )
    return response


def generate_images_for_app(search):
    raw = requests.get(
        "https://api.openverse.org/v1/images/",
        params={
            "q": search,
        },
    ).json()
    results = raw["results"]
    return [
        {
            "url": result["url"],
            "height": result["height"],
            "width": result["width"],
        }
        for result in results
    ]


class SkeletonStructure(BaseModel):
    App_js: str


def generate_js(search, references, skeleton, images):
    llm_structured = llm.with_structured_output(SkeletonStructure, method="json_mode")
    response = llm_structured.invoke(
        [
            SystemMessage(
                content=(
                    f'I have this structure for an app about "{search}": '
                    f"{skeleton}. "
                    "I have these images that can be used when in an element you need an image: "
                    f"{images}. "
                    "For logos, icons or navigation images, use icons that exists on @chakra-ui/icons, or use react-icons. "
                    "Attached screenshot is a reference to create this web app. "
                    "Generate chakra-ui App.js content that can be rendered in a webpage. "
                    "Consider, that I only have this available packages: "
                    f"{PACKAGES}. "
                    f"Include style or colors, and improve icons and logo, use this as color reference: {generate_random_color()}. "
                    "Include some good font in this style. "
                    "Do necessary imports, don't use props because it can lead to errors. "
                    "ONLY output content of App.js in json format with this key App_js, use this boilerplate as example: "
                    "import * as React from 'react' "
                    "import { ChakraProvider } from '@chakra-ui/react' "
                    "function App() { "
                    "  return ( "
                    "    <ChakraProvider> "
                    "      <TheRestOfYourApplication /> "
                    "    </ChakraProvider> "
                    "  ) "
                    "} "
                    "After you finish, fix imports and review if all imports are good, if not fix that."
                )
            ),
            HumanMessage(
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:{file_extension_descriptive};base64,{file_base64}".format(
                                file_extension_descriptive=FILES_ALLOWED_EXTENSIONS[reference["extension"]],
                                file_base64=reference["base64"],
                            ),
                        },
                    }
                    for reference in references
                ]
            ),
        ]
    )
    return response
