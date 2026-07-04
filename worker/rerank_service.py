import os
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import CrossEncoder

app = FastAPI()
model = CrossEncoder(os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"))


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_k: int = 5

class Scored(BaseModel):
    index: int
    score: float

@app.post("/rerank")
def rerank(req: RerankRequest):
    pairs = [(req.query, doc) for doc in req.documents]
    scores = model.predict(pairs)
    ranked = sorted(
        [Scored(index=i, score=float(s)) for i,s in enumerate(scores)],
        key = lambda x: x.score,
        reverse=True,
    )
    return {"results" : ranked[: req.top_k]}