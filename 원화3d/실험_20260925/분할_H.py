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
