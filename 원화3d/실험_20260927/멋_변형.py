# -*- coding: utf-8 -*-
"""오메가몬 PG — 「멋져 보이는」 비례 변형 썸네일 (2026-09-27).

    python 멋_변형.py            -> Blender 4.0 헤드리스로 12 변형 × 3 컷 렌더 + 시트 셋
    python 멋_변형.py --시트만    -> 렌더는 그대로 두고 시트만 다시

부품은 새로 짓지 않는다. 최신 디자인 판 STL(몸통 · 다리 · 머리어깨 − 색분할 대체 + 색분할 + 돌출)을
부위 묶음으로 나눠 부착점(관절.json 피벗) 기준 스케일 · 이동만 한다. 원본 STL 은 안 건드린다.
변형 값은 아래 「변형」 표 — 사용자가 고르면 이 값으로 실제 설계(디자인_*.py)를 고친다.

출력: out/출력/오메가몬_PG/멋/렌더/{글자}_{컷}.png · 썸네일.png(영웅 3/4) · 썸네일_자세.png · 썸네일_정면.png(원화와 같은 정사각 정면)
"""
import os, sys, json, math, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # G:/art2real/원화3d
DES = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인")
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "멋")
REN = os.path.join(OUT, "렌더")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
원화 = r"G:\art2real\트레일\trail7_part3d\in\omega_front_clean.png"
FRA = os.path.join(ROOT, "out", "키트", "FRA_오메가몬", "dalong", "frs45_02.jpg")

# ── 변형 표 ─────────────────────────────────────────────────────────────
# 키: 허리 = 복부·허리 x,y 배율(축 x=0) · 머리 = 목위 피벗 기준 균일 · 뿔 = 가운데 뿔 전체 배율(머리 배율 포함)
#     어깨 = 어깨돔(+방패·가시) 어깨회전 피벗 기준 균일, 안쪽 가장자리 고정 · 다리 = 발목~고관절 z 배율(윗몸은 따라 올림)
#     팔머리 = 팔꿈치 피벗 기준 균일(팔끝·손·칼·대포·뿔·날·코) · 발 = 발 x,y 배율(발 중심)
#     팔머리올림 = 팔머리를 z 로 올리는 mm · 망토 = 등 뒤 판 넷(폭 = 전고 × 값)
# 비율 근거: README 「원작 → 피규어 번역 규칙」 · out/번역/디지몬/비율.json (우리_원화 ÷ 우리_모델)
BASE = dict(허리=1.0, 머리=1.0, 뿔=1.0, 어깨=1.0, 다리=1.0, 팔머리=1.0, 발=1.0, 팔머리올림=0.0, 망토=0.0)
_I = dict(허리=0.77, 머리=0.75, 어깨=1.15, 다리=1.10, 팔머리=1.30, 발=1.15)          # 키트(FRA) 쪽 번역 규칙
_J = dict(머리=0.087 / 0.097, 뿔=0.060 / 0.055, 어깨=1.17, 팔머리=0.30 / 0.26, 발=0.228 / 0.194)  # 원화 비율 (어깨 1.17 = 돔 폭 36 mm 가 바깥으로 6 mm → 어깨폭 130→142 = ×1.095)
# 원화 과장 더 밀기(J+): J 가 바꾼 양을 1.5 제곱(어깨는 바깥 증가분 ×1.5) + 허리 조임.
# ⚠ 비율.json 으로 보면 원화는 평균(tri·FRA)보다 어깨가 좁고(0.392 < 0.431) 허리가 넓다(0.108 > 0.089) —
#    「평균에서 벗어난 방향」을 기계적으로 밀면 어깨가 좁아진다. 사용자가 말한 방향(어깨↑ 팔머리↑ 허리↓ 머리↓ 발↑)을 따랐다.
_Jp = dict(머리=(0.087 / 0.097) ** 1.5, 뿔=(0.060 / 0.055) ** 1.5, 어깨=1 + 0.17 * 1.5, 팔머리=(0.30 / 0.26) ** 1.5,
           발=(0.228 / 0.194) ** 1.5, 허리=0.85)
