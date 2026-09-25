# -*- coding: utf-8 -*-
"""분할 C — 학습된 부품 특징(NVIDIA PartField, ICCV 2025)으로 가르기 (2026-09-25).

  1) 특징:  G:\\art2real\\트레일\\trail7_part3d\\venv\\Scripts\\python.exe 분할_C.py 특징
            몸.ply → 면마다 448 차 특징 → out/분할후보/C_특징.npy  (torch_scatter 는 trail9 shim)
  2) 가르기: python 분할_C.py [판본…]
            면 특징 → 면 인접 계층 군집(ward) → n 부품 → 대칭 구역은 왼쪽 반을 거울로 → 부피 칸 라벨 → 채점
"""
import os, sys
import numpy as np

D = r"G:\art2real\원화3d\out\분할후보"
PF = r"G:\art2real\트레일\trail9_partfield"
특징파일 = os.path.join(D, "C_특징.npy")


def 특징():
    import types, torch, trimesh
    sys.path[:0] = [os.path.join(PF, "shim"), os.path.join(PF, "PartField")]
    for m in ("boto3", "mesh2sdf", "tetgen", "vtk", "pymeshlab"):  # 데이터로더만 쓰는 것들 — 추론엔 안 쓴다
        sys.modules[m] = types.ModuleType(m)
    # lightning 은 이 venv 에서 transformers 와 순환 임포트로 죽는다 — 추론엔 nn.Module 이면 된다
    L = types.ModuleType("lightning"); Lp = types.ModuleType("lightning.pytorch")
    Lp.LightningModule = type("LightningModule", (torch.nn.Module,), {"save_hyperparameters": lambda self, *a, **k: None})
    L.pytorch = Lp; sys.modules["lightning"] = L; sys.modules["lightning.pytorch"] = Lp
    from partfield.config import setup
    from partfield.model_trainer_pvcnn_only_demo import Model
    from partfield.model.PVCNN.encoder_pc import sample_triplane_feat
    a = types.SimpleNamespace(config_file=os.path.join(PF, "PartField", "configs", "final", "demo.yaml"), opts=[])
    cfg = setup(a, freeze=False)
    net = Model(cfg)
    sd = torch.load(os.path.join(PF, "model", "model_objaverse.ckpt"), map_location="cpu", weights_only=False)["state_dict"]
    print("가중치", net.load_state_dict(sd, strict=False))
    net = net.cuda().eval()
    m = trimesh.load(os.path.join(D, "몸.ply"), process=False)
    V = np.asarray(m.vertices, np.float64)[:, [0, 2, 1]]  # 높이를 y 로 (Objaverse 는 y 위)
    c = (V.min(0) + V.max(0)) / 2; V = (V - c) * (2 * 0.9 / (V.max(0) - V.min(0)).max())
    m2 = trimesh.Trimesh(V, m.faces, process=False)
    torch.manual_seed(0); np.random.seed(0)
    pc, _ = trimesh.sample.sample_surface(m2, 100000, seed=0)
    pc = torch.tensor(pc, dtype=torch.float32, device="cuda")[None]
    with torch.no_grad():
        planes = net.triplane_transformer(net.pvcnn(pc, pc))
        part = planes[:, :, 64:]
        # 면마다 무게중심 좌표 k 점을 뽑아 평균
        k = 64; Vt = torch.tensor(V, dtype=torch.float32, device="cuda"); Ft = torch.tensor(m.faces, device="cuda")
        out = []
        for s in range(0, len(Ft), 2000):
            f = Ft[s:s + 2000]; u = torch.rand(len(f), k, 1, device="cuda").sqrt(); v = torch.rand(len(f), k, 1, device="cuda")
            p = (1 - u) * Vt[f[:, 0]][:, None] + u * (1 - v) * Vt[f[:, 1]][:, None] + u * v * Vt[f[:, 2]][:, None]
            out.append(sample_triplane_feat(part, p.reshape(1, -1, 3)).reshape(len(f), k, -1).mean(1).float().cpu())
    F = torch.cat(out).numpy()
    np.save(특징파일, F.astype(np.float32)); print("면 특징", F.shape)


