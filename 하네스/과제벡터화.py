# 하네스 과제 「벡터화」 — 학습 없음 · 선지도 판(137)이 칠한 화소 → 선 목록(선마다 토큰 한 줄: 뷰 · 종류 · 시작 · 끝 · 휨 · 숨음) · 정답 모서리(CAD 투영)와 맞춰 잼 · 10-24
# 순서: 선 화소 → 1 화소 뼈대 → 마디(꼭짓점 열지도 봉우리 + 뼈대 끝 · 갈림) → 마디 사이 가지 → 가지마다 휨(현에서 가장 먼 화소) ≥ 휨문턱 이면 원(호)을 대어 보고 안 맞으면 꺾은 점에서 직선으로 쪼갬
# 종류는 눈 기준(10-23: 정답 곡선 55 % 가 1.5 화소도 안 휨) — 정답 · 예측 모두 같은 휨문턱으로 다시 정함
# 대조 = 같은 벡터화를 정답 선지도(입력 선에 맞춘 것)에 돌린 값(천장) · 지표 끝에 _정답
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
뷰이름 = ["위", "앞", "옆"]
def 휨(yx, a, b):   # 현 a-b 에서 가장 먼 화소 거리
    현 = yx[b] - yx[a]; 길 = np.hypot(*현)
    if 길 < 1: return float(np.hypot(*(yx - yx.mean(0)).T).max())
    return float((np.abs(현[0] * (yx[:, 1] - yx[a, 1]) - 현[1] * (yx[:, 0] - yx[a, 0])) / 길).max())
def 먼쌍(yx):
    d = ((yx[:, None] - yx[None]) ** 2).sum(-1); return np.unravel_index(d.argmax(), d.shape)
def 줄세우기(px):   # 가지 화소(집합) → 한쪽 끝에서 따라 걸은 순서
    s = {tuple(p) for p in px}; 이웃 = lambda p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and (p[0] + dy, p[1] + dx) in s]
    끝 = [p for p in s if len(이웃(p)) <= 1]; p = 끝[0] if 끝 else next(iter(s)); 길 = [p]; 본 = {p}
    while True:
        n = [q for q in 이웃(p) if q not in 본]
        if not n: break
        p = min(n, key=lambda q: abs(q[0] - p[0]) + abs(q[1] - p[1])); 길.append(p); 본.add(p)   # 곧은 이웃 먼저
    return np.array(길), not 끝
def 원맞춤(yx):   # 대수 원 맞춤 → (잔차 RMS, 반지름)
    y, x = yx[:, 0].astype(float), yx[:, 1].astype(float); A = np.c_[x, y, np.ones_like(x)]; b = -(x ** 2 + y ** 2)
    c = np.linalg.lstsq(A, b, rcond=None)[0]; cx, cy = -c[0] / 2, -c[1] / 2; r = np.sqrt(max(cx ** 2 + cy ** 2 - c[2], 1e-9))
    return float(np.sqrt(((np.hypot(x - cx, y - cy) - r) ** 2).mean())), float(r)
