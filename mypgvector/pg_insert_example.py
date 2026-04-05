
from langchain_text_splitters import RecursiveCharacterTextSplitter
from myai.my_open_ai_ref import embedding_data_for_str
from pg_vector_util import pg_create_table_index, pg_execute_many, pg_execute

model_name = "text-embedding-3-small"


def pg_vector_chunks(filename):
    # load example document "/Users/venu/sample_text.txt"
    with open(filename) as file:
        # set a really small chunk size, just to show
        file_data = file.read()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=20, length_function=len,
                                                   is_separator_regex=False)
    texts = text_splitter.create_documents([file_data])
    print("texts size,", len(texts))
    insert_data = []
    for text_date in texts:
        embedding = embedding_data_for_str(model_name, text_date.page_content)
        insert_data.append((text_date.page_content, embedding))
    return insert_data


embed_table = """
CREATE TABLE IF NOT EXISTS myrag (
    id SERIAL PRIMARY KEY,
    text VARCHAR(2000) NOT NULL,
    embedding vector(512) -- vector data
);"""

# pg_create_table_index(embed_table)

myrag_index = """
CREATE INDEX IF NOT EXISTS myrag_embedding_idx
ON myrag
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);"""

# pg_create_table_index(myrag_index)

vector_chunks = pg_vector_chunks("/Users/venu/sample_text.txt")

insert_statement = "INSERT INTO myrag (text, embedding) VALUES (%s, %s)"

# pg_execute_many(insert_statement, vector_chunks)

query_embedding = embedding_data_for_str(model_name, "sodales at quam")

# -- Cosine distance (recommended for text embeddings)
# embedding <=> %s::vector

# -- Euclidean (L2)
# embedding <-> %s::vector

# -- Inner product
# embedding <#> %s::vector


query = """
SELECT id, text, embedding <-> %s::vector AS distance
FROM myrag
ORDER BY distance
LIMIT 2;
"""
response = pg_execute(query, query_embedding)
print(response)


