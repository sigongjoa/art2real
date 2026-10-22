# 선 정답 — 부품의 CAD 형상(B-rep 모서리 · 꼭짓점)을 도면과 같은 카메라로 투영 · 학습 없음 · 10-22
# ① 화소 지도: 128×128 화소마다 0 없음 · 1 직선 · 2 곡선(원 · 호 · 스플라인) · 3 곡면 테(모서리가 아닌 윤곽 — 원통 옆 · 구 둘레) + 숨은선 여부 + 꼭짓점 열 지도
# ② 목록: 점 [(x, y, 숨음)] · 선 [{점 a, 점 b, 종류, 숨음, 화소 꺾은선}] — 뷰마다
# 사용(cadrille · ART_MEM_GB=10): python 하네스/선정답.py 12003 → out/하네스/130CNN만/선정답_<부품>.png
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
N = 128; 축 = ((0, 1), (0, 2), (1, 2))   # 위 · 앞 · 옆 (숨은선88.그리기 와 같은 카메라)
def 화소(p):   # 정규화 좌표 (…, 2) → (열, 행)
    return (p[..., 0] + .55) / 1.1 * N - .5, (.55 - p[..., 1]) / 1.1 * N - .5
def 꼭짓점(선들, 붙음=1.5, 같은방향=15):   # 진짜 꼭짓점만: 선 끝들이 모인 자리에서 서로 다른 방향이 셋 이상 · 또는 둘이 꺾여 만남(곧게 이어지는 곡면 쪼갬 이음점은 뺌)
    끝 = [(np.array(l["끝"][k]), np.array(l["끝방향"][k])) for l in 선들 for k in (0, 1)]; 쓴 = [False] * len(끝); 점 = []
    for i, (p, _) in enumerate(끝):
        if 쓴[i]: continue
        무리 = [k for k, (q, _) in enumerate(끝) if not 쓴[k] and np.hypot(*(q - p)) < 붙음]
        for k in 무리: 쓴[k] = True
        각 = []
        for k in 무리:
            d = 끝[k][1]
            if np.hypot(*d) < 1e-6: continue
            t = np.degrees(np.arctan2(d[1], d[0]))
            if all(abs((t - u + 180) % 360 - 180) > 같은방향 for u in 각): 각.append(t)
        꺾임 = len(각) == 2 and abs(abs((각[0] - 각[1] + 180) % 360 - 180) - 180) > 20
        if len(각) >= 3 or 꺾임: c = np.mean([끝[k][0] for k in 무리], 0); 점.append((round(float(c[0]), 1), round(float(c[1]), 1)))
    return sorted(set(점))
