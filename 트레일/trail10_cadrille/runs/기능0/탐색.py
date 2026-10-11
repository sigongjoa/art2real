# -*- coding: utf-8 -*-
"""기능0 자동 정답 찾기 — 교차(복셀)에서 시작해 후보 기능(포켓 · 구 빼기 · 원기둥 껍질)을 하나씩 더해 정답 깊이와 제일 맞는 순서를 고른다 · 10-11
정답 = 여섯 방향 실물 깊이로 깎은 복셀(보이는 깊이 천장 · 메시 불필요) · 후보는 그림 + 깊이로만 만든다
python runs/기능0/탐색.py 시험 [번호…]   →  탐색/시험_NN.json"""
import os, sys, json, numpy as np, cv2
from scipy import ndimage
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); n = 128
X_ = lambda 판: np.load(os.path.join(R, "깊이학습", 판 + ".npz"))["X"]
ax_of = lambda k: k // 2
def 칸(k):   # 그 방향 깊이 축 좌표(칸 중심) 0..1 · 낮은 쪽이면 (i+.5)/n · 높은 쪽이면 1 − 그것
    t = (np.arange(n) + .5) / n; return t if k % 2 == 0 else 1 - t
def 펼(a2, k):   # (o0, o1) 그림 → (x, y, z) 복셀 배열로 브로드캐스트할 모양
    ax = ax_of(k); return np.expand_dims(a2, ax)
def 축(k):
    ax = ax_of(k); s = [1, 1, 1]; s[ax] = n; return 칸(k).reshape(s)
def 교차(S): return S[0][None] & S[2][:, None] & S[4][:, :, None]
def 깎기(D):   # 여섯 방향 깊이 앞에 있는 칸은 빔
    V = np.ones((n, n, n), bool)
    for k in range(6): V &= 축(k) >= 펼(D[k], k) - 1e-6
    return V
def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
def 덩이수(V): return ndimage.label(V)[1]

def 점들(D, S, k, m):   # 깊이 그림 화소 → 3D 점(복셀 단위)
    r, c = np.nonzero(m & S[k]); ax = ax_of(k); o = [j for j in range(3) if j != ax]
    P = np.zeros((len(r), 3)); P[:, o[0]] = r + .5; P[:, o[1]] = c + .5; d = D[k][r, c]; P[:, ax] = (d if k % 2 == 0 else 1 - d) * n; return P
def 구맞춤(P):
    A = np.c_[2 * P, np.ones(len(P))]; x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]; o = x[:3]; Rr = float(np.sqrt(max(x[3] + o @ o, 0)))
    return o, Rr, float(np.median(np.abs(np.linalg.norm(P - o, axis=1) - Rr)))
def 원맞춤(q):
    A = np.c_[2 * q, np.ones(len(q))]; x = np.linalg.lstsq(A, (q ** 2).sum(1), rcond=None)[0]; o = x[:2]; Rr = float(np.sqrt(max(x[2] + o @ o, 0)))
    return o, Rr, float(np.median(np.abs(np.linalg.norm(q - o, axis=1) - Rr)))

def 후보들(S, D, Dh):
    """그림 + 깊이로만 만든 후보 기능 → [(이름, 매개변수, 지울 복셀)]"""
    I = np.indices((n, n, n)).transpose(1, 2, 3, 0) + .5; out = []
    for k in range(6):
        깊 = S[k] & (D[k] - Dh[k] > 3 / n); m_, nl = ndimage.label(깊)
        for j in range(1, nl + 1):
            c = m_ == j
            if c.sum() < 8: continue
            바닥 = float(np.median(D[k][c])); 기둥 = 펼(c, k) & (축(k) < 바닥 - 1e-6)   # 평평한 바닥 포켓
            r_, c_ = np.nonzero(c); out.append(("포켓", {"쪽": k, "네모": [int(r_.min()), int(r_.max()) + 1, int(c_.min()), int(c_.max()) + 1], "바닥": round(바닥, 4), "넓이": int(c.sum())}, 기둥))
            P = 점들(D, S, k, c)
            if len(P) >= 20:
                o, Rr, e = 구맞춤(P); 앞 = o[ax_of(k)] < np.median(P[:, ax_of(k)]) if k % 2 == 0 else o[ax_of(k)] > np.median(P[:, ax_of(k)])
                if e < 1.0 and 3 < Rr < n / 2 and 앞:   # 오목 = 중심이 보는 쪽에 있음
                    out.append(("구 빼기", {"쪽": k, "중심": o.round(2).tolist(), "R": round(Rr, 2), "잔차": round(e, 3)}, ((I - o) ** 2).sum(-1) < Rr ** 2))
        ax = ax_of(k); o2 = [j for j in range(3) if j != ax]; P = 점들(D, S, k, np.ones_like(S[k]))
        if len(P) < 50: continue
        두께 = np.where(S[k] & S[k ^ 1], np.abs((1 - D[k ^ 1]) - D[k]) * n if k % 2 == 0 else np.abs((1 - D[k]) - D[k ^ 1]) * n, np.nan); t = float(np.nanmedian(두께)) if np.isfinite(두께).any() else 0
        for 축j in o2:   # 원기둥 축 = 그림 안의 한 축
            jj = [j for j in range(3) if j != 축j]; q = P[:, jj]; o, Rr, e = 원맞춤(q); 깊축 = jj.index(ax)
            뒤 = o[깊축] > np.median(q[:, 깊축]) if k % 2 == 0 else o[깊축] < np.median(q[:, 깊축])   # 볼록 = 중심이 반대쪽
            if e < .6 and 뒤 and 4 < Rr < 4 * n and 1 < t < n / 8:
                qq = I[..., [j for j in range(3) if j != 축j]]; 안 = ((qq - o) ** 2).sum(-1) < (Rr - t) ** 2
                out.append(("원기둥 껍질", {"쪽": k, "축": 축j, "중심": o.round(2).tolist(), "R": round(Rr, 2), "두께": round(t, 2), "잔차": round(e, 3)}, 안))
    return out

def 찾기(x, 최대=6, 문턱=.003):
    S = x[0] > .5; D = x[3].astype(np.float32); Dh = x[2].astype(np.float32)
    정 = 깎기(D); V = 교차(S); 처음 = iou(V, 정); 덩0 = 덩이수(V); 후 = 후보들(S, D, Dh); 고름 = []
    for _ in range(최대):
        best = None
        for j, (이름, p, 지움) in enumerate(후):
            if any(j == g[0] for g in 고름): continue
            W = V & ~지움
            if 덩이수(W) > 덩0: continue                   # 부스러기 생기면 안 씀
            g = iou(W, 정) - iou(V, 정)
            if best is None or g > best[1]: best = (j, g, W)
        if best is None or best[1] < 문턱: break
        고름.append((best[0], round(best[1], 4))); V = best[2]
    return {"교차 IoU": round(처음, 4), "끝 IoU": round(iou(V, 정), 4), "후보 수": len(후),
            "순서": [{"기능": 후[j][0], **후[j][1], "얻음": g} for j, g in 고름]}

if __name__ == "__main__":
    판 = sys.argv[1]; X = X_(판); ids = [int(a) for a in sys.argv[2:]] or range(len(X)); O = os.path.join(H, "탐색"); os.makedirs(O, exist_ok=True)
    for i in ids:
        r = 찾기(X[i].astype(np.float32)); json.dump(r, open(os.path.join(O, "%s_%02d.json" % (판, i)), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, r["교차 IoU"], "→", r["끝 IoU"], "후보", r["후보 수"], [(s["기능"], s["쪽"]) for s in r["순서"]], flush=True)
