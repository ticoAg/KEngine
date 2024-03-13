import sys
from pathlib import Path

import numpy

sys.path.append(Path(__file__).parents[1].as_posix())
from configs import config
from src.serve import embeddings_pool
from src.utils.Logger import logger

embed_model = embeddings_pool.load_embeddings(model=config.embedding.default)
sentences = ["This is a test sentence", "Another test sentence"]
embeddings = embed_model.embed_documents(sentences)
logger.debug(numpy.array(embeddings).shape)