# ---------- 가르기 (메인 파이썬) ----------
def 거울로(lab, O, 축i, 문턱=0.85, 팔폭=18):
    """왼쪽(x<축) 라벨 중 거울 자리가 거의 다 몸인 것(몸통·머리·허리·다리)을 오른쪽에 복사.
    가운데를 지나는 라벨은 같은 번호, 한쪽에만 있는 라벨은 새 번호(거울 짝). 팔처럼 거울이 안 맞는 라벨은 그대로."""
    X = np.arange(O.shape[0]); j = np.round(2 * 축i - X).astype(int); ok = (j >= 0) & (j < O.shape[0])
    ML = np.zeros_like(lab); ML[ok] = lab[j[ok]]          # 거울 자리의 라벨
    MO = np.zeros_like(O); MO[ok] = O[j[ok]]
    왼 = (X < 축i)[:, None, None] & O; 오 = (X > 축i)[:, None, None] & O
    n = lab.max(); new = lab.copy(); zs = np.nonzero(O.any((0, 1)))[0]
    for L in np.unique(lab[왼]):
        m = 왼 & (lab == L)
        if (m & MO).sum() < 문턱 * m.sum(): continue          # 팔 · 무기 — 좌우가 원래 다르다
        # 팔 덩이는 부피로는 거울이 맞아도(0.95) 모양이 달라 줄무늬가 된다 — 옆으로 멀고 다리보다 높으면 팔
        p = np.argwhere(m); 높 = (p[:, 2].mean() - zs[0]) / (zs[-1] - zs[0])
        if abs(p[:, 0].mean() - 축i) > 팔폭 and 높 > 0.3: continue
        가운데 = (lab == L)[np.abs(X - 축i) <= 1].any()
        대상 = 오 & (ML == L)
        new[대상] = L if 가운데 else L + n
        # 오른쪽에 원래 있던 같은 번호(거울 밖)는 비워 두면 조각정리가 이웃에 붙인다
        if not 가운데: new[오 & (lab == L) & ~대상] = 0
    # 비운 칸은 가장 가까운 라벨로
    from scipy import ndimage
    빈 = O & (new == 0)
    if 빈.any():
        _, (a, b, c) = ndimage.distance_transform_edt(new == 0, return_indices=True)
        new[빈] = new[a[빈], b[빈], c[빈]]
    return new


def 평면으로(lab, O, 폭=6):
    """맞닿은 두 부품마다 경계 근처(폭 칸) 칸을 한 평면으로 다시 가른다 — 계단 이음면을 평평하게.
    평면 = 두 부품 칸의 선형 판별(LDA, 경계 근처만)."""
    from scipy import ndimage
    lab = lab.copy()
    for _ in range(2):
        쌍 = {}
        for a in range(3):
            a0 = np.take(lab, range(lab.shape[a] - 1), axis=a); a1 = np.take(lab, range(1, lab.shape[a]), axis=a)
            d = (a0 != a1) & (a0 > 0) & (a1 > 0)
            for p, q in zip(a0[d], a1[d]): 쌍[(min(p, q), max(p, q))] = 쌍.get((min(p, q), max(p, q)), 0) + 1
        for (p, q), w in sorted(쌍.items(), key=lambda t: -t[1]):
            if w < 20: continue
            A, B = lab == p, lab == q
            띠 = (ndimage.binary_dilation(A, iterations=폭) & B) | (ndimage.binary_dilation(B, iterations=폭) & A)
            P = np.argwhere(띠).astype(float); y = lab[띠] == p
            if y.all() or (~y).all(): continue
            mu0, mu1 = P[y].mean(0), P[~y].mean(0)
            S = np.cov(P[y].T) + np.cov(P[~y].T) + 1e-3 * np.eye(3)
            wv = np.linalg.solve(S, mu0 - mu1); c = wv @ (mu0 + mu1) / 2
            new = np.where(P @ wv > c, p, q)
            if (new == np.where(y, p, q)).mean() < 0.8: continue   # 평면으로 못 가르는 쌍(ㄷ자로 감싼 것)은 두기
            lab[띠] = new
    return lab


