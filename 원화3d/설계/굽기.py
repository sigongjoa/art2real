"""키트설계.src.html 에 원화 두 장(정면 · 옆)을 박아 한 파일로 — out/키트설계_오메가몬.html
원화는 저장소 밖(트레일/…/in)이라 결과 html 은 커밋하지 않는다."""
import base64, io, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hull as H  # noqa

def 박기(path):
    im = Image.open(path).convert("RGBA"); bg = Image.new("RGBA", im.size, "white"); bg.alpha_composite(im)
    b = io.BytesIO(); bg.convert("RGB").save(b, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()

c = "오메가몬"; src, base = H.CASES[c]["src"], H.art_dir(c)
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "키트설계.src.html"), encoding="utf-8").read()
t = t.replace("__FRONT__", 박기(os.path.join(base, src["front"]))).replace("__SIDE__", 박기(os.path.join(base, src["side"])))
out = os.path.join(H.OUT, "키트설계_%s.html" % c); open(out, "w", encoding="utf-8").write(t)
print(out, "%.0f KB" % (os.path.getsize(out) / 1024))
