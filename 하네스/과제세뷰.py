# 하네스 과제 「세뷰」 — 학습 없음 · CAD 3D 모서리를 위 · 앞 · 옆에 투영 → 한 뷰에서 같은 2D 선에 포개진 모서리 무리(층)를 다른 두 뷰가 가르나 · 천장(정답 형상) · 10-24
# 사용자 10-24 「겹치면 2d 라서 층별로 다른 게 쌓인 건지 둥근 테두리인지 모르잖아」 → 겹침은 한 장에서 풀지 않고 세 뷰 짝으로 푼다 — 그게 되는지 정답으로 먼저 잰다
# 1 단계(모서리 투영): 부품마다 3D 모서리 번호별 뷰 3 장 마스크 → out/하네스/세뷰/<부품>.npz (부품마다 따로 프로세스 · 시간 상한)
# 2 단계(재기): 뷰마다 포갬(서로를 70 % 이상 1.5 화소 안에서 덮음)으로 무리 → 둘 이상 무리 = 겹침 → 무리 안 모든 짝이 다른 뷰 하나에서라도 안 포개지면 「가름」
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
저장 = f"{뿌리}/out/하네스/세뷰/"; 뷰이름 = ["위", "앞", "옆"]
def _투영(i):   # 부품 하나 → m{v}: (모서리 수, 2048) packbits · 그림{v}: 도면에 그려짐(보 | 숨 위 80 %) · 종류
    p = 저장 + f"{i:05d}.npz"
    if os.path.exists(p): return
    try:
        import cv2, 선정답 as S, 모델124 as B, 조립124 as C, 숨은선88 as H
        s = json.load(open(B.D + f"사양/{i:05d}.json", encoding="utf-8")); w = C.짓기(s["코드"]); m = C.메시(w)[0]
        c = m.bounds.mean(0); e = float(m.extents.max()); 래 = H.그리기((m.vertices - c) / e, m.faces)
        점들, 종 = [], []
        for ed in w.val().Edges():
            점들.append((np.array([tuple(ed.positionAt(t)) for t in np.linspace(0, 1, 64)]) - c) / e); 종.append(1 if ed.geomType() == "LINE" else 2)
        짐 = {"종": np.array(종, np.int8)}
        for j, (a, b) in enumerate(S.축):
            보, 숨 = 래[j]; 선 = cv2.dilate((보 | 숨).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0; ms, 그 = [], []
            for 점 in 점들:
                x, y = S.화소(점[:, [a, b]]); img = np.zeros((128, 128), np.uint8)
                cv2.polylines(img, [np.c_[x, y].round().astype(np.int32)], False, 1, 1); 화 = img > 0
                ms.append(np.packbits(화)); 그.append(bool(선[화].mean() >= .8))
            짐[f"m{j}"] = np.array(ms) if ms else np.zeros((0, 2048), np.uint8); 짐[f"그림{j}"] = np.array(그, bool)
        np.savez_compressed(p, **짐)
    except Exception as ex: open(p + ".err", "w", encoding="utf-8").write(str(ex)[:300])
def 투영들(일꾼=6, 초=120):   # 시험 부품 전부(겹침그림.모서리들 과 같은 꼴 — 부품마다 프로세스 · 상한 넘으면 죽이고 err)
    import time, multiprocessing as mp, 모델124 as B
    os.makedirs(저장, exist_ok=True); 일 = [r["i"] for r in B.색인() if r["i"] >= B.NT]; 일 = [i for i in 일 if not os.path.exists(저장 + f"{i:05d}.npz")]; 도는 = {}
    while 일 or 도는:
        while 일 and len(도는) < 일꾼: i = 일.pop(); pr = mp.Process(target=_투영, args=(i,)); pr.start(); 도는[i] = (pr, time.time())
        for i, (pr, t) in list(도는.items()):
            if not pr.is_alive(): 도는.pop(i)
            elif time.time() - t > 초: pr.kill(); 도는.pop(i); open(저장 + f"{i:05d}.npz.err", "w", encoding="utf-8").write("시간 넘음")
        time.sleep(.2)
def 포갬(a, b, 거리=1.5, 덮음=.7):   # 두 마스크가 서로를 덮나(점처럼 보이는 모서리는 화소 하나)
    import cv2
    da = cv2.distanceTransform((~a).astype(np.uint8), cv2.DIST_L2, 3); db = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 3)
    return (db[a] <= 거리).mean() >= 덮음 and (da[b] <= 거리).mean() >= 덮음
def 무리(ms):   # 포갠 것끼리 이음(합집합-찾기)
    부 = list(range(len(ms)))
    def 뿌(k):
        while 부[k] != k: 부[k] = 부[부[k]]; k = 부[k]
        return k
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            if 뿌(i) != 뿌(j) and 포갬(ms[i], ms[j]): 부[뿌(i)] = 뿌(j)
    g = {}
    for k in range(len(ms)): g.setdefault(뿌(k), []).append(k)
    return list(g.values())
