# -*- coding: utf-8 -*-
"""조립 과정 HTML — 부품이 하나씩 붙는 순서를 그림으로 (2026-09-28).

    python 조립.py            -> 지식/조립/오메가몬.html (그림을 속에 넣은 한 파일) + 오메가몬.json (부품 목록)
    python 조립.py --점검      -> 지금 부품(out/오메가몬2/<부위>/단계4)과 json 이 같은지만 본다(다르면 종료 1)
부품 · 색은 부위 스크립트가 낸 out/오메가몬2/<부위>/단계4/*.stl + 색.json 에서. **부품이 바뀌면 다시 돌린다**(작업흐름 ⑧).
조립 순서(가정): 프레임 → 검은 속 → 큰 갑주부터 작은 것으로. 끼움 구조(핀 · 홈)는 아직 없다 — 모양 단계의 순서.
"""
import os, sys, json, base64, subprocess, datetime, html
import numpy as np, trimesh
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
OUT = os.path.join(원화3d, "out", "오메가몬2"); 조립D = os.path.join(R, "조립"); os.makedirs(조립D, exist_ok=True)
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
부위들 = [("몸통", False, ()), ("머리", False, ()), ("어깨", False, ()), ("방패", False, ()), ("허벅지", True, ()), ("정강이", True, ("허벅지끝",)), ("발", True, ())]
설명 = {"몸통": "척추 프레임에 검은 허리 · 목을 끼우고 가슴 · 골반을 씌운 뒤 줄무늬 · 문장 · 테를 얹는다", "머리": "속머리 위에 투구 · 마스크 미늘 · 차양 · 볼 판, 마지막에 뿔과 안테나",
        "어깨": "그림 오른쪽 어깨: 위팔 → 어깨 갑주 → 띠 · 고리 → 가시 넷", "방패": "그림 왼쪽 어깨: 위팔 → 어깨 → 방패 테 → 금색 면",
        "허벅지": "허벅지 → 검은 무릎 속 → 무릎 덮개와 테 (좌우 같음)", "정강이": "검은 발목 → 정강이 → 발목 단 · 덧단 → V 테 → 복사뼈 덮개 (좌우 같음)", "발": "발등 → 발톱 뿌리 덮개 → 금색 발톱 셋 (좌우 같음)"}

def 부품목록(이름, 뺌):
    D = os.path.join(OUT, 이름, "단계4"); 색 = json.load(open(os.path.join(D, "색.json"), encoding="utf-8")); L = []
    for n, c in 색.items():
        if n in 뺌: continue
        t = trimesh.load(os.path.join(D, n + ".stl")); e = t.extents
        L.append(dict(이름=n, 색=[round(v, 3) for v in c], 크기=[round(float(v), 1) for v in e], 부피=round(float(abs(t.volume)), 1), 파일=os.path.join(D, n + ".stl")))
    검 = lambda p: max(p["색"]) < 0.2
    L.sort(key=lambda p: (p["이름"] != "프레임", not 검(p), -p["부피"]))      # 프레임 → 검은 속 → 큰 것부터
    return L
def 목록():
    return {이름: dict(거울=거울, 부품=부품목록(이름, 뺌)) for 이름, 거울, 뺌 in 부위들 if os.path.exists(os.path.join(OUT, 이름, "단계4", "색.json"))}
def 요약(M_): return {k: [p["이름"] for p in v["부품"]] for k, v in M_.items()}

