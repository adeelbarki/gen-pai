import redis
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query as RedisQuery
from redis.exceptions import ResponseError


INDEX_NAME = "symptom_index"
VECTOR_DIM = 1536
VECTOR_FIELD_NAME = "embedding"
DISTANCE_METRIC = "COSINE"

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=False,
)

def ensure_symptom_index_exists():
    try:
        r.ft(INDEX_NAME).info()

    except ResponseError as e:
        if "no such index" in str(e).lower():
            print(f"⚠️ Index '{INDEX_NAME}' not found. Creating it now...")
            r.ft(INDEX_NAME).create_index(
                fields=[
                    TextField("symptom"),
                    TextField("questions"),
                    VectorField("embedding", "FLAT", {
                        "TYPE": "FLOAT32",
                        "DIM": VECTOR_DIM,
                        "DISTANCE_METRIC": DISTANCE_METRIC
                    })
                ],
                definition=IndexDefinition(prefix=["symptom:"], index_type=IndexType.HASH)
            )
            print(f"✅ Created index '{INDEX_NAME}'")
        else:
            raise e
        
