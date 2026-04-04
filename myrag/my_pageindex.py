# https://docs.pageindex.ai/
# https://pageindex.ai   (API Key)
# https://www.youtube.com/watch?v=SmCDsF7r_zU
import os
from pageindex import PageIndexClient
import openai
import pageindex.utils as utils
from dotenv import load_dotenv
import time
import json

load_dotenv()

# Get your PageIndex API key from https://dash.pageindex.ai/api-keys
PAGEINDEX_API_KEY = os.getenv("page_index_key")
pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
pdf_path = "/Users/venu/venus/ai_samples/file-upload/uploads/docs/DischargeForm.pdf"


async def call_llm(prompt, model="gpt-4.1-mini", temperature=0):
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content.strip()


def read_pdf(doc_path:str):
    print("pdf file path:", doc_path)
    result = pi_client.submit_document(doc_path)
    doc_id = result["doc_id"]
    print('Document Submitted:', doc_id)

    print("Waiting for document to be processed...")
    # while not pi_client.is_retrieval_ready(doc_id):
    #     status = pi_client.get_document(doc_id)["status"]
    #     print("Still processing... retrying in 10 seconds - status", status)
    #     time.sleep(10)

    while pi_client.get_document(doc_id)["status"] != "completed":
        print("Still processing... retrying in 10 seconds ")
        time.sleep(1)

    tree = pi_client.get_tree(doc_id, node_summary=True)
    print('Simplified Tree Structure of the Document:', tree['result'])
    utils.print_tree(tree)
    return doc_id

print("starting...")
doc_tree_id = read_pdf(pdf_path)
response = pi_client.chat_completions(
    messages=[{"role": "user", "content": "What is discharge form?"}],
    doc_id=doc_tree_id
)

print(response["choices"][0]["message"]["content"])


# query = "What is Discharge Form?"
#
# tree_without_text = utils.remove_fields(tree.copy(), fields=['text'])
#
# search_prompt = f"""
# You are given a question and a tree structure of a document.
# Each node contains a node id, node title, and a corresponding summary.
# Your task is to find all nodes that are likely to contain the answer to the question.
#
# Question: {query}
#
# Document tree structure:
# {json.dumps(tree_without_text, indent=2)}
#
# Please reply in the following JSON format:
# {{
#     "thinking": "<Your thinking process on which nodes are relevant to the question>",
#     "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
# }}
# Directly return the final JSON structure. Do not output anything else.
# """
#
# tree_search_result = await call_llm(search_prompt)
# print(tree_search_result)
#
# node_map = utils.create_node_mapping(tree)
# tree_search_result_json = json.loads(tree_search_result)
#
# print('Reasoning Process:')
# utils.print_wrapped(tree_search_result_json['thinking'])
#
# print('\nRetrieved Nodes:')
# for node_id in tree_search_result_json["node_list"]:
#     node = node_map[node_id]
#     print(f"Node ID: {node['node_id']}\t Page: {node['page_index']}\t Title: {node['title']}")
#
# node_list = tree_search_result_json["node_list"]
# relevant_content = "\n\n".join(node_map[node_id]["text"] for node_id in node_list)
#
# print('Retrieved Context:\n')
# utils.print_wrapped(relevant_content[:1000] + '...')
#
# answer_prompt = f"""
# Answer the question based on the context:
#
# Question: {query}
# Context: {relevant_content}
#
# Provide a clear, concise answer based only on the context provided.
# """
#
# print('Generated Answer:\n')
# answer = await call_llm(answer_prompt)
# utils.print_wrapped(answer)
#
#
# async def ask(query):
#     tree_without_text = utils.remove_fields(tree.copy(), fields=['text'])
#     search_prompt = f"""
#     You are given a question and a tree structure of a document.
#     Each node contains a node id, node title, and a corresponding summary.
#     Your task is to find all nodes that are likely to contain the answer to the question.
#     Question: {query}
#
#     Document tree structure:
#     {json.dumps(tree_without_text, indent=2)}
#
#     Please reply in the following JSON format:
#     {{
#         "thinking": "<Your thinking process on which nodes are relevant to the question>",
#         "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
#     }}
#     Directly return the final JSON structure. Do not output anything else.
#     """
#
#     search_result = await call_llm(search_prompt)
#     search_result_json = json.loads(search_result)
#
#     node_list = search_result_json["node_list"]
#     relevant_content = "\n\n".join(node_map[node_id]["text"] for node_id in node_list)
#
#     answer_prompt = f"""
#     Answer the question based on the context:
#
#     Question: {query}
#     Context: {relevant_content}
#
#     Provide a clear, concise answer based only on the context provided.
#     """
#
#     answer = await call_llm(answer_prompt)
#
#     print(f"Query: {query}")
#     print(f"\nRelevant Nodes: {node_list}")
#     print("\nAnswer:")
#     utils.print_wrapped(answer)
#     print("-" * 60)
#
# # --- Enter your query below and run this cell ---
# user_query = input("Enter your query: ")
# await ask(user_query)
#
