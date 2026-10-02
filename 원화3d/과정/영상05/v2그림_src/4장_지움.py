# -*- coding: utf-8 -*-
"""4-1 · 4-2 · 4-3 · 4-4 · 4-7: 4장_선렌더.py 의 선 렌더에서 선을 지운다(중간 지움 vs 꼭짓점 지움) · 가림 판 창(4-1 · 4-7).
python 4장_지움.py   (먼저 blender -b -P 4장_선렌더.py)"""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
from scipy.ndimage import convolve, distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "_raw"); OUT = os.path.dirname(HERE)
W, H = 1920, 1080
FONT = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 34)
rng = np.random.default_rng(7)

def load(name):
    a = cv2.imdecode(np.fromfile(os.path.join(RAW, "선_%s.png" % name), np.uint8), cv2.IMREAD_UNCHANGED)
    L = (a[..., 3] > 100) & (a[..., :3].mean(2) < 128)
    ys, xs = np.nonzero(L); m = 12
    return L[ys.min() - m:ys.max() + m, xs.min() - m:xs.max() + m]

def vertices(L, merge=18):
    """꼭짓점 = 골격의 끝점 · 갈림점 + 모서리 검출. 가까운 것은 하나로."""
    sk = skeletonize(L); n = convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
    pts = [(y, x) for y, x in zip(*np.nonzero(sk & ((n == 1) | (n >= 3))))]
    g = cv2.goodFeaturesToTrack(cv2.GaussianBlur(L.astype(np.float32), (0, 0), 3), 80, 0.08, 20)
    if g is not None: pts += [(int(y), int(x)) for x, y in g[:, 0]]
    out = []
    for p in pts:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > merge ** 2 for q in out): out.append(p)
    return out

def dist_to(shape, pts):
    m = np.ones(shape, bool)
    for y, x in pts: m[y, x] = False
    return distance_transform_edt(m)

def del_vertex(L, V, p):
    """꼭짓점 둘레 반지름 r 안의 선을 지운다 — 지운 몫이 p 가 되게 r 을 찾는다."""
    d = dist_to(L.shape, V); tot = L.sum(); lo, hi = 0.0, 400.0
    for _ in range(30):
        r = (lo + hi) / 2
        if (L & (d < r)).sum() / tot < p: lo = r
        else: hi = r
    return L & ~(d < hi)

def mid_centers(L, V, margin=55):
    """꼭짓점에서 가장 먼 선 점부터 차례로(FPS) — 선 토막 한가운데."""
    dv = dist_to(L.shape, V); ys, xs = np.nonzero(L); dd = dv[ys, xs].copy(); C = []
    while True:
        i = int(dd.argmax())
        if dd[i] < margin: break
        C.append((ys[i], xs[i])); dd = np.minimum(dd, np.hypot(ys - ys[i], xs - xs[i]))
    return C, dv

def del_mid(L, V, p, step=75):
    """중간 지움: 꼭짓점과 고르게 놓인 점(간격 step) 둘레만 남긴다 → 틈은 늘 토막 가운데. 남는 몫이 1-p 가 되게 반지름을 찾는다."""
    C, _ = mid_centers(L, V, margin=step); dk = dist_to(L.shape, list(V) + C); tot = L.sum(); lo, hi = 0.0, 400.0
    for _ in range(30):
        r = (lo + hi) / 2
        if (L & (dk < r)).sum() / tot < 1 - p: lo = r
        else: hi = r
    return L & (dk < hi)

