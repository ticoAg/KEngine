import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from configs import config
from src.protocol.api_protocol import BaseResponse

try:
    from pydantic.v1 import BaseSettings
except ImportError:
    from pydantic import BaseSettings

import argparse

import aiohttp
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from src.serve import (EmbeddingsRequest, EmbeddingsResponse, ErrorCode, UsageInfo, check_api_key,
                       check_model, create_error_response, embeddings_pool, process_input)

app = FastAPI()

fetch_timeout = aiohttp.ClientTimeout(total=3 * 3600)


async def document():
    return RedirectResponse(url="/docs")


async def fetch_remote(url, pload=None, name=None):
    async with aiohttp.ClientSession(timeout=fetch_timeout) as session:
        async with session.post(url, json=pload) as response:
            chunks = []
            if response.status != 200:
                ret = {
                    "text": f"{response.reason}",
                    "error_code": ErrorCode.INTERNAL_ERROR,
                }
                return json.dumps(ret)

            async for chunk, _ in response.content.iter_chunks():
                chunks.append(chunk)
        output = b"".join(chunks)

    if name is not None:
        res = json.loads(output)
        if name != "":
            res = res[name]
        return res

    return output


# @app.get("/v1/models", dependencies=[Depends(check_api_key)])
# async def show_available_models():
#     models = await fetch_remote(controller_address + "/list_models", None, "models")

#     models.sort()
#     # TODO: return real model permission details
#     model_cards = []
#     for m in models:
#         model_cards.append(ModelCard(id=m, root=m, permission=[ModelPermission()]))
#     return ModelList(data=model_cards)

app.get("/", response_model=BaseResponse, summary="swagger 文档")(document)


@app.post("/v1/embeddings", dependencies=[Depends(check_api_key)])
@app.post("/v1/engines/{model_name}/embeddings", dependencies=[Depends(check_api_key)])
async def create_embeddings(request: EmbeddingsRequest, model_name: str = None):
    """Creates embeddings for the text"""
    request.input = process_input(request.model, request.input)

    data = []
    token_num = 0
    batch_size = 32
    batches = [
        request.input[i : min(i + batch_size, len(request.input))] for i in range(0, len(request.input), batch_size)
    ]
    for num_batch, batch in enumerate(batches):
        payload = {
            "model": request.model,
            "input": batch,
            "encoding_format": request.encoding_format,
        }
        embedding = await get_embedding(payload)
        if "error_code" in embedding and embedding["error_code"] != 0:
            return create_error_response(embedding["error_code"], embedding["text"])
        data += [
            {
                "object": "embedding",
                "embedding": emb,
                "index": num_batch * batch_size + i,
            }
            for i, emb in enumerate(embedding["embedding"])
        ]
        token_num += embedding["token_num"]
    return EmbeddingsResponse(
        data=data,
        model=request.model,
        usage=UsageInfo(
            prompt_tokens=token_num,
            total_tokens=token_num,
            completion_tokens=None,
        ),
    ).dict(exclude_none=True)


async def get_embedding(payload: Dict[str, Any]):
    model_name = payload.get("model", config.embedding.default)
    embed_model = embeddings_pool.load_embeddings(model=model_name)
    embeddings = await embed_model.aembed_documents(payload["input"])
    return {"embedding": embeddings, "token_num": len("".join(payload["input"])), "error_code": 0, "text": ""}


def create_app():
    parser = argparse.ArgumentParser(description="KEngine Embedding Server")
    parser.add_argument("--host", default=config.server.host, type=str, help="Host address")
    parser.add_argument("--port", default=config.server.port, type=int, help="Port number")
    parser.add_argument("--allow-credentials", action="store_true", help="allow credentials")
    parser.add_argument("--allowed-origins", type=json.loads, default=["*"], help="allowed origins")
    parser.add_argument("--allowed-methods", type=json.loads, default=["*"], help="allowed methods")
    parser.add_argument("--allowed-headers", type=json.loads, default=["*"], help="allowed headers")
    parser.add_argument(
        "--api-keys",
        type=lambda s: s.split(","),
        help="Optional list of comma separated API keys",
    )

    args = parser.parse_args()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=args.allowed_origins,
        allow_credentials=args.allow_credentials,
        allow_methods=args.allowed_methods,
        allow_headers=args.allowed_headers,
    )
    return args


if __name__ == "__main__":
    args = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="debug")
