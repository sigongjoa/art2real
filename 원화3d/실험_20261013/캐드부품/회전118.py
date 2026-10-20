# 판정기준118 — 회전(시점) 맞추기 + 화소 비교기: 후보마다 방위 12 × 고도 3 렌더 → 입력(155°)과 실루엣 IoU 최대 시점 → 그 시점에서 실루엣 IoU × 모서리 F 로 1 등 · 10-20
# 사용(cadrille venv · ART_MEM_GB=10): 회전118.py → out/설명/캐드부품/임베딩117/회전118.json
import json, numpy as np, cv2
import 설계116 as S, 데이터117 as Q
D = Q.D; 방위 = list(range(0, 360, 30)); 고도 = [15, 25, 35]
def 실루엣(img): return img.min(-1) < 250
def 모서리(img): return cv2.Canny(cv2.GaussianBlur(img, (3, 3), 0), 40, 120) > 0
def F(a, b, r=2):
    k = np.ones((2 * r + 1, 2 * r + 1), np.uint8); ad, bd = cv2.dilate(a.astype(np.uint8), k) > 0, cv2.dilate(b.astype(np.uint8), k) > 0
    p = (a & bd).sum() / max(a.sum(), 1); q = (b & ad).sum() / max(b.sum(), 1); return 2 * p * q / max(p + q, 1e-9)
def 맞추기(m, 입):   # → (점수, 방위, 고도)
    s0, e0 = 실루엣(입), 모서리(입); best = (-1, 0, 0)
    for e in 고도:
        for a in 방위:
            img, _ = Q.렌더(m, a, e); s = 실루엣(img); iou = (s & s0).sum() / max((s | s0).sum(), 1)
            if iou > best[0]: best = (iou, a, e, img)
    iou, a, e, img = best; return iou * F(모서리(img), e0), a, e, iou
if __name__ == "__main__":
    색 = json.load(open(D + "색인.json", encoding="utf-8")); 결 = {"T1": [], "T2": []}; 오차 = []; 종류별 = {}
    사양 = lambda c: json.loads(c["코드"])
    for t, r in enumerate(색):
        입 = cv2.imdecode(np.fromfile(D + "렌더/" + r["정답"]["이름"] + "_155.png", np.uint8), 1)[..., ::-1].copy()
        캐 = {}
        def 점(c):
            if c["이름"] not in 캐: m, *_ = S.메시(S.짓기(사양(c))); 캐[c["이름"]] = 맞추기(m, 입)
            return 캐[c["이름"]]
        for 과 in ("T1", "T2"):
            후 = [r["정답"]] + r[과]; s = [점(c)[0] for c in 후]; 결[과].append(int(np.argmax(s) == 0))
            if 과 == "T2": 종류별.setdefault(r["정답"]["종류"], []).append(결[과][-1])
        _, a, e, _ = 점(r["정답"]); 대칭 = r["정답"]["종류"] != "상자" and not 사양(r["정답"])["특징"] and not 사양(r["정답"])["기울임"]
        오차.append((min(abs(a - 155) % 360, 360 - abs(a - 155) % 360), e - 25, 대칭))
        print(t, r["정답"]["종류"], "T1", 결["T1"][-1], "T2", 결["T2"][-1], "시점", a, e, flush=True)
    방 = np.array([o[0] for o in 오차 if not o[2]]); 결과 = {"T1": float(np.mean(결["T1"])), "T2": float(np.mean(결["T2"])), "시점 방위 오차 중앙(비대칭 부품)": float(np.median(방)) if len(방) else None,
        "시점 방위 ≤ 15° 몫(비대칭)": float((방 <= 15).mean()) if len(방) else None, "고도 맞음 몫": float(np.mean([o[1] == 0 for o in 오차])), "T2 종류별": {k: round(float(np.mean(v)), 2) for k, v in 종류별.items()}}
    print(json.dumps(결과, ensure_ascii=False, indent=1)); json.dump(결과, open(D + "회전118.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