def 벡터화(있, 열=None, 숨=None, 휨문턱=2., 최소=3, 이음=False, 숨메움=False):   # 있: (128, 128) bool · 열: 꼭짓점 열지도 · 숨: 숨은선 확률/여부 → [선] · 이음(141): 마디를 봉우리 한 화소로 · 짧은 조각 남겨 잇기 · 끝에 잇기()
    import cv2
    from skimage.morphology import skeletonize
    if 숨메움 and 숨 is not None:   # 143: 도면 점선이 화면 대각 줄무늬((x + y) // 3 % 2 · 모델123.그림)로 잘려 붙은 숨은선 띠가 빗금(/) 기둥이 됨 → 숨은선 화소만 5×5 로 메워 띠 하나로 · 실선 곁 1 화소엔 안 메움
        숨선 = (있 & (숨 > .5)).astype(np.uint8); 실곁 = cv2.dilate((있 & ~(숨 > .5)).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        더 = (cv2.morphologyEx(숨선, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0) & ~있 & ~실곁; 있 = 있 | 더; 숨 = (숨 > .5) | 더
    sk = skeletonize(있).astype(np.uint8); 이 = cv2.filter2D(sk, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - sk
    마 = (sk > 0) & (이 != 2)
    if 열 is not None:
        봉 = (열 == cv2.dilate(열, np.ones((5, 5), np.uint8))) & (열 > .3)
        if 이음:   # 140: 봉우리 둘레 3×3 을 다 마디로 → 가까운 꼭짓점 사이 짧은 모서리가 마디에 먹혀 사라짐(놓친 것 59 % 가 6 화소 이하) → 봉우리에서 가장 가까운 뼈대 한 화소만
            뼈 = np.argwhere(sk > 0)
            for q in np.argwhere(봉):
                if len(뼈): d = np.abs(뼈 - q).max(1); i = d.argmin(); 마[tuple(뼈[i])] |= d[i] <= 2
        else: 마 |= (cv2.dilate(봉.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (sk > 0)
    가 = (sk > 0) & ~마; n, 라 = cv2.connectedComponents(가.astype(np.uint8), connectivity=8); 선들 = []
    for k in range(1, n):
        px = np.argwhere(라 == k)
        곁마 = np.argwhere((cv2.dilate((라 == k).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & 마)   # 붙은 마디 화소를 다시 붙여 선이 꼭짓점까지 닿게
        if len(px) + len(곁마) < (2 if 이음 else 최소): continue
        길, 닫힘 = 줄세우기(np.r_[px, 곁마] if len(곁마) <= 2 else px)
        for 조각 in 쪼개기(길, 닫힘, 휨문턱):
            a, b = (0, len(조각) - 1); h = 휨(조각, a, b) if not 닫힘 else 휨(조각, *먼쌍(조각))
            m = np.zeros((128, 128), bool); m[조각[:, 0], 조각[:, 1]] = True
            숨음 = bool(숨[m].mean() > .5) if 숨 is not None else False
            선들.append({"종류": "원호" if h >= 휨문턱 else "직선", "시작": 조각[0][::-1].tolist(), "끝": 조각[-1][::-1].tolist(), "휨": round(h, 1), "숨음": 숨음, "중간": 조각[len(조각) // 2][::-1].tolist(), "_m": m, "_p": 조각})
    if 이음: 선들 = [l for l in 잇기(선들, 휨문턱, 숨) if l["_m"].sum() >= 최소]
    return 선들
def 선만들기(p, 휨문턱, 숨):
    m = np.zeros((128, 128), bool); m[p[:, 0], p[:, 1]] = True; h = 휨(p, 0, len(p) - 1)
    return {"종류": "원호" if h >= 휨문턱 else "직선", "시작": p[0][::-1].tolist(), "끝": p[-1][::-1].tolist(), "휨": round(h, 1), "숨음": bool(숨[m].mean() > .5) if 숨 is not None else False, "중간": p[len(p) // 2][::-1].tolist(), "_m": m, "_p": p}
def 잇기(선들, 휨문턱, 숨, 점선틈=4., 닿음=2.):   # 141: ① 같은 방향 직선 토막(점선 · 마디로 잘린 직선)은 틈 4 화소까지 한 선으로 ② 끝이 닿은 두 조각이 원 하나에 맞으면(잔차 0.8) 한 원호로
    import cv2
    def 선채움(a, b):   # 틈을 화소로 메움
        m = np.zeros((128, 128), np.uint8); cv2.line(m, tuple(int(v) for v in a[::-1]), tuple(int(v) for v in b[::-1]), 1, 1); return np.argwhere(m > 0)
    바뀜 = True
    while 바뀜:
        바뀜 = False
        for i in range(len(선들)):
            for j in range(i + 1, len(선들)):
                A, B = 선들[i]["_p"], 선들[j]["_p"]
                짝 = min(((np.hypot(*(A[ia] - B[ib])), ia, ib) for ia in (0, -1) for ib in (0, -1)), key=lambda t: t[0]); d, ia, ib = 짝
                if d > 점선틈: continue
                a = A[::-1] if ia == 0 else A; b = B if ib == 0 else B[::-1]   # a 끝 → b 시작
                새 = None
                if 선들[i]["종류"] == "직선" and 선들[j]["종류"] == "직선" and len(a) >= 2 and len(b) >= 2:
                    u = (a[-1] - a[0]) / max(np.hypot(*(a[-1] - a[0])), 1e-6); w = (b[-1] - b[0]) / max(np.hypot(*(b[-1] - b[0])), 1e-6)
                    옆 = abs(u[0] * (b[-1] - a[0])[1] - u[1] * (b[-1] - a[0])[0])
                    if u @ w > np.cos(np.radians(10)) and 옆 < 1.5: 새 = np.r_[a, 선채움(a[-1], b[0]), b]
                if 새 is None and d <= 닿음 and "원호" in (선들[i]["종류"], 선들[j]["종류"]) and len(a) + len(b) >= 6:
                    합 = np.r_[a, b]; rms, r = 원맞춤(합)
                    if rms < .8 and r < 200: 새 = np.r_[a, 선채움(a[-1], b[0]), b]
                if 새 is not None:
                    _, 순 = np.unique(새, axis=0, return_index=True); 새 = 새[np.sort(순)]
                    선들[i] = 선만들기(새, 휨문턱, 숨); 선들.pop(j); 바뀜 = True; break
            if 바뀜: break
    return 선들
def 쪼개기(길, 닫힘, 휨문턱):   # 휜 가지: 원에 잘 맞으면 원호 하나 · 아니면 꺾은 점(Douglas-Peucker 1.5 화소)에서 직선들로
    import cv2
    if len(길) < 4 or 휨(길, 0, len(길) - 1) < 휨문턱: return [길]
    rms, r = 원맞춤(길)
    if rms < .8 and r < 200: return [길]
    꼭 = cv2.approxPolyDP(길[:, None, ::-1].astype(np.int32), 1.5, 닫힘)[:, 0, ::-1]
    자리 = sorted({int(np.argmin(np.abs(길 - q).sum(1))) for q in 꼭} | {0, len(길) - 1})
    return [길[i:j + 1] for i, j in zip(자리[:-1], 자리[1:]) if j - i >= 2] or [길]
윤곽저장 = f"{뿌리}/out/하네스/윤곽/"
def _윤곽(i):   # 144: 둥근 면의 윤곽선(곡면 테) — CAD 모서리가 아니라 정답에서 빠졌음(12050 앞 · 옆 입력 선의 약 20 %) · 메시에서 뷰 방향으로 앞면 · 뒷면이 바뀌는 매끈한 이음(이면각 < 40°) → 이어진 무리마다 마스크
    p = 윤곽저장 + f"{i:05d}.npz"
    if os.path.exists(p): return
    try:
        import cv2, 선정답 as S, 모델124 as B, 조립124 as C, 숨은선88 as H
        sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
        s = json.load(open(B.D + f"사양/{i:05d}.json", encoding="utf-8")); w = C.짓기(s["코드"]); m = C.메시(w)[0]
        c = m.bounds.mean(0); e = float(m.extents.max()); V = (m.vertices - c) / e; 래 = H.그리기(V, m.faces)
        adj, ae, ang, N = m.face_adjacency, m.face_adjacency_edges, m.face_adjacency_angles, m.face_normals; 짐 = {}
        for j, (a, b) in enumerate(S.축):
            d = 3 - a - b; sn = N[:, d]; 뒤 = (sn[adj[:, 0]] * sn[adj[:, 1]] < 0) & (ang < np.radians(40)); E = ae[뒤]
            보, 숨 = 래[j]; 선 = cv2.dilate((보 | 숨).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0; ms = []
            if len(E):   # 꼭짓점을 공유하는 이음끼리 한 무리
                부 = {}
                def 뿌(k):
                    while 부.setdefault(k, k) != k: 부[k] = 부[부[k]]; k = 부[k]
                    return k
                for u, v in E: 부[뿌(u)] = 뿌(v)
                무 = {}
                for u, v in E: 무.setdefault(뿌(u), []).append((u, v))
                for 이음들 in 무.values():
                    img = np.zeros((128, 128), np.uint8)
                    for u, v in 이음들:
                        x, y = S.화소(V[[u, v]][:, [a, b]]); cv2.line(img, (int(round(x[0])), int(round(y[0]))), (int(round(x[1])), int(round(y[1]))), 1, 1)
                    화 = img > 0
                    if 화.sum() >= 3 and 선[화].mean() >= .8: ms.append(np.packbits(화))
            짐[f"m{j}"] = np.array(ms) if ms else np.zeros((0, 2048), np.uint8)
        np.savez_compressed(p, **짐)
    except Exception as ex: open(p + ".err", "w", encoding="utf-8").write(str(ex)[:300])
def 윤곽들(일꾼=6, 초=120):   # 시험 부품 전부 · 부품마다 프로세스 · 시간 상한
    import time, multiprocessing as mp
    sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품"); import 모델124 as B
    os.makedirs(윤곽저장, exist_ok=True); 일 = [r["i"] for r in B.색인() if r["i"] >= B.NT]; 일 = [i for i in 일 if not os.path.exists(윤곽저장 + f"{i:05d}.npz")]; 도는 = {}
    while 일 or 도는:
        while 일 and len(도는) < 일꾼: i = 일.pop(); pr = mp.Process(target=_윤곽, args=(i,)); pr.start(); 도는[i] = (pr, time.time())
        for i, (pr, t) in list(도는.items()):
            if not pr.is_alive(): 도는.pop(i)
            elif time.time() - t > 초: pr.kill(); 도는.pop(i); open(윤곽저장 + f"{i:05d}.npz.err", "w", encoding="utf-8").write("시간 넘음")
        time.sleep(.2)
def 정답선(부품, v, 휨문턱=2., 윤곽=False):   # 겹침 npz 모서리 마스크 → 눈 기준 종류 · 윤곽(144~): 곡면 테 윤곽선도 정답 선으로(「윤곽」 표시)
    import 공통자
    out = []
    for m, _, 상 in 공통자.모서리(부품, v):
        yx = np.argwhere(m); h = 휨(yx, *먼쌍(yx)) if len(yx) > 1 else 0
        out.append({"종류": "원호" if h >= 휨문턱 else "직선", "_m": m, "상황": 상})
    if 윤곽 and os.path.exists(윤곽저장 + f"{부품}.npz"):
        z = np.load(윤곽저장 + f"{부품}.npz")
        if len(z[f"m{v}"]):
            for m in np.unpackbits(z[f"m{v}"], axis=1)[:, :128 * 128].reshape(-1, 128, 128).astype(bool):
                yx = np.argwhere(m); h = 휨(yx, *먼쌍(yx)) if len(yx) > 1 else 0
                out.append({"종류": "원호" if h >= 휨문턱 else "직선", "_m": m, "상황": 0 if h < 휨문턱 else 1, "윤곽": True})
    return out
def 맞추기(정, 예, 거리=2., 덮음=.7):   # 정답 모서리 · 예측 선을 화소 덮음으로 짝(둘 다 서로를 70 % 이상 2 화소 안에서 덮음) · 욕심 짝
    import cv2
    if not 정 or not 예: return []
    거정 = [cv2.distanceTransform((~e["_m"]).astype(np.uint8), cv2.DIST_L2, 3) for e in 정]; 거예 = [cv2.distanceTransform((~l["_m"]).astype(np.uint8), cv2.DIST_L2, 3) for l in 예]
    후보 = []
    for i, e in enumerate(정):
        for j, l in enumerate(예):
            a = (거예[j][e["_m"]] <= 거리).mean(); b = (거정[i][l["_m"]] <= 거리).mean()
            if a >= 덮음 and b >= 덮음: 후보.append((a * b, i, j))
    짝, 쓴i, 쓴j = [], set(), set()
    for s, i, j in sorted(후보, reverse=True):
        if i not in 쓴i and j not in 쓴j: 짝.append((i, j)); 쓴i.add(i); 쓴j.add(j)
    return 짝
def 재기(쌍들, 거리=2., 덮음=.7):   # [(정답 선들, 예측 선들, 곡면 테, 정답 숨은선 지도)] → 지표 · 덮음으로 셈(10-24: 일대일 짝은 포갠 모서리를 놓침으로 셌다 — F1 정답 0.20)
    # 끊김(143~): 찾은 정답 모서리가 선 여럿으로 덮였고 그 선 끝 하나가 모서리 가운데(양 끝 3 화소 밖)에 있는데 2 화소 안에 다른 정답 모서리가 없음 = 갈림목 아닌 데서 끊김(141 「한선」은 갈림목 끊김까지 셌음)
    import cv2
    import collections; 합 = collections.Counter()   # 칸을 미리 안 적어도 0 에서 시작(143 첫 판: 끊김_보임 · 종_숨 칸이 없어 멈춤)
    for 쌍 in 쌍들:
        정, 예, 테, 숨지 = (list(쌍) + [None, None])[:4]
        합["정수"] += len(정); 합["예수"] += len(예)
        숨들 = [bool(숨지[e["_m"]].mean() > .5) if 숨지 is not None else False for e in 정]
        for h in 숨들: 합["정_숨" if h else "정_보임"] += 1
        합["정_윤곽"] += sum(bool(e.get("윤곽")) for e in 정)
        if not 예 or not 정: continue
        거예 = [cv2.distanceTransform((~l["_m"]).astype(np.uint8), cv2.DIST_L2, 3) <= 거리 for l in 예]
        모정 = np.zeros((128, 128), bool)
        for e in 정: 모정 |= e["_m"]
        if 테 is not None: 모정 |= 테
        곁정 = cv2.distanceTransform((~모정).astype(np.uint8), cv2.DIST_L2, 3) <= 거리
        합["정밀"] += sum(곁정[l["_m"]].mean() >= 덮음 for l in 예)
        for i, e in enumerate(정):
            m = e["_m"]; n = m.sum(); 몫 = np.array([g[m].sum() for g in 거예]); 덮 = np.zeros((128, 128), bool)
            for g, c in zip(거예, 몫):
                if c >= 3: 덮 |= g
            if (덮[m].sum() / n) < 덮음: continue
            꼬 = "_숨" if 숨들[i] else "_보임"; 합["재"] += 1; 합["재" + 꼬] += 1; 쓴 = 몫 >= 3; 합["조"] += int(쓴.sum()); 한선 = 몫.max() / n >= 덮음; 합["한"] += 한선
            표 = {"직선": 0, "원호": 0}
            for l, c in zip(예, 몫): 표[l["종류"]] += c
            맞 = max(표, key=표.get) == e["종류"]; 합["종"] += 맞; 합["종" + 꼬] += 맞
            if e.get("윤곽"): 합["재_윤곽"] += 1; 합["종_윤곽"] += 맞
            if 한선 or 쓴.sum() < 2: continue
            남 = np.zeros((128, 128), bool)
            for j, f in enumerate(정):
                if j != i: 남 |= f["_m"]
            곁남 = cv2.distanceTransform((~남).astype(np.uint8), cv2.DIST_L2, 3) <= 2; yx = np.argwhere(m); 양끝 = [yx[d] for d in 먼쌍(yx)]
            끊 = any(not 곁남[tuple(q)] and min(np.abs(q - t).sum() for t in 양끝) > 3 and m[max(q[0] - 2, 0):q[0] + 3, max(q[1] - 2, 0):q[1] + 3].any()
                    for l, c in zip(예, 몫) if c >= 3 for q in (l["_p"][0], l["_p"][-1]) if "_p" in l)
            합["끊김"] += 끊; 합["끊김" + 꼬] += 끊
    r재, r정 = 합["재"] / max(합["정수"], 1), 합["정밀"] / max(합["예수"], 1)
    return {"벡_재현": round(r재, 4), "벡_정밀": round(float(r정), 4), "벡_F1": round(float(2 * r재 * r정 / max(r재 + r정, 1e-9)), 4), "벡_종류": round(합["종"] / max(합["재"], 1), 4),
            "벡_조각": round(합["조"] / max(합["재"], 1), 4), "벡_한선": round(float(합["한"] / max(합["재"], 1)), 4), "벡_끊김": round(float(합["끊김"] / max(합["재"], 1)), 4),
            "벡_재현_보임": round(합["재_보임"] / max(합["정_보임"], 1), 4), "벡_종류_보임": round(합["종_보임"] / max(합["재_보임"], 1), 4),
            "벡_재현_숨": round(합["재_숨"] / max(합["정_숨"], 1), 4), "벡_끊김_숨": round(float(합["끊김_숨"] / max(합["재_숨"], 1)), 4),
            "벡_재현_윤곽": round(합["재_윤곽"] / max(합["정_윤곽"], 1), 4), "벡_종류_윤곽": round(합["종_윤곽"] / max(합["재_윤곽"], 1), 4), "벡_윤곽수": int(합["정_윤곽"])}
def 점검(cfg, 폴더):   # 하네스가 부름(학습 없음) — 입력 판 모델로 시험 부품 예측 → 벡터화 → 정답과 맞춤 · 같은 벡터화를 정답 선지도에(대조 · 천장)
    import torch, 과제선지도 as G, 분석그림 as A, 겹침그림 as Q
    from omegaconf import OmegaConf
    s = cfg.벡터화
    if s.get("윤곽정답"): 윤곽들()
    판 = str(s.입력판); c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); X, Y, _, idx, vx, 이, Xnp = G.자료("cuda", c)
    o = G.예측(A.불러(판).cuda(), X[vx])[:, :, :G.출].float(); pr = o[:, :, :G.K].softmax(2)
    있 = (1 - pr[:, :, 0] > .5).cpu().numpy(); 열 = torch.sigmoid(o[:, :, G.K + 1]).cpu().numpy(); 숨 = (o[:, :, G.K] > 0).cpu().numpy()
    정지 = Y["지도"][vx].cpu().numpy(); 정열 = Y["열"][vx].float().cpu().numpy(); 정숨 = Y["숨"][vx].cpu().numpy(); 부품들 = [이[int(j)] for j in vx.tolist()]
    예쌍, 천쌍, 보기, 대쌍 = [], [], [], []
    for k, 부품 in enumerate(부품들):
        if not os.path.exists(Q.저장 + f"{부품}.npz"): continue
        for v in range(3):
            손 = {"이음": bool(s.get("이음", False)), "숨메움": bool(s.get("숨메움", False))}; 정 = 정답선(부품, v, s.휨문턱, 윤곽=bool(s.get("윤곽정답", False)))
            예 = 벡터화(있[k, v], 열[k, v], 숨[k, v], s.휨문턱, **손); 천 = 벡터화(정지[k, v] > 0, 정열[k, v], 정숨[k, v], s.휨문턱, **손)
            테 = 정지[k, v] == 3; 예쌍.append((정, 예, 테, 정숨[k, v])); 천쌍.append((정, 천, 테, 정숨[k, v]))
            if s.get("대조손잡이"): 대쌍.append((정, 벡터화(있[k, v], 열[k, v], 숨[k, v], s.휨문턱, **(손 | {str(s.대조손잡이): False})), 테, 정숨[k, v]))
            if 부품 == "12050": 보기.append((v, 정, 예, Xnp[이.index(부품), v], 테))
    지 = 재기(예쌍) | {f"{k}_정답": v for k, v in 재기(천쌍).items()}
    if 대쌍:   # 판 안 대조: 같은 입력 · 대조손잡이만 끈 계산 → _대조 · _차(이 판 − 대조) · 끊김_숨 비(이 판 / 대조)
        대 = 재기(대쌍); 지 |= {f"{k}_대조": v for k, v in 대.items()} | {f"{k}_차": round(지[k] - 대[k], 4) for k in 대}; 지["벡_끊김_숨_비"] = round(지["벡_끊김_숨"] / max(대["벡_끊김_숨"], 1e-9), 4)
    토큰 = [[뷰이름[v], l["종류"], *l["시작"], *l["끝"], l["휨"], "예" if l["숨음"] else "아니오"] for v, _, 예, _, _ in 보기 for l in 예]
    json.dump(토큰, open(폴더 + "토큰_12050.json", "w", encoding="utf-8"), ensure_ascii=False)
    그림(폴더, 보기); return 지
def 맞은선(정, 예, 테, 거리=2., 덮음=.7):   # 정답 모서리 · 곡면 테 위에 70 % 이상 있는 예측 선 번호
    import cv2
    모 = np.zeros((128, 128), bool)
    for e in 정: 모 |= e["_m"]
    if 테 is not None: 모 |= 테
    곁 = cv2.distanceTransform((~모).astype(np.uint8), cv2.DIST_L2, 3) <= 거리; return {j for j, l in enumerate(예) if 곁[l["_m"]].mean() >= 덮음}
def 그림(폴더, 보기):   # 부품 12050 세 뷰: 입력 · 정답 모서리 · 예측 선(짝 맞은 선 = 종류 색 · 짝 없는 선 = 빨강)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from PIL import Image
    plt.rcParams["font.family"] = "Malgun Gothic"; 색 = {"직선": np.array([74, 123, 209]), "원호": np.array([40, 160, 80])}
    def 칠(선들, 맞은=None):
        im = np.full((128, 128, 3), 255, np.uint8)
        for i, l in enumerate(선들): im[l["_m"]] = 색[l["종류"]] if 맞은 is None or i in 맞은 else (216, 38, 43)
        return im
    fig, ax = plt.subplots(len(보기), 3, figsize=(15, 5.2 * len(보기))); fig.suptitle("벡터화 — 입력 · 정답 모서리 · 계산으로 뽑은 선(빨강 = 정답 모서리 · 곡면 테 위가 아님) · 부품 12050", fontsize=18, weight="bold")
    for r, (v, 정, 예, x, 테) in enumerate(보기):
        짝 = 맞은선(정, 예, 테)
        for c, (im, t) in enumerate(((255 - x, f"입력 {뷰이름[v]}"), (칠(정), f"정답 {len(정)} 선"), (칠(예, 짝), f"벡터화 {len(예)} 선 · 맞음 {len(짝)}"))):
            ax[r, c].imshow(im, cmap="gray" if c == 0 else None); ax[r, c].set_title(t, fontsize=14); ax[r, c].axis("off")
    fig.savefig(폴더 + "시트.png", dpi=60, bbox_inches="tight"); plt.close(fig)
    v, 정, 예, x, 테 = 보기[1] if len(보기) > 1 else 보기[0]
    Image.fromarray(np.kron(칠(정), np.ones((5, 5, 1), np.uint8))).save(폴더 + "정답.png"); Image.fromarray(np.kron(칠(예, 맞은선(정, 예, 테)), np.ones((5, 5, 1), np.uint8))).save(폴더 + "예측전체.png")
    Image.fromarray(np.kron(255 - x, np.ones((5, 5), np.uint8))).save(폴더 + "도면_앞.png")
if __name__ == "__main__":   # 자체 시험: ㄱ 자(직선 둘) · 반원(원호 하나) · 닫힌 원 → 벡터화가 정답과 다 짝
    import cv2
    im = np.zeros((128, 128), np.uint8); cv2.line(im, (10, 20), (60, 20), 1, 1); cv2.line(im, (60, 20), (60, 70), 1, 1)
    cv2.ellipse(im, (95, 40), (20, 20), 0, 0, 180, 1, 1); cv2.circle(im, (40, 100), 15, 1, 1)
    열 = np.zeros((128, 128), np.float32); 열[20, 60] = 1.; 열[20, 10] = 1.; 열[70, 60] = 1.
    예 = 벡터화(im > 0, 열); 종 = sorted(l["종류"] for l in 예); assert 종 == ["원호", "원호", "직선", "직선"], [(l["종류"], l["시작"], l["끝"], l["휨"]) for l in 예]
    정 = [{"종류": l["종류"], "_m": l["_m"]} for l in 예]; r = 재기([(정, 예)]); assert r["벡_F1"] == 1 and r["벡_종류"] == 1, r
    r = 재기([(정, 예[:2])]); assert r["벡_재현"] == .5 and r["벡_정밀"] == 1, r
    r = 재기([(정 + 정, 예)]); assert r["벡_재현"] == 1 and r["벡_F1"] == 1, r   # 투영에서 포갠 모서리 둘 = 선 하나로 다 덮임
    점 = np.zeros((128, 128), np.uint8)   # 141 이음: 점선(3 화소 선 · 2 화소 틈) → 한 선 · 마디로 둘이 된 반원 → 한 원호
    for x0 in range(10, 100, 5): cv2.line(점, (x0, 110), (x0 + 2, 110), 1, 1)
    예2 = 벡터화(점 > 0, 이음=True); assert len(예2) == 1 and 예2[0]["종류"] == "직선", [(l["시작"], l["끝"]) for l in 예2]
    assert len(벡터화(점 > 0)) > 1   # 이음 없으면 토막
    반 = np.zeros((128, 128), np.uint8); cv2.ellipse(반, (60, 60), (30, 30), 0, 0, 180, 1, 1); 열2 = np.zeros((128, 128), np.float32); 열2[90, 60] = 1.
    예3 = 벡터화(반 > 0, 열2, 이음=True); assert len(예3) == 1 and 예3[0]["종류"] == "원호", [(l["종류"], l["시작"], l["끝"]) for l in 예3]
    긴 = np.zeros((128, 128), bool); 긴[50, 10:100] = True; 반쪽 = [dict(l) for l in 벡터화(긴)]   # 갈림목 없는 데서 둘로 끊긴 보이는 선 → 끊김 1
    a, b = 긴.copy(), 긴.copy(); a[50, 55:] = False; b[50, :56] = False; 끊은 = [선만들기(np.argwhere(a), 2., None), 선만들기(np.argwhere(b), 2., None)]
    r = 재기([([{"종류": "직선", "_m": 긴}], 끊은, None, np.zeros((128, 128)))]); assert r["벡_끊김"] == 1 and r["벡_재현_보임"] == 1, r
    yy, xx = np.mgrid[:128, :128]; 띠 = np.zeros((128, 128), bool); 띠[10:110, 60:63] = True; 띠 &= ((xx + yy) // 3) % 2 == 0   # 143: 도면과 같은 대각 줄무늬로 자른 숨은선 띠
    예4 = 벡터화(띠, 숨=띠.astype(float), 이음=True, 숨메움=True); assert len(예4) == 1 and 예4[0]["종류"] == "직선", [(l["시작"], l["끝"]) for l in 예4]
    assert len(벡터화(띠, 숨=띠.astype(float), 이음=True)) > 5   # 메움 없으면 빗금 토막
    print("과제벡터화 시험 통과", 재기([(정, 예)]))
