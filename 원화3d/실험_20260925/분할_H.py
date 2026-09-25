# -*- coding: utf-8 -*-
"""방식 H — 사람이 설계한 키트의 분할을 오메가몬 몸에 옮겨 심는다 (2026-09-25).

    python 분할_H.py      -> out/분할후보/H1 · H2 · H3 · H4 /lab.npy · 크게.png (채점까지)

조립 좌표가 산 사람형 키트는 둘뿐이다(813280 · 680191 · 588149 는 출력판 배치라 조립 좌표가 없다):
  529278 건담 (Anycubic)  y 위 · +z 앞 · 몸 부품 9 (머리 · 몸통 · 허리 · 허벅지 2 · 종아리+발 2 · 팔 2 — 팔은 안 쓴다)
  529483 Ex-S Pose1       z 위 · −y 앞 · 몸 부품 5 (머리 · 몸통 · 허리날개 · 다리 2 통짜) · 나머지는 등짐 · 무기
대응: 골격 높이(바닥 · 발목 · 무릎 · 가랑이 · 복부 · 목 · 꼭대기)로 z 를 조각별 선형, 높이 한 줄마다 (x, 깊이) 는
그 줄 경계 상자를 [0,1]² 로 맞춘다 (다리는 왼 다리끼리 · 몸통은 몸통끼리). 오메가몬 칸 → 키트 점 → 가장 가까운 키트 겉 점의 부품.
H1 건담 · H2 Ex-S · H3 H1 × H2 (두 키트 컷 겹치기) · H4 H1 + 블록 앞뒤 반쪽(813280 식 1st/2nd half)."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image
sys.path[:0] = [r"G:\art2real\원화3d\실험_20260925"]
import 채점 as C, 분할_A as A

O, N, 축 = A.O, A.N, A.축
X, Y, Zi = A.X, A.Y, A.Zi
c4 = A.기울스냅(A.스냅(dict(A.컷)))
AL, AR = A.팔(c4)
몸 = O & ~AL & ~AR
zs = np.nonzero(O.any((0, 1)))[0]
가운 = O[축 - 1:축 + 2].any((0, 1))
우리 = dict(바닥=zs[0], 발목=c4["발목"], 무릎=(c4["무릎위"] + c4["무릎아래"]) / 2,
          가랑이=int(np.nonzero(가운)[0][0]), 복부=c4["복부"], 목=c4["머리"], 꼭대기=zs[-1])

키트경로 = r"G:\art2real\원화3d\out\키트정답"
# 키트: 축 바꾸기 (키트 → [x 좌우, y 깊이 작은 쪽 앞, z 위]) · 몸 부품(역할) · 골격 높이(손 값, 가랑이는 자동)
키트 = {
    "529278": dict(축=lambda p: np.c_[p[:, 0], -p[:, 2], p[:, 1]],
                   부품={"Head": "머리", "Body": "몸", "Waist": "몸", "Right_thigh": "다리", "Left_thigh": "다리",
                         "Right_calf": "다리", "Left_calf": "다리"},
                   높이=dict(바닥=-44.8, 발목=-37, 무릎=-7, 복부=17, 목=33.1, 꼭대기=47.7)),
    "529483": dict(축=lambda p: p.copy(),
                   부품={"Pose1_Head.": "머리", "Pose1_Torso.": "몸", "Pose1_WaistWingsV2.": "몸",
                         "Pose1_LeftLeg.": "다리", "Pose1_RightLeg.": "다리"},
                   높이=dict(바닥=-1, 발목=6, 무릎=15, 목=48.4, 꼭대기=54.5)),
}


def 키트읽기(번호, 밀도=40.0):
    """부품 겉 점(넓이 비례) · 부품 번호 · 부품 이름 · 역할."""
    k = 키트[번호]; P, L, 이름, 역 = [], [], [], []
    for f in sorted(os.listdir(os.path.join(키트경로, 번호))):
        맞 = [v for s, v in k["부품"].items() if s in f and "_Sup" not in f]
        if not f.endswith(".stl") or not 맞: continue
        m = trimesh.load(os.path.join(키트경로, 번호, f), force="mesh")
        p = k["축"](m.sample(int(max(3000, min(40000, m.area * 밀도)))))
        P.append(p); L.append(np.full(len(p), len(이름))); 이름.append(f[4:-4]); 역.append(맞[0])
    P, L = np.concatenate(P), np.concatenate(L)
    중 = np.median(P[np.array(역)[L] == "머리", 0])                     # 좌우 가운데 = 머리 가운데
    P[:, 0] -= 중
    h = dict(k["높이"])
    c = np.abs(P[:, 0]) < 1.0
    h["가랑이"] = float(P[c, 2].min())                                   # 가운데 기둥이 몸에 닿는 가장 낮은 높이
    return P, L, 이름, np.array(역), h


옮긴이름 = {}


def 옮기기(번호):
    """오메가몬 몸(팔 뺀) 왼 반 + 가운데의 칸마다 키트 부품 번호 (0 = 없음)."""
    P, L, 이름, 역, h = 키트읽기(번호)
    키 = [k for k in ("바닥", "발목", "무릎", "가랑이", "복부", "목", "꼭대기") if k in h]
    zo = np.array([우리[k] for k in 키], float); zk = np.array([h[k] for k in 키], float)
    print("  %s 골격 높이 (우리 → 키트):" % 번호, {k: "%.0f→%.1f" % (a, b) for k, a, b in zip(키, zo, zk)}, flush=True)
    나무 = cKDTree(P)
    다리점 = (역[L] == "다리") & (P[:, 0] < 0)                          # 왼(작은 x) 다리
    몸점 = 역[L] != "무"
    반 = (zk[-1] - zk[0]) / (zo[-1] - zo[0]) * 2.0                       # 키트 쪽 한 줄 두께 (우리 2 칸)
    lab = np.zeros(O.shape, np.int32)
    상자 = []
    for z in range(zs[0], zs[-1] + 1):
        다리층 = z < 우리["가랑이"]
        M = 몸[:, :, z] & ((np.arange(N) <= 축)[:, None])
        if 다리층: M &= (np.arange(N) < 축)[:, None]
        if not M.any(): continue
        tz = np.interp(z, zo, zk)
        sel = (다리점 if 다리층 else 몸점) & (np.abs(P[:, 2] - tz) < 반)
        if sel.sum() < 30: sel = (다리점 if 다리층 else 몸점) & (np.abs(P[:, 2] - tz) < 3 * 반)
        q = P[sel]
        klo, khi = np.percentile(q[:, :2], 1, 0), np.percentile(q[:, :2], 99, 0)
        if not 다리층: klo[0], khi[0] = min(klo[0], -khi[0]), max(khi[0], -klo[0])   # 몸통 줄은 가운데 대칭 상자
        xs, ys = np.nonzero(몸[:, :, z] & (((np.arange(N) < 축) if 다리층 else np.ones(N, bool))[:, None]))
        olo = np.array([xs.min(), ys.min()], float); ohi = np.array([xs.max(), ys.max()], float) + 1
        if not 다리층: olo[0], ohi[0] = min(olo[0], 2 * 축 - ohi[0]), max(ohi[0], 2 * 축 - olo[0])
        상자.append((z, 다리층, olo, ohi, klo, khi, tz))
    # 줄 상자를 z 로 매끈하게 (다리층 · 몸통층 따로, 이웃 5 줄 중앙값)
    배 = np.array([np.r_[s[2], s[3], s[4], s[5]] for s in 상자]); 층 = np.array([s[1] for s in 상자])
    for v in (True, False):
        i = 층 == v
        배[i] = ndimage.median_filter(배[i], size=(5, 1), mode="nearest")
    for (z, 다리층, *_, tz), b in zip(상자, 배):
        olo, ohi, klo, khi = b[0:2], b[2:4], b[4:6], b[6:8]
        M = 몸[:, :, z] & ((np.arange(N) <= 축)[:, None])
        if 다리층: M &= (np.arange(N) < 축)[:, None]
        xs, ys = np.nonzero(M)
        u = (np.c_[xs + .5, ys + .5] - olo) / np.maximum(ohi - olo, 1e-6)
        k = klo + u * (khi - klo)
        _, j = 나무.query(np.c_[k, np.full(len(k), tz)])
        lab[xs, ys, z] = L[j] + 1
    print("  %s 옮긴 부품:" % 번호, {이름[i]: int((lab == i + 1).sum()) for i in range(len(이름))}, flush=True)
    옮긴이름[번호] = 이름
    return lab


def 거울(lab, 영역=None):
    """x<=축 → x>축. 가운데(축에 닿는) 부품은 같은 번호, 한쪽 부품은 새 번호 짝."""
    영역 = 몸 if 영역 is None else 영역
    j = np.clip(2 * 축 - np.arange(N), 0, N - 1)
    가운부품 = set(np.unique(lab[축][lab[축] > 0]).tolist())
    짝 = np.arange(lab.max() + 1); n = lab.max()
    for p in range(1, lab.max() + 1):
        if p not in 가운부품 and (lab == p).any(): n += 1; 짝[p] = n
    거 = lab[j]; 오 = 영역 & (X > 축)
    lab = lab.copy(); lab[오] = np.where(영역[j] & (거 > 0), 짝[거], 0)[오]
    남 = 영역 & (lab == 0)
    if 남.any():
        i = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab[남] = lab[tuple(i)][남]
    return lab


def 평면맞춤(lab, 한계=1.5, 이웃=4):
    """맞닿은 짝마다 이음 칸에 평면 → 이음 이웃(이웃 칸 안) 칸을 평면 편으로 다시 가른다. RMS > 한계 인 짝은 둔다(곡면 컷).
    왼 반(x<=축)만 고친다 — 오른쪽은 뒤에 거울. 가운데-가운데 짝은 법선 x 성분 0 (좌우 대칭 유지)."""
    _, 짝 = C.경계(np.where(X <= 축, lab, 0))
    가운부품 = set(np.unique(lab[축][lab[축] > 0]).tolist())
    고침 = 0
    for (p, q), pts in sorted(짝.items(), key=lambda t: -len(t[1])):
        P = np.array(pts, float) + .5
        if len(P) < 20: continue
        c = P.mean(0)
        if p in 가운부품 and q in 가운부품:                               # (y, z) 안에서만 맞춘다 → 법선 x = 0
            n = np.r_[0, np.linalg.svd(P[:, 1:] - c[1:], full_matrices=False)[2][-1]]
        else:
            n = np.linalg.svd(P - c, full_matrices=False)[2][-1]
        rms = np.sqrt(np.mean(((P - c) @ n) ** 2))
        if rms > 한계 or rms < 0.05: continue
        이음 = np.zeros(O.shape, bool); ii = np.array(pts); 이음[tuple(ii.T)] = True
        근 = ndimage.binary_dilation(이음, iterations=이웃) & ((lab == p) | (lab == q)) & (X <= 축)
        g = np.argwhere(근); s = (g + .5 - c) @ n >= 0
        # 어느 편이 p 인가: 지금 라벨 다수결
        cur = lab[tuple(g.T)] == p
        p편 = (cur & s).sum() >= (cur & ~s).sum()
        new = np.where(s == p편, p, q)
        고침 += int((new != lab[tuple(g.T)]).sum()); lab[tuple(g.T)] = new
    print("  평면 맞춤: 바뀐 칸 %d" % 고침, flush=True)
    return lab


def 팔붙이기(lab):
    """팔 구역은 A4 라벨 그대로 (칼 · 대포 · 늑대/드라몬 머리는 키트에 없다)."""
    a4 = np.load(os.path.join(C.D, "A4", "lab.npy")).astype(np.int32)
    팔 = (AL | AR) & O; lab = lab.copy()
    _, inv = np.unique(a4[팔], return_inverse=True)
    lab[팔] = lab.max() + 1 + inv
    return lab


def 크게보기(lab, 경로):
    """앞 · 뒤 · 왼옆 · 오른옆 (부품 색 + 경계 검정 + 깊이 음영) · 4 배 — 분할_E 와 같은 판."""
    rng = np.random.default_rng(3); col = (rng.uniform(.3, .95, (lab.max() + 1, 3)) * 255).astype(np.uint8)
    판 = []
    for L, 뒤집 in ((lab, False), (lab[:, ::-1], True), (lab.transpose(1, 0, 2), False), (lab.transpose(1, 0, 2)[:, ::-1], True)):
        d = np.argmax(L > 0, 1); h = (L > 0).any(1)
        img = np.where(h, np.take_along_axis(L, d[:, None, :], 1)[:, 0, :], 0)
        e = np.zeros_like(h)
        for a in (0, 1): e |= np.pad(np.diff(img, axis=a) != 0, [(0, 1) if k == a else (0, 0) for k in range(2)])
        sh = 1 - 0.45 * (d - d[h].min()) / max(1, np.ptp(d[h]))
        rgb = (col[img] * sh[..., None]).astype(np.uint8); rgb[e & h] = 0; rgb[~h] = 255
        rgb = np.transpose(rgb, (1, 0, 2))[::-1]
        if 뒤집: rgb = rgb[:, ::-1]
        판.append(rgb[15:178, 30:170] if len(판) < 2 else rgb[15:178, 65:130])
    im = np.concatenate(판, 1)
    Image.fromarray(im).resize((im.shape[1] * 4, im.shape[0] * 4), Image.NEAREST).save(경로)


def 마무리(판본, lab, 한계=1.5):
    lab = A.조각정리(lab, 몸 & (X <= 축))
    lab = 평면맞춤(lab, 한계)
    lab = A.조각정리(lab, 몸 & (X <= 축))
    lab = 거울(lab)
    lab = 팔붙이기(lab)
    lab = A.조각정리(lab, O)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape)
    os.makedirs(os.path.join(C.D, 판본), exist_ok=True)
    np.save(os.path.join(C.D, 판본, "lab.npy"), lab.astype(np.int16))
    크게보기(lab, os.path.join(C.D, 판본, "크게.png"))
    C.채점(판본)


def 앞뒤반(lab):
    """부품마다 옆 실루엣이 가장 넓은 깊이에서 반 가르기 (A.앞뒤 와 같은 규칙, 왼 반만)."""
    lab = lab.copy(); n = lab.max()
    for p in range(1, n + 1):
        M = lab == p
        if M.sum() < 400: continue
        y0 = int(np.argmax(M.sum((0, 2)))); n += 1; lab[M & (Y < y0)] = n
    return lab


def 꺾은선(x, h, 최대=3, 줄임=0.3):
    """h(x) 에 맞춘 이어진 꺾은선 (조각 1 ~ 최대). 조각을 늘려 RMS 가 줄임 칸 넘게 줄 때만 늘린다 → 함수 f(X)."""
    x, h = np.asarray(x, float), np.asarray(h, float)
    def 맞(꺾):
        B = np.column_stack([np.ones_like(x), x] + [np.maximum(x - k, 0) for k in 꺾])
        c = np.linalg.lstsq(B, h, rcond=None)[0]; return float(np.sqrt(np.mean((B @ c - h) ** 2))), c, list(꺾)
    후 = np.unique(x)[2:-2] + .5
    최 = 맞([])
    if 최대 >= 2 and len(후):
        새 = min((맞([k]) for k in 후), key=lambda t: t[0])
        if 최[0] - 새[0] > 줄임: 최 = 새
    if 최대 >= 3 and len(최[2]) == 1:
        새 = min((맞([a, b]) for i, a in enumerate(후) for b in 후[i + 3:]), key=lambda t: t[0])
        if 최[0] - 새[0] > 줄임: 최 = 새
    r, c, 꺾 = 최
    print("    꺾은선: 조각 %d · 꺾임 x %s · 기울기 %s · RMS %.2f 칸" % (len(꺾) + 1, [round(k, 1) for k in 꺾],
          [round(float(v), 2) for v in np.cumsum(c[1:])], r), flush=True)
    return lambda X_: c[0] + c[1] * X_ + sum(ck * np.maximum(X_ - k, 0) for ck, k in zip(c[2:], 꺾))


def 짓기H5():
    """A9 뼈대에 건담 키트 모양 둘만 이식: 허리/허벅지 경계 = V 스커트 꺾은 평면 · 무릎 아래(앞 반) = 뾰족 무릎 장갑 꺾은 평면.
    모양(꺾은선)은 H1 전이 라벨에서 x 마다 이음 높이 중앙값 → 꺾은선 맞춤. 컷 면은 모두 법선 y = 0 인 평면 조각이다."""
    import json, shutil
    t0 = time.time(); d9 = os.path.join(C.D, "A9"); d5 = os.path.join(C.D, "H5")
    lab = np.load(os.path.join(d9, "lab.npy")).astype(np.int32); lab = np.where(O, lab, 0); lab9 = lab.copy()
    이름 = {int(k): v for k, v in json.load(open(os.path.join(d9, "이름.json"), encoding="utf-8")).items()}
    id_ = {v: k for k, v in 이름.items()}
    g = 옮기기("529278"); kn = 옮긴이름["529278"]
    W, T, Cf = kn.index("Waist") + 1, kn.index("Right_thigh") + 1, kn.index("Right_calf") + 1
    좌 = X < 축

    def y가름(n):                                             # A 의 앞뒤 가름 y0 (Y < y0 쪽 라벨)
        a, b = id_[n + "앞"], id_[n + "뒤"]
        ya, yb = np.nonzero((lab == a).any((0, 2)))[0], np.nonzero((lab == b).any((0, 2)))[0]
        return (yb.max() + 1, b, a) if yb.mean() < ya.mean() else (ya.max() + 1, a, b)
    def 반쪽(n):
        y0, 작, 큰 = y가름(n); return np.where(Y < y0, 작, 큰)

    def 이음높이(위, 아래, S, 위쪽끝, 겉="작"):                  # (x,y) 기둥마다 위 부품 아래끝(또는 아래 부품 위끝) → x 마다 겉 3 기둥 중앙값
        xs, h = [], []                                          # 겉 = 작은 y(앞 겉) · 큰 y(뒤 겉) — 눈에 보이는 이음선 모양
        for x in range(축 - 3):
            a = (g[x] == 위) & S[x]; b = (g[x] == 아래) & S[x]; ok = a.any(1) & b.any(1)
            if ok.sum() < 2: continue
            z = (N - 1 - np.argmax(b[:, ::-1], 1)) if 위쪽끝 else np.argmax(a, 1)
            yy = np.nonzero(ok)[0]; yy = yy[:3] if 겉 == "작" else yy[-3:]
            xs.append(x); h.append(float(np.median(z[yy])))
        return xs, h

    # ① V 스커트: 허리 ↔ 허벅지
    ysW, _, _ = y가름("허리")
    허 = np.isin(lab, [id_[n] for n in ("허리앞", "허리뒤", "L허벅지앞", "L허벅지뒤")]) & 좌 & (np.abs(X - 축) > 3)
    lo = np.nonzero(np.isin(lab, [id_["L허벅지앞"], id_["L허벅지뒤"]]).any((0, 1)))[0].min() + 4
    hi = np.nonzero(np.isin(lab, [id_["복부앞"], id_["복부뒤"]]).any((0, 1)))[0].min() - 3
    면 = {}
    for 쪽, S in (("작은y", Y < ysW), ("큰y", Y >= ysW)):
        print("  V 스커트 %s:" % 쪽, flush=True); 면[쪽] = 꺾은선(*이음높이(W, T, S, False, 쪽[0]))
    경 = np.clip(np.where(Y < ysW, 면["작은y"](X), 면["큰y"](X)), lo, hi)
    lab[허] = np.where(Zi >= 경, 반쪽("허리"), 반쪽("L허벅지"))[허]
    # ② 뾰족 무릎: 무릎 ↔ 정강이, 앞(작은 y) 반만 · 뒤는 원래 가로 컷
    ysK, _, _ = y가름("L정강이")
    무 = np.isin(lab, [id_[n] for n in ("L무릎", "L정강이앞", "L정강이뒤")]) & 좌
    zK = np.nonzero((lab == id_["L무릎"]).any((0, 1)))[0]
    print("  뾰족 무릎 (앞 반):", flush=True)
    f = 꺾은선(*이음높이(T, Cf, Y < ysK, True))
    경 = np.where(Y < ysK, np.clip(f(X) + 1, zK.min() - 6, zK.max() - 1), zK.min())
    lab[무] = np.where(Zi >= 경, id_["L무릎"], 반쪽("L정강이"))[무]
    # 거울: 왼 → 오른 (L 이름 → R 이름, 가운데 이름은 그대로)
    바뀐 = [id_[n] for n in ("허리앞", "허리뒤", "L허벅지앞", "L허벅지뒤", "L무릎", "L정강이앞", "L정강이뒤")]
    짝 = {k: id_.get("R" + 이름[k][1:], k) if 이름[k].startswith("L") else k for k in 바뀐}
    오 = np.isin(lab9, list(set(짝.values()))) & (X > 축)
    j = np.clip(2 * 축 - np.arange(N), 0, N - 1); 거 = lab[j]
    쓸 = 오 & np.isin(거, 바뀐)
    lab[쓸] = np.vectorize(lambda v: 짝.get(v, v))(거[쓸])
    lab = A.조각정리(lab, O)
    os.makedirs(d5, exist_ok=True)
    for f_ in ("이름.json", "막대.json"): shutil.copy(os.path.join(d9, f_), os.path.join(d5, f_))
    np.save(os.path.join(d5, "lab.npy"), lab.astype(np.int16))
    크게보기(lab, os.path.join(d5, "크게.png")); C.채점("H5")
    # 평면.json: A9 것 그대로 · 경계 칸이 달라진 짝만 새로 맞춰 갈아 끼운다
    A.평면내보내기("H5")
    새 = json.load(open(os.path.join(d5, "평면.json"), encoding="utf-8"))
    옛 = json.load(open(os.path.join(d9, "평면.json"), encoding="utf-8"))
    _, p9 = C.경계(lab9); _, p5 = C.경계(lab)
    달라 = {k for k in set(p9) | set(p5) if sorted(p9.get(k, [])) != sorted(p5.get(k, []))}
    달라 = {(int(a), int(b)) for a, b in 달라}
    def 원천(e):
        ns = [이름.get(v, "?") for v in e["짝"]]
        if e["원천"].startswith("앞뒤") or e["원천"].startswith("소켓"): return e["원천"]
        if any("무릎" in n for n in ns) and any("정강이" in n for n in ns): return "키트무릎"
        if any("허리" in n for n in ns) and any("허벅지" in n for n in ns): return "키트V"
        return e["원천"]
    합 = [e for e in 옛 if tuple(e["짝"]) not in 달라]
    for e in 새:
        if tuple(e["짝"]) in 달라: e["원천"] = 원천(e); 합.append(e)
    합.sort(key=lambda e: tuple(e["짝"]))
    json.dump(합, open(os.path.join(d5, "평면.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("  평면.json: A9 %d 항 → 바뀐 짝 %d · H5 %d 항 (키트V %d · 키트무릎 %d · rms>0.5 %d) · %.0f s" % (
        len(옛), len(달라), len(합), sum(e["원천"] == "키트V" for e in 합), sum(e["원천"] == "키트무릎" for e in 합),
        sum(e.get("rms", 0) > .5 for e in 합), time.time() - t0), flush=True)
    for e in 합:
        if e["원천"] in ("키트V", "키트무릎"): print("   ", e["짝"], [이름.get(v) for v in e["짝"]], e["원천"], e["법선"], e["rms"], e["칸"])


if __name__ == "__main__" and sys.argv[1:] == ["H5"]:
    짓기H5(); sys.exit()

if __name__ == "__main__":
    t0 = time.time()
    g = 옮기기("529278"); print("  H1 옮김 %.0f s" % (time.time() - t0)); 마무리("H1", g.copy())
    e = 옮기기("529483"); 마무리("H2", e.copy())
    _, h3 = np.unique(g.astype(np.int64) * 100 + e, return_inverse=True)            # 두 키트 컷 겹치기 (0·0 → 0)
    마무리("H3", h3.reshape(O.shape))
    마무리("H4", 앞뒤반(A.조각정리(g, 몸 & (X <= 축))))
    마무리("H1p", g.copy(), 한계=np.inf)                                        # 이음면 모두 평면 (키트 곡면 컷 버림)
    마무리("H4p", 앞뒤반(A.조각정리(g, 몸 & (X <= 축))), 한계=np.inf)
    for n in ("A4", "E8"): C.채점(n)
    print("전체 %.0f s" % (time.time() - t0))
