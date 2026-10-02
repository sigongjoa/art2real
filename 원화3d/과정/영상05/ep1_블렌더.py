# -*- coding: utf-8 -*-
"""영상05 1 편 — 블렌더 안에서 만드는 판 (10-02 사용자 「이건 영상이 아니라 프레젠테이션 · 블렌더를 쓰라고 했다」).
한 3D 무대(원화 판 · 실험 3D · 교재 판)를 카메라가 움직이며 잇는다. 나레이션 · 자막은 VSE(편집 장면)에 소리 · 글자 띠로, 키프레임은 그 길이에 맞춘다.
    blender -b -P ep1_블렌더.py -- [캐릭터 파일] [--render]
→ out/영상05/ep1/ep1_블렌더.blend (사람이 열어 고칠 수 있다) · --render 면 out/영상05/ep1/ep1_블렌더.mp4"""
import bpy, sys, os, math, hashlib, asyncio, subprocess, wave, mathutils
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RENDER = "--render" in argv; argv = [a for a in argv if a != "--render"]
CHAR = argv[0] if argv else r"G:\art2real\out\영상05\B1\head60k.blend"
R = r"G:\art2real"; OUT = os.path.join(R, r"out\영상05\ep1"); TTS = os.path.join(OUT, "_tts"); os.makedirs(TTS, exist_ok=True)
ART = os.path.join(R, r"트레일\trail7_part3d\in\omega_front_clean.png"); FONT = "C:/Windows/Fonts/malgunbd.ttf"
VOICE, FPS = "ko-KR-SunHiNeural", 30

def tts(text):
    """ep1_굽기.py 와 같은 캐시 이름 — 이미 만든 소리를 다시 쓴다."""
    h = hashlib.md5((VOICE + text).encode()).hexdigest()[:12]; mp3 = os.path.join(TTS, h + ".mp3"); wav = os.path.join(TTS, h + ".wav")
    if not os.path.exists(wav):
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE).save(mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", "24000", wav], check=True)
    with wave.open(wav) as w: return wav, w.getnframes() / w.getframerate()

# ---------- 장면 둘: 무대(3D) · 편집(VSE) ----------
bpy.ops.wm.read_homefile(use_empty=True)
st = bpy.context.scene; st.name = "무대"
st.render.engine = "BLENDER_EEVEE"; st.eevee.taa_render_samples = 16; st.view_settings.view_transform = "Standard"
st.render.resolution_x, st.render.resolution_y, st.render.fps = 1920, 1080, FPS
st.world = bpy.data.worlds.new("w"); st.world.use_nodes = True; st.world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.012, 0.018, 1)
def emis(name, color=None, img=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial"); e.inputs[1].default_value = strength
    if img:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img); nt.links.new(t.outputs[0], e.inputs[0])
        mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        nt.links.new(t.outputs[1], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
        m.blend_method = "BLEND"
    else:
        e.inputs[0].default_value = color; nt.links.new(e.outputs[0], o.inputs[0])
    return m
def gray(name, c=(0.75, 0.75, 0.78)):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.55; return m

# 원화 판: 세로로 세운 판, 정면 = -Y
img = bpy.data.images.load(ART); asp = img.size[0] / img.size[1]
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 5.95), rotation=(math.pi / 2, 0, 0)); art = bpy.context.object; art.name = "원화"
art.scale = (10 * asp, 10, 1); art.data.materials.append(emis("원화", img=ART))

# 머리 셋: 캐릭터를 불러 세 벌 · 깊이(Y)만 0.5 / 1 / 1.5
def load_char():
    if CHAR.lower().endswith(".blend"):
        with bpy.data.libraries.load(CHAR) as (src, dst): dst.objects = [n for n in src.objects]
        obs = [o for o in dst.objects if o and o.type == "MESH"]
    else:
        (bpy.ops.import_scene.gltf if CHAR.lower().endswith((".glb", ".gltf")) else bpy.ops.import_scene.fbx)(filepath=CHAR)
        obs = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    me = obs[0].data.copy(); o = bpy.data.objects.new("머리", me)
    vs = [v.co for v in me.vertices]; lo = mathutils.Vector([min(v[i] for v in vs) for i in range(3)]); hi = mathutils.Vector([max(v[i] for v in vs) for i in range(3)])
    me.transform(mathutils.Matrix.Translation(-(lo + hi) / 2)); me.transform(mathutils.Matrix.Scale(4.0 / max(hi - lo), 4))
    for p in me.polygons: p.use_smooth = True
    me.materials.clear(); me.materials.append(gray("머리")); return me
HX = 40; heads = []
me = load_char()
for i, lam in enumerate((0.5, 1.0, 1.5)):
    o = bpy.data.objects.new("머리_%.1f" % lam, me); st.collection.objects.link(o)
    o.location = (HX + (i - 1) * 6, 0, 3); o.scale = (1, lam, 1); heads.append(o)
    bpy.ops.object.text_add(location=(HX + (i - 1) * 6, 0, 6.3), rotation=(math.pi / 2, 0, 0)); t = bpy.context.object
    t.data.body = "깊이 ×%s" % ("0.5" if lam == 0.5 else "1" if lam == 1 else "1.5"); t.data.font = bpy.data.fonts.load(FONT); t.data.size = 0.7; t.data.align_x = "CENTER"
    t.data.materials.append(emis("글", (1.0, 0.75, 0.35, 1), strength=2)); t.name = "표_%d" % i
