# 얇은 판 예시: 정답(파랑) · 칸 깎기(빨강) · 겹침(보라) — 48³ 칸 가운데 대 192³ · 부품마다 가장 많이 찬 단면 하나
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
import 채점후보 as K
O = K.O; ks = [int(x) for x in sys.argv[1:]]
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; del d
L = json.load(open(O + "목록.json", encoding="utf-8")); 범 = json.load(open(O + "범위46.json")); R = {r["k"]: r for r in json.load(open("결과.json", encoding="utf-8"))}
z = np.load(O + "데이터51.npz"); ii = [te[범[k]] for k in ks]; 층 = z["층"][ii]; 반 = z["반"][ii]; del z
fig, ax = plt.subplots(len(ks), 3, figsize=(12, 4.2 * len(ks)), squeeze=False)
for n, (k, i) in enumerate(zip(ks, ii)):
    v, f, H = K.J.정규메시(L[i]); 표 = K.깊이표(층[n], 반[n]); 상자 = (v.min(0) - 1e-4, v.max(0) + 1e-4)
    o = {m: (K.점유(v, f, m), K.깎기칸(표, 상자, m)) for m in (48, 192)}
    a192 = o[192][0]; 축 = int(np.argmin(np.ptp(v, 0)))   # 가장 얇은 축에 수직이 아니라 — 얇은 축을 단면에 담는다
    보 = [c for c in range(3) if c != 축][0]; s192 = int(np.argmax(a192.sum(axis=tuple(c for c in range(3) if c != 보)))) if a192.any() else 96
    def 단(q, m):
        s = s192 * m // 192; sl = np.take(q, s, axis=보); return sl
    for c, m in enumerate((48, 192)):
        g, c_ = 단(o[m][0], m), 단(o[m][1], m); img = np.ones(g.shape + (3,)); img[g & ~c_] = (.2, .4, 1); img[c_ & ~g] = (1, .3, .3); img[g & c_] = (.55, .2, .7)
        ax[n, c].imshow(img.transpose(1, 0, 2), origin="lower", interpolation="nearest"); ax[n, c].set_title(f"{m}³ 칸 가운데 · 정답 {int(g.sum())}칸 · 깎기 {int(c_.sum())}칸 · IoU {K.IoU(o[m][1], o[m][0]):.2f}", fontsize=10); ax[n, c].axis("off")
    # 실제 메시 단면(선)
    import trimesh
    m_ = trimesh.Trimesh(v, f, process=False); g192 = (np.arange(192) + .5) / 192 * 1.1 - .55; 원점 = np.zeros(3); 원점[보] = g192[s192]; 법 = np.zeros(3); 법[보] = 1
    sec = m_.section(plane_origin=원점, plane_normal=법); 남 = [c for c in range(3) if c != 보]
    if sec is not None:
        for e in sec.discrete: ax[n, 2].plot(e[:, 남[0]], e[:, 남[1]], "b-", lw=.8)
    ax[n, 2].set_xlim(-.55, .55); ax[n, 2].set_ylim(-.55, .55); ax[n, 2].set_aspect("equal")
    for t in np.linspace(-.55, .55, 49): ax[n, 2].axvline(t, c=".85", lw=.3); ax[n, 2].axhline(t, c=".85", lw=.3)
    r = R.get(k, {}); ax[n, 2].set_title(f"#{k} 실제 메시 단면 + 48³ 격자 · H={H:.3f} · 천장 {r.get('천장53', 0):.2f}", fontsize=10)
fig.text(.5, .005, "파랑 = 정답만 · 빨강 = 여섯 방향 정답 깊이 칸 깎기만 · 보라 = 둘 다", ha="center"); fig.tight_layout(rect=(0, .02, 1, 1))
fig.savefig(sys.argv[0].replace("그림.py", "") + "얇은판_예시.png", dpi=110); print("ok")
