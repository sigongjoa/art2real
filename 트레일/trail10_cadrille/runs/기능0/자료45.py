# 쇼츠 45 「판결」 재료 — 화면 부품은 변형 허용만: 회전 #17 #26 #30 #32(검증) · 뒤집힘 시험 #22 #4 · 10-12
# python runs/기능0/자료45.py  →  G:/art2real/out/영상05/대화/45_판결/자료/
import os, sys, json, numpy as np, trimesh
os.environ["SET"] = "검증"
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0"), H]
from render import render
from PIL import Image
O = "G:/art2real/out/영상05/대화/45_판결/자료/"; os.makedirs(O, exist_ok=True); RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]
노, 파, 초, 보 = (0.95, 0.85, 0.35), (0.45, 0.68, 0.98), (0.55, 0.8, 0.5), (0.85, 0.55, 0.9)
def 정(m, 기준=None):
    b = (기준 or m).bounds; m = m.copy(); m.apply_translation(-b.mean(0)); m.apply_scale(0.9 / max(b[1] - b[0])); m.apply_translation([.5] * 3); return m
def 찍(m, 색, c=300, v=(1, .6, .8)): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), list(v), img_size=c, cols=np.tile(색, (len(m.faces), 1)))))
def 사람(k): return trimesh.load(RR + L[k]["부품"], force="mesh")
for i in (17, 26, 30, 32):
    k = "검증/%02d" % i; 찍(정(사람(k)), 노).save(O + "사_%02d.png" % i)
    찍(정(trimesh.load(os.path.join(H, "B_교차_검증/%02d.stl" % i))), 파).save(O + "교_%02d.png" % i); 찍(정(trimesh.load(os.path.join(H, "B_회전_검증/%02d.stl" % i))), 보).save(O + "회_%02d.png" % i)
for s, i in (("시험", 22), ("시험", 4)):
    d = "" if s == "시험" else "_검증"; 찍(정(사람("%s/%02d" % (s, i))), 노).save(O + "뒤사_%02d.png" % i)
    찍(정(trimesh.load(os.path.join(H, "B_교차%s/%02d.stl" % (d, i)))), 파).save(O + "뒤교_%02d.png" % i); 찍(정(trimesh.load(os.path.join(H, "B_모델T_검증뺌%s/%02d.stl" % (d, i)))), 초).save(O + "뒤우_%02d.png" % i)
# 한 바퀴 돌림 — #17 반쪽 옆모습을 각도 θ 만큼만 돌린 것(교차와 안 겹침) · 같은 틀(최종 회전체 기준)로 맞춤
import cadquery as cq, cv2
from 도구 import 실루엣, c, 화, V
from 회전 import 찾기
from 윤곽 import 메시로
i = 17; f = 찾기(실루엣(i)); a = f["축"]; oa = [j for j in range(3) if j != a]; 중 = [0.0, 0.0, 0.0]; 중[oa[0]] = c(f["중심"][0]); 중[oa[1]] = c(f["중심"][1])
zs = sorted(f["r"]); 줄 = [(zs[0], 0.0)] + [(z, f["r"][z]) for z in zs] + [(zs[-1], 0.0)]
p = cv2.approxPolyDP(np.array([[r * 10, z * 10] for z, r in 줄], np.int32).reshape(-1, 1, 2), 8, False)[:, 0, :] / 10.0
pts = []
for r, z in p:
    q = list(중); q[a] = c(z); q[oa[0]] += r * 화; pts.append(V(*q))
면 = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)); 축0 = list(중); 축0[a] = -50; 축1 = list(중); 축1[a] = 150
끝 = 메시로(cq.Workplane().add(cq.Solid.revolve(면, 360, V(*축0), V(*축1))))
for t, g in enumerate(np.linspace(20, 360, 12)):
    m = 메시로(cq.Workplane().add(cq.Solid.revolve(면, float(g), V(*축0), V(*축1)))); 찍(정(m, 끝), 보, 420).save(O + "돌림_%02d.png" % t)
print("ok")
