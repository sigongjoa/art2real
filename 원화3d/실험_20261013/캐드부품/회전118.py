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
def 맞추기(m, 입):   # → (점수, 방위, 고도, 실루엣 IoU) · 118b: 시점 점수도 실루엣 IoU × 모서리 F(실루엣만이면 회전 대칭 몸통의 구멍 자리를 못 봄) · 30° 격자 뒤 ±15° 를 5° 간격 · 고도 ±5°
    s0, e0 = 실루엣(입), 모서리(입)
    def 점(a, e):
        img, _ = Q.렌더(m, a, e); s = 실루엣(img); iou = (s & s0).sum() / max((s | s0).sum(), 1); return iou * F(모서리(img), e0), iou
    best = max(((점(a, e), a, e) for e in 고도 for a in 방위), key=lambda x: x[0][0])
    (sc, iou), a0, e0_ = best
    for e in (e0_ - 5, e0_, e0_ + 5):
        for a in range(a0 - 15, a0 + 16, 5):
            (s1, i1) = 점(a % 360, e)
            if s1 > sc: sc, iou, best = s1, i1, ((s1, i1), a % 360, e)
    return sc, best[1], best[2], iou
if __name__ == "__main__":
    색 = json.load(open(D + "색인.json", encoding="utf-8")); 결 = {"T1": [], "T2": []}; 엄 = {"T1": [], "T2": []}; 나눔 = {"T1": [], "T2": []}; 점수들 = {"T1": [], "T2": []}; 오차 = []; 종류별 = {}
    사양 = lambda c: json.loads(c["코드"])
    for t, r in enumerate(색):
        입 = cv2.imdecode(np.fromfile(D + "렌더/" + r["정답"]["이름"] + "_155.png", np.uint8), 1)[..., ::-1].copy()
        캐 = {}
        def 점(c):
            if c["이름"] not in 캐: m, *_ = S.메시(S.짓기(사양(c))); 캐[c["이름"]] = 맞추기(m, 입)
            return 캐[c["이름"]]
        for 과 in ("T1", "T2"):
            후 = [r["정답"]] + r[과]; s = np.array([점(c)[0] for c in 후]); 결[과].append(int(np.argmax(s) == 0))
            동 = np.isclose(s, s.max(), atol=1e-6); 엄[과].append(int(동[0] and 동.sum() == 1)); 나눔[과].append(float(동[0]) / 동.sum()); 점수들[과].append(s.round(4).tolist())   # 118b 재채점: 동점이면 argmax 가 늘 0 번(정답)을 골랐음 → 엄격(혼자 1 등) · 나눔(동점 k 개면 1/k)
            if 과 == "T2": 종류별.setdefault(r["정답"]["종류"], []).append(결[과][-1])
        _, a, e, _ = 점(r["정답"]); 대칭 = r["정답"]["종류"] != "상자" and not 사양(r["정답"])["특징"] and not 사양(r["정답"])["기울임"]
        오차.append((min(abs(a - 155) % 360, 360 - abs(a - 155) % 360), abs(e - 25) <= 2, 대칭))
        print(t, r["정답"]["종류"], "T1", 결["T1"][-1], "T2", 결["T2"][-1], "시점", a, e, flush=True)
    방 = np.array([o[0] for o in 오차 if not o[2]]); 결과 = {"T1": float(np.mean(결["T1"])), "T2": float(np.mean(결["T2"])), "T2 엄격(동점 = 틀림)": float(np.mean(엄["T2"])), "T2 나눔(동점 1/k)": float(np.mean(나눔["T2"])), "T1 엄격": float(np.mean(엄["T1"])), "T2 동점 있었던 부품": int(sum(len(x) and np.isclose(np.array(x), max(x), atol=1e-6).sum() > 1 for x in 점수들["T2"])), "점수들": 점수들, "시점 방위 오차 중앙(비대칭 부품)": float(np.median(방)) if len(방) else None,
        "시점 방위 ≤ 15° 몫(비대칭)": float((방 <= 15).mean()) if len(방) else None, "고도 맞음 몫": float(np.mean([o[1] for o in 오차])), "T2 종류별": {k: round(float(np.mean(v)), 2) for k, v in 종류별.items()}}
    print(json.dumps(결과, ensure_ascii=False, indent=1)); json.dump(결과, open(D + "회전118b_재채점.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
