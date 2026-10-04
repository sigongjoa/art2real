# -*- coding: utf-8 -*-
"""O2 키메 각도 (와타나베 「입체에도 키메 각도가 있다」 · 사카이 「어느 장면의 그 녀석」).
3/4 원화(판_3 · 짓는 데 안 쓴 검증 장)와 같은 카메라를 찾는다 — 움직이는 것은 **카메라만**(yaw · pitch · 배율 · 위치), 모양은 안 건드림.
  직교 투영 · 실루엣을 원화 3/4 마스크 상자에 맞추고 IoU 최대인 yaw(−70..70) · pitch(−30..30) 를 5° 격자 → 1° 다듬기
  그 각도로 면 명암(법선 · 빛) 렌더를 원화 위에 반투명으로 겹친 그림 + 윤곽 빨강
python 키메각도.py <ply 이름> [...] → 키메_<이름>.png · 숫자"""
import os, sys, json, numpy as np, cv2, trimesh
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_3_원화.png"), np.uint8), 1); M3 = np.load(os.path.join(A, "판_3_Z.npz"))["m"].astype(np.uint8)
H, W = M3.shape; ys, xs = np.nonzero(M3); abox = (xs.min(), ys.min(), xs.max(), ys.max())
def 회전(v, yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])   # z 축 둘레(위 = z)
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return v @ Ry.T @ Rx.T
# 2 판: 실루엣 상자 맞춤은 3/4 원화가 위아래로 잘려 각도가 엉뚱했다(pitch 45) → 특징점 대응으로 카메라를 푼다
#   3D 점 = 정면 (x, 행) + 옆 깊이(B 맞춤 T) · 왼쪽 점은 오른쪽 짝의 깊이 · 턱 끝 깊이 = 옆 부리 앞끝(B 짝)
import contextlib, io
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
FP = json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8")); f1, f2, f3 = FP["1"], FP["2"], FP["3"]
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
def 깊이(이름):
    오 = 이름.replace("/왼", "/오른"); 옆 = {"턱 끝": "부리 앞끝"}.get(오, 오)
    return K["T"](*f2[옆])[0] if 옆 in f2 else None
P3, P2 = [], []
for 이름, uv in f3.items():
    d_ = 깊이(이름)
    if 이름 in f1 and d_ is not None: P3.append((f1[이름][0] - cu, d_, -f1[이름][1])); P2.append(uv)
P3, P2 = np.array(P3, float), np.array(P2, float)
def 닮음(a, b):   # a → b 2D 닮음(배율 · 회전 · 이동) 최소제곱
    ma, mb = a.mean(0), b.mean(0); A_, B_ = a - ma, b - mb; U, S_, Vt = np.linalg.svd(A_.T @ B_); R = (U @ Vt).T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = (U @ Vt).T
    sc = S_.sum() / (A_ ** 2).sum(); return sc, R, mb - sc * ma @ R.T
캠 = None
for yaw in range(-80, 81, 2):
    for pitch in range(-40, 41, 2):
        v = 회전(P3, yaw, pitch); a = np.c_[v[:, 0], -v[:, 2]]; sc, R, t = 닮음(a, P2); 잔 = np.sqrt((((sc * a @ R.T + t) - P2) ** 2).sum(1).mean())
        if 캠 is None or 잔 < 캠[0]: 캠 = (잔, yaw, pitch, sc, R, t)
print({"특징점": len(P3), "잔차(화소)": round(캠[0], 2), "yaw": 캠[1], "pitch": 캠[2]})
def 투영(me, yaw, pitch):
    _, yaw, pitch, sc, R, t = 캠; v = 회전(me.vertices, yaw, pitch); a = np.c_[v[:, 0], -v[:, 2]]
    return sc * a @ R.T + t, v[:, 1], sc
def 실루엣(P, faces):
    img = np.zeros((H, W), np.uint8)
    cv2.fillPoly(img, [np.round(P[f]).astype(np.int32) for f in faces], 1); return img
def iou(a, b): return float((a & b).sum() / max(1, (a | b).sum()))
결과 = {}
for nm in sys.argv[1:]:
    me = trimesh.load(os.path.join(B, nm + ".ply"), process=False)
    yaw, pitch = 캠[1], 캠[2]; P, dep, _ = 투영(me, yaw, pitch); s_ = iou(실루엣(P, me.faces), M3)
    n = 회전(me.face_normals, yaw, pitch); L = np.array([-0.4, -0.8, 0.45]); L /= np.linalg.norm(L)
    shade = np.clip(0.35 + 0.65 * np.clip(n @ (-L * np.array([1, 1, -1])), 0, 1), 0, 1)
    col = me.visual.vertex_colors[me.faces][:, :, :3].mean(1).astype(float)
    img = np.zeros((H, W, 3), np.uint8); order = np.argsort(-dep[me.faces].mean(1))   # 먼 면부터(앞 = −y)
    for f in order:
        c = (col[f] * shade[f])[::-1]; cv2.fillPoly(img, [np.round(P[me.faces[f]]).astype(np.int32)], c.tolist())
    sil = 실루엣(P, me.faces); over = art.copy(); over[sil > 0] = (0.5 * art[sil > 0] + 0.5 * img[sil > 0]).astype(np.uint8)
    cs, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(over, cs, -1, (0, 0, 255), 1)
    cs2, _ = cv2.findContours(M3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(over, cs2, -1, (0, 255, 0), 1)
    sheet = np.concatenate([art, img, over], 1); sheet = cv2.resize(sheet, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png", sheet)[1].tofile(os.path.join(B, f"키메_{nm}.png")); 결과[nm] = {"3/4 IoU": round(s_, 3), "yaw": yaw, "pitch": pitch}
print(json.dumps(결과, ensure_ascii=False))
