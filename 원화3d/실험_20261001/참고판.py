# -*- coding: utf-8 -*-
"""블렌더 참고판 장면 (10-03 · 여덟 번 자동 합치기 실패 뒤 사용자 「ㄱㄱ」 — 합치기는 코드에 맡기지 않고 사람이 숫자를 정한다).
  바탕 = 정면 껍질(접힌 판 · 정면 화소 단위 · 앞 = −y) · 뒤에 정면 원화 판 · 왼쪽에 옆 원화 판(얼굴이 −y 쪽)
  옆 판 배율 = 정면 · 옆의 「눈 → 뿔 뿌리」 세로 거리 비(특징점.json) — 「눈 → 턱 끝」 비와 다르다(0.92 대 0.63 · 화면에 두 줄로 보임). 어느 쪽이 맞는지는 사람이 정한다.
  옆 판 가로(깊이) 자리는 아직 근거 없음 — 눈을 정면 껍질 앞끝에서 40 뒤에 임시로(GUI 에서 옮길 것).
  가이드 줄: 눈 높이(파랑) · 뿔 뿌리(노랑) · 턱 끝 정면(초록) · 턱 끝 옆(빨강).
blender -b -P 참고판.py → out/오메가몬2/블렌더/참고판.blend · 참고판_{정면,옆,34}.png"""
import bpy, os, sys, json, math, numpy as np
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))
sc = H.scene(res=(800, 800), transparent=False); sc.world.color = (0.55, 0.55, 0.58); sh = sc.display.shading; sh.color_type = "TEXTURE"; sh.light = "STUDIO"
z = np.load(os.path.join(O, "판_1_Z.npz")); m, Z = z["m"], z["Z"]; ys, xs = np.nonzero(m); cu, cv = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
# 정면 껍질
vid = -np.ones(m.shape, int); vid[ys, xs] = np.arange(len(ys)); zz = Z[ys, xs]; front = -60.0
V = np.c_[xs - cu, -(zz - np.nanmax(zz)) + front, -(ys - cv)]
a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
F = np.r_[np.c_[a[ok], c[ok], b[ok]], np.c_[b[ok], c[ok], d[ok]]]
me = bpy.data.meshes.new("정면껍질"); me.from_pydata(V.tolist(), [], F.tolist()); me.update(); sh_o = bpy.data.objects.new("정면껍질", me); sc.collection.objects.link(sh_o)
mat = bpy.data.materials.new("껍질"); mat.diffuse_color = (0.9, 0.9, 0.93, 1); sh_o.data.materials.append(mat)
def 판(이름, 그림, w, h, loc, rot):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = 이름; o.scale = (w, h, 1)
    mt = bpy.data.materials.new(이름); mt.use_nodes = True; nt = mt.node_tree; tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(그림)
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"]); o.data.materials.append(mt); return o
im1 = os.path.join(O, "판_1_원화.png"); im2 = os.path.join(O, "판_2_원화.png")
H1, W1 = 301, 244; H2, W2 = 301, 499
# 정면 판: 화소 (cu, cv) 가 x = 0 · z = 0 · 뒤(y = +150)
판("정면원화", im1, W1, H1, (W1 / 2 - cu, 150, -(H1 / 2 - cv)), (math.radians(90), 0, 0))
# 옆 판 배율 · 자리
f, s2 = P["1"], P["2"]; eye_f = (f["눈/왼"][1] + f["눈/오른"][1]) / 2; eye_s = s2["눈/오른"][1]
k = (eye_f - f["뿔 뿌리"][1]) / (eye_s - s2["뿔 뿌리"][1]); k_턱 = (f["턱 끝"][1] - eye_f) / (s2["턱 끝"][1] - eye_s)
eye_y = front + 40; ex = s2["눈/오른"][0]
cx = (W2 / 2 - ex) * k + eye_y; cz = -((H2 / 2 - eye_s) * k) + -(eye_f - cv)
옆 = 판("옆원화", im2, W2 * k, H2 * k, (-150, cx, cz), (math.radians(90), 0, math.radians(90)))   # +90: 그림 오른쪽 = +y(뒤) · 얼굴(그림 왼쪽)이 −y(앞) — −90 은 좌우가 뒤집혔다
# 가이드 줄
def 줄(이름, zv, 색):
    mt = bpy.data.materials.new(이름); mt.diffuse_color = 색 + (1,)
    for loc, sca in (((0, 148, zv), (300, 1, 1.2)), ((-148, 0, zv), (1, 330, 1.2))):   # 두 원화 판 위에만 가는 줄(3/4 에서 판을 가리지 않게)
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = 이름; o.scale = sca; o.data.materials.append(mt)
줄("눈", -(eye_f - cv), (0.1, 0.3, 1)); 줄("뿔뿌리", -(f["뿔 뿌리"][1] - cv), (1, 0.85, 0.1)); 줄("턱정면", -(f["턱 끝"][1] - cv), (0.1, 0.8, 0.2))
줄("턱옆", -(eye_f - cv) - (s2["턱 끝"][1] - eye_s) * k, (0.9, 0.1, 0.1))
print("옆 배율(뿔 뿌리 기준)", round(k, 3), "· 턱 기준이면", round(k_턱, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, "참고판.blend"))
for nm, (yaw, pitch) in {"정면": (0, 0), "옆": (90, 0), "34": (40, 12)}.items():
    H.look((0, 0, -10), yaw, pitch, 420, dist=900); H.shot(os.path.join(B, f"참고판_{nm}.png"))
print("ok")