변형 = {
    "A": ("지금 그대로 (대조)", {}),
    "B": ("허리만 조임", dict(허리=0.77)),
    "C": ("어깨돔만 크게", dict(어깨=1.15)),
    "D": ("팔머리만 크게", dict(팔머리=1.30)),
    "E": ("다리만 길게", dict(다리=1.10)),
    "F": ("허리 조임 + 어깨돔 (역삼각)", dict(허리=0.77, 어깨=1.15)),
    "G": ("키트 번역 규칙 전부", _I),
    "H": ("원화 비율로 (머리·뿔·어깨·팔머리·발)", _J),
    "I": ("H + 등 뒤 망토 판", dict(_J, 망토=0.55)),
    "J": ("원화 과장을 더 밀기", _Jp),
    "K": ("J + 등 뒤 망토 판", dict(_Jp, 망토=0.55)),
    "L": ("K + 다리 길게 · 팔머리 올려 묵직한 팔", dict(_Jp, 망토=0.55, 다리=1.08, 팔머리올림=16.0)),
}
컷 = {  # 이름: (자세, 카메라 방위°(+ = 보는 쪽 오른쪽), 카메라 높이/전고, 초점 mm, 가로, 세로)
    "영웅": (False, 32, 0.22, 70, 640, 832),
    "자세": (True, 32, 0.22, 70, 640, 832),
    "정면": (False, 0, 0.30, 85, 768, 768),
}


# ════════════════════════════ Blender 쪽 ════════════════════════════
def 묶음(n, x):
    s = "L" if x < 0 else "R"
    if n == "뿔": return "뿔"
    if any(k in n for k in ("팔끝", "손", "칼", "대포", "L뿔", "L날", "R코")): return "팔머리" + s
    if any(k in n for k in ("투구", "얼굴", "V안테나")): return "머리"
    if any(k in n for k in ("어깨돔", "방패", "가시")): return "어깨" + s
    if "윗팔" in n: return "팔" + s
    if any(k in n for k in ("복부", "허리")): return "허리"
    if "가슴" in n or "목깃" in n: return "가슴"
    if any(k in n for k in ("발바닥", "발등", "발목띠", "발톱", "발끝")): return "발" + s
    return "다리" + s   # 허벅지 · 정강이 · 무릎 · 옆스커트 · 가랑이


