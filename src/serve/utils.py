import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from starlette.responses import RedirectResponse

from configs import config
from src.serve.model_worker import embeddings_pool
from src.serve.openai_api_server import (
    EmbeddingsRequest,
    EmbeddingsResponse,
    UsageInfo,
    create_error_response,
    process_input,
)


def parse_args():
    parser = argparse.ArgumentParser(description="KEngine Embedding Server")
    parser.add_argument("--host", default=config.server.host, type=str, help="Host address")
    parser.add_argument("--port", default=config.server.port, type=int, help="Port number")
    parser.add_argument("--allow-credentials", type=bool, default=True, help="allow credentials")
    parser.add_argument("--allowed-origins", type=json.loads, default=["*"], help="allowed origins")
    parser.add_argument("--allowed-methods", type=json.loads, default=["*"], help="allowed methods")
    parser.add_argument("--allowed-headers", type=json.loads, default=["*"], help="allowed headers")
    parser.add_argument(
        "--api-keys",
        type=lambda s: s.split(","),
        help="Optional list of comma separated API keys",
    )

    args = parser.parse_args()
    return args


async def document():
    return RedirectResponse(url="/docs")


async def get_embedding(payload: Dict[str, Any]):
    model_name = payload.get("model", config.embedding.default)
    embed_model = embeddings_pool.load_embeddings(model=model_name)
    embeddings = await embed_model.aembed_documents(payload["input"])
    return {"embedding": embeddings, "token_num": len("".join(payload["input"])), "error_code": 0, "text": ""}


async def create_embeddings(request: EmbeddingsRequest, model_name: str = None) -> EmbeddingsResponse:
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