블 = r'''
import bpy, sys, json, math
from mathutils import Vector
a = json.loads(open(sys.argv[-1], encoding="utf-8").read())
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.80, 0.80, 0.82, 1)
for loc, e in (((-300, -500, 600), 2.2), ((500, -300, 150), 0.8)):
    d = bpy.data.lights.new("s", "SUN"); d.energy = e; o = bpy.data.objects.new("s", d); sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 20000
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x, sc.render.resolution_y = a["해상"]; sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 82
sc.render.use_freestyle = True; sc.render.line_thickness = 1.0
fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(140)
for l in list(fs.linesets): fs.linesets.remove(l)
l = fs.linesets.new("l"); l.linestyle = bpy.data.linestyles.new("ls"); l.select_silhouette = True; l.select_border = True
def 재(c):
    m = bpy.data.materials.new("m"); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.5; return m
for 묶 in a["묶음"]:
    for o in list(bpy.data.objects):
        if o.type == "MESH": bpy.data.objects.remove(o, do_unlink=True)
    obs = []
    for p in 묶["부품"]:
        parts = []
        for f, 거울 in p["파일"]:
            bpy.ops.import_mesh.stl(filepath=f); o = bpy.context.selected_objects[0]
            if 거울: o.scale = (-1, 1, 1)
            parts.append(o)
        참 = 재(p["색"]); 흐 = 재([0.55 + 0.45 * (0.3 * v + 0.62) * 0 + 0.0 for v in p["색"]]) ; 흐 = 재([0.72 * 0.6 + 0.4 * v for v in p["색"]])
        obs.append((parts, 참, 흐))
    t = Vector(묶["중심"]); az, el = math.radians(묶["방위"]), math.radians(묶["올림"]); r = 3000
    cam.location = t + Vector((r * math.sin(az) * math.cos(el), -r * math.cos(az) * math.cos(el), r * math.sin(el))); cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = 묶["폭"]
    for i in range(len(obs)):
        for j, (parts, 참, 흐) in enumerate(obs):
            for o in parts:
                o.hide_render = j > i; o.data.materials.clear(); o.data.materials.append(참 if (j == i or 묶.get("모두참")) else 흐)
        sc.render.filepath = 묶["out"] + "/%03d.jpg" % i; bpy.ops.render.render(write_still=True)
'''

