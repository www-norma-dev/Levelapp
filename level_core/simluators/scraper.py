"""
Async page scraper and chunker for RAG.
"""
from typing import List

import httpx
from bs4 import BeautifulSoup

from .rag_schemas import ChunkInfo
from .event_collector import log_rag_event


async def scrape_page(page_url: str, chunk_size: int) -> List[ChunkInfo]:
    """Scrape a page and return paragraph-based chunks."""
    log_rag_event("INFO", f"Scraping page: {page_url}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.get(page_url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    paras = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    full_text = "\n".join(paras)

    if full_text:
        preview = full_text[:400] + ("..." if len(full_text) > 400 else "")
        log_rag_event("INFO", f"SCRAPE_PREVIEW ({len(full_text)} chars): {preview}")

    # Create paragraph-based chunks to keep text readable and reorderable
    chunks: List[ChunkInfo] = []
    current: List[str] = []
    current_len = 0
    sep = "\n\n"  # separate paragraphs inside a chunk

    for para in paras:
        p_len = len(para)
        if current_len == 0:
            # start a new chunk
            current = [para]
            current_len = p_len
        else:
            projected = current_len + len(sep) + p_len
            if projected > chunk_size:
                chunk_content = sep.join(current)
                word_count = len(chunk_content.split())
                chunks.append(ChunkInfo(index=len(chunks), content=chunk_content, word_count=word_count))
                current = [para]
                current_len = p_len
            else:
                current.append(para)
                current_len = projected

    if current_len > 0:
        chunk_content = sep.join(current)
        word_count = len(chunk_content.split())
        chunks.append(ChunkInfo(index=len(chunks), content=chunk_content, word_count=word_count))

    log_rag_event("INFO", f"Created {len(chunks)} chunks from {page_url}")
    return chunks
