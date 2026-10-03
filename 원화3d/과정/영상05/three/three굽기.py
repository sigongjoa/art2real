"""Three.js 장난감 장면 → 프레임 PNG → 기존 굽기(소리 · 자막)로 mp4.
    python three굽기.py <편> <장면.html> [still]
still: 컷마다 3/4 지점 한 장 → out/.../three_스틸.jpg (내가 먼저 본다). 아니면 전 프레임을 frames/ 에 그리고
`장난감굽기.py <편> 자막만` 을 불러 <편>.mp4 를 만든다(블렌더 판은 <편>_블렌더.mp4 로 비켜 둔다)."""
import sys, os, json, glob, base64, shutil, subprocess, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

NAME, HTML = sys.argv[1], os.path.abspath(sys.argv[2]); STILL = "still" in sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__)); D = "G:/art2real/out/영상05/장난감/" + NAME; FR = D + "/frames"
T = json.load(open(D + "/시간표.json", encoding="utf-8"))
if STILL:
    s, fs = 1, []
    for c in T["cuts"]: fs.append(s + c["n"] * 3 // 4); s += c["n"]
else:
    fs = list(range(1, sum(c["n"] for c in T["cuts"]) + 1))
    os.makedirs(FR, exist_ok=True)
    for p in glob.glob(FR + "/*.png"): os.remove(p)

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-angle=d3d11", "--enable-gpu"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.on("console", lambda m: m.type == "error" and print("console:", m.text))
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.add_init_script("window.__T = %s;" % json.dumps(T))
    pg.goto(pathlib.Path(HTML).as_uri()); pg.wait_for_function("window.ready === true", timeout=60000)
    ims = []
    for f in fs:
        url = pg.evaluate("f => { draw(f); return document.querySelector('canvas').toDataURL('image/png'); }", f)
        png = base64.b64decode(url.split(",", 1)[1])
        if STILL: p = D + "/_three_still_%04d.png" % f; open(p, "wb").write(png); ims.append(p)
        else: open(FR + "/%04d.png" % f, "wb").write(png)
        if f % 100 == 0: print(f, "/", fs[-1], flush=True)
    b.close()

if STILL:
    th = [Image.open(p).convert("RGB").resize((270, 480)) for p in ims]
    o = Image.new("RGB", (270 * min(8, len(th)), 480 * ((len(th) + 7) // 8)), "white")
    for i, im in enumerate(th): o.paste(im, (270 * (i % 8), 480 * (i // 8)))
    o.save(D + "/three_스틸.jpg"); [os.remove(p) for p in ims]; print(D + "/three_스틸.jpg", len(th), "컷"); sys.exit()

mp4 = D + "/%s.mp4" % NAME
if os.path.exists(mp4) and not os.path.exists(D + "/%s_블렌더.mp4" % NAME): shutil.copy(mp4, D + "/%s_블렌더.mp4" % NAME)
subprocess.run([sys.executable, os.path.join(HERE, "..", "장난감굽기.py"), NAME, "자막만"], check=True)
