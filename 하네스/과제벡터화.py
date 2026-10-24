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
def 벡터화(있, 열=None, 숨=None, 휨문턱=2., 최소=3):   # 있: (128, 128) bool · 열: 꼭짓점 열지도 · 숨: 숨은선 확률/여부 → [선]
    import cv2
    from skimage.morphology import skeletonize
    sk = skeletonize(있).astype(np.uint8); 이 = cv2.filter2D(sk, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - sk
    마 = (sk > 0) & (이 != 2)
    if 열 is not None:
        봉 = (열 == cv2.dilate(열, np.ones((5, 5), np.uint8))) & (열 > .3); 마 |= (cv2.dilate(봉.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (sk > 0)
    가 = (sk > 0) & ~마; n, 라 = cv2.connectedComponents(가.astype(np.uint8), connectivity=8); 선들 = []
    for k in range(1, n):
        px = np.argwhere(라 == k)
        곁마 = np.argwhere((cv2.dilate((라 == k).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & 마)   # 붙은 마디 화소를 다시 붙여 선이 꼭짓점까지 닿게
        if len(px) + len(곁마) < 최소: continue
        길, 닫힘 = 줄세우기(np.r_[px, 곁마] if len(곁마) <= 2 else px)
        for 조각 in 쪼개기(길, 닫힘, 휨문턱):
            a, b = (0, len(조각) - 1); h = 휨(조각, a, b) if not 닫힘 else 휨(조각, *먼쌍(조각))
            m = np.zeros((128, 128), bool); m[조각[:, 0], 조각[:, 1]] = True
            숨음 = bool(숨[m].mean() > .5) if 숨 is not None else False
            선들.append({"종류": "원호" if h >= 휨문턱 else "직선", "시작": 조각[0][::-1].tolist(), "끝": 조각[-1][::-1].tolist(), "휨": round(h, 1), "숨음": 숨음, "중간": 조각[len(조각) // 2][::-1].tolist(), "_m": m})
    return 선들
def 쪼개기(길, 닫힘, 휨문턱):   # 휜 가지: 원에 잘 맞으면 원호 하나 · 아니면 꺾은 점(Douglas-Peucker 1.5 화소)에서 직선들로
    import cv2
    if len(길) < 4 or 휨(길, 0, len(길) - 1) < 휨문턱: return [길]
    rms, r = 원맞춤(길)
    if rms < .8 and r < 200: return [길]
    꼭 = cv2.approxPolyDP(길[:, None, ::-1].astype(np.int32), 1.5, 닫힘)[:, 0, ::-1]
    자리 = sorted({int(np.argmin(np.abs(길 - q).sum(1))) for q in 꼭} | {0, len(길) - 1})
    return [길[i:j + 1] for i, j in zip(자리[:-1], 자리[1:]) if j - i >= 2] or [길]
def 정답선(부품, v, 휨문턱=2.):   # 겹침 npz 모서리 마스크 → 눈 기준 종류
    import 공통자
    out = []
    for m, _, 상 in 공통자.모서리(부품, v):
        yx = np.argwhere(m); h = 휨(yx, *먼쌍(yx)) if len(yx) > 1 else 0
        out.append({"종류": "원호" if h >= 휨문턱 else "직선", "_m": m, "상황": 상})
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
def 재기(쌍들):   # [(정답 선들, 예측 선들)] → 지표
    정수 = 예수 = 맞 = 종 = 0
    for 정, 예 in 쌍들:
        짝 = 맞추기(정, 예); 정수 += len(정); 예수 += len(예); 맞 += len(짝); 종 += sum(정[i]["종류"] == 예[j]["종류"] for i, j in 짝)
    재, 정밀 = 맞 / max(정수, 1), 맞 / max(예수, 1)
    return {"벡_재현": round(재, 4), "벡_정밀": round(정밀, 4), "벡_F1": round(2 * 재 * 정밀 / max(재 + 정밀, 1e-9), 4), "벡_종류": round(종 / max(맞, 1), 4), "벡_조각": round(예수 / max(정수, 1), 4)}
def 점검(cfg, 폴더):   # 하네스가 부름(학습 없음) — 입력 판 모델로 시험 부품 예측 → 벡터화 → 정답과 맞춤 · 같은 벡터화를 정답 선지도에(대조 · 천장)
    import torch, 과제선지도 as G, 분석그림 as A, 겹침그림 as Q
    from omegaconf import OmegaConf
    s = cfg.벡터화; 판 = str(s.입력판); c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); X, Y, _, idx, vx, 이, Xnp = G.자료("cuda", c)
    o = G.예측(A.불러(판).cuda(), X[vx])[:, :, :G.출].float(); pr = o[:, :, :G.K].softmax(2)
    있 = (1 - pr[:, :, 0] > .5).cpu().numpy(); 열 = torch.sigmoid(o[:, :, G.K + 1]).cpu().numpy(); 숨 = (o[:, :, G.K] > 0).cpu().numpy()
    정지 = Y["지도"][vx].cpu().numpy(); 정열 = Y["열"][vx].float().cpu().numpy(); 정숨 = Y["숨"][vx].cpu().numpy(); 부품들 = [이[int(j)] for j in vx.tolist()]
    예쌍, 천쌍, 보기 = [], [], []
    for k, 부품 in enumerate(부품들):
        if not os.path.exists(Q.저장 + f"{부품}.npz"): continue
        for v in range(3):
            정 = 정답선(부품, v, s.휨문턱); 예 = 벡터화(있[k, v], 열[k, v], 숨[k, v], s.휨문턱); 천 = 벡터화(정지[k, v] > 0, 정열[k, v], 정숨[k, v], s.휨문턱)
            예쌍.append((정, 예)); 천쌍.append((정, 천))
            if 부품 == "12050": 보기.append((v, 정, 예, Xnp[이.index(부품), v]))
    지 = 재기(예쌍) | {f"{k}_정답": v for k, v in 재기(천쌍).items()}
    토큰 = [[뷰이름[v], l["종류"], *l["시작"], *l["끝"], l["휨"], "예" if l["숨음"] else "아니오"] for v, _, 예, _ in 보기 for l in 예]
    json.dump(토큰, open(폴더 + "토큰_12050.json", "w", encoding="utf-8"), ensure_ascii=False)
    그림(폴더, 보기); return 지
def 그림(폴더, 보기):   # 부품 12050 세 뷰: 입력 · 정답 모서리 · 예측 선(짝 맞은 선 = 종류 색 · 짝 없는 선 = 빨강)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from PIL import Image
    plt.rcParams["font.family"] = "Malgun Gothic"; 색 = {"직선": np.array([74, 123, 209]), "원호": np.array([40, 160, 80])}
    def 칠(선들, 맞은=None):
        im = np.full((128, 128, 3), 255, np.uint8)
        for i, l in enumerate(선들): im[l["_m"]] = 색[l["종류"]] if 맞은 is None or i in 맞은 else (216, 38, 43)
        return im
    fig, ax = plt.subplots(len(보기), 3, figsize=(15, 5.2 * len(보기))); fig.suptitle("벡터화 — 입력 · 정답 모서리 · 계산으로 뽑은 선(빨강 = 정답과 짝 없음) · 부품 12050", fontsize=18, weight="bold")
    for r, (v, 정, 예, x) in enumerate(보기):
        짝 = 맞추기(정, 예)
        for c, (im, t) in enumerate(((255 - x, f"입력 {뷰이름[v]}"), (칠(정), f"정답 {len(정)} 선"), (칠(예, {j for _, j in 짝}), f"벡터화 {len(예)} 선 · 짝 {len(짝)}"))):
            ax[r, c].imshow(im, cmap="gray" if c == 0 else None); ax[r, c].set_title(t, fontsize=14); ax[r, c].axis("off")
    fig.savefig(폴더 + "시트.png", dpi=60, bbox_inches="tight"); plt.close(fig)
    v, 정, 예, x = 보기[1] if len(보기) > 1 else 보기[0]
    Image.fromarray(np.kron(칠(정), np.ones((5, 5, 1), np.uint8))).save(폴더 + "정답.png"); Image.fromarray(np.kron(칠(예, {j for _, j in 맞추기(정, 예)}), np.ones((5, 5, 1), np.uint8))).save(폴더 + "예측전체.png")
    Image.fromarray(np.kron(255 - x, np.ones((5, 5), np.uint8))).save(폴더 + "도면_앞.png")
if __name__ == "__main__":   # 자체 시험: ㄱ 자(직선 둘) · 반원(원호 하나) · 닫힌 원 → 벡터화가 정답과 다 짝
    import cv2
    im = np.zeros((128, 128), np.uint8); cv2.line(im, (10, 20), (60, 20), 1, 1); cv2.line(im, (60, 20), (60, 70), 1, 1)
    cv2.ellipse(im, (95, 40), (20, 20), 0, 0, 180, 1, 1); cv2.circle(im, (40, 100), 15, 1, 1)
    열 = np.zeros((128, 128), np.float32); 열[20, 60] = 1.; 열[20, 10] = 1.; 열[70, 60] = 1.
    예 = 벡터화(im > 0, 열); 종 = sorted(l["종류"] for l in 예); assert 종 == ["원호", "원호", "직선", "직선"], [(l["종류"], l["시작"], l["끝"], l["휨"]) for l in 예]
    정 = [{"종류": l["종류"], "_m": l["_m"]} for l in 예]; r = 재기([(정, 예)]); assert r["벡_F1"] == 1 and r["벡_종류"] == 1, r
    r = 재기([(정, 예[:2])]); assert r["벡_재현"] == .5 and r["벡_정밀"] == 1, r
    print("과제벡터화 시험 통과", 재기([(정, 예)]))
