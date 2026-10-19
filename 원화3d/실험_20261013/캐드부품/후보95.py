# 다른 도면에서 깊이 후보 읽기 — 사용자 10-19 「다른 이미지에서 깊이정보를 얻을 수 있다며 · 정확히 이미지로」 · 10-19
# 위 도면 화소 (x, y) 의 깊이 = 그 자리 수평 면의 높이 z → 그 면은 앞 도면 열 x 와 옆 도면 열 y 에 수평선(실선이든 점선이든)으로 나온다
# 후보 = 앞 열 x 의 수평선 높이 ∩ 옆 열 y 의 수평선 높이 → 32 층으로 · 정답 층이 후보 안에 있는 몫을 잰다(위 방향만 · 시험 300)
# 사용(venv · ART_MEM_GB=8): 후보95.py → 후보95.json · 후보95.py 그림 → out/설명/캐드부품/후보95.png · 후보95.gif
import json, cv2, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 여섯방향 as S6
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; N = 128; K = 32
d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h88 = np.load(O + "숨은선88.npz"); HF, HS = h88["HF"], h88["HS"]
반 = np.load(O + "데이터51.npz")["반"]; 층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
def 수평(L):   # 가로로 5 화소 넘게 이어진 선만(세로 겹선의 옆 이웃은 뺀다)
    k = np.ones((1, 5), np.uint8); return cv2.dilate(cv2.erode((L > 0).astype(np.uint8), k), k) > 0
def 층으로(r, h):   # 앞 · 옆 도면 행 r → 높이 z(칸 위 끝) → 위 방향 깊이 층
    z = S6.g[N - 1 - r] + S6.칸 / 2; return np.clip(np.floor((h - z) / (2 * h / K) + 1e-6), 0, K - 1).astype(int)
def 후보(i, 숨은=True):   # → 열마다 후보 층 집합: 앞[x] (K,) bool · 옆[y] (K,) bool
    h = float(반[i][0]); out = []
    for 실, 점 in ((F[i], HF[i]), (S[i], HS[i])):
        L = 수평(np.maximum(실, 점) if 숨은 else 실); c = np.zeros((N, K), bool); r, col = np.nonzero(L); c[col, 층으로(r, h)] = True; out.append(c)
    return out
def 재기(i, 숨은=True):
    앞, 옆 = 후보(i, 숨은); g = 층[i, 0].astype(int); 안 = (입[i, 0, 1] > 0) & (g < K); Y, Xx = np.nonzero(안); iy = N - 1 - Y
    c = 앞[Xx] & 옆[iy]; gg = g[Y, Xx]; 맞 = c[np.arange(len(gg)), gg]; 곁 = 맞 | c[np.arange(len(gg)), np.clip(gg - 1, 0, K - 1)] | c[np.arange(len(gg)), np.clip(gg + 1, 0, K - 1)]
    깎 = gg >= 껍[i, 0][Y, Xx].astype(int) + 2
    return dict(n=len(gg), 맞=맞.sum(), 곁=곁.sum(), 수=c.sum(1).sum(), 깎n=깎.sum(), 깎맞=(맞 & 깎).sum(), 깎곁=(곁 & 깎).sum())
