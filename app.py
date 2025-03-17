#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from blocker import Blocker

from flask import Flask, jsonify
from flask.wrappers import Response as FlaskResponse

from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
from flask_openapi3 import Info, Tag
from flask_openapi3 import OpenAPI, APIBlueprint

class ValidationErrorModel(BaseModel):
    code: int = Field(-1, description="Status Code")
    message: str = Field("Unauthorized!", description="Exception ValidationErrorModel")

class Unauthorized(BaseModel):
    code: int = Field(-1, description="Status Code")
    message: str = Field("Unauthorized!", description="Exception Unauthorized")

class ServiceUnavailable(BaseModel):
    code: int = Field(503, description="Status Code")
    message: str = Field("ServiceUnavailable!", description="Resource down - Service Unavailable")

class NotFoundResponse(BaseModel):
    code: int = Field(-1, description="Status Code")
    message: str = Field("NotFoundResponse!", description="Exception: NotFoundResponse")

class BlockedMinedResponse(BaseModel):
    message: str = Field()  #'message': 'A block is MINED',
    index: str = Field()#'index': block['index'],
    timestamp: str = Field()#'timestamp': block['timestamp'],
    proof: str = Field()#'proof': block['proof'],
    previous_hash: str = Field()#'previous_hash': block['previous_hash']

# Callbacks
def validation_error_callback(e: ValidationError) -> FlaskResponse:
    validation_error_object = ValidationErrorModel(code="400", message=e.json())
    response = make_response(validation_error_object.json())
    response.headers["Content-Type"] = "application/json"
    response.status_code = getattr(current_app, "validation_error_status", 422)
    return response

blocker = Blocker()
info = Info(title="Blocker - Blockchain API", version="1.0.0")

#app = Flask(__name__)
#app = OpenAPI(__name__, info=info)
app  = OpenAPI(
    __name__,
    validation_error_status=400,
    validation_error_model=ValidationErrorModel,
    validation_error_callback=validation_error_callback

)

jwt = \
{
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT"
}

tag = Tag \
(
    name='Blocker ', 
    description="Blocker a naive implementation of blockchain"
)

security_schemes = \
{
    "jwt": jwt
}

security = [
    {"jwt": []},
    {"oauth2": ["write:pets", "read:pets"]}
]

api = APIBlueprint \
(
    '/blocker',
    __name__,
    url_prefix='/api',
    abp_tags=[tag],
    abp_security=security,
    abp_responses={"401": Unauthorized},
    doc_ui=True
)

class MineBlock(BaseModel):
    message: int = Field("das", description='the id')
    index: Optional[int] = Field(None, ge=2, le=4, description='Age')
    timestamp: str = Field(None, min_length=2, max_length=4, description='Author')

class BlockerResponse(BaseModel):
    code: int = Field(0, description="Status Code")
    message: str = Field("ok", description="Exception Information")
    data: Optional[MineBlock]

@app.post \
(
    "/mine_block",
    responses=\
    {
        200: BlockedMinedResponse,
        400: ValidationErrorModel
    },
    doc_ui=True
)
def mine_block():
    previous_block = blocker.print_previous_block()
    previous_proof = previous_block['proof']
    proof = blocker.proof_of_work(previous_proof)
    previous_hash = blocker.hash(previous_block)
    block = blocker.create_block(proof, previous_hash)

    response = BlockedMinedResponse(
        message = "A block is mined",
        index = block["index"],
        timestamp = block["timestamp"],
        proof = block["proof"],
        previous_hash = block["previous_hash"]
    )

    #response = {
    #    'message': 'A block is MINED',
    #    'index': block['index'],
    #    'timestamp': block['timestamp'],
    #    'proof': block['proof'],
    #    'previous_hash': block['previous_hash']
    #}

    return jsonify(response), 200

@app.get \
(
    '/get_chain', 
    methods=['GET'],
    responses={404: NotFoundResponse},
    doc_ui=True
)
def display_chain():
    response = {'chain': blocker.chain,
                'length': len(blocker.chain)}
    return jsonify(response), 200

@app.get \
(
    '/validate',
    methods=['GET'],
    responses={
        200: {"content": {"application/json": {"schema": {"type": "string"}}}},
        403: ServiceUnavailable
    }, 
    doc_ui=True
)
def validate():
    valid = blocker.chain_valid(blocker.chain)

    if valid:
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200



# Register API
app.register_api(api)

if __name__ == "__main__":
    app.run(
        host='127.0.0.1', 
        port=5000,
        debug=True
    ) 
