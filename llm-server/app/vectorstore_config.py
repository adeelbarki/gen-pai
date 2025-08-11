from langchain_redis import RedisVectorStore
from langchain_redis.config import RedisConfig
from redis import Redis
from langchain_openai import OpenAIEmbeddings

RAG_INDEX_NAME = "symptom_question_rag"
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

config = RedisConfig(
    index_name=RAG_INDEX_NAME,
    dimensions=1536,
    distance_metric="COSINE",
    vector_index_type="FLAT",
    vector_datatype="FLOAT32",
    # make metadata filterable
    metadata_schema=[
        {"name": "symptom", "type": "tag"},
        {"name": "section", "type": "tag"},
    ],
    key_prefix="doc"
)

vectorstore = RedisVectorStore(
    redis_url="redis://localhost:6379",
    config=config,
    embeddings=embedding_model,
)