if __name__ == "__main__" and __import__("sys").argv[1:] != ["그림"]:
    te = np.nonzero(시)[0][:300]; r = {}
    for 숨은 in (True, False):
        s = {}
        for i in te:
            for k, v in 재기(i, 숨은).items(): s[k] = s.get(k, 0) + v
        r["실선 + 점선" if 숨은 else "실선만"] = {"정답 층이 후보 안": round(s["맞"] / s["n"], 3), "± 1 층 안": round(s["곁"] / s["n"], 3), "화소당 후보 수": round(s["수"] / s["n"], 2),
            "속 깎임(정답 ≥ 껍질 + 2) 화소에서 후보 안": round(s["깎맞"] / s["깎n"], 3), "속 깎임 ± 1": round(s["깎곁"] / s["깎n"], 3)}
    print(r); json.dump(r, open("후보95.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def 그림(i=None, 점=None, 공개=None, 쓸=None):   # 시험 부품 중 속 깎임 화소를 후보가 가장 많이 맞히는 것 하나 · 점 · 공개(⑦ 를 열 몇까지 보일지)는 움직임용
    te = np.nonzero(시)[0][:300]; i = i if i is not None else max(te, key=lambda i: (lambda r: r["깎맞"] * (r["깎맞"] / max(r["깎n"], 1)))(재기(i)))
    h = float(반[i][0]); 앞, 옆 = 후보(i); g = 층[i, 0].astype(int); 안 = (입[i, 0, 1] > 0) & (g < K); s = 껍[i, 0].astype(int)
    멀 = cv2.distanceTransform((X[i] == 0).astype(np.uint8), cv2.DIST_L2, 3) >= 8; Y, Xx = np.nonzero(안 & (g >= s + 2) & 멀); iy = N - 1 - Y; ok = 앞[Xx, g[Y, Xx]] & 옆[iy, g[Y, Xx]]; j = np.nonzero(ok)[0][len(np.nonzero(ok)[0]) // 2]; py, px = 점 or (Y[j], Xx[j]); y = N - 1 - py
    c = 앞[:, None, :] & 옆[None, :, :]   # [x, y, 층]
    오 = np.full((N, N), np.nan); YY, XX = np.nonzero(안)   # 후보 중 정답에 가장 가까운 것(신탁 고르기) — 정보가 있는지
    for a, b in zip(YY, XX):
        cc = np.nonzero(c[b, N - 1 - a])[0]; 오[a, b] = cc[np.argmin(np.abs(cc - g[a, b]))] if len(cc) else s[a, b]
    판 = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 부 = list(np.load(O + "학습69_판0/예측부품.npy")); pp = 판[부.index(i), 0].astype(float) if i in 부 else None
    f = plt.figure(figsize=(20, 11)); 회 = "Greys"
    def 선(a, 실, 점, 제):
        a.imshow(np.where(실 > 0, 0, np.where(점 > 0, .55, 1)), cmap="gray", vmin=0, vmax=1); a.set_title(제, fontsize=14); a.set_xticks([]); a.set_yticks([])
    a1 = f.add_subplot(2, 4, 1); 선(a1, X[i], h88["HX"][i], "① 위 도면 — 이 점의 깊이는?"); a1.plot(px, py, "o", ms=14, mfc="none", mec="#d33", mew=3)
    a2 = f.add_subplot(2, 4, 2); 선(a2, F[i], HF[i], "② 앞 도면 — 같은 x 세로줄"); a2.axvline(px, color="#d33", lw=1.5)
    a3 = f.add_subplot(2, 4, 3); 선(a3, S[i], HS[i], "③ 옆 도면 — 같은 y 세로줄"); a3.axvline(y, color="#d33", lw=1.5)
    for a, 열, cc in ((a2, px, 앞[px]), (a3, y, 옆[y])):
        L = 수평(np.maximum(F[i], HF[i]) if a is a2 else np.maximum(S[i], HS[i]))
        for r in np.nonzero(L[:, 열])[0]: a.plot(열, r, "_", ms=22, mew=3, color="#1a9850" if 앞[px, 층으로(r, h)] & 옆[y, 층으로(r, h)] else "#f0a030")
    a4 = f.add_subplot(2, 4, 4); 층들 = np.arange(K)
    for xx, v, 색, 이 in ((0, 앞[px], "#f0a030", "앞 후보"), (1, 옆[y], "#f0a030", "옆 후보"), (2, 앞[px] & 옆[y], "#1a9850", "둘 다(∩)")):
        a4.scatter(np.full(v.sum(), xx), 층들[v], s=160, color=색, marker="s"); a4.text(xx, -2.6, 이, ha="center", fontsize=12)
    a4.axhline(g[py, px], color="#d33", lw=2, ls="--"); a4.text(2.45, g[py, px], "정답 %d층" % g[py, px], color="#d33", va="center", fontsize=12)
    a4.axhline(s[py, px], color="#888", lw=2, ls=":"); a4.text(2.45, s[py, px], "껍질 %d층\n(지금 입력)" % s[py, px], color="#666", va="center", fontsize=11)
    a4.set_ylim(K, -4); a4.set_xlim(-.6, 4.2); a4.set_xticks([]); a4.set_ylabel("위에서 잰 깊이 층(0 = 맨 위)"); a4.set_title("④ 후보 층 = 앞 ∩ 옆 수평선", fontsize=14)
    m = lambda v: np.where(안, v, np.nan)
    for n, (v, 제) in enumerate(((g, "⑤ 정답 깊이"), (s, "⑥ 지금 모델이 받는 깊이 = 껍질"), (오 if 공개 is None else np.where(np.arange(N)[None] <= 공개, 오, np.nan), "⑦ ④ 의 후보에서 고르면(정보 천장)"), (pp, "⑧ 판0 예측"))):
        a = f.add_subplot(2, 4, 5 + n); a.set_xticks([]); a.set_yticks([])
        if v is None: a.set_title(제 + " (없음)"); continue
        a.imshow(m(v), cmap="viridis", vmin=0, vmax=K - 1); 틀 = np.mean((np.nan_to_num(v, nan=-1) == g)[안]); a.set_title("%s\n층 맞음 %.2f" % (제, 틀), fontsize=13); a.plot(px, py, "o", ms=12, mfc="none", mec="#d33", mew=2.5)
    f.suptitle("부품 %d · 위 도면의 빨간 점 깊이를 앞 · 옆 도면 수평선(실선 검정 · 점선 회색)에서 읽는다 · 초록 = 두 도면 모두에 있는 높이" % i, fontsize=15)
    plt.tight_layout(); 쓸 = 쓸 or O + "후보95.png"; f.savefig(쓸, dpi=70); plt.close(f); return i, py, px
def 움직임():   # 빨간 점이 바닥 한 줄을 가로지른다 → 후보95.gif
    from PIL import Image
    i, py, _ = 그림(쓸=O + "후보95_0.png"); 안 = np.nonzero(입[i, 0, 1][py] > 0)[0]; 판 = []
    for n, px in enumerate(np.linspace(안[0] + 1, 안[-1] - 1, 28).astype(int)):
        p = O + "후보95_f.png"; 그림(i, (py, px), px, p); 판.append(Image.open(p).convert("P", palette=Image.ADAPTIVE)); 
    판[0].save(O + "후보95.gif", save_all=True, append_images=판[1:] + [판[-1]] * 6, duration=450, loop=0); print(O + "후보95.gif", len(판))
if __name__ == "__main__" and __import__("sys").argv[1:] == ["그림"]: print(그림()); 움직임()