def 부품재기(z):   # → (선 수, 겹친 선 수, 가른 겹친 선 수, 겹친 선에 숨은 모서리 수)
    풀 = lambda v: np.unpackbits(z[f"m{v}"], axis=1)[:, :128 * 128].reshape(-1, 128, 128).astype(bool) if len(z[f"m{v}"]) else np.zeros((0, 128, 128), bool)
    ms = [풀(v) for v in range(3)]; 선 = 겹 = 가 = 숨 = 0
    for v in range(3):
        쓴 = np.nonzero(z[f"그림{v}"] & (ms[v].reshape(len(ms[v]), -1).sum(1) > 0))[0]
        for g in 무리([ms[v][k] for k in 쓴]):
            선 += 1
            if len(g) < 2: continue
            겹 += 1; 숨 += len(g); 모 = [쓴[k] for k in g]
            가 += all(any(not 포갬(ms[u][e], ms[u][f]) for u in range(3) if u != v) for i, e in enumerate(모) for f in 모[i + 1:])
    return 선, 겹, 가, 숨
def 점검(cfg, 폴더):   # 하네스가 부름(학습 · 모델 없음 — 정답 형상으로 잰 천장)
    import 모델124 as B
    투영들(); 부품 = sorted(f[:5] for f in os.listdir(저장) if f.endswith(".npz")); 합 = np.zeros(4); 실패 = len([f for f in os.listdir(저장) if f.endswith(".err")])
    for p in 부품: 합 += 부품재기(np.load(저장 + f"{p}.npz"))
    선, 겹, 가, 숨 = 합
    지 = {"세뷰_부품": len(부품), "세뷰_실패": 실패, "세뷰_겹침몫": round(겹 / max(선, 1), 4), "세뷰_가름": round(가 / max(겹, 1), 4), "세뷰_겹침당모서리": round(숨 / max(겹, 1), 2)}
    그림(폴더, np.load(저장 + "12050.npz") if os.path.exists(저장 + "12050.npz") else None); return 지
def 그림(폴더, z):   # 부품 12050 앞 뷰: 겹친 선(빨강) · 그 모서리들이 위 · 옆에서 어디로 가나(같은 색)
    if z is None: return
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from PIL import Image
    plt.rcParams["font.family"] = "Malgun Gothic"
    풀 = lambda v: np.unpackbits(z[f"m{v}"], axis=1)[:, :128 * 128].reshape(-1, 128, 128).astype(bool)
    ms = [풀(v) for v in range(3)]; 쓴 = np.nonzero(z["그림1"])[0]; 겹들 = [g for g in 무리([ms[1][k] for k in 쓴]) if len(g) >= 2][:6]
    팔 = plt.get_cmap("tab10"); fig, ax = plt.subplots(1, 3, figsize=(18, 6.4)); fig.suptitle("세 뷰 짝 — 앞 뷰에서 포개진 모서리 무리(색마다 한 무리)가 위 · 옆에서는 어디로 가나 · 부품 12050", fontsize=16, weight="bold")
    for c, v in enumerate((1, 0, 2)):
        im = np.full((128, 128, 3), 235, np.uint8); 바 = ms[v][np.nonzero(z[f"그림{v}"])[0]].any(0) if z[f"그림{v}"].any() else np.zeros((128, 128), bool); im[바] = 150
        for n, g in enumerate(겹들):
            for k in g: im[ms[v][쓴[k]]] = (np.array(팔(n)[:3]) * 255).astype(np.uint8)
        ax[c].imshow(im); ax[c].set_title(f"{뷰이름[v]}" + (" — 포개진 선" if v == 1 else " — 같은 모서리들"), fontsize=14); ax[c].axis("off")
    fig.savefig(폴더 + "시트.png", dpi=60, bbox_inches="tight"); plt.close(fig)
if __name__ == "__main__":   # 자체 시험: 앞에서 포갠 두 가로 모서리가 위에서 앞뒤 두 줄이면 가름 · 위에서도 포개면 못 가름
    import cv2
    def 선(p, q): m = np.zeros((128, 128), np.uint8); cv2.line(m, p, q, 1, 1); return np.packbits(m > 0)
    앞 = [선((10, 50), (90, 50)), 선((10, 50), (90, 50))]; 위1 = [선((10, 20), (90, 20)), 선((10, 60), (90, 60))]; 옆 = [선((40, 50), (41, 50)), 선((80, 50), (81, 50))]
    z = {"m0": np.array(위1), "m1": np.array(앞), "m2": np.array(옆), **{f"그림{v}": np.array([True, True]) for v in range(3)}}
    r = 부품재기(z); assert r[1] >= 1 and r[2] == r[1], r
    z2 = dict(z, m0=np.array([선((10, 20), (90, 20))] * 2), m2=np.array([선((40, 50), (41, 50))] * 2)); r2 = 부품재기(z2); assert r2[1] >= 1 and r2[2] == 0, r2
    print("과제세뷰 시험 통과", r, r2)
