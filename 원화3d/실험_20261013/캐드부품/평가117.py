# 판정기준117 평가 — (이미지 입력 = 턴테이블 155° 프레임 · 후보 렌더 = 35° — 정답 후보가 입력과 같은 그림이면 자명해서) EmbeddingGemma 2(학습 없음)로 입력(이미지 · 턴테이블 영상 · 글) 과 후보(렌더 · 코드 문자열)를 한 공간에 넣고 코사인 1 등 맞힘 · 대조 찍기 · 실루엣 IoU · 10-20
# 사용(gemma venv): 평가117.py → out/설명/캐드부품/임베딩117/결과.json
import json, numpy as np
from PIL import Image
D = "G:/art2real/out/설명/캐드부품/임베딩117/"
if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer
    import torch
    색 = json.load(open(D + "색인.json", encoding="utf-8"))
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda" if torch.cuda.is_available() else "cpu", model_kwargs={"torch_dtype": torch.bfloat16})
    캐 = {}
    import cv2
    def 다른시점(nm):   # 턴테이블 영상 5 번째 프레임(35 + 4 × 30 = 155°)
        if ("o", nm) not in 캐:
            c = cv2.VideoCapture(D + "영상/" + nm + ".mp4"); c.set(cv2.CAP_PROP_POS_FRAMES, 4); ok, fr = c.read(); c.release(); p = D + "렌더/" + nm + "_155.png"; cv2.imwrite(p, fr)
            캐[("o", nm)] = m.encode({"text": "<|image|>", "image": [p]}, normalize_embeddings=True)
        return 캐[("o", nm)]
    def 그림(nm):
        if ("g", nm) not in 캐: 캐[("g", nm)] = m.encode({"text": "<|image|>", "image": [D + "렌더/" + nm + ".png"]}, normalize_embeddings=True)
        return 캐[("g", nm)]
    def 영상(nm):
        if ("v", nm) not in 캐: 캐[("v", nm)] = m.encode({"text": "<|video|>", "video": D + "영상/" + nm + ".mp4"}, normalize_embeddings=True)
        return 캐[("v", nm)]
    def 글(t):
        if ("t", t) not in 캐: 캐[("t", t)] = m.encode(t, normalize_embeddings=True)
        return 캐[("t", t)]
    실 = lambda nm: np.unpackbits(np.load(D + "렌더/" + nm + "_실루엣.npy"))[:256 * 256].astype(bool)
    결 = {}
    for 과 in ("T1", "T2"):
        맞 = {}
        for r in 색:
            후 = [r["정답"]] + r[과]   # 0 번이 정답
            입 = {"이미지(다른 시점)": 다른시점(r["정답"]["이름"]), "영상": 영상(r["정답"]["이름"]), "글": 글(r["정답"]["글"])}
            표 = {"렌더": [그림(c["이름"]) for c in 후], "코드": [글(c["코드"]) for c in 후]}
            for 입이름, e in 입.items():
                for 표이름, es in 표.items():
                    s = [float(np.dot(np.ravel(e), np.ravel(x))) for x in es]; 맞.setdefault(f"{입이름}→{표이름}", []).append(int(np.argmax(s) == 0))
        결[과] = {k: round(float(np.mean(v)), 3) for k, v in 맞.items()}; 결[과]["찍기"] = round(1 / 6, 3)
    print(json.dumps(결, ensure_ascii=False, indent=1)); json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
