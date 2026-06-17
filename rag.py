import os
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from typing import List, Dict


class RAG:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(embedding_model)
        self.docs: List[Dict] = []
        self.embeddings = None
        key = os.getenv("OPENAI_API_KEY")
        if key:
            openai.api_key = key

    def add_documents(self, docs: List[Dict]):
        for d in docs:
            text = d.get("text") or d.get("content") or ""
            self.docs.append({"id": d.get("id"), "text": text, "meta": d.get("meta")})
        texts = [d["text"] for d in self.docs]
        if texts:
            self.embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        else:
            self.embeddings = None

    def retrieve(self, query: str, top_k: int = 3):
        if not self.docs:
            return []
        q_emb = self.model.encode([query], convert_to_numpy=True)[0]
        embs = self.embeddings
        sims = np.dot(embs, q_emb) / (np.linalg.norm(embs, axis=1) * np.linalg.norm(q_emb) + 1e-10)
        idx = np.argsort(-sims)[:top_k]
        return [{"id": self.docs[i]["id"] or i, "text": self.docs[i]["text"], "score": float(sims[i])} for i in idx]

    def generate_answer(self, query: str, top_k: int = 3, system_prompt: str = ""):
        context = self.retrieve(query, top_k)
        context_text = "\n\n".join([f"Document {r['id']}:\n{r['text']}" for r in context]) if context else "No context available."
        prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nUser question: {query}\n\nAnswer:"
        if not getattr(openai, 'api_key', None):
            return {"answer": "OPENAI_API_KEY not set. Set it to enable generation.", "context": context}
        resp = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )
        ans = resp["choices"][0]["message"]["content"].strip()
        return {"answer": ans, "context": context}
