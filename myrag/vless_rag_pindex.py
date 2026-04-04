"""
Page-Indexed Vectorless RAG with PDF files
==========================================
Sends each PDF page as a separate document block with page metadata.
Claude can then cite exact page numbers in its answers.

Install deps:
    pip install anthropic pymupdf

Usage:
    python page_indexed_rag.py                        # interactive REPL
    python page_indexed_rag.py --query "What is X?"  # single query
    python page_indexed_rag.py --pdf report.pdf --pdf paper.pdf --query "Summarise"
"""

import base64
from dataclasses import dataclass, field
from pathlib import Path
import os
import glob

import anthropic
import fitz  # PyMuPDF
from dotenv import load_dotenv  # only needed locally


load_dotenv()
claude_key = os.environ.get("my_claude_key")


# ── Data structures ────────────────────────────────────────────────────────────
@dataclass
class PageBlock:
    """A single PDF page encoded as base64 with metadata."""
    doc_name: str
    page_num: int          # 1-based
    total_pages: int
    b64_data: str          # base64-encoded page PDF bytes
    text_preview: str      # first 200 chars of extracted text (for logging)


@dataclass
class RAGIndex:
    """The 'index' — just a list of page blocks, ordered by (doc, page)."""
    pages: list[PageBlock] = field(default_factory=list)

    @property
    def doc_names(self) -> list[str]:
        seen = []
        for p in self.pages:
            if p.doc_name not in seen:
                seen.append(p.doc_name)
        return seen

    def pages_for_doc(self, doc_name: str) -> list[PageBlock]:
        return [p for p in self.pages if p.doc_name == doc_name]


# ── Indexing ───────────────────────────────────────────────────────────────────

def index_pdf(path: str | Path) -> list[PageBlock]:
    """
    Open a PDF with PyMuPDF, extract each page as its own single-page PDF,
    encode to base64, and return a list of PageBlocks.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(str(path))
    blocks = []

    for page_num in range(len(doc)):
        # Create a new single-page PDF for this page
        single = fitz.open()
        single.insert_pdf(doc, from_page=page_num, to_page=page_num)
        page_bytes = single.write()
        single.close()

        b64 = base64.standard_b64encode(page_bytes).decode()

        # Extract plain text for preview/logging
        page = doc[page_num]
        text = page.get_text().strip()
        preview = text[:200].replace("\n", " ") if text else "(no extractable text)"

        blocks.append(PageBlock(
            doc_name=path.name,
            page_num=page_num + 1,
            total_pages=len(doc),
            b64_data=b64,
            text_preview=preview,
        ))

    doc.close()
    print(f"  Indexed '{path.name}': {len(blocks)} pages")
    return blocks


def build_index(pdf_paths: list[str | Path]) -> RAGIndex:
    """Index one or more PDFs into a RAGIndex."""
    index = RAGIndex()
    for path in pdf_paths:
        index.pages.extend(index_pdf(path))
    return index


# ── Prompt building ────────────────────────────────────────────────────────────

def build_message_content(index: RAGIndex, question: str) -> list[dict]:
    """
    Build the `content` list for a Claude API message.

    Structure:
      [page_doc_block_1, page_doc_block_2, ..., question_text_block]

    Each page document block carries a title like:
      "[doc=report.pdf | page=3/18]"
    so the model can reference exact locations in its answer.
    """
    content = []

    for page in index.pages:
        title = f"[doc={page.doc_name} | page={page.page_num}/{page.total_pages}]"
        content.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": page.b64_data,
            },
            "title": title,
            # Cache the document blocks for efficiency on repeated questions
            "cache_control": {"type": "ephemeral"},
        })

    content.append({
        "type": "text",
        "text": question,
    })

    return content


SYSTEM_PROMPT = """You are a precise document assistant with access to PDF documents,
provided one page at a time. Each page is labelled [doc=<filename> | page=<n>/<total>].

When answering:
- Always cite your sources using the format: (doc.pdf, p.N) or (doc.pdf, pp.N-M)
- If the answer spans multiple documents or pages, cite each one
- If the answer is not found in any page, say so explicitly
- Be concise but complete
"""


# ── Query engine ───────────────────────────────────────────────────────────────

class PageIndexedRAG:
    """
    Vectorless RAG engine that maintains conversation history across turns.eh
    All page blocks are re-sent on every turn (prompt caching makes this cheap).
    """
    def __init__(self, index: RAGIndex, model: str = "claude-opus-4-5"):
        self.index = index
        self.model = model
        self.client = anthropic.Anthropic(api_key=claude_key)

        self.history: list[dict] = []

        total = len(index.pages)
        docs = len(index.doc_names)
        print(f"\nRAG ready: {docs} doc(s), {total} page(s) indexed")
        print(f"Model: {model}")
        print(f"Documents: {', '.join(index.doc_names)}\n")

    def query(self, question: str, verbose: bool = False) -> str:
        """
        Ask a question. The full page index is injected into every API call.
        Conversation history is maintained for follow-up questions.
        """
        # Build user message with all page blocks + question
        user_content = build_message_content(self.index, question)
        print("Content count", user_content)

        self.history.append({"role": "user", "content": user_content})

        if verbose:
            page_count = len(self.index.pages)
            print(f"  [Sending {page_count} page blocks + question to API...]")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=self.history,
        )

        answer = response.content[0].text

        # Add assistant reply to history (text only — no need to re-store pages)
        self.history.append({"role": "assistant", "content": answer})

        if verbose:
            usage = response.usage
            print(f"  [Tokens — input: {usage.input_tokens}, output: {usage.output_tokens}]")
            if hasattr(usage, "cache_read_input_tokens"):
                print(f"  [Cache read: {usage.cache_read_input_tokens} tokens]")

        return answer

    def reset_history(self):
        """Clear conversation history to start a fresh session."""
        self.history = []
        print("  Conversation history cleared.")


# ── Selective page retrieval (optional optimisation) ──────────────────────────
def filter_pages_by_keyword(index: RAGIndex, keywords: list[str]) -> RAGIndex:
    """
    Optional: pre-filter pages to those containing at least one keyword.
    Useful for very large PDFs where you want to reduce token usage.
    This is the only 'retrieval' step — done via text search, not vectors.
    """
    keywords_lower = [k.lower() for k in keywords]
    filtered = RAGIndex()
    for page in index.pages:
        if any(kw in page.text_preview.lower() for kw in keywords_lower):
            filtered.pages.append(page)

    kept = len(filtered.pages)
    total = len(index.pages)
    print(f"  Keyword filter: {kept}/{total} pages retained")
    return filtered if filtered.pages else index  # fallback to full index


def run_demo(index: RAGIndex, query: str):
    """Run a small demo with preset questions."""
    rag = PageIndexedRAG(index)
    answer = rag.query(query, verbose=True)
    print(f"A: {answer}\n")
    print("-" * 60 + "\n")
    return answer


def fetch_query(folder_path: str, query: str):
    # ── Build index ────────────────────────────────────────────────────────────
    print("\nIndexing PDFs...")
    pdf_files = glob.glob(folder_path + "/*.pdf")
    index = build_index(pdf_files)
    return run_demo(index, query)


# print("Starting")
#
# qry = "what are council rates"
# fetch_query("/Users/venu/venus/ai_samples/file-upload/uploads/docs", qry)