def 계산(i):
    import 모델124 as B, 조립124 as C, 숨은선88 as H, cv2
    s = json.load(open(B.D + f"사양/{i:05d}.json", encoding="utf-8")); w = C.짓기(s["코드"]); m = C.메시(w)[0]
    c = m.bounds.mean(0); e = float(m.extents.max()); 래 = H.그리기((m.vertices - c) / e, m.faces)
    모 = []
    for ed in w.val().Edges():
        종 = ed.geomType(); 점 = (np.array([tuple(ed.positionAt(t)) for t in np.linspace(0, 1, 64)]) - c) / e
        모.append(("직선" if 종 == "LINE" else "곡선", 점, (np.array(tuple(ed.startPoint())) - c) / e, (np.array(tuple(ed.endPoint())) - c) / e))
    뷰들 = []
    for j, (a, b) in enumerate(축):
        보, 숨 = 래[j]; 선 = cv2.dilate((보 | 숨).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0; 보곁 = cv2.dilate(보.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        지도 = np.zeros((N, N), np.uint8); 숨지도 = 숨.copy(); 목록선 = []
        for 종, 점, p0, p1 in 모:
            x, y = 화소(점[:, [a, b]]); 열, 행 = np.clip(np.round(x).astype(int), 0, N - 1), np.clip(np.round(y).astype(int), 0, N - 1)
            if np.hypot(x[-1] - x[0], y[-1] - y[0]) < 1 and np.ptp(x) < 1 and np.ptp(y) < 1: continue   # 보는 방향과 나란한 모서리 → 점
            img = np.zeros((N, N), np.uint8); cv2.polylines(img, [np.c_[x, y].round().astype(np.int32)], False, 1, 1); 화 = img > 0
            if 선[화].mean() < .8: continue   # 도면에 안 그려진 모서리(곡면을 나누는 위도 · 경도 · 이음매) — 3D 샘플이 아니라 그린 화소로 잼(옆에서 본 원은 샘플이 양 끝에 몰림)
            q = np.c_[x, y]; 현 = q[-1] - q[0]; 길 = np.hypot(*현)
            휨 = (np.abs(np.cross(현, q - q[0])) / 길).max() if 길 > 1 else np.hypot(*(q - q.mean(0)).T).max()   # 현에서 가장 먼 화소 거리 · 닫힌 원은 반지름
            종2 = "직선" if 휨 < .75 else "곡선"   # 도면에 보이는 2D 모양으로 — 옆에서 본 원은 직선
            지도[화 & (지도 == 0)] = 1 if 종2 == "직선" else 2
            목록선.append({"종류": 종2, "3D종류": 종, "숨음": bool(보곁[화].mean() < .5), "끝": [q[0].round(2).tolist(), q[-1].round(2).tolist()],
                         "끝방향": [(q[min(4, len(q) - 1)] - q[0]).tolist(), (q[max(-5, -len(q))] - q[-1]).tolist()], "꺾은선": q[::2].round(1).tolist()})
        지도[(보 | 숨) & (cv2.dilate((지도 > 0).astype(np.uint8), np.ones((3, 3), np.uint8)) == 0)] = 3   # 그려졌는데 모서리가 없는 화소 = 곡면 테
        점목록 = 꼭짓점(목록선)
        yy, xx = np.mgrid[:N, :N]; 열지도 = np.zeros((N, N), np.float32)
        for u, v in 점목록: 열지도 = np.maximum(열지도, np.exp(-((xx - u) ** 2 + (yy - v) ** 2) / (2 * 1.5 ** 2)))
        뷰들.append({"보": 보, "숨": 숨, "지도": 지도, "숨지도": 숨지도, "열지도": 열지도, "점": 점목록, "선": 목록선})
    return 뷰들
def 그림(i, 뷰들, 경로):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib.colors import ListedColormap
    plt.rcParams["font.family"] = "Malgun Gothic"; 색 = {"직선": "#4a7bd1", "곡선": "#28a050"}
    fig, ax = plt.subplots(3, 3, figsize=(19, 19)); fig.suptitle(f"부품 {i:05d} — 선 정답을 CAD 형상에서 계산(학습 없음 · 격자 없음)", fontsize=22, weight="bold")
    for j, v in enumerate(뷰들):
        nm = ("위", "앞", "옆")[j]; 도 = np.full((N, N), 255, np.uint8); 도[v["숨"]] = 170; 도[v["보"]] = 0
        a = ax[j, 0]; a.imshow(도, cmap="gray", vmin=0, vmax=255); a.set_title(f"{nm} · 입력 도면", fontsize=15)
        a = ax[j, 1]; rgb = np.full((N, N, 3), 255, np.uint8)
        for k, c_ in ((1, (74, 123, 209)), (2, (40, 160, 80)), (3, (217, 160, 32))): rgb[v["지도"] == k] = c_
        rgb[(v["지도"] > 0) & v["숨"]] = (rgb[(v["지도"] > 0) & v["숨"]] * .45 + 140).astype(np.uint8)
        a.imshow(rgb); a.imshow(np.dstack([np.full((N, N), 1.), np.zeros((N, N)), np.zeros((N, N)), v["열지도"] * .9]))
        a.set_title(f"{nm} · ① 화소 지도 (파랑 직선 · 초록 곡선 · 노랑 곡면 테 · 흐림 숨은선 · 빨강 꼭짓점)", fontsize=12)
        a = ax[j, 2]; a.set_xlim(-.5, N - .5); a.set_ylim(N - .5, -.5); a.set_aspect("equal"); a.set_facecolor("white")
        for l in v["선"]:
            p = np.array(l["꺾은선"] + [l["끝"][1]]); a.plot(p[:, 0], p[:, 1], color=색[l["종류"]], lw=2.5, ls="--" if l["숨음"] else "-")
        if v["점"]: p = np.array(v["점"]); a.scatter(p[:, 0], p[:, 1], s=40, c="#d8262b", zorder=5)
        n직 = sum(l["종류"] == "직선" for l in v["선"]); n곡 = len(v["선"]) - n직; n숨 = sum(l["숨음"] for l in v["선"])
        a.set_title(f"{nm} · ② 목록: 점 {len(v['점'])} · 선 {len(v['선'])} (직선 {n직} · 곡선 {n곡} · 숨음 {n숨})", fontsize=13)
        for a in ax[j]: a.set_xticks([]); a.set_yticks([])
    fig.savefig(경로, dpi=55, bbox_inches="tight"); plt.close(fig)
저장 = f"{뿌리}/out/하네스/선정답/"; M점 = 96
def _하나(i):   # 부품 하나 → 저장/<i>.npz (지도 3×128×128 · 숨 · 꼭짓점 3×96×2 NaN 채움) · 실패는 .err
    p = 저장 + f"{i:05d}.npz"
    if os.path.exists(p) or os.path.exists(p + ".err"): return
    try:
        뷰들 = 계산(i); 점 = np.full((3, M점, 2), np.nan, np.float32)
        for j, v in enumerate(뷰들): q = np.array(v["점"][:M점], np.float32).reshape(-1, 2); 점[j, :len(q)] = q
        np.savez_compressed(p, 지도=np.stack([v["지도"] for v in 뷰들]), 숨=np.stack([v["숨지도"] for v in 뷰들]), 점=점)
    except Exception as ex: open(p + ".err", "w", encoding="utf-8").write(str(ex)[:300])
def 번호들(학습수=3000):
    import 모델124 as B; 이 = [r["i"] for r in B.색인()]; return [i for i in 이 if i < B.NT][:학습수] + [i for i in 이 if i >= B.NT]
def 모두(학습수=3000, 일꾼=6, 초=120):   # 부품마다 새 프로세스 · 초 넘으면 죽이고 .err(10-22: Pool 일꾼이 OCC 합치기에 30 분 넘게 멈춤 · 오래 산 일꾼은 IVtkOCC import 가 깨져 시험 271 실패)
    import time, multiprocessing as mp
    os.makedirs(저장, exist_ok=True); 일 = [i for i in 번호들(학습수) if not os.path.exists(저장 + f"{i:05d}.npz") and not os.path.exists(저장 + f"{i:05d}.npz.err")]; 도는 = {}; 끝낸 = 0
    print("남음", len(일), flush=True)
    while 일 or 도는:
        while 일 and len(도는) < 일꾼: i = 일.pop(0); p = mp.Process(target=_하나, args=(i,)); p.start(); 도는[i] = (p, time.time())
        for i, (p, t) in list(도는.items()):
            if not p.is_alive(): p.join(); del 도는[i]; 끝낸 += 1; 끝낸 % 50 == 0 and print(끝낸, flush=True)
            elif time.time() - t > 초: p.kill(); p.join(); open(저장 + f"{i:05d}.npz.err", "w", encoding="utf-8").write(f"시간 초과 {초} 초"); del 도는[i]; 끝낸 += 1
        time.sleep(.2)
    print("끝 · 실패", len([f for f in os.listdir(저장) if f.endswith(".err")]), flush=True)
if __name__ == "__main__" and sys.argv[1] == "모두": 모두(int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
elif __name__ == "__main__":
    i = int(sys.argv[1]); 뷰들 = 계산(i); d = f"{뿌리}/out/하네스/130CNN만/"; os.makedirs(d, exist_ok=True); 그림(i, 뷰들, d + f"선정답_{i:05d}.png")
    json.dump([{"점": v["점"], "선": v["선"]} for v in 뷰들], open(d + f"선정답_{i:05d}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in enumerate(뷰들): print(("위", "앞", "옆")[k], "점", len(v["점"]), "선", len(v["선"]), "화소", {n: int((v["지도"] == q).sum()) for q, n in ((1, "직선"), (2, "곡선"), (3, "곡면테"))})
