# 감사126 S4-2 — 옮긴 3면도 → 얼린 EmbeddingGemma 2(모델124.임베딩 과 같은 호출) · gemma_venv 에서 · 10-22
import json, numpy as np, torch
from sentence_transformers import SentenceTransformer
D = "G:/art2real/out/설명/캐드부품/감사126/옮김/"; 뷰 = ("위", "앞", "옆")
ns = json.load(open(D + "목록.json")); m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16})
e = m.encode([{"text": "<|image|>", "image": [D + f"{n}_{v}.png"]} for n in ns for v in 뷰], normalize_embeddings=True, batch_size=16)
np.savez(D + "임베딩.npz", E=np.asarray(e, np.float32).reshape(len(ns), 3, -1), 이름=np.array(ns)); print("끝", len(ns))
