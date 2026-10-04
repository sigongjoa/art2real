# -*- coding: utf-8 -*-
"""도안 장면 — A(사람이 블렌더에서 짓기)용 (10-04 「둘 다 테스트」).
블렌더 틀: x 오른 · y 앞이 − · z 위 · 단위 = 정면 판 화소(머리 높이 약 150). 눈 = (0 깊이).
  정면 원화 판: 뒤(y = +160) · 정면 화소 (px, py) → (px − cu, +160, −py)
  옆 원화 판: 왼쪽(x = −160) · B 맞춤 그대로(배율 · 기울기) — 옆 화소의 네 모서리를 T 로 옮겨 기운 사각형으로(층선과 같은 높이에 맞음)
  층 6 = 가로 선(정면 · 옆 판 위) · 정면 축 = 세로 선 · 옆 축 = 세로 선 · 잰 숫자 = 깊이 −17 의 「창 입구」 판(투명)
  창 모듈 3 판(창모듈2.ply) = 시작점(지울 수 있음)
blender -b -P 도안장면.py → out/오메가몬2/블렌더/도안.blend · 도안_{정면,옆,34}.png"""
import bpy, os, sys, json, math
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
기준 = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8")); 층, 정면축, 옆축 = 기준["층(정면 판 화소 행)"], 기준["정면 축(판 화소 열)"], 기준["옆 축(눈 = 0 · 정면 화소 · 앞 −)"]
P = json.load(open(os.path.join(A, "특징점.json"), encoding="utf-8")); f, s = P["1"], P["2"]
k, tdeg = 기준["옆 맞춤"]; t = math.radians(tdeg)
ex, ey = s["눈/오른"]; xm = sum(s[n][0] for n in ("눈/오른", "뿔 뿌리", "턱 끝", "번개/오른", "안테나 뿌리/오른")) / 5
# 기준선.py 의 c(세로 이동)를 다시: 다섯 점 평균으로(같은 식)
import numpy as np
avg = lambda a, b: (f[a][1] + f[b][1]) / 2
쌍 = [(avg("눈/왼", "눈/오른"), s["눈/오른"]), (f["뿔 뿌리"][1], s["뿔 뿌리"]), (f["턱 끝"][1], s["부리 앞끝"]), (avg("번개/왼", "번개/오른"), s["번개/오른"]), (avg("안테나 뿌리/왼", "안테나 뿌리/오른"), s["안테나 뿌리/오른"])]
c = float(np.mean([yf - k * (sp[1] * math.cos(t) + (sp[0] - xm) * math.sin(t)) for yf, sp in 쌍]))
T = lambda x, y: (k * ((x - ex) * math.cos(t) - (y - ey) * math.sin(t)), k * (y * math.cos(t) + (x - xm) * math.sin(t)) + c)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; xs = np.nonzero(m1)[1]; cu = (xs.min() + xs.max()) / 2
sc = H.scene(res=(800, 800), transparent=False); sc.world.color = (0.5, 0.5, 0.53); sh = sc.display.shading; sh.color_type = "TEXTURE"; sh.light = "STUDIO"
def 이미지판(이름, 그림, 꼭짓점):
    me = bpy.data.meshes.new(이름); me.from_pydata(꼭짓점, [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(); [setattr(uv.data[i], "uv", u) for i, u in enumerate([(0, 1), (1, 1), (1, 0), (0, 0)])]
    o = bpy.data.objects.new(이름, me); sc.collection.objects.link(o)
    mt = bpy.data.materials.new(이름); mt.use_nodes = True; nt = mt.node_tree; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(그림)
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"]); o.data.materials.append(mt); return o
h1, w1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"].shape; h2, w2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"].shape   # 블렌더 파이썬엔 PIL 이 없음 · 판 크기 = 마스크 크기
이미지판("정면원화", os.path.join(A, "판_1_원화.png"), [(0 - cu, 160, 0), (w1 - cu, 160, 0), (w1 - cu, 160, -h1), (0 - cu, 160, -h1)])
옆꼭 = []
for (x, y) in ((0, 0), (w2, 0), (w2, h2), (0, h2)):
    d, r = T(x, y); 옆꼭.append((-160, d, -r))
이미지판("옆원화", os.path.join(A, "판_2_원화_밝게.png"), 옆꼭)   # 밤 장면이라 밝게
def 선(이름, a, b, 색, 굵기=0.8):
    bpy.ops.mesh.primitive_cylinder_add(radius=굵기, depth=1, vertices=6); o = bpy.context.object; o.name = 이름
    import mathutils; va, vb = mathutils.Vector(a), mathutils.Vector(b); o.location = (va + vb) / 2; o.scale = (1, 1, (vb - va).length)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (vb - va).to_track_quat("Z", "Y")
    mt = bpy.data.materials.new(이름); mt.diffuse_color = 색 + (1,); o.data.materials.append(mt); o.color = 색 + (1,)
층색 = [(0.8, 0.15, 0.15), (0.9, 0.5, 0), (0.15, 0.35, 0.9), (0.15, 0.6, 0.25), (0, 0.6, 0.6), (0.5, 0.25, 0.7)]
for (nm, row), col in zip(층.items(), 층색):
    선(nm + "_정면", (-130, 158, -row), (130, 158, -row), col); 선(nm + "_옆", (-158, -140, -row), (-158, 200, -row), col)
for nm, x in 정면축.items(): 선("축 " + nm, (x - cu, 157, -층["L7 뿔 뿌리"] - 40), (x - cu, 157, -층["L2 턱 끝"] - 10), (0.05, 0.05, 0.05), 0.4)
for nm, d in 옆축.items(): 선("옆축 " + nm, (-157, d, -층["L7 뿔 뿌리"] - 40), (-157, d, -층["L2 턱 끝"] - 10), (0.05, 0.05, 0.05), 0.4)
bpy.ops.wm.ply_import(filepath=os.path.join(B, "창모듈2.ply"), forward_axis="Y", up_axis="Z"); bpy.context.selected_objects[0].name = "창모듈3(시작점)"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, "도안.blend"))
sh.color_type = "TEXTURE"
for nm, (yaw, pitch) in {"정면": (0, 0), "옆": (90, 0), "34": (40, 15)}.items():   # 옆 판은 x = −160(먼 쪽) — +x 에서 봐야 모델이 판 앞 · 얼굴이 왼쪽
    H.look((0, 0, -200), yaw, pitch, 380, dist=900); H.shot(os.path.join(B, f"도안_{nm}.png"))
print("ok")
