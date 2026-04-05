from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv  # only needed locally

load_dotenv()

# | OpenAI Model                      | Dimension |
# | --------------------------------- | --------- |
# | `text-embedding-3-large`          | **3072**  |
# | `text-embedding-3-small`          | **1536**  |
# | `text-embedding-ada-002` (legacy) | **1536**  |
# | `text-embedding-3-large-1` (new)  | **1024**  |
# | `multimodal-embedding-1` (new)    | **768**   | (text + image + audio)

open_ai_key = os.environ.get("OPEN_AI_KEY")
client = OpenAI(api_key=open_ai_key)


def get_dimension(model_name):
    if model_name == "text-embedding-3-large":
        return 3072
    elif model_name == "text-embedding-3-large-1":
        return 1536
    elif model_name == "text-embedding-3-small":
        return 512
    elif model_name == "multimodal-embedding-1":
        return 768
    else:
        return 100


def embedding_data(model_name, input_data):
    embedding = client.embeddings.create(
        model=model_name,  # example "text-embedding-3-large",
        input=input_data,
        encoding_format="float",
        dimensions=get_dimension(model_name)
    ).data[0].embedding
    return embedding


def embedding_data_for_str(model_name, input_data: str):
    embedding = client.embeddings.create(
        model=model_name,  # example "text-embedding-3-large",
        input=input_data,
        encoding_format="float",
        dimensions=get_dimension(model_name)
    ).data[0].embedding
    return embedding


def get_query_embedding(query, model="text-embedding-3-small", dim=512):
    embeddings = OpenAIEmbeddings(api_key=open_ai_key, model=model, dimensions=dim)
    return embeddings.embed_query(query)



