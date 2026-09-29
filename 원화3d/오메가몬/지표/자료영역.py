# -*- coding: utf-8 -*-
"""자료 영역 — 확보한 실루엣 · 선(자료확보.py)에서 선으로 닫힌 면을 색 · 번호로 (09-29 「이거에 대해서 영역을 색상으로 표시」). 우리 모델 · 원화 · 자세 없음.
    python 자료영역.py -> out/오메가몬2/자료/<이름>_영역.png(면 색 + 번호 | 원본 겹침) · <이름>_영역.npz(라벨 · 3 배) · 자료영역_셋.png · 자료영역.json(면 수 · 면적)
면 = 실루엣 안 ∧ 선(닫힘 5 px) 아닌 곳의 4-연결 성분 · 400 px(3 배 기준) 미만은 이웃 큰 면에 합침 · 남은 선 화소는 가장 가까운 면으로.
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); S = 3; 닫힘, 최소 = 5, 400
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 면나누기(sil3, 선3):
    선 = cv2.morphologyEx(선3.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((닫힘, 닫힘), np.uint8)) > 0
    n, lab, st, _ = cv2.connectedComponentsWithStats((sil3 & ~선).astype(np.uint8), connectivity=4)
    최소_ = max(최소, int(0.004 * sil3.sum())); 큰 = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 최소_]; 라벨 = np.where(np.isin(lab, 큰), lab, 0).astype(np.int32)   # 실루엣의 0.4 % 미만은 이웃에 합침
    for i in range(1, n):
        if i in 큰: continue
        m = lab == i; nb = 라벨[(cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & (라벨 > 0)]
        if nb.size: 라벨[m] = np.bincount(nb).argmax()
    _, idx = cv2.distanceTransformWithLabels((라벨 == 0).astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(라벨 > 0); 값 = np.zeros(idx.max() + 1, np.int32); 값[idx[ys, xs]] = 라벨[ys, xs]; 채움 = 값[idx]; 채움[~sil3] = 0
    번호 = {v: k + 1 for k, v in enumerate(sorted(set(채움[채움 > 0].tolist()), key=lambda v: (np.nonzero(채움 == v)[0].mean(), np.nonzero(채움 == v)[1].mean())))}   # 위 → 아래 순 번호
    return np.vectorize(lambda v: 번호.get(v, 0))(채움).astype(np.int32), 선
def 음영합치기(라벨, im3, 여유=6, 색차=10, 띠=5, 최소띠=60):
    """그늘로 갈린 면 합치기(09-29 「뿔이 그림자 때문에 같은 건데 분할되네」): 맞닿은 두 면의 경계 띠에 먹선(블랙햇)이 적고 색상(a*·b*)이 같으면 같은 재질 → 합침. 규칙/캡처는-실루엣-선-면 · 알베도."""
    g = cv2.cvtColor(im3, cv2.COLOR_BGR2GRAY); 먹 = cv2.dilate((cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 18).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    lab = cv2.cvtColor(im3, cv2.COLOR_BGR2LAB).astype(np.float32); ids = [i for i in np.unique(라벨) if i > 0]; 색 = {i: np.median(lab[라벨 == i], 0) for i in ids}; 부모 = {i: i for i in ids}
    def 찾(a):
        while 부모[a] != a: 부모[a] = 부모[부모[a]]; a = 부모[a]
        return a
    k = np.ones((띠, 띠), np.uint8); 팽 = {i: cv2.dilate((라벨 == i).astype(np.uint8), k) > 0 for i in ids}; 팽3 = {i: cv2.dilate((라벨 == i).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0 for i in ids}; 합침 = []
    for x, a in enumerate(ids):
        for b in ids[x + 1:]:
            band = 팽[a] & (라벨 == b); n = int(band.sum())
            if n < 최소띠: continue
            경계 = 팽3[a] & 팽3[b]; La, Lb = float(np.median(g[라벨 == a])), float(np.median(g[라벨 == b]))
            if not 경계.any(): continue
            경밝 = float(np.median(g[경계])); 선있음 = 경밝 < min(La, Lb) - 여유                      # 밝기만으로는 옅은 먹선(80)과 그늘 면(68)을 못 가른다(09-29) → 자동 합침 대신 **후보 제안 · 사람 결정**
            dc = float(np.hypot(*(색[a][1:] - 색[b][1:])))
            비 = min(La, Lb) / max(La, Lb, 1)                                                      # 셀 음영 톤 비는 0.55~0.85 · 검정 대 흰은 0.2 미만
            if not 선있음 and dc < 색차 and 비 >= 0.45 and min(La, Lb) >= 40: 합침.append(dict(쌍=(int(a), int(b)), 경계밝기=int(경밝), 면밝기=(int(La), int(Lb)), 색차=round(dc, 1), 경계=경계))
    return 라벨, 합침                                                                                  # 라벨은 그대로 · 합침 = 후보(사람이 고른다)
if __name__ == "__main__":
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); fs = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 15); 판들 = []; 표 = {}
    for n in ("02_정면", "02_3-4", "02_옆"):
        im = 읽기(기록[n]["파일"]); sil = 읽기(J(D, n + "_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; 선3 = 읽기(J(D, n + ("_선닫힘.png" if os.path.exists(J(D, n + "_선닫힘.png")) else "_선.png")), cv2.IMREAD_GRAYSCALE) < 128   # 면닫기.py 결과가 있으면 그것
        sil3 = cv2.resize(sil.astype(np.uint8), (선3.shape[1], 선3.shape[0]), interpolation=cv2.INTER_NEAREST) > 0; 라벨, 선 = 면나누기(sil3, 선3)
        im3_ = cv2.resize(im, (선3.shape[1], 선3.shape[0]), interpolation=cv2.INTER_CUBIC); 라벨, 후보 = 음영합치기(라벨, im3_); ids = [i for i in np.unique(라벨) if i > 0]; print(n, "면", len(ids), "· 합칠 후보", [c["쌍"] for c in 후보])
        np.savez_compressed(J(D, n + "_영역.npz"), 라벨=라벨); 표[n] = {int(i): int((라벨 == i).sum()) for i in ids}
        rng = np.random.RandomState(5); im3 = cv2.resize(im, (선3.shape[1], 선3.shape[0]), interpolation=cv2.INTER_CUBIC); 면 = np.full(im3.shape, 255, np.uint8)
        for i in ids: 면[라벨 == i] = tuple(int(x) for x in rng.randint(60, 240, 3))
        면[선 & sil3] = (0, 0, 0)
        for c in 후보: 면[cv2.dilate(c["경계"].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = (0, 0, 255)          # 합칠 후보 경계 = 빨강
        겹 = cv2.addWeighted(im3, 0.45, 면, 0.55, 0)
        x0, y0, x1, y1 = [v * S for v in 기록[n]["상자"]]; A = Image.fromarray(면[y0:y1, x0:x1][:, :, ::-1]); B = Image.fromarray(겹[y0:y1, x0:x1][:, :, ::-1]); d = ImageDraw.Draw(A)
        for i in ids:
            ys, xs = np.nonzero(라벨[y0:y1, x0:x1] == i)
            if len(xs): d.text((int(np.median(xs)) - 8, int(np.median(ys)) - 9), str(i), font=fs, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
        out = Image.new("RGB", (A.width * 2 + 10, A.height), (250, 250, 248)); out.paste(A, (0, 0)); out.paste(B, (A.width + 10, 0)); ImageDraw.Draw(out).text((8, 6), "%s  면 %d · 빨강 = 합칠 후보 %s" % (n, len(ids), " ".join("%d+%d" % c["쌍"] for c in 후보)), font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255)); out.save(J(D, n + "_영역.png"))
        표[n + "_후보"] = [dict(쌍=c["쌍"], 경계밝기=c["경계밝기"], 면밝기=c["면밝기"], 색차=c["색차"]) for c in 후보]
        h = 520; 판들.append(out.resize((int(out.width * h / out.height), h))); print(n, "면", len(ids))
    W = max(p.width for p in 판들); 시트 = Image.new("RGB", (W, sum(p.height + 6 for p in 판들)), (250, 250, 248)); y = 0
    for p in 판들: 시트.paste(p, (0, y)); y += p.height + 6
    시트.save(J(D, "자료영역_셋.png")); json.dump(표, open(J(D, "자료영역.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(J(D, "자료영역_셋.png"))
