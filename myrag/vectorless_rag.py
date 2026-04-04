from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import pdfplumber
import os
from dotenv import load_dotenv  # only needed locally

load_dotenv()

open_ai_key = os.environ.get("OPEN_AI_KEY")
client = OpenAI(api_key=open_ai_key)


class VectorlessRetriever:
    def __init__(self, chunks):
        self.texts = [c["text"] for c in chunks]
        self.metadata = chunks

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_vectors = self.vectorizer.fit_transform(self.texts)

    def search(self, query, top_k=5):
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_vectors)[0]

        top_indices = scores.argsort()[-top_k:][::-1]

        results = []
        for i in top_indices:
            results.append({
                "text": self.texts[i],
                "source": self.metadata[i]["source"],
                "score": scores[i]
            })

        return results


def load_pdf(pdf_file):
    docs = []
    print("File Path :", os.getcwd() + pdf_file)
    text = ""
    with pdfplumber.open(os.getcwd() + pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    docs.append({
        "source": pdf_file,
        "content": text
    })

    return docs


def load_pdfs(pdf_folder):
    docs = []

    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            path = os.path.join(pdf_folder, file)
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            docs.append({
                "source": file,
                "content": text
            })

    return docs


def chunk_text(docs, chunk_size=500, overlap=100):
    chunks = []

    for doc in docs:
        text = doc["content"]
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            chunks.append({
                "text": chunk,
                "source": doc["source"]
            })

            start += chunk_size - overlap

    return chunks


def generate_answer(query, results):
    context = "\n\n".join(
        [f"[Source: {r['source']}]\n{r['text']}" for r in results]
    )

    prompt = f"""
    Answer the question using ONLY the context below.
    If the answer is not found, say "I don't know".

    Context:
    {context}

    Question: {query}
    Answer:
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


def rag_response(pdf_file: str, query: str):
    print("inside rag_response :", pdf_file + " : " + query)
    # Step 1: Load PDFs
    docs = load_pdf("/uploads/docs/" + pdf_file)
    print("pdf file is :", docs)
    # Step 2: Chunk them
    chunks = chunk_text(docs)

    # Step 3: Build retriever
    retriever = VectorlessRetriever(chunks)
    results = retriever.search(query, top_k=5)
    answer = generate_answer(query, results)

    print("Top Results:")
    for r in results:
        print(f"- {r['source']} (score={r['score']:.3f})")

    return answer
