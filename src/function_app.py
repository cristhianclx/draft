# -*- coding: utf-8 -*-

import datetime
import logging
import os
from uuid import uuid4

import azure.functions as func
from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel, ValidationError, constr, validator
import requests

from function_utils import (
    BASE_PATH,
    file_upload_to_blob,
    generate_embedding,
    generate_images_for_app,
    generate_images_from_urls,
    generate_js,
    generate_random_slug,
    generate_skeleton_for_app,
    get_close_match_with_threshold,
    get_closest_matches,
    model_dimensions,
)
from migrations_types import VectorType

DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_SSL_CA = os.path.join(BASE_PATH, "certs/ssl_ca.pem")

DATABASE_URI = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?"
    f"ssl_verify_cert=true&ssl_verify_identity=true&"
    f"ssl_ca={DATABASE_SSL_CA}"
)

STORAGE_CONTAINER_FILES_NAME = os.getenv("STORAGE_CONTAINER_FILES_NAME")


_app = Flask(__name__)
_app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(_app)

db = SQLAlchemy(_app)
migrate = Migrate(_app, db)


class Screen(db.Model):

    __tablename__ = "screens"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    content = db.Column(
        db.Text,
        nullable=False,
    )
    embedding = db.Column(
        VectorType(dim=model_dimensions),
        comment="hnsw(distance=cosine)",
    )
    url = db.Column(
        db.String(255),
        nullable=False,
    )

    def __repr__(self):
        return f"<Screen id={self.id}>"


class Search(db.Model):

    __tablename__ = "searches"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_random_slug,
        nullable=False,
    )
    q = db.Column(
        db.Text,
        nullable=False,
    )
    embedding = db.Column(
        VectorType(dim=model_dimensions),
        comment="hnsw(distance=cosine)",
    )
    url = db.Column(
        db.String(255),
    )

    def __repr__(self):
        return f"<Search id={self.id}>"


api = Api(_app)


@_app.route("/")
@_app.route("/s/<id>/")
def www(id=None):
    return Response(
        render_template("index.html"),
    )


@_app.route("/server/")
def server():
    return Response(
        render_template("index.txt"),
        mimetype="text/plain",
    )


@_app.route("/robots.txt")
def robots():
    return Response(
        render_template("robots.txt"),
        mimetype="text/plain",
    )


class PINGResource(Resource):
    def get(self):
        return jsonify(response="pong")


class GenerateForm(BaseModel):
    q: constr(min_length=5)

    @validator("q")
    def validate_q(cls, v: str) -> str:
        v = v.lower().strip()
        if len(v) == 0:
            raise ValueError("Not enough to generate")
        return v


class GenerateResource(Resource):
    def post(self):
        try:
            form = GenerateForm(**request.get_json(force=True))
        except ValidationError:
            return {
                "message": "Validation error",
            }, 400
        try:
            search = form.q
            search_vector = generate_embedding(search)
            search_close_result = get_close_match_with_threshold(
                session=db.session,
                reference=Search,
                search_vector=search_vector,
                search_threshold=0.2,
            )
            if search_close_result:
                return {
                    "id": search_close_result[0].id,
                    "url": search_close_result[0].url,
                }
            closest_screens = get_closest_matches(
                session=db.session,
                reference=Screen,
                search_vector=search_vector,
            )
            references = generate_images_from_urls(
                urls=closest_screens,
            )
            skeleton = generate_skeleton_for_app(
                search=search,
                references=references,
            )
            images = generate_images_for_app(
                search=search,
            )
            script = generate_js(
                search=search,
                references=references,
                skeleton=skeleton,
                images=images,
            )
            slug = generate_random_slug()
            url = file_upload_to_blob(
                CONTAINER_NAME=STORAGE_CONTAINER_FILES_NAME,
                file_name=f"{slug}/App.tsx",
                file_extension_descriptive="text/plain",
                file_content=script.App_js.encode("utf-8"),
            )
            db.session.add(
                Search(
                    id=slug,
                    q=search,
                    embedding=generate_embedding(search),
                    url=url,
                )
            )
            db.session.commit()
            return {
                "id": slug,
                "script": script.App_js,
                "url": url,
            }
        except Exception:
            return {
                "message": "Error trying to generate, please try again in some minutes",
            }, 400


class DataResource(Resource):
    def get(self, id: str):
        item = Search.query.get(id)
        if not item:
            return {
                "message": "Not found",
            }, 404
        return {
            "id": item.id,
            "script": requests.get(item.url).content.decode("utf-8"),
            "url": item.url,
        }


api.add_resource(PINGResource, "/ping/")
api.add_resource(GenerateResource, "/server/generate/")
api.add_resource(DataResource, "/server/data/<id>/")


app = func.WsgiFunctionApp(
    app=_app.wsgi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS,
)


@app.function_name(name="warm")
@app.timer_trigger(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=True,
)
def warm(timer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info("Python timer trigger function ran at %s", utc_timestamp)
