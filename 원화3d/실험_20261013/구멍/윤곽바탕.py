# 1c 바탕 — 선 그림의 「가장 바깥 닫힌 선」만 → 원이면 원 · 아니면 꺾은선(직선) → CadQuery 로 높이 10 밀기 · 안쪽 선(구멍 · 홈)은 버림(모델 몫) · 10-13
import numpy as np, cv2
import 캐드점수2 as K

def 바깥(그림):   # 그림(0~1, 128²) → (채운 마스크, 바깥 윤곽 점들)
    g = (그림 > .3).astype(np.uint8) * 255; g = cv2.morphologyEx(g, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))   # 선 끊김 메움
    cs, _ = cv2.findContours(g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
    m = np.zeros_like(g); cv2.drawContours(m, [c], -1, 255, -1); return m > 0, c[:, 0, :]
def 맞추기(c):   # 원인가(둥근 정도 · 반지름 흩어짐) → ("원", 중심, 반지름) | ("다각", 꼭짓점)
    (x, y), r = cv2.minEnclosingCircle(c.astype(np.float32)); d = np.hypot(c[:, 0] - x, c[:, 1] - y)
    if d.std() / d.mean() < .04: return ("원", (x, y), float(d.mean()))
    p = cv2.approxPolyDP(c.reshape(-1, 1, 2).astype(np.float32), 1.5, True)[:, 0, :]; return ("다각", p)
def 화소mm(v): return v / K.N * 2 * K.반 - K.반
def 짓기(그림):
    import cadquery as cq
    _, c = 바깥(그림); f = 맞추기(c)
    if f[0] == "원": (x, y), r = f[1], f[2]; return cq.Workplane("XY").center(화소mm(x), -화소mm(y)).circle(r / K.N * 2 * K.반).extrude(K.높), f
    pts = [(화소mm(x), -화소mm(y)) for x, y in f[1]]; return cq.Workplane("XY").polyline(pts).close().extrude(K.높), f

if __name__ == "__main__":   # 자기 검사: 합성 그림 20 장 — 바탕 IoU(바탕만의 윗면 vs 정답 바탕 윗면)
    g = np.random.default_rng(5); s = []
    for _ in range(20):
        p = K.무작위(g); q = dict(p); q["칸"] = [(0, 0, 0, 0, 0)] * 3; 정 = K.윗면(K.짓기(q)); 바, f = 짓기(K.그림(p)); 우 = K.윗면(바)
        s.append((정 & 우).sum() / (정 | 우).sum())
    print("바탕 IoU 평균 %.3f · 최소 %.3f" % (np.mean(s), np.min(s))); assert np.min(s) > .95
