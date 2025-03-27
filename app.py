#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from blocker.blocker import Blocker

import json

from flask import Flask, jsonify, request
from flask.wrappers import Response as FlaskResponse

from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
from flask_openapi3 import Info, Tag
from flask_openapi3 import OpenAPI, APIBlueprint

from pymongo import MongoClient
from bson import ObjectId, json_util

# DB
client = MongoClient \
(
    host="blocker_mongodb",
    port=27017,
    username="root",
    password="pass",
    authSource="admin"
)
db = client.blocker_db
blocker_collection = db.blockchain

# Responses
class ValidationErrorModel(BaseModel):
    code: int = Field(401, description="Status Code")
    message: str = Field("Unauthorized!", description="Exception ValidationErrorModel")

class Unauthorized(BaseModel):
    code: int = Field(403, description="Status Code")
    message: str = Field("Unauthorized!", description="Exception Unauthorized")

class ServiceUnavailable(BaseModel):
    code: int = Field(503, description="Status Code")
    message: str = Field("ServiceUnavailable!", description="Resource down - Service Unavailable")

class NotFoundResponse(BaseModel):
    code: int = Field(404, description="Status Code")
    message: str = Field("NotFoundResponse!", description="Exception: NotFoundResponse")

class BlockedMinedResponse(BaseModel):
    message: str = Field("A block is MINED"),
    index: str = Field(description="Index of the mined block"),
    timestamp: str = Field(description="Timestamp of the mined block"),
    proof: str = Field(description="Proof of work for the mined block"),
    previous_hash: str = Field(description="Previous hash of the mined block"),

class MineBlock(BaseModel):
    message: int = Field("id", description="the id")
    index: Optional[int] = Field(None, ge=2, le=4, description="Age")
    timestamp: str = Field(None, min_length=2, max_length=4, description="Author")

class BlockerResponse(BaseModel):
    code: int = Field("200", description="Status Code")
    message: str = Field("ok", description="Exception Information")
    data: Optional[MineBlock]

class GetChainResponse(BaseModel):
    code: int = Field("200", description="Status Code")
    message: str = Field("ok", description="Chain validation")
    data: Optional[MineBlock]

class ValidateResponse(BaseModel):
    code: int = Field("200", description="Status Code")
    message: str = Field("ok", description="Validation of block")
    content: str = Field("application/json")

# Callbacks
def validation_error_callback(e: ValidationError) -> FlaskResponse:
    validation_error_object = ValidationErrorModel(code="400", message=e.json())
    response = make_response(validation_error_object.json())
    response.headers["Content-Type"] = "application/json"
    response.status_code = getattr(current_app, "validation_error_status", 422)
    return response

# Misc
def parse_json(data):
    return json.loads(json_util.dumps(data))


# Setup
blocker = Blocker()

app  = OpenAPI(
    "Blocker API",
    validation_error_status=400,
    validation_error_model=ValidationErrorModel,
    validation_error_callback=validation_error_callback
)

blocker_tag = Tag(name="Blockchain", description="Basic blockchain management")
operations_tag = Tag(name="Operations", description="Operations and status information")
database_tag = Tag(name="Database", description="Database CRUD operations")
api_version = "v1"


# Endpoints
@app.post (
    f"/{api_version}/mine",
    methods=["POST"],
    responses=\
    {
        200: BlockedMinedResponse,
        400: ValidationErrorModel
    },
    summary="Mine a new block and add to the blockchain", 
    tags=[blocker_tag],
    doc_ui=True
)
def mine_block():
    previous_block = blocker.print_previous_block()
    previous_proof = previous_block["proof"]
    proof = blocker.proof_of_work(previous_proof)
    previous_hash = blocker.hash(previous_block)
    block = blocker.create_block(proof, previous_hash)

    response = {
        "message": "A block is MINED",
        "index": block["index"],
        "timestamp": block["timestamp"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"]
    }

    return jsonify(response), 200



@app.get (
    f"/{api_version}/get_chain",
    methods=["GET"],
    responses=\
    {
        200: GetChainResponse,
        404: NotFoundResponse
    },
    summary="Get the entire blockchain", 
    tags=[blocker_tag],
    doc_ui=True
)
def display_chain():
    response = \
    {
        "chain": blocker.chain,
        "length": len(blocker.chain)
    }
    return jsonify(response), 200



@app.get (
    f"/{api_version}/validate",
    methods=["GET"],
    responses=
    {
        200: ValidateResponse,
        403: ServiceUnavailable
    }, 
    summary="Validate the blockchain", 
    tags=[blocker_tag],
    doc_ui=True
)
def validate_blockchain():
    valid = blocker.chain_valid(blocker.chain)

    if valid:
        response = {"message": "The Blockchain is valid."}
    else:
        response = {"message": "The Blockchain is not valid."}
    return jsonify(response), 200



@app.get (
    "/health",
    methods=["GET"],
    responses=
    {
        200: {"content": {"application/json": {"schema": {"type": "string"}}}}
    },
    summary="Check if the API is online", 
    tags=[operations_tag],
    doc_ui=True
)
def status():
    response = {"status": "ok"}
    return jsonify(response), 200

@app.post (
    "/insert",
    methods=["POST"],
    responses=
    {
        200: {"content": {"application/json": {"schema": {"type": "string"}}}}
    },
    tags=[database_tag]
)
def create():
    item_name = request.json["name"]
    blocker_collection.insert_one({"name": item_name})
    response = {"status": "ok"}
    return jsonify(response), 200

@app.get(
    "/read",
    methods=["GET"],
    responses=
    {
        200: {"content": {"application/json": {"schema": {"type": "string"}}}}
    },
    tags=[database_tag]
)
def readall():
    items = []
    for item in blocker_collection.find():
        items.append(item)
    return parse_json(items), 200

@app.get(
    "/read/<string:blocker_id>",
    methods=["GET"],
    responses=
    {
        200: {"content": {"application/json": {"schema": {"type": "string"}}}}
    },
    tags=[database_tag]
)
def readone():
    items = []
    for item in blocker_collection.find():
        items.append(item)
    return parse_json(items), 200

@app.get(
    "/delete/<string:blocker_id>",
    methods=["GET"],
    responses=
    {
        200: {"content": {"application/json": {"schema": {"type": "string"}}}},
        404: {"content": {"application/json": {"schema": {"type": "string"}}}}
    },
    tags=[database_tag]
)
def delete(blocker_id):
    blocker_collection.delete_one({'_id': ObjectId(blocker_id)})
    response = {"status": "ok"}
    return response, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0", 
        port=5050,
        debug=True
    ) 
