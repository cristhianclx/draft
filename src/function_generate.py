# -*- coding: utf-8 -*-

import base64
import os

from langchain_core.messages import HumanMessage, SystemMessage

from function_app import BASE_PATH, Screen, _app, db
from function_utils import FILES_ALLOWED_EXTENSIONS, file_upload_to_blob, generate_embedding, llm

STORAGE_CONTAINER_SCREENS_NAME = os.getenv("STORAGE_CONTAINER_SCREENS_NAME")

DIRECTORY = "data"
FILES_TO_EXCLUDE = ["README"]


def generate_content(file_extension, file_base64):
    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an assistant tasked with analyzing a mobile app screenshot for a design reference. "
                    "Construct a compact yet detail-rich description that captures the app's purpose and primary features. "
                    "Highlight the type app focused on this content type or app displays, describe notable interface elements like visible buttons, big text and navigation icons. "
                    "Emphasize the functionality and its specialization. "
                    "Integrate terms about app type and discuss app's focus. "
                    "Integrate all these elements into a single, continuous statement that encapsulates the essence of the app's offerings. "
                    "If the screenshot provides insufficient information or is overly generic, respond only with 'NO-RESPONSE'. "
                    "Your description will assist in searching for reference examples for app designs."
                )
            ),
            HumanMessage(
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:{file_extension_descriptive};base64,{file_base64}".format(
                                file_extension_descriptive=FILES_ALLOWED_EXTENSIONS[file_extension],
                                file_base64=file_base64,
                            ),
                        },
                    },
                ]
            ),
        ]
    )
    if "NO-RESPONSE" not in result.content:
        return result.content


with _app.app_context():
    for file_path in os.listdir(os.path.join(BASE_PATH, DIRECTORY)):
        file_path = file_path.lower()
        if file_path in FILES_TO_EXCLUDE:
            continue
        file_id, file_extension = os.path.splitext(file_path)
        file_exists = db.session.query(
            db.session.query(Screen)
            .filter_by(
                id=file_id,
            )
            .exists()
        ).scalar()
        if file_exists:
            print(f"{file_path} exists")
            continue
        file_extension = file_extension[1:]
        if file_extension not in list(FILES_ALLOWED_EXTENSIONS.keys()):
            continue
        if len(file_id) != 36:
            print(f"{file_path} was not included")
            continue
        with open(os.path.join(BASE_PATH, DIRECTORY, file_path), "rb") as file_image:
            print(f"{file_path} in process")
            file_image_content = file_image.read()
            file_base64 = base64.b64encode(file_image_content).decode("utf-8")
            file_content = generate_content(file_extension, file_base64)
            if file_content:
                file_url = file_upload_to_blob(
                    CONTAINER_NAME=STORAGE_CONTAINER_SCREENS_NAME,
                    file_name=file_path,
                    file_extension_descriptive=FILES_ALLOWED_EXTENSIONS[file_extension],
                    file_content=file_image_content,
                )
                db.session.add(
                    Screen(
                        id=file_id,
                        content=file_content,
                        embedding=generate_embedding(file_content),
                        url=file_url,
                    )
                )
                db.session.commit()