def 가르기(이름, n, 거울대칭=True, 특=None, 거울복사=False, 평면=False):
    import trimesh
    from scipy import sparse, ndimage
    from sklearn.cluster import AgglomerativeClustering
    I = np.load(os.path.join(D, "입력.npz")); O = I["O"]; ux, uy, z = I["ux"], I["uy"], I["z"]; 축i = float(I["축i"])
    m = trimesh.load(os.path.join(D, "몸.ply"), process=False)
    F = np.load(특징파일) if 특 is None else 특
    F = F / np.linalg.norm(F, axis=1, keepdims=True)
    fc = m.triangles_center; 칸 = (ux[1] - ux[0])
    축x = ux[0] + 축i * 칸
    if 거울대칭:
        # 오른쪽(x>축) 면의 특징을 거울 짝 면 특징과 평균 — 대칭 구역 경계가 같은 곳에 서게. 팔은 뒤에서 되돌린다
        from scipy.spatial import cKDTree
        mf = fc.copy(); mf[:, 0] = 2 * 축x - mf[:, 0]
        d, j = cKDTree(fc).query(mf)
        짝 = d < 2 * 칸
        F = F.copy(); F[짝] = (F[짝] + F[j[짝]]) / 2
    adj = m.face_adjacency
    A = sparse.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])), shape=(len(fc),) * 2)
    A = (A + A.T).tocsr()
    # 연결 성분이 여럿이면(몸 2 덩이) 가까운 면끼리 이어 준다
    nc, cc = sparse.csgraph.connected_components(A)
    if nc > 1:
        from scipy.spatial import cKDTree
        t = cKDTree(fc[cc == np.bincount(cc).argmax()]); big = np.nonzero(cc == np.bincount(cc).argmax())[0]
        rows, cols = [], []
        for c in range(nc):
            if c == np.bincount(cc).argmax(): continue
            ids = np.nonzero(cc == c)[0]; d, j = t.query(fc[ids]); i = d.argmin(); rows.append(ids[i]); cols.append(big[j[i]])
        A = A + sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=A.shape) + sparse.coo_matrix((np.ones(len(rows)), (cols, rows)), shape=A.shape)
    fl = AgglomerativeClustering(n_clusters=n, connectivity=A, linkage="ward").fit_predict(F) + 1
    # 면 라벨 → 부피 칸: 가장 가까운 겉 면
    from scipy.spatial import cKDTree
    X, Y, Z = np.meshgrid(ux, uy, z, indexing="ij"); idx = np.argwhere(O)
    P = np.stack([ux[idx[:, 0]], uy[idx[:, 1]], z[idx[:, 2]]], 1)
    _, j = cKDTree(fc).query(P)
    lab = np.zeros(O.shape, np.int32); lab[O] = fl[j]
    if 거울복사: lab = 거울로(lab, O, 축i)
    # 작은 조각 합치기 (0.3% 미만 · 이어진 덩이 단위)
    lab = 조각정리(lab, O, 0.003)
    if 평면: lab = 평면으로(lab, O); lab = 조각정리(lab, O, 0.003)
    if 평면 == "거울":  # 평면화가 좌우를 따로 움직였다 — 왼쪽을 다시 거울로
        lab = 조각정리(거울로(lab, O, 축i), O, 0.003)
    os.makedirs(os.path.join(D, 이름), exist_ok=True); np.save(os.path.join(D, 이름, "lab.npy"), lab)
    return lab


def 조각정리(lab, O, 최소):
    from scipy import ndimage
    lab = lab.copy(); nO = O.sum()
    for _ in range(5):
        바뀜 = False; 새 = np.zeros_like(lab); k = 0
        for v in np.unique(lab[lab > 0]):
            cc, n = ndimage.label(lab == v)
            for c in range(1, n + 1):
                k += 1; 새[cc == c] = k
        lab = 새; 크 = np.bincount(lab.ravel())
        for v in np.argsort(크):
            if v == 0 or 크[v] == 0 or 크[v] >= 최소 * nO: continue
            m = lab == v; 테 = ndimage.binary_dilation(m) & ~m & (lab > 0)
            if 테.any(): lab[m] = np.bincount(lab[테]).argmax()
            else:  # 떨어진 부스러기 — 가장 가까운 다른 부품에
                _, ix = ndimage.distance_transform_edt(~((lab > 0) & ~m), return_indices=True)
                q = np.argwhere(m)[0]; lab[m] = lab[tuple(ix[:, q[0], q[1], q[2]])]; 크 = np.bincount(lab.ravel(), minlength=len(크)); 바뀜 = True
        if not 바뀜: break
    u = np.unique(lab); r = np.zeros(u.max() + 1, np.int32); r[u] = np.arange(len(u)); return r[lab]


if __name__ == "__main__":
    if sys.argv[1:] == ["특징"]:
        특징(); sys.exit()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 채점 as S
    판 = {"C1_n20": (20, {}), "C1_n30": (30, {}), "C1_n40": (40, {}),
         "C2_n30": (30, dict(거울복사=True)), "C2_n40": (40, dict(거울복사=True)),
         "C3_n30": (30, dict(거울복사=True, 평면=True)), "C3_n40": (40, dict(거울복사=True, 평면=True)),
         "C4_n30": (30, dict(거울복사=True, 평면="거울")), "C4_n40": (40, dict(거울복사=True, 평면="거울"))}
    for 이름 in (sys.argv[1:] or 판):
        가르기(이름, 판[이름][0], **판[이름][1]); S.채점(이름)