def blender_main(args):
    import bpy, bmesh
    from mathutils import Matrix, Vector

    J = {j["이름"]: Vector(j["피벗mm"]) for j in json.load(open(os.path.join(ROOT, "out", "가동", "관절.json"), encoding="utf-8"))["관절"]}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene

    # ── 부품 읽기 ──
    목록 = []   # (이름, 경로, 색)
    대체 = set(json.load(open(os.path.join(DES, "색분할", "부품.json"), encoding="utf-8"))["대체"])
    for 폴더 in ("몸통", "다리", "머리어깨", "색분할", "돌출"):
        P = json.load(open(os.path.join(DES, 폴더, "부품.json"), encoding="utf-8"))["부품"]
        for n, v in P.items():
            if 폴더 == "머리어깨" and n in 대체: continue
            c = v.get("색")
            if not isinstance(c, list):                              # 다리 json 은 「흰 · 검정 · 금」 이름
                c = {"검정": [0.22, 0.22, 0.24], "금": [0.9, 0.72, 0.2]}.get(c, [0.93, 0.93, 0.95])
            목록.append((n, os.path.join(DES, 폴더, v.get("파일", n + ".stl")), c))
    mats = {}
    def 재질(c):
        k = tuple(round(t, 3) for t in c)
        if k not in mats:
            m = bpy.data.materials.new("m%d" % len(mats)); m.use_nodes = True
            b = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*[t ** 2.2 for t in k], 1)
            gold = k[0] > 0.8 and k[2] < 0.35
            b.inputs["Roughness"].default_value = 0.3 if gold else 0.42
            b.inputs["Metallic"].default_value = 0.6 if gold else 0.0
            mats[k] = m
        return mats[k]
    objs = []
    for n, p, c in 목록:
        bpy.ops.wm.stl_import(filepath=p)
        o = bpy.context.selected_objects[0]
        me = o.data
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(35)
        for f in me.polygons: f.use_smooth = True
        me.materials.append(재질(c))
        vs = [v.co for v in me.vertices]
        lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
        g = 묶음(n.split("_", 1)[1] if n.startswith("돌출") else n, (lo.x + hi.x) / 2)
        objs.append((o, g, lo, hi))
    def 경계(gs):
        L = [(lo, hi) for o, g, lo, hi in objs if g in gs]
        return Vector([min(l[i] for l, h in L) for i in range(3)]), Vector([max(h[i] for l, h in L) for i in range(3)])
    전고0 = 경계({g for _, g, _, _ in objs})[1].z
    if "--재기" in args:
        for g in sorted({g for _, g, _, _ in objs}):
            lo, hi = 경계({g}); print("묶음", g, [round(t, 1) for t in lo], [round(t, 1) for t in hi])
        print("전고", 전고0); return

    def S(v, s):       # 점 v 기준 배율 (s = 수 또는 (sx,sy,sz))
        s = (s, s, s) if not isinstance(s, tuple) else s
        M = Matrix.Diagonal((*s, 1.0))
        return Matrix.Translation(v) @ M @ Matrix.Translation(-v)
    def R(v, ax, deg): return Matrix.Translation(v) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-v)
    T = Matrix.Translation

    z발목, z엉덩 = J["L발목볼"].z, J["L고관절벌림"].z

    def 행렬(p, 자세):
        올림 = T((0, 0, (p["다리"] - 1) * (z엉덩 - z발목)))
        M = {"가슴": 올림, "허리": 올림 @ S(Vector((0, 14.7, 0)), (p["허리"], p["허리"], 1.0)),
             "머리": 올림 @ S(J["목위"], p["머리"])}
        뿔lo, 뿔hi = 경계({"뿔"})
        M["뿔"] = M["머리"] @ S(Vector(((뿔lo.x + 뿔hi.x) / 2, (뿔lo.y + 뿔hi.y) / 2, 뿔lo.z)), p["뿔"] / p["머리"])
        for s, sg in (("L", -1), ("R", 1)):
            lo, hi = 경계({"어깨" + s}); piv = J[s + "어깨회전"]
            안 = hi.x if sg < 0 else lo.x                               # 몸 쪽 가장자리 x
            밀기 = 안 - (piv.x + (안 - piv.x) * p["어깨"])              # 커져서 몸 쪽으로 파고든 만큼 바깥으로
            M["어깨" + s] = 올림 @ T((밀기, 0, 0)) @ S(piv, p["어깨"])
            M["팔" + s] = 올림
            M["팔머리" + s] = 올림 @ T((0, 0, p["팔머리올림"])) @ S(J[s + "팔꿈치"], p["팔머리"])
            M["다리" + s] = S(Vector((0, 0, z발목)), (1.0, 1.0, p["다리"]))
            lo, hi = 경계({"발" + s})
            M["발" + s] = S(Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0)), (p["발"], p["발"], 1.0))
        if 자세:   # 팔 조금 벌리고 · L 다리 한 발 앞 · R 다리 조금 뒤 · 발은 바닥과 평행
            for s, sg in (("L", 1), ("R", -1)):
                piv = M["팔" + s] @ J[s + "어깨들기"]
                for g in ("팔" + s, "팔머리" + s): M[g] = R(piv, "Y", 20 * sg) @ M[g]
            for s, deg in (("L", -18), ("R", 9)):
                hip = M["다리" + s] @ J[s + "고관절"]; ank = M["다리" + s] @ J[s + "발목볼"]
                Rh = R(hip, "X", deg); ank2 = Rh @ ank
                M["다리" + s] = Rh @ M["다리" + s]
                M["발" + s] = R(ank2, "X", -deg) @ Rh @ M["발" + s]
        return M

    # ── 망토 판 넷 (J/K 용 · 이 파일에서만 · 흰 겉 / 빨강 안) ──
    def 망토(p, M, 전고):
        W = p["망토"] * 전고; w = W / 4 * 1.12
        lo, hi = 경계({"가슴"}); top = (M["가슴"] @ Vector((0, 0, hi.z - 8))).z; ybk = hi.y + 4
        L = 0.62 * 전고
        흰, 빨 = 재질((0.93, 0.93, 0.95)), 재질((0.72, 0.1, 0.08))
        out = []
        for i, (cx, fan) in enumerate(((-1.5, -13), (-0.5, -4), (0.5, 4), (1.5, 13))):
            h = L * (1.0 if abs(cx) < 1 else 0.9)
            pts = [(-w / 2, 0), (w / 2, 0), (w / 2, -h * 0.8), (0.1 * w, -h), (-w / 2, -h * 0.86)]
            if cx > 0: pts = [(-x, z) for x, z in pts][::-1]
            bm = bmesh.new()
            앞 = [bm.verts.new((x, 0, z)) for x, z in pts]; 뒤 = [bm.verts.new((x, 2.4, z)) for x, z in pts]
            f1 = bm.faces.new(앞[::-1]); f2 = bm.faces.new(뒤)
            for k in range(len(pts)): bm.faces.new((앞[k], 앞[(k + 1) % 5], 뒤[(k + 1) % 5], 뒤[k]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces: f.material_index = 0 if f.normal.y < -0.5 else 1
            me = bpy.data.meshes.new("망토%d" % i); bm.to_mesh(me); bm.free()
            me.materials.append(빨); me.materials.append(흰)
            o = bpy.data.objects.new("망토%d" % i, me); 몸.objects.link(o)
            o.matrix_world = Matrix.Scale(0.01, 4) @ T((cx * W / 4, ybk + abs(cx) * 3, top)) @ Matrix.Rotation(math.radians(fan), 4, "Y") @ Matrix.Rotation(math.radians(-12), 4, "X")
            out.append(o)
        return out

    # ── 조명 · 바닥 · 카메라 (모든 변형 같음 · 단위 m = mm × 0.01) ──
    sc.render.engine = "CYCLES"
    try:
        pr = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try: pr.compute_device_type = t; pr.get_devices(); break
            except TypeError: pass
        for d in pr.devices: d.use = True
        sc.cycles.device = "GPU"
    except Exception as e: print("GPU 안 됨", e)
    sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.52, 0.55, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=60); bpy.context.object.is_shadow_catcher = True
    몸 = bpy.data.collections.new("몸"); sc.collection.children.link(몸)
    for o, *_ in objs: sc.collection.objects.unlink(o); 몸.objects.link(o)
    def 빛(name, loc, e, size, col=(1, 1, 1)):
        L = bpy.data.lights.new(name, "AREA"); L.energy = e; L.size = size; L.color = col
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0.2, 1.6)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    빛("키", (-3.2, -4.5, 5.0), 330, 2.5, (1, 0.97, 0.92))
    빛("림L", (-3.5, 4.0, 3.8), 520, 1.2, (0.85, 0.9, 1))
    빛("림R", (3.8, 3.5, 3.2), 460, 1.2, (0.85, 0.9, 1))
    # 윤곽선(프리스타일): 실루엣 · 접힘(각진 모서리) · 재질 경계 = 색 경계. 선은 원화 먹선처럼 짙은 회색
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = 1.1
    fs = sc.view_layers[0].freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("선")
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new("선")
    ls.select_by_collection = True; ls.collection = 몸   # 바닥 가장자리 선 빼기
    ls.select_silhouette = ls.select_border = ls.select_crease = ls.select_material_boundary = True
    sc.view_layers[0].freestyle_settings.crease_angle = math.radians(125)
    ls.linestyle.color = (0.08, 0.08, 0.1); ls.linestyle.alpha = 0.85
    빛("채움", (4.5, -5.0, 1.2), 90, 4.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam

    골라 = [a for a in args if a in 변형] or list(변형)
    컷들 = [a for a in args if a in 컷] or list(컷)
    os.makedirs(REN, exist_ok=True)
    for c in 컷들:
        자세, az, ch, lens, rw, rh = 컷[c]
        sc.render.resolution_x, sc.render.resolution_y = rw, rh
        cam.data.lens = lens
        H = 전고0 * 0.01 * 1.06; tgt = Vector((0, 0.2, H * 0.5))
        vfov = 2 * math.atan(18 / lens) if rh >= rw else 2 * math.atan(18 * rh / rw / lens)
        d = H * 0.56 / math.tan(vfov / 2)
        a = math.radians(az)
        cam.location = Vector((d * math.sin(a), -d * math.cos(a), H * ch))
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        for k in 골라:
            p = dict(BASE, **변형[k][1])
            M = 행렬(p, 자세)
            for o, g, lo, hi in objs: o.matrix_world = Matrix.Scale(0.01, 4) @ M[g]
            bpy.context.view_layer.update()
            바닥 = min((o.matrix_world @ Vector(b)).z for o, g, _, _ in objs if g.startswith("발") for b in o.bound_box)   # 발로 선다(칼 끝이 바닥 밑으로 가도 발을 띄우지 않게)
            for o, g, lo, hi in objs: o.matrix_world = T((0, 0, -바닥)) @ o.matrix_world
            전고 = 전고0 * p["다리"]
            extra = 망토(p, M, 전고) if p["망토"] else []
            for e in extra: e.matrix_world = T((0, 0, -바닥)) @ e.matrix_world
            sc.render.filepath = os.path.join(REN, "%s_%s.png" % (k, c))
            bpy.ops.render.render(write_still=True)
            for e in extra: bpy.data.objects.remove(e)
            print("렌더", k, c, flush=True)


# ════════════════════════════ 시트 (보통 파이썬) ════════════════════════════
def 시트(c):
    from PIL import Image, ImageDraw, ImageFont
    f1 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 34); f2 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
    _, _, _, _, rw, rh = 컷[c]
    cw, chh = 400, int(400 * rh / rw); lab = 64
    def 배경(w, h):
        g = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(g)
        for y in range(h):
            t = y / h; v = int(212 - 40 * t); d.line([(0, y), (w, y)], fill=(v, v, v + 4))
        return g
    칸 = [("원화", "원화 (참고)", Image.open(원화).convert("RGBA")), ("FRA", "FRA 키트 완성 (참고)", Image.open(FRA).convert("RGBA"))]
    for k, (설명, _) in 변형.items():
        칸.append((k, 설명, Image.open(os.path.join(REN, "%s_%s.png" % (k, c))).convert("RGBA")))
    cols = 7; rows = math.ceil(len(칸) / cols)
    S = Image.new("RGB", (cols * cw, rows * (chh + lab)), (245, 245, 243))
    for i, (k, 설명, im) in enumerate(칸):
        x, y = (i % cols) * cw, (i // cols) * (chh + lab)
        cell = 배경(cw, chh) if k not in ("원화", "FRA") else Image.new("RGB", (cw, chh), (255, 255, 255))
        im.thumbnail((cw - 8, chh - 8), Image.LANCZOS)
        cell.paste(im, ((cw - im.width) // 2, (chh - im.height) // 2), im)
        S.paste(cell, (x, y))
        d = ImageDraw.Draw(S)
        d.text((x + 12, y + chh + 8), k if len(k) == 1 else "", font=f1, fill=(30, 30, 30))
        d.text((x + (52 if len(k) == 1 else 12), y + chh + 20), 설명, font=f2, fill=(50, 50, 50))
        d.rectangle([x, y, x + cw - 1, y + chh + lab - 1], outline=(200, 200, 200))
    이름 = {"영웅": "썸네일.png", "자세": "썸네일_자세.png", "정면": "썸네일_정면.png"}[c]
    S.save(os.path.join(OUT, 이름)); print("시트", os.path.join(OUT, 이름))


if __name__ == "__main__":
    try:
        import bpy  # noqa
        a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        blender_main(a)
    except ImportError:
        a = sys.argv[1:]
        if "--시트만" not in a:
            r = subprocess.run([BLENDER, "-b", "-P", os.path.abspath(__file__), "--"] + a)
            assert r.returncode == 0
        for c in (x for x in 컷 if not [y for y in a if y in 컷] or x in a):
            시트(c)