# 빛: 머리 무대에만 (원화 판은 스스로 빛남)
for loc, en in (((HX - 8, -10, 10), 2500), ((HX + 10, -6, 4), 800), ((HX, 8, 8), 1500)):
    L = bpy.data.lights.new("빛", "AREA"); L.energy = en; L.size = 6; lo_ = bpy.data.objects.new("빛", L); st.collection.objects.link(lo_); lo_.location = loc
    lo_.rotation_euler = (mathutils.Vector((HX, 0, 3)) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=44, location=(HX, 6, 0.9)); fl = bpy.context.object; fl.data.materials.append(gray("바닥", (0.05, 0.05, 0.07)))

cam = bpy.data.objects.new("카메라", bpy.data.cameras.new("카메라")); st.collection.objects.link(cam); st.camera = cam
target = bpy.data.objects.new("시선", None); st.collection.objects.link(target)
tc = cam.constraints.new("TRACK_TO"); tc.target = target; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

# ---------- 시간표: 나레이션 길이로 프레임을 정한다 ----------
beats = [
    ("전신", "이건 디지몬의 오메가몬이에요. 저는 이 그림 한 장으로 피규어를 만들어 보려고 했습니다.", 0),
    ("머리로", "이상한 건, 여러분도 저도, 이 그림을 보자마자 다 안다는 거예요. 투구가 둥글다는 것, 뿔이 앞으로 튀어나왔다는 것까지.", 0),
    ("머리", "눈으로는 다 아는데, 왜 만들 수가 없을까요.", 0),
    ("셋으로", "확인해 봤어요. 같은 머리를 셋 만들었습니다. 하나는 앞뒤로 절반 납작하게, 하나는 그대로, 하나는 1.5배 길게.", 0),
    ("정면", "정면에서 보면, 똑같습니다.", 0),
    ("돌기", "", 4.0),
    ("옆", "그런데 돌려 보면, 전혀 다른 머리 셋입니다. 정면 그림 한 장에는, 이 셋을 가를 정보가 처음부터 없었던 거예요.", 0),
]
LEAD, PAD = 0.3, 0.7; f = 1; plan = []
for name, say, mins in beats:
    wav, d = tts(say) if say else (None, 0)
    dur = max(mins, LEAD + d + PAD); n = int(round(dur * FPS)); plan.append((name, say, wav, f, n)); f += n
st.frame_start, st.frame_end = 1, f - 1

def key(frame, loc, look, lens):
    cam.location = loc; cam.keyframe_insert("location", frame=frame); target.location = look; target.keyframe_insert("location", frame=frame)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=frame)
P = {n: (s, s + k) for n, _, _, s, k in plan}
ART_C = (0, 0, 5.95); HEAD_ART = (0, 0, 10.05)           # 원화 판(바닥 0.95 · 높이 10) 위 머리 자리: 1024 판 y≈110 → 10.95 − 1.07 ≈ 9.9
key(P["전신"][0], (0, -32, 6), ART_C, 50); key(P["전신"][1], (0, -28, 6.2), ART_C, 50)
key(P["머리로"][1], (0, -8.0, 10.05), HEAD_ART, 50); key(P["머리"][1], (0, -7.4, 10.05), HEAD_ART, 50)
HC = (HX, 0, 3.2)
key(P["셋으로"][0] + 25, (4, -30, 6.5), (6, 0, 5), 50); key(P["셋으로"][0] + 75, (HX - 6, -40, 6), HC, 85); key(P["셋으로"][1], (HX, -60, 3.4), HC, 135)     # 원화에서 무대로 흘러가며 망원으로 → 평평한 정면
key(P["옆"][1], (HX, -62, 3.4), HC, 135)
for o in heads:                                          # 턴테이블: 정면 → 옆 90°
    o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", frame=P["돌기"][0])
    o.rotation_euler = (0, 0, math.radians(90)); o.keyframe_insert("rotation_euler", frame=P["돌기"][1])
for ob in [cam, target] + heads:
    for fc in (ob.animation_data.action.fcurves if ob.animation_data else []):
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"

# ---------- 편집 장면: 무대 띠 + 소리 띠 + 자막 띠 ----------
ed = bpy.data.scenes.new("편집"); ed.render.resolution_x, ed.render.resolution_y, ed.render.fps = 1920, 1080, FPS
ed.frame_start, ed.frame_end = st.frame_start, st.frame_end; se = ed.sequence_editor_create()
s = se.sequences.new_scene("무대", st, channel=1, frame_start=1); s.scene_input = "CAMERA"
fnt = bpy.data.fonts.load(FONT)
for name, say, wav, f0, n in plan:
    if not say: continue
    se.sequences.new_sound(name, wav, channel=2, frame_start=f0 + int(LEAD * FPS))
    tx = se.sequences.new_effect(name + "_자막", "TEXT", channel=3, frame_start=f0, frame_end=f0 + n)
    tx.text = say; tx.font = fnt; tx.font_size = 46; tx.wrap_width = 0.8; tx.location = (0.5, 0.08); tx.align_x = "CENTER"; tx.align_y = "BOTTOM"
    tx.use_box = True; tx.box_color = (0.03, 0.03, 0.05, 0.85); tx.box_margin = 0.012
ed.render.image_settings.file_format = "FFMPEG"; ed.render.ffmpeg.format = "MPEG4"; ed.render.ffmpeg.codec = "H264"
ed.render.ffmpeg.audio_codec = "AAC"; ed.render.ffmpeg.audio_bitrate = 160; ed.render.ffmpeg.constant_rate_factor = "HIGH"
ed.render.filepath = os.path.join(OUT, "ep1_블렌더.mp4")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "ep1_블렌더.blend"))
print("길이 %.1f 초 · 프레임 %d" % ((f - 1) / FPS, f - 1))
if RENDER:
    bpy.ops.render.render(animation=True, scene="편집")
    print("끝", ed.render.filepath)
