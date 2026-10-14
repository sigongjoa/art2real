# 판정기준34 그림 — ③ − ① 이 큰 시험 부품 4 개 + 중간 2 개: 정답 · ① 위만 · ② 세 실루엣 · ③ 위앞옆 파기 (복셀 48 → 마칭 큐브 → 광선 음영) · 10-14
import json, numpy as np, cv2, open3d as o3d
from skimage.measure import marching_cubes
import 천장34 as T
O = T.O
def 그리기(m, s=300):
    if m.sum() == 0: return np.full((s, s, 3), 30, np.uint8)
    vv, ff, _, _ = marching_cubes(np.pad(m, 1).astype(np.float32), .5); vv = (vv - 1 + .5) / m.shape[0] * 1.1 - .55
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(vv.astype(np.float32)), o3d.core.Tensor(ff.astype(np.uint32)))
    r = o3d.t.geometry.RaycastingScene.create_rays_pinhole(30.0, [0, 0, 0], [1.6, -1.9, 1.5], [0, 0, 1], s, s); h = sc.cast_rays(r)
    nn = h["primitive_normals"].numpy(); ok = np.isfinite(h["t_hit"].numpy()); L = np.array([.4, -.5, .77]); L /= np.linalg.norm(L)
    c = np.clip(np.abs(nn @ L), 0, 1); img = np.full((s, s, 3), 30, np.uint8); img[ok] = (np.stack([150 + 90 * c, 160 + 85 * c, 180 + 70 * c], -1)[ok]).astype(np.uint8)
    return img
if __name__ == "__main__":
    R = np.load(O + "부피IoU_34.npy"); d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    차 = R[:, 3] - R[:, 1]; 순 = np.argsort(-차); 고름 = list(순[:4]) + list(순[[60, 100]])
    from PIL import Image, ImageDraw, ImageFont
    F = lambda s: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", s); 열 = [("정답", None), ("① 위에서만", "①"), ("② 세 실루엣", "②"), ("③ 위 · 앞 · 옆 파기", "③")]
    W = Image.new("RGB", (60 + 4 * 310, 120 + len(고름) * 330), (14, 20, 36)); D = ImageDraw.Draw(W)
    D.text((30, 20), "판정기준34 — 정답 지도로 판 천장 (학습 없음 · 복셀 48)", font=F(40), fill="white")
    for j, (t, _) in enumerate(열): D.text((60 + j * 310, 80), t, font=F(28), fill=(240, 200, 90))
    for i, k in enumerate(고름):
        sc, v, f, H = T.장면(L[te[k]]); 정, 판 = T.복셀(sc, v, f, H, 48)
        for j, (_, key) in enumerate(열):
            W.paste(Image.fromarray(그리기(정 if key is None else 판[key])), (60 + j * 310, 120 + i * 330))
            if key: D.text((70 + j * 310, 125 + i * 330), "%.2f" % R[k, {"①": 1, "②": 2, "③": 3}[key]], font=F(30), fill="white")
        D.text((8, 250 + i * 330), "중간" if i >= 4 else "큰차", font=F(20), fill=(160, 170, 190))
    W.save(O + "결과34.png"); print("ok", [int(x) for x in 고름])
