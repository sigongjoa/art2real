# -*- coding: utf-8 -*-
"""원화에서 **광원 방향을 역산**한다.

    python light.py

깊이와 달리 이건 잘 정의된 문제다. 근거는 하나다 —
**실루엣에서는 법선을 공짜로 안다.** 바깥 윤곽에서 표면 법선은 화면 안에 있고
윤곽에 수직이다: n = (nx, ny, 0). 그러면

    밝기 = 알베도 * (n . l) = 알베도 * (nx*lx + ny*ly)

lz 가 아예 안 들어가고 (lx, ly) 가 선형으로 풀린다. 세 가지로 재고 서로 대조한다.

    A. 최댓점    윤곽에서 제일 밝은 점의 법선 = l 의 화면 성분 방향
    B. 회귀      윤곽 전체에서 밝기 ~ nx*lx + ny*ly 최소제곱
    C. 종단선    셀은 2톤이라 명/암이 뒤집히는 점이 종단선(n.l = t).
                 그 점들의 (nx,ny) 가 직선 위에 놓이고 그 법선이 l 이다
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
INSET = 3          # 윤곽에서 안쪽으로 이만큼 들어가 색을 읽는다 (먹선을 피한다)


def load():
    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    y0, y1 = int(rr(0.985)), int(rr(0.775))
    x0, x1 = int(cc(0.118)), int(cc(0.252))
    return raw[..., :3].astype(np.uint8)[y0:y1, x0:x1], (raw[..., 3] > 0)[y0:y1, x0:x1]


def hue_class(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if min(mc) > 170 else "dark"


def main():
    C, S = load()
    L = np.load(os.path.join(HERE, "out", "_L.npy"))
    H, W = S.shape

    # --- 실루엣과 바깥 법선 ---
    dt = cv2.distanceTransform(S.astype(np.uint8), cv2.DIST_L2, 5)
    gy, gx = np.gradient(cv2.GaussianBlur(dt, (0, 0), 1.2))   # 안쪽을 향한다
    cnts, _ = cv2.findContours(S.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cn = max(cnts, key=cv2.contourArea).reshape(-1, 2)

    # 재질별 대표 밝기 — 알베도로 나눠 준다
    cls = {}
    for v in np.unique(L):
        if v <= 1:
            continue
        cls[int(v)] = hue_class(C[L == v].mean(0))
    A0 = {"lav": 205., "gold": 235., "white": 250., "dark": 95.}

    N, B, KIND = [], [], []
    for (px, py) in cn[::2]:
        n = np.array([gx[py, px], gy[py, px]])       # 안쪽
        nn = np.linalg.norm(n)
        if nn < 1e-6:
            continue
        n = -n / nn                                   # 바깥 법선
        qx = int(round(px + n[0] * -INSET))
        qy = int(round(py + n[1] * -INSET))
        if not (0 <= qx < W and 0 <= qy < H) or not S[qy, qx]:
            continue
        v = int(L[qy, qx])
        if v <= 1:
            continue
        k = cls[v]
        b = float(C[qy, qx].max()) / A0[k]
        N.append(n); B.append(b); KIND.append(k)
    N = np.array(N); B = np.array(B)
    print("실루엣 표본 %d점  (재질: %s)" % (len(N), {k: KIND.count(k) for k in set(KIND)}))
    print("  정규화 밝기 n.l  분위수 %s" % [round(float(np.percentile(B, q)), 3) for q in (5, 25, 50, 75, 95)])

    def ang(v):
        return (np.degrees(np.arctan2(-v[1], v[0]))) % 360   # 화면 위쪽이 +90도

    # A. 최댓점
    top = np.argsort(-B)[:max(len(B) // 20, 3)]
    a = N[top].mean(0); a /= np.linalg.norm(a)
    print("\nA 최댓점   l 화면방향 %.0f도   (상위 %d점 평균)" % (ang(a), len(top)))

    # B. 회귀  b = nx*lx + ny*ly + c
    M = np.column_stack([N[:, 0], N[:, 1], np.ones(len(N))])
    p, *_ = np.linalg.lstsq(M, B, rcond=None)
    lxy = p[:2]
    res = float(np.sqrt(((M @ p - B) ** 2).mean()))
    r2 = 1 - ((M @ p - B) ** 2).sum() / max(((B - B.mean()) ** 2).sum(), 1e-9)
    print("B 회귀     l 화면방향 %.0f도   |lxy| %.3f  offset %.3f  RMS %.3f  R^2 %.3f"
          % (ang(lxy), np.linalg.norm(lxy), p[2], res, r2))

    # C. 종단선 — 명/암이 뒤집히는 자리
    thr = float(np.median(B))
    lit = B > thr
    flips = [i for i in range(len(B)) if lit[i] != lit[(i + 1) % len(B)]]
    print("C 종단선   윤곽에서 명/암 뒤집힘 %d회 (임계 %.3f)" % (len(flips), thr))
    if len(flips) >= 2:
        F = np.array([N[i] for i in flips])
        # nx*lx + ny*ly = t  -> (nx,ny) 가 직선 위. 직선의 법선이 l 방향
        mu = F.mean(0)
        _, s, vt = np.linalg.svd(F - mu, full_matrices=False)
        d = vt[1]                                    # 직선의 법선
        if d @ N[int(np.argmax(B))] < 0:
            d = -d
        print("           l 화면방향 %.0f도   직선 적합 잔차비 %.3f (작을수록 직선)"
              % (ang(d), float(s[1] / max(s[0], 1e-9))))

    # --- 검증: 추정 l 로 내부 판의 명/암을 설명할 수 있나 ---
    print("\n검증 — 추정 l 이 내부 판의 밝기 순서를 맞추나")
    lxyn = lxy / max(np.linalg.norm(lxy), 1e-9)
    rows = []
    for v, k in cls.items():
        m = L == v
        if m.sum() < 60:
            continue
        ys, xs = np.nonzero(m)
        # 판 중심에서 실루엣까지의 방향을 법선 대용으로 (거친 대용품이다)
        n = np.array([gx[int(ys.mean()), int(xs.mean())], gy[int(ys.mean()), int(xs.mean())]])
        nn = np.linalg.norm(n)
        if nn < 1e-6:
            continue
        rows.append((float(C[m].max(0).max()) / A0[k], float(-n @ lxyn / nn)))
    R = np.array(rows)
    print("  판 %d개   밝기 vs (대용 법선 . l)  상관 r = %+.3f" % (len(R), float(np.corrcoef(R[:, 0], R[:, 1])[0, 1])))
    print("  (대용 법선은 거칠다 — 이 상관은 부호만 참고)")
    json.dump({"lxy": [float(lxy[0]), float(lxy[1])], "deg": float(ang(lxy)),
               "r2": float(r2), "n": int(len(N))},
              open(os.path.join(HERE, "out", "light.json"), "w"))


if __name__ == "__main__":
    main()
