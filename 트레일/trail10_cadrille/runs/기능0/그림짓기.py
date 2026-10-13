# -*- coding: utf-8 -*-
"""진짜 그림(앞 · 옆 두 장 · 위 없음)을 지금 기본 H 에 넣어 본다 · 10-13 사용자 「실제로 되는지 확인하자」
python 그림짓기.py <그림> <이름> <행0> <행1> <앞열0> <앞열1> <옆열0> <옆열1>  →  그림/<이름>.stl · 그림/<이름>.png
같은 행 띠를 앞 · 옆에서 자름(정사영 3면도는 높이가 맞음) · 위 보기 = 앞 ∩ 옆이 만드는 그림자 · 깊이는 모름 → 교차 깊이로 채움"""
import os, sys, numpy as np, cv2
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import 도구 as T
import 짓기C as JC, 회전 as RV, 회전2 as R2
sys.path.insert(0, os.path.join(T.R, "깊이학습")); from 준비 import 교차깊이

def 마스크(rgb):   # 흰 배경이 아닌 곳 → 구멍 채움 → 가장 큰 덩이
    m = (rgb.min(-1) < 235).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m); m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); f = np.zeros_like(m); cv2.drawContours(f, cs, -1, 1, -1); return f > 0
def 선그림(rgb, m): return (cv2.Canny(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 60, 150) > 0) & m

def 보기들(앞, 옆, n):
    """앞 (행 = 높이 · 열 = Y) · 옆 (행 = 높이 · 열 = X) 화소 → 실물보기 규약 6 방향 (n × n)
    ax0 (Y, Z) · ax1 (X, Z) · ax2 (X, Y) · Z 는 위쪽이 큼 · 가장 긴 변 = 1 · 가운데 0.5"""
    h, wy, wx = 앞.shape[0], 앞.shape[1], 옆.shape[1]; s = max(h, wy, wx)
    u = (np.arange(n) + .5) / n * 1.1 - .05                                   # 격자 → 세계 [0, 1]
    pz = np.clip(((.5 - u) * s + h / 2).astype(int), -1, h)                 # Z → 행 (위가 0)
    py = np.clip(((u - .5) * s + wy / 2).astype(int), -1, wy); px = np.clip(((u - .5) * s + wx / 2).astype(int), -1, wx)
    g = lambda img, r, c: np.where((r[:, None] >= 0) & (r[:, None] < img.shape[0]) & (c[None] >= 0) & (c[None] < img.shape[1]), img[np.clip(r, 0, img.shape[0] - 1)][:, np.clip(c, 0, img.shape[1] - 1)], 0)
    A0 = g(앞, pz, py).T                                                      # (Y, Z)
    A1 = g(옆, pz, px).T                                                      # (X, Z)
    return A0, A1

def 짓기(그림, 이름, r0, r1, a0, a1, b0, b1):
    im = np.asarray(Image.open(그림).convert("RGB")); fa, fb = im[r0:r1, a0:a1], im[r0:r1, b0:b1]
    ma, mb = 마스크(fa), 마스크(fb)
    S, X = [], []
    for n, out in ((256, S), (128, X)):
        s0, s1 = [a > 0 for a in 보기들(ma.astype(np.uint8), mb.astype(np.uint8), n)]
        s2 = (s1[:, None, :] & s0[None, :, :]).any(-1)                       # 위 = ∃z 앞 ∧ 옆 · (X, Y)
        out += [s0, s0, s1, s1, s2, s2]
    S = np.stack(S).astype(np.float32); Sx = np.stack(X).astype(np.float32)
    l0, l1 = [a > 0 for a in 보기들(선그림(fa, ma).astype(np.uint8), 선그림(fb, mb).astype(np.uint8), 128)]
    L = np.stack([l0, l0, l1, l1, np.zeros_like(l0), np.zeros_like(l0)]).astype(np.float32)
    Dx = 교차깊이(Sx); Xin = np.stack([Sx, L, Dx, Dx])                       # 깊이는 모름 → 교차 깊이
    i = -1; T._S[i] = S; T._X[i] = Xin
    교 = T.돌출(i, 0).intersect(T.돌출(i, 1)).intersect(T.돌출(i, 2)); s = 교; 순서 = ["교차"]; n0 = len(s.solids().vals())
    f = RV.찾기(S)   # 짓기C 의 H(HREV=1) 순서 그대로
    f2 = None if f["걸림"] else R2.찾기(R2.학생부피(Xin))
    if f["걸림"]:
        try: s = RV.짓기(i, f); 순서.append("회전 축 %d" % f["축"])
        except Exception: 순서.append("회전 실패")
    elif f2 is not None and f2["걸림"]:
        try:
            t = R2.짓기(f2, 교)
            if t is not None: s = t; 순서.append("회전2 기움 %.0f°" % f2["기움"])
        except Exception: 순서.append("회전2 실패")
    else:
        for a, (cy, cx), 런 in JC.원기둥구간(S):
            oa = [j for j in range(3) if j != a]; 중 = [0.0, 0.0, 0.0]; 중[oa[0]] = T.c(cy); 중[oa[1]] = T.c(cx)
            for rs in 런:
                try:
                    rv, z0, z1, rmax = JC.회전기둥(a, 중, rs); lo = [중[j] - rmax - T.화 for j in range(3)]; hi = [중[j] + rmax + T.화 for j in range(3)]; lo[a], hi[a] = z0, z1
                    s, 됨 = JC.깎기(s, T.상자(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]).cut(rv))
                    if 됨: 순서.append("원기둥 구간 축 %d" % a)
                except Exception: pass
    for ctr, r, 두축 in JC.공찾기(S):
        try:
            s, 됨 = JC.공깎기(s, [T.c(t) for t in ctr], r * T.화, 두축)
            if 됨: 순서.append("공 R%.0f" % r)
        except Exception: pass
    from 윤곽 import 메시로
    os.makedirs(os.path.join(H, "그림"), exist_ok=True); pm = 메시로(s); pm.export(os.path.join(H, "그림", 이름 + ".stl"))
    from render import render
    C = 256; v = pm.copy(); v.apply_translation(-v.bounds.mean(0)); v.apply_scale(0.8 / v.extents.max())
    v.vertices = v.vertices[:, [0, 2, 1]] * [1, 1, -1] + .5                # 렌더러는 Y 가 위 → Z(위)를 Y 로
    그 = lambda w: Image.fromarray(np.asarray(render(np.asarray(v.vertices), np.asarray(v.faces), w, dist=-1.05, img_size=C, cols=np.tile((0.55, 0.8, 0.5), (len(v.faces), 1)))))
    판 = [Image.fromarray(fa).resize((C * fa.shape[1] // max(fa.shape[:2]), C * fa.shape[0] // max(fa.shape[:2]))), Image.fromarray(fb).resize((C * fb.shape[1] // max(fb.shape[:2]), C * fb.shape[0] // max(fb.shape[:2])))]
    판 += [그(w) for w in ([1, .03, .03], [.03, .03, 1], [1, -.5, .9], [-1, -.5, -.9])]   # 앞(그림 앞과 같은 방향) · 옆 · 비스듬 둘
    out = Image.new("RGB", (sum(p.width for p in 판) + 10 * len(판), C), "white"); x = 0
    for p in 판: out.paste(p, (x, (C - p.height) // 2)); x += p.width + 10
    out.save(os.path.join(H, "그림", 이름 + ".png")); print(이름, 순서, "조각", len(s.solids().vals()), flush=True)

if __name__ == "__main__":
    짓기(sys.argv[1], sys.argv[2], *[int(x) for x in sys.argv[3:9]])
