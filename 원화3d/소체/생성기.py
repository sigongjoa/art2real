# -*- coding: utf-8 -*-
"""소체 생성기 (2026-09-28) — 골격 · 비율 · 체형 · 키 → 소체 STL + 관절표 JSON.

    python 생성기.py            -> 이족 8 (비율 4 × 남 · 여) 을 짓고 검사 · 그림 out/소체/소체_시트.png
    from 생성기 import 이족, 사족;  몸, 관절, 뼈 = 이족("영웅", "남", 300)
위키: 원화3d/지식/베이스/ · 관절 목록은 S.H.Figuarts 소체(볼 · 이중 경첩 · 발목 흔들 · 발끝)를 따름.
수치: 메카 남 · 영웅 여 일부 · SD 두신은 실측/공식(09-28), 나머지는 드로잉 통념(가설) — 비율표 주석에 칸마다 출처.
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M, trimesh
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
OUT = os.path.join(원화3d, "out", "소체"); os.makedirs(OUT, exist_ok=True)
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"

# ════════ 비율 표 — u = 키/8 (보통 머리 높이) ════════
#        두신 n · 다리/머리아래 · 너비(u) 남: 어깨 · 엉덩이 · 허리 / 여: 같은 순 · 팔다리 굵기 배 · 머리 배
# 실측(09-28): 달롱넷 · 리뷰 정면 전신 사진 px(out/키트/*/dalong|추가 · 원근 몇 % · 벌린 다리로 키 −2~3 %). 머리 = 정수리(뿔 · 안테나 뺌) → 턱.
#   어깨 = 어깨 덩어리 바깥 폭 · 엉덩이 = 허벅지 바깥 폭 · 다리 = 샅 높이 / 턱 아래 키. 표는 지식/베이스/인간.md 「실측 (09-28)」
비율표 = {
    # 전부 통념 — 사람 실사 비율 키트가 없다(figma · Figuarts 소체는 공개 두신 수치 못 찾음)
    "사실": dict(n=7.5, 다리=0.53, 남=(2.1, 1.45, 1.2), 여=(1.8, 1.65, 1.0), 굵기=1.0, 머리=1.0),
    # 여 어깨 · 엉덩이 · 다리 = 30MS 리시에타 · FAG 轟雷 실측(n=2: 어깨/키 .224 · 엉덩이/키 .200 · 다리 .62). 두신 8.5 · 남 · 허리는 통념
    #   (두 키트 두신은 6.4 · 6.9 — 머리카락 포함 애니 소녀 머리라 「영웅」 8.5 와 다른 판. n 은 안 바꿈)
    "영웅": dict(n=8.5, 다리=0.62, 남=(2.5, 1.45, 1.15), 여=(1.8, 1.6, 0.95), 굵기=1.0, 머리=1.0),
    # 남 = 건담 실측: 두신 · 다리 · 엉덩이 n=6(EG · HG · RG · MG · PG RX-78 + MG 자쿠 · 두신 9.1~9.6 · 다리 .56~.61),
    #   어깨 n=5(RX-78 만 · 자쿠는 방패 · 가시 어깨라 뺌 · 어깨/키 .394~.432). 허리 · 여 전부 통념.
    #   머리 0.85 → 1.0: 작은 머리는 이제 n 이 이미 담는다(겹치면 재기 두신이 10.1 로 나옴)
    "메카": dict(메카형=True, n=9.4, 다리=0.58, 남=(3.27, 2.16, 1.2), 여=(2.5, 1.8, 1.0), 굵기=1.3, 머리=1.0),
    # n 2.5 = 넨도로이드 공식 「2.5頭身 · 全高約100mm」(goodsmile.info/ja/aboutnendoroids). 나머지 통념(넨도 사진 실측 없음)
    # 오메가몬: 원화 정면(트레일/trail7_part3d/in/omega_front_clean.png · 1024 px) 눈대중 px — 돔 100 · 턱 182 · 샅 480 · 발바닥 960 · 어깨 몸통 폭 300 · 엉덩이 160 · 허리 90 (n = 1)
    "오메가몬": dict(메카형=True, n=10.5, 다리=0.62, 남=(2.8, 1.5, 0.85), 여=(2.8, 1.5, 0.85), 굵기=1.3, 머리=1.0),
    "SD":   dict(n=2.5, 다리=0.42, 남=(2.0, 1.7, 1.5), 여=(1.8, 1.8, 1.4), 굵기=1.4, 머리=1.0),
}

def 공(c, r): return M.Manifold.sphere(1.0, 48).scale(list(np.broadcast_to(r, 3))).translate(list(c))
def 막대(a, b, ra, rb=None):
    rb = ra if rb is None else rb; return M.Manifold.hull_points(np.vstack([공(a, ra).to_mesh().vert_properties[:, :3], 공(b, rb).to_mesh().vert_properties[:, :3]]))
def 합(xs): return M.Manifold.batch_boolean(list(xs), M.OpType.Add)

def 이족(비율="영웅", 체형="남", 키=300.0):
    p = 비율표[비율]; n = p["n"]; T = 키; H = T / n; u = T / 8; B = T - H
    sw, hw, ww = [v * u for v in p[체형]]; g = p["굵기"] * (0.85 if 체형 == "여" else 1.0) * u
    턱 = T - H; 어깨z = 턱 - (0.08 if 비율 == "SD" else 0.05) * B; 샅 = 턱 - (1 - p["다리"]) * B
    발목z = 0.05 * T; 무릎z = 샅 - 0.5 * (샅 - 발목z)
    손목z = 샅 + (0.12 * B if 비율 == "SD" else -0.02 * H); 팔꿈치z = (어깨z + 손목z) / 2 + 0.03 * H
    r위팔, r아래팔, r허벅, r정강 = 0.2 * g, 0.17 * g * (1.3 if p.get("메카형") else 1), 0.3 * g, 0.22 * g * (1.3 if p.get("메카형") else 1)
    어깨x = sw / 2 - 0.8 * r위팔; 고x = hw / 2 * 0.55; 몸h = 어깨z - 샅
    관 = []   # (이름, 종류, 위치, 축, 범위)
    def J(이름, 종류, c, 축=(1, 0, 0), 범위=""): 관.append(dict(이름=이름, 종류=종류, 위치=[round(float(v), 2) for v in c], 축=축, 범위=범위)); return np.array(c, float)
    머리J = J("머리", "볼", (0, 0.05 * H, 턱 + 0.12 * H), 범위="끄덕 −25~+20 · 돌림 ±60")
    목J = J("목", "볼", (0, 0.05 * H, 어깨z + 0.04 * B), 범위="±20")
    배J = J("배", "볼", (0, 0, 어깨z - 0.62 * 몸h), 범위="돌림 ±30 · 굽힘 ±20")
    몸 = [공((0, 0.05 * H, 턱 + 0.5 * H), np.array([0.36 if 비율 != "SD" else 0.45, 0.45, 0.5]) * H * p["머리"]),
         막대(목J, 머리J, 0.16 * g if 비율 != "SD" else 0.1 * g),
         공((0, 0, 어깨z - 0.28 * 몸h), (sw / 2 * 0.8, 0.45 * sw / 2 * (0.9 if p.get("메카형") else 1.0), 0.36 * 몸h)),
         공((0, 0, 배J[2]), (ww / 2, ww * 0.4, 0.2 * 몸h)),
         공((0, 0, 샅 + 0.12 * 몸h), (hw / 2, hw * 0.38, 0.2 * 몸h))]
    뼈 = [(머리J, 목J), (목J, 배J)]
    for s, 쪽 in ((1, "L"), (-1, "R")):
        어 = J("어깨" + 쪽, "볼", (s * 어깨x, 0, 어깨z), 범위="들기 0~90")
        팔 = J("팔꿈치" + 쪽, "이중경첩", (s * (어깨x + 0.08 * H), 0.02 * H, 팔꿈치z), 범위="0~130")
        손 = J("손목" + 쪽, "볼", (s * (어깨x + 0.14 * H), 0, 손목z), 범위="±40")
        고 = J("고관절" + 쪽, "볼", (s * 고x, 0, 샅 + 0.06 * 몸h), 범위="앞 90 · 옆 45")
        무 = J("무릎" + 쪽, "이중경첩", (s * 고x * 1.02, -0.02 * H, 무릎z), 범위="0~130")
        발 = J("발목" + 쪽, "흔들", (s * 고x * 1.04, 0, 발목z), 범위="앞뒤 ±25 · 옆 ±20")
        끝 = J("발끝" + 쪽, "경첩", (s * 고x * 1.04, -(0.75 if 비율 == "SD" else 0.9) * u * (1.2 if p.get("메카형") else 1), 0.03 * T), 범위="0~30")
        몸 += [공(어, r위팔 * (1.6 if p.get("메카형") else 1.25)), 막대(어, 팔, r위팔, r위팔 * 0.9), 막대(팔, 손, r아래팔, r아래팔 * 0.8),
              공(손 - (0, 0, 0.3 * u), (0.14 * u, 0.2 * u, 0.36 * u) * np.array(1.2 if p.get("메카형") else 1.0)),
              막대(고, 무, r허벅, r허벅 * 0.75), 막대(무, 발, r정강, r정강 * 0.7), 막대(발, 끝, r정강 * 0.75, r정강 * 0.5)]
        뼈 += [(목J, 어), (어, 팔), (팔, 손), (배J, 고), (고, 무), (무, 발), (발, 끝)]
    return 합(몸), 관, 뼈

# 사족 · 조류 · 뱀 · 물고기 · 다족 · 탈것 · 부착은 골격들.py

# ════════ 검사 ════════
def 재기(몸, 관, 뼈, 키, n=None, 이족형=True):
    b = 몸.bounding_box(); 높이 = b[5] - b[2]; 거울 = 몸.mirror([1, 0, 0])
    r = dict(조각=len(몸.decompose()), 높이=round(높이, 1), 대칭차=round((몸 - 거울).volume() / 몸.volume(), 4))
    if 이족형:
        J = {j["이름"]: np.array(j["위치"]) for j in 관}
        머리높이 = b[5] - (J["머리"][2] - 0.12 * 키 / n)
        r.update(두신=round(높이 / 머리높이, 2), 어깨폭_머리폭=round(2 * abs(J["어깨L"][0]) / (몸 ^ M.Manifold.cube([400, 400, 1]).translate([-200, -200, b[5] - 0.5 * 머리높이])).bounding_box()[3] / 2, 2))
        assert J["어깨L"][2] > J["팔꿈치L"][2] > J["손목L"][2] and J["고관절L"][2] > J["무릎L"][2] > J["발목L"][2], "관절 순서"
        assert abs(r["두신"] - n) / n < 0.08, ("두신", r["두신"], n)
    assert r["조각"] == 1 and r["대칭차"] < 0.01 and abs(높이 - 키) / 키 < 0.06, r
    return r

# ════════ 그림 ════════
블 = r'''
import bpy, sys, json, math
from mathutils import Vector
a = json.loads(open(sys.argv[-1], encoding="utf-8").read())
for 판 in a["판"]:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    for f, c in 판["부품"]:
        bpy.ops.import_mesh.stl(filepath=f); o = bpy.context.selected_objects[0]
        m = bpy.data.materials.new("m"); m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.5
        o.data.materials.append(m)
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.62, 0.64, 1)
    for loc, e in (((-300, -500, 600), 2.2), ((500, -300, 150), 0.8)):
        d = bpy.data.lights.new("s", "SUN"); d.energy = e; o = bpy.data.objects.new("s", d); sc.collection.objects.link(o)
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.clip_end = 20000; cam.data.ortho_scale = 판["폭"]
    sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x, sc.render.resolution_y = 판["해상"]
    sc.view_settings.view_transform = "Standard"      # Filmic 은 색을 씻어낸다(파랑 → 연보라 · 빨강 → 분홍)
    sc.render.use_freestyle = True; sc.render.line_thickness = 1.0
    fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(140)
    for l in list(fs.linesets): fs.linesets.remove(l)
    l = fs.linesets.new("l"); l.linestyle = bpy.data.linestyles.new("ls"); l.select_silhouette = True; l.select_border = True
    t = Vector(판["중심"]); cam.location = t + Vector((0, -3000, 0)); cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = 판["out"]; bpy.ops.render.render(write_still=True)
'''
색 = dict(몸=(0.78, 0.78, 0.8), 볼=(0.85, 0.2, 0.15), 경첩=(0.15, 0.35, 0.85), 뼈=(0.15, 0.15, 0.17))
def 뼈대(관, 뼈, 굵=2.0):
    공들 = [공(j["위치"], 굵 * 2.6) for j in 관 if j["종류"] in ("볼", "볼사슬", "흔들")]
    축들 = [막대(np.array(j["위치"]) - 3 * 굵 * np.array(j["축"]), np.array(j["위치"]) + 3 * 굵 * np.array(j["축"]), 굵 * 2.0) for j in 관 if "경첩" in j["종류"]]
    return 합([막대(a, b, 굵 * 0.7) for a, b in 뼈]), 합(공들), 합(축들)
def 돌려(m, 각, x): return m.rotate([0, 0, 각]).translate([x, 0, 0])

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    이족들 = [(b, t) for b in 비율표 if b != "오메가몬" for t in ("남", "여")]; 간격 = 175.0; 판 = []; 표 = {}
    묶음 = {k: [] for k in ("정면몸", "옆몸", "정면뼈", "정면볼", "정면경첩")}
    for i, (b, t) in enumerate(이족들):
        몸, 관, 뼈 = 이족(b, t, 300.0); 표[b + t] = 재기(몸, 관, 뼈, 300.0, 비율표[b]["n"])
        d = os.path.join(OUT, "이족_%s_%s" % (b, t)); os.makedirs(d, exist_ok=True)
        trimesh.Trimesh(몸.to_mesh().vert_properties[:, :3], 몸.to_mesh().tri_verts).export(os.path.join(d, "소체.stl"))
        json.dump(dict(골격="이족", 비율=b, 체형=t, 키=300.0, 관절=관, 검사=표[b + t]), open(os.path.join(d, "관절.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        x = i * 간격; 뼈m, 볼m, 경m = 뼈대(관, 뼈)
        묶음["정면몸"].append(돌려(몸, 0, x)); 묶음["옆몸"].append(돌려(몸, -90, x)); 묶음["정면뼈"].append(돌려(뼈m, 0, x)); 묶음["정면볼"].append(돌려(볼m, 0, x)); 묶음["정면경첩"].append(돌려(경m, 0, x))
        print(b, t, 표[b + t], flush=True)
    T = os.path.join(OUT, "_그림"); os.makedirs(T, exist_ok=True)
    def 저장(k):
        m = 합(묶음[k]); f = os.path.join(T, k + ".stl"); trimesh.Trimesh(m.to_mesh().vert_properties[:, :3], m.to_mesh().tri_verts).export(f); return f
    cx = 간격 * 3.5; W = 간격 * 8 + 40
    판 = [dict(부품=[(저장("정면몸"), 색["몸"])], 폭=W, 해상=(2400, 620), 중심=(cx, 0, 150), out=os.path.join(T, "정면.png")),
         dict(부품=[(저장("옆몸"), 색["몸"])], 폭=W, 해상=(2400, 620), 중심=(cx, 0, 150), out=os.path.join(T, "옆.png")),
         dict(부품=[(저장("정면뼈"), 색["뼈"]), (저장("정면볼"), 색["볼"]), (저장("정면경첩"), 색["경첩"])], 폭=W, 해상=(2400, 620), 중심=(cx, 0, 150), out=os.path.join(T, "뼈.png")),]
    jf = os.path.join(T, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(T, "블.py"); open(pf, "w", encoding="utf-8").write(블)
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    # 시트
    ft, fs = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26), ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    img = {k: Image.open(os.path.join(T, k + ".png")).convert("RGB") for k in ("정면", "옆", "뼈")}
    S = Image.new("RGB", (2420, 60 + 3 * 700), (245, 245, 243)); dr = ImageDraw.Draw(S)
    dr.text((10, 10), "소체 생성기 — 이족 8(비율 4 × 남 · 여) · 키 300 mm · 빨강 = 볼 · 파랑 = 경첩", font=ft, fill=(20, 20, 20))
    for r_, (k, 제목) in enumerate((("정면", "정면"), ("옆", "옆"), ("뼈", "뼈대 + 관절"))):
        y = 60 + r_ * 700; S.paste(img[k], (10, y + 30)); dr.text((14, y), 제목, font=ft, fill=(20, 20, 20))
        if r_ == 0:
            for i, (b, t) in enumerate(이족들):
                q = 표[b + t]; px = 10 + (i + 0.5) * 2400 / 8 - 90
                dr.text((px, y + 652), "%s %s · %.1f 두신 · 어깨/머리 %.2f" % (b, t, q["두신"], q["어깨폭_머리폭"]), font=fs, fill=(30, 30, 30))
    p = os.path.join(OUT, "소체_시트.png"); S.save(p); print("시트", p, S.size)