def 그리기(M_):
    T = os.path.join(OUT, "_조립"); os.makedirs(T, exist_ok=True); 묶음 = []
    def 상자(ps, 거울):
        b = np.array([trimesh.load(p["파일"]).bounds for p in ps]); lo, hi = b[:, 0].min(0), b[:, 1].max(0)
        if 거울: lo[0], hi[0] = min(lo[0], -hi[0]), max(hi[0], -lo[0])
        return lo, hi
    for 이름, v in M_.items():
        lo, hi = 상자(v["부품"], False); d = os.path.join(T, 이름); os.makedirs(d, exist_ok=True)
        묶음.append(dict(부품=[dict(파일=[(p["파일"], False)], 색=p["색"]) for p in v["부품"]], 중심=list(map(float, (lo + hi) / 2)), 폭=float(max(hi - lo) * 1.35), 방위=-32, 올림=12, out=d.replace("\\", "/")))
    # 전신: 부위를 하나씩(다리는 좌우 같이) — 부위 안의 부품은 색별로 묶지 않고 그대로
    전 = []; alo, ahi = [], []
    for 이름, v in M_.items():
        lo, hi = 상자(v["부품"], v["거울"]); alo.append(lo); ahi.append(hi)
        for p in v["부품"]:
            전.append((이름, dict(파일=[(p["파일"], False)] + ([(p["파일"], True)] if v["거울"] else []), 색=p["색"])))
    lo, hi = np.min(alo, 0), np.max(ahi, 0); d = os.path.join(T, "전신"); os.makedirs(d, exist_ok=True)
    # 전신은 부위 단위로 단계를 세야 하므로 부위마다 부품을 한 「부품」으로 합친다(파일 여럿 · 색은 부품마다 달라 묶음을 부위 수만큼 따로 그림)
    json.dump(dict(묶음=묶음, 해상=(440, 550)), open(os.path.join(T, "판.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(T, "블.py"), "w", encoding="utf-8").write(블)
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(T, "블.py"), "--", os.path.join(T, "판.json")], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    # 전신 단계: 부위 k 까지의 모든 부품을 참색으로
    묶2 = []
    for k, 이름 in enumerate(M_):
        ps = [p for n, p in 전 if list(M_).index(n) <= k]; dd = os.path.join(d, "%d" % k); os.makedirs(dd, exist_ok=True)
        묶2.append(dict(부품=[dict(파일=sum([p["파일"] for p in ps], []), 색=[0.8, 0.8, 0.82])], 중심=list(map(float, (lo + hi) / 2)), 폭=float(max(hi - lo) * 1.12), 방위=-25, 올림=8, out=dd.replace("\\", "/"), 모두참=True))
    # 색을 살리려면 부품마다 따로 넣고 마지막 장만 쓴다
    for k, 이름 in enumerate(M_):
        ps = [p for n, p in 전 if list(M_).index(n) <= k]; 묶2[k]["부품"] = ps
    json.dump(dict(묶음=묶2, 해상=(560, 700)), open(os.path.join(T, "판2.json"), "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(T, "블.py"), "--", os.path.join(T, "판2.json")], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    return T

def b64(f): return "data:image/jpeg;base64," + base64.b64encode(open(f, "rb").read()).decode()
def 색hex(c): return "#%02x%02x%02x" % tuple(int(round(min(1, v) * 255)) for v in c)

CSS = """
:root{--bg:#f6f6f4;--fg:#1c1c1f;--mut:#6a6a72;--card:#fff;--line:#dcdce0;--acc:#b8461f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ececf0;--mut:#a0a0aa;--card:#222227;--line:#38383f;--acc:#ff9466}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ececf0;--mut:#a0a0aa;--card:#222227;--line:#38383f;--acc:#ff9466}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 "Malgun Gothic","Apple SD Gothic Neo",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:1.7rem;margin:.2em 0}h2{font-size:1.3rem;margin:2.2em 0 .3em;border-top:1px solid var(--line);padding-top:1.2em}
.mut{color:var(--mut);font-size:.92rem}nav{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}nav a{padding:4px 12px;border:1px solid var(--line);border-radius:999px;color:var(--fg);text-decoration:none;background:var(--card)}
.stage{display:grid;grid-template-columns:minmax(0,440px) minmax(0,1fr);gap:20px;align-items:start}@media(max-width:760px){.stage{grid-template-columns:1fr}}
.view{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px;position:sticky;top:8px}.view img{width:100%;height:auto;border-radius:8px;display:block}
.ctl{display:flex;gap:8px;align-items:center;margin-top:8px}.ctl button{font:inherit;padding:6px 14px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}.ctl .n{margin-left:auto;color:var(--mut)}
ol{list-style:none;margin:0;padding:0}ol li{display:flex;gap:10px;align-items:center;padding:7px 10px;border:1px solid transparent;border-radius:8px;cursor:pointer}
ol li.on{border-color:var(--acc);background:var(--card)}ol li .k{width:1.8em;color:var(--mut);text-align:right}ol li .sw{width:16px;height:16px;border-radius:4px;border:1px solid var(--line);flex:none}
ol li .sz{margin-left:auto;color:var(--mut);font-size:.88rem;white-space:nowrap}.warn{color:var(--acc)}
.whole{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}.whole figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:6px}.whole img{width:100%;border-radius:6px;display:block}.whole figcaption{font-size:.88rem;text-align:center;padding-top:4px}
"""
JS = """
document.querySelectorAll('.stage').forEach(s=>{const im=s.querySelector('img'),li=[...s.querySelectorAll('li')],n=s.querySelector('.n');let i=li.length-1;
function go(k){i=Math.max(0,Math.min(li.length-1,k));im.src=li[i].dataset.src;li.forEach((e,j)=>e.classList.toggle('on',j===i));n.textContent=(i+1)+' / '+li.length}
li.forEach((e,j)=>e.onclick=()=>go(j));s.querySelector('.p').onclick=()=>go(i-1);s.querySelector('.x').onclick=()=>go(i+1);s.querySelector('.a').onclick=()=>{let k=0;go(0);const t=setInterval(()=>{k++;go(k);if(k>=li.length-1)clearInterval(t)},700)};go(0)});
"""
def 쓰기(M_, T):
    H = ['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>오메가몬 PG 조립 과정</title><style>%s</style></head><body><main>' % CSS]
    총 = sum(len(v["부품"]) * (2 if v["거울"] else 1) for v in M_.values())
    H.append('<h1>오메가몬 PG — 조립 과정</h1><p class="mut">만든 날 %s · 부위 %d · 부품 %d (다리는 좌우 합) · 모양 단계 — 끼움 구조(핀 · 홈) · 속 비움은 아직 없음 · 순서는 「프레임 → 검은 속 → 큰 갑주 → 작은 것」 가정 · 아래팔(짐승 머리) · 망토 없음</p>' % (datetime.date.today(), len(M_), 총))
    H.append('<nav><a href="#전신">전신</a>' + "".join('<a href="#%s">%s</a>' % (k, k) for k in M_) + "</nav>")
    H.append('<h2 id="전신">전신 — 부위를 하나씩</h2><div class="whole">')
    for k, 이름 in enumerate(M_):
        n = sum(len(M_[x]["부품"]) for x in list(M_)[:k + 1]); H.append('<figure><img alt="%s 까지 붙인 전신" src="%s"><figcaption>%d. %s</figcaption></figure>' % (이름, b64(os.path.join(T, "전신", str(k), "%03d.jpg" % (n - 1))), k + 1, 이름))
    H.append("</div>")
    for 이름, v in M_.items():
        ps = v["부품"]; H.append('<h2 id="%s">%s <span class="mut">부품 %d%s</span></h2><p class="mut">%s</p>' % (이름, 이름, len(ps), " × 좌우" if v["거울"] else "", html.escape(설명.get(이름, ""))))
        H.append('<div class="stage"><div class="view"><img alt="%s 조립 단계"><div class="ctl"><button class="p">이전</button><button class="x">다음</button><button class="a">처음부터</button><span class="n"></span></div></div><ol>' % 이름)
        for i, p in enumerate(ps):
            작 = max(p["크기"]) < 8; 얇 = min(p["크기"]) < 1.2
            H.append('<li data-src="%s"><span class="k">%d</span><span class="sw" style="background:%s"></span><span>%s%s</span><span class="sz">%s mm</span></li>'
                     % (b64(os.path.join(T, 이름, "%03d.jpg" % i)), i + 1, 색hex(p["색"]), html.escape(p["이름"]), ' <span class="warn">(작음)</span>' if 작 else (' <span class="warn">(얇음)</span>' if 얇 else ""), " × ".join("%g" % s for s in p["크기"])))
        H.append("</ol></div>")
    H.append("<script>%s</script></main></body></html>" % JS)
    f = os.path.join(조립D, "오메가몬.html"); open(f, "w", encoding="utf-8").write("\n".join(H))
    json.dump(dict(만든날=str(datetime.date.today()), 부품=요약(M_)), open(os.path.join(조립D, "오메가몬.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("html", f, "%.1f MB" % (os.path.getsize(f) / 1e6), "· 부품", 총); return f

if __name__ == "__main__":
    if "--점검" in sys.argv:
        f = os.path.join(조립D, "오메가몬.json")
        if not os.path.isdir(OUT): print("out 없음 — 건너뜀"); sys.exit(0)
        같 = os.path.exists(f) and json.load(open(f, encoding="utf-8"))["부품"] == 요약(목록()); print("조립 html 과 부품이 " + ("같음" if 같 else "다름 — python 조립.py 다시")); sys.exit(0 if 같 else 1)
    M_ = 목록(); 쓰기(M_, 그리기(M_))