def to_img(L, box):
    """선 마스크를 box(w, h) 안에 맞춰 흰 바탕 검은 선 PIL 이미지로."""
    h, w = L.shape; s = min(box[0] / w, box[1] / h)
    a = cv2.resize(L.astype(np.float32), (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
    a = np.clip(a * 1.6, 0, 1)
    return Image.fromarray((255 - a * 255).astype(np.uint8))

def paste_c(cv, im, cx, cy): cv.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def text_c(dr, s, cx, cy, font=FONT, fill=(40, 40, 40)):
    b = dr.textbbox((0, 0), s, font=font); dr.text((cx - (b[2] - b[0]) / 2, cy - (b[3] - b[1]) / 2 - b[1]), s, font=font, fill=fill)
def save(cv, name): cv.save(os.path.join(OUT, name + ".png")); print("저장", name)

# ---------- 4-2: 물체 5 · 원래 / 중간 지움 / 꼭짓점 지움 ----------
cv = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(cv)
names = ["컵", "와인잔", "물뿌리개", "가위", "의자"]; rows = ["원래", "중간 지움", "꼭짓점 지움"]
x0, cw, y0, rh = 470, 290, 140, 300
for j, nm in enumerate(names):
    L = load(nm); V = vertices(L)
    for i, M in enumerate([L, del_mid(L, V, 0.55), del_vertex(L, V, 0.55)]):
        paste_c(cv, to_img(M, (240, 250)), x0 + cw * j, y0 + rh * i + 130)
for i, s in enumerate(rows): text_c(dr, s, 260, y0 + rh * i + 130)
dr.line([(370, y0 + rh - 10), (1760, y0 + rh - 10)], fill=(200, 200, 200), width=2)
save(cv, "4-2")

# ---------- 4-3: 컵 하나 · 25/45/65% · 중간 vs 꼭짓점 ----------
cv = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(cv)
L = load("컵"); V = vertices(L)
text_c(dr, "중간 지움", 900, 125); text_c(dr, "꼭짓점 지움", 1420, 125)
for i, p in enumerate([0.25, 0.45, 0.65]):
    cy = 330 + 270 * i; text_c(dr, "%d%%" % round(p * 100), 470, cy)
    paste_c(cv, to_img(del_mid(L, V, p), (330, 230)), 900, cy); paste_c(cv, to_img(del_vertex(L, V, p), (330, 230)), 1420, cy)
dr.line([(1160, 160), (1160, 1000)], fill=(60, 60, 60), width=3)
for y in (465, 735): dr.line([(400, y), (1680, y)], fill=(160, 160, 160), width=2)
save(cv, "4-3")

# ---------- 4-4: 물뿌리개 · 복원 불가(꼭짓점 지움) vs 복원 가능(남은 선 절반) ----------
cv = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(cv)
L = load("물뿌리개"); V = vertices(L)
A = del_vertex(L, V, 0.5); B = del_mid(L, V, 1 - 0.5 * A.sum() / L.sum())
print("4-4 남은 선 비 오른/왼 = %.2f" % (B.sum() / A.sum()))
for cx, M, s in ((620, A, "복원 불가"), (1300, B, "복원 가능")):
    dr.rectangle([cx - 290, 150, cx + 290, 880], outline=(0, 0, 0), width=5); paste_c(cv, to_img(M, (500, 640)), cx, 515); text_c(dr, s, cx, 940)
save(cv, "4-4")

# ---------- 4-1 · 4-7: 손전등 위에 검은 가림 판 · 창(흰 얼룩) 으로만 보인다 ----------
def blob(cx, cy, R, ang, elong):
    t = np.linspace(0, 2 * np.pi, 120, endpoint=False); r = np.ones_like(t)
    for k in (2, 3, 4, 5): r += rng.uniform(0.03, 0.12) * np.cos(k * t + rng.uniform(0, 6.3))
    x, y = R * elong * r * np.cos(t), R * r * np.sin(t); c, s = np.cos(ang), np.sin(ang)
    return np.stack([cx + c * x - s * y, cy + s * x + c * y], 1).astype(np.int32)

def occluded(at_vertex, name):
    L = load("손전등"); h, w = L.shape; s = min(1400 / w, 720 / h)
    L = cv2.resize(L.astype(np.uint8) * 255, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) > 60
    L = cv2.dilate(skeletonize(L).astype(np.uint8), np.ones((4, 4), np.uint8)) > 0   # 키운 뒤 선 굵기를 4 px 로
    V = vertices(L, merge=45); C, dv = mid_centers(L, V, margin=70)
    oy, ox = (H - L.shape[0]) // 2, (W - L.shape[1]) // 2
    win = np.zeros((H, W), np.uint8); DL = distance_transform_edt(~L)
    if at_vertex:   # 복원 가능: 창이 꼭짓점 · 이음부를 보여 준다 = 판은 선 중간을 가린다
        for y, x in V: cv2.fillPoly(win, [blob(x + ox, y + oy, rng.uniform(36, 48), rng.uniform(0, 3.1), rng.uniform(1.0, 1.5))], 1)
    else:           # 복원 불가: 창이 선 중간만 보여 준다 = 판은 꼭짓점을 가린다
        for y, x in C[:14]:
            R = max(14, min(60, dv[y, x] - 20))
            ang = rng.uniform(0, 3.1)
            cv2.fillPoly(win, [blob(x + ox, y + oy, R * 0.6, ang, 1.6)], 1)
    for _ in range(7):  # 아무 선도 없는 빈 창
        for _ in range(200):
            x, y = rng.uniform(250, 1670), rng.uniform(150, 930)
            yy, xx = int(y - oy), int(x - ox)
            far = not (0 <= yy < L.shape[0] and 0 <= xx < L.shape[1]) or DL[yy, xx] > 90
            if far: break
        cv2.fillPoly(win, [blob(x, y, rng.uniform(30, 48), rng.uniform(0, 3.1), rng.uniform(1.0, 1.7))], 1)
    img = np.full((H, W), 255, np.uint8); field = np.zeros((H, W), bool); field[100:980, 190:1730] = True
    Lfull = np.zeros((H, W), bool); Lfull[oy:oy + L.shape[0], ox:ox + L.shape[1]] = L
    img[field & (win == 0)] = 0; img[field & (win == 1) & Lfull] = 0
    cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, name + ".png")); print("저장", name)

occluded(False, "4-1"); occluded(True, "4-7")
