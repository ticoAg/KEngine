# We provide the advanced preproc tokenization for reranking.
from BCEmbedding.tools.langchain import BCERerank

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.faiss import FAISS

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.retrievers import ContextualCompressionRetriever
import asyncio
import os
from pathlib import Path

os.environ["all_proxy"] = "http://127.0.0.1:8888"

# init embedding model
embedding_model_name = "maidalun1020/bce-embedding-base_v1"
embedding_model_kwargs = {"device": "cuda:0"}
embedding_encode_kwargs = {"batch_size": 32, "normalize_embeddings": True}

embed_model = HuggingFaceEmbeddings(
    model_name=embedding_model_name, model_kwargs=embedding_model_kwargs, encode_kwargs=embedding_encode_kwargs
)
embed_model.show_progress = False

reranker_args = {"model": "maidalun1020/bce-reranker-base_v1", "top_n": 5, "device": "cuda:0"}
reranker = BCERerank(**reranker_args)


texts = []
dir_path = Path("example_data")
for path in dir_path.glob("*.pdf"):
    documents = PyPDFLoader(path.as_posix()).load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    texts += text_splitter.split_documents(documents)

# example 1. retrieval with embedding and reranker
retriever = FAISS.from_documents(texts, embed_model, distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT).as_retriever(
    search_type="similarity", search_kwargs={"score_threshold": 0.3, "k": 100}
)
compression_retriever = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=retriever)

async def task(i):
    results = await compression_retriever.aget_relevant_documents("What is Llama 2?")
    print(results)

async def main():
    task_list = []
    for i in range(10):
        task_list.append(asyncio.create_task(task(i)))
  
    for i in asyncio.as_completed(task_list):
        await i

asyncio.run(main())