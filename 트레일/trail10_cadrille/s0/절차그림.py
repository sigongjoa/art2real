# -*- coding: utf-8 -*-
"""학습 절차를 실제 예시 하나로 그림 (2026-10-05 사용자 「학습 절차를 시각적으로 보여줘」)
정답 레시피(CadQuery) → 실행(3D) → 문제 만들기(회색 4 장 · 애니풍 · 뭉갠 점) → cadrille 지금 답 → 정답과 비교 → LoRA 조금 고침 → 반복
python s0/절차그림.py → s0/절차/학습절차.png"""
import os, sys, textwrap, numpy as np, torch, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
import s0 as S
from render import render
O = os.path.join(H, "절차"); os.makedirs(O, exist_ok=True)
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); M = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)

# 1 정답 레시피 — 메카 차양 비슷한 V 판 + 윗모서리 모따기 + 가운데 홈
정답 = """import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().segment((-90,10),(-10,-40)).segment((10,-40)).segment((90,10)).segment((70,30)).segment((0,-10)).segment((-70,30)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(8,200,10).translate((0,0,24)))"""
gt = S.run_code(정답); gt.export(os.path.join(O, "정답.stl"))
u = S.unit(gt)
# 2 회색 4 장(cadrille 학습 그림)
it, grid = S.item_img(u); grid.save(os.path.join(O, "회색4장.png"))
# 3 애니풍(셀 2 단 + 먹선) — 우리가 덧배울 그림
def 애니(m, front):
    g = np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), front, img_size=256)).astype(float)
    lum = g.mean(2); fg = lum < 250
    out = np.full_like(g, 255.0); base = np.array([232, 236, 248.0]); dark = np.array([150, 160, 190.0])
    out[fg & (lum >= np.percentile(lum[fg], 45))] = base; out[fg & (lum < np.percentile(lum[fg], 45))] = dark
    e = cv2.Canny(lum.astype(np.uint8), 20, 60); e = cv2.dilate(e, np.ones((2, 2), np.uint8)); out[e > 0] = [20, 20, 30]
    return Image.fromarray(out.astype(np.uint8))
애 = [ImageOps.expand(애니(u, f), border=3, fill="black") for f in [[1, 1, 1], [-1, 1, -1]]]
# 4 뭉갠 점 — 정답을 복셀로 뭉갠 뒤 256 점
v = u.voxelized(1 / 24).fill().marching_cubes; v.apply_scale(1 / 24); v.apply_translation(u.bounds[0] - v.bounds[0] + (u.extents - v.extents) / 2)
pts = S.fps(trimesh.sample.sample_surface(v, 4096)[0], 256)
def 점그림(p):
    im = Image.new("RGB", (256, 256), "white"); d = ImageDraw.Draw(im); q = (p - p.mean(0)); q = q / np.abs(q).max() * 105
    for x, y, z in q: d.ellipse((128 + x - 0.6 * y - 3, 140 - z - 0.3 * y - 3, 128 + x - 0.6 * y + 3, 140 - z - 0.3 * y + 3), fill=(40, 90, 200))
    return im
점 = 점그림(pts)
# 5 cadrille 지금 답(학습 전) — 실제로 돌림
from transformers import AutoProcessor
from cadrille import Cadrille, collate
W = os.path.join(os.path.dirname(H), "weights")
model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
it["file_name"] = "x"; b = collate([it], processor=proc, n_points=256, eval=True)
with torch.no_grad():
    out = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                         pixel_values_videos=b["pixel_values_videos"].cuda(), video_grid_thw=b["video_grid_thw"].cuda(), max_new_tokens=768)
답 = proc.batch_decode([out[0][len(b["input_ids"][0]):]], skip_special_tokens=True)[0]; open(os.path.join(O, "지금답.py"), "w").write(답)
try:
    pm = S.run_code(답); pm.apply_scale(1 / 200.0); pm.apply_translation([0.5] * 3); 답그림 = render(np.asarray(pm.vertices), np.asarray(pm.faces), [0.35, -0.5, -1], img_size=256)
except Exception as e:
    답그림 = Image.new("RGB", (256, 256), "white"); ImageDraw.Draw(답그림).text((20, 120), "실행 실패", font=F(28), fill="red")
정답그림 = render(np.asarray(u.vertices), np.asarray(u.faces), [0.35, -0.5, -1], img_size=256)

# ── 한 장으로
Wd, Hd = 2200, 1500; c = Image.new("RGB", (Wd, Hd), (250, 250, 252)); d = ImageDraw.Draw(c)
def 상자(x, y, w, h, 제목, col):
    d.rounded_rectangle((x, y, x + w, y + h), 22, outline=col, width=5, fill="white"); d.text((x + 18, y + 10), 제목, font=F(34), fill=col)
def 화살(x0, y0, x1, y1, t=""):
    d.line((x0, y0, x1, y1), fill=(90, 90, 100), width=6); a = np.arctan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - 22 * np.cos(a - 0.45), y1 - 22 * np.sin(a - 0.45)), (x1 - 22 * np.cos(a + 0.45), y1 - 22 * np.sin(a + 0.45))], fill=(90, 90, 100))
    if t: d.text(((x0 + x1) / 2 - 60, (y0 + y1) / 2 - 44), t, font=F(26), fill=(90, 90, 100))
def 코드(x, y, s, w=46, n=9, col=(30, 30, 30)):
    ls = []
    for l in s.split("\n"): ls += textwrap.wrap(l, w) or [""]
    for i, l in enumerate(ls[:n]): d.text((x, y + i * 26), l, font=M(21), fill=col)
d.text((40, 20), "학습 절차 — 「레시피(CAD) 먼저 → 요리(3D) → 사진(그림) → 사진 보고 레시피 맞히기」", font=F(44), fill=(20, 40, 90))
B1 = (31, 78, 140); B2 = (190, 120, 20); B3 = (30, 140, 70); B4 = (190, 50, 60)
# 줄 1: 데이터 만들기
d.text((40, 90), "① 데이터 한 쌍 만들기 (컴퓨터가 자동으로 수천 번)", font=F(36), fill=B1)
상자(40, 140, 620, 330, "1 정답 레시피 (CadQuery)", B1); 코드(60, 200, 정답, w=44, n=9)
화살(670, 300, 760, 300, "실행")
상자(770, 140, 330, 330, "2 3D 부품", B1); c.paste(정답그림.resize((270, 270)), (800, 190))
화살(1110, 300, 1200, 300, "렌더")
상자(1210, 140, 950, 330, "3 문제 = 그림 + 뭉갠 점", B2)
c.paste(grid.resize((220, 220)), (1240, 195)); d.text((1240, 425), "회색 4 장(원래 배운 것)", font=F(22), fill=B2)
c.paste(애[0].resize((200, 200)), (1510, 225)); c.paste(애[1].resize((200, 200)), (1720, 225)); d.text((1560, 430), "애니풍(덧배울 것)", font=F(22), fill=B2)
c.paste(점.resize((200, 200)), (1935, 225)); d.text((1950, 430), "뭉갠 점 256", font=F(22), fill=B2)
# 줄 2: 학습 한 번
d.text((40, 530), "② 학습 한 번 (한 쌍마다)", font=F(36), fill=B4)
화살(1680, 480, 1680, 590)
상자(1210, 590, 950, 380, "4 cadrille 가 레시피를 씀 (지금, 학습 전)", B4)
c.paste(답그림.resize((260, 260)), (1240, 650)); 코드(1520, 650, 답, w=40, n=11, col=(150, 30, 40))
화살(1200, 780, 1110, 780, "")
상자(40, 590, 1060, 380, "5 정답 레시피와 글자 단위로 비교", B4)
d.text((70, 645), "정답", font=F(26), fill=B3); d.text((150, 648), ".extrude(24).edges('>Z').chamfer(6).cut(...)  ← 홈", font=M(24), fill=B3)
d.text((70, 695), "지금", font=F(26), fill=B4); d.text((150, 698), ".extrude(21).union(…).extrude(26)", font=M(24), fill=B4); d.text((70, 740), "→ V 판 모양은 거의 맞췄지만 모따기 · 홈이 빠짐", font=F(26), fill=B4)
d.text((70, 790), "틀린 글자마다 「얼마나 틀렸나」(손실)를 계산 →", font=F(28), fill=(40, 40, 40))
d.text((70, 832), "6 LoRA(옆에 붙인 작은 조정판)만 아주 조금 고침", font=F(32), fill=B4)
d.text((70, 880), "   원래 실력(기계 부품 100 만 개)은 그대로 둠", font=F(26), fill=(90, 90, 100))
# 줄 3: 반복 · 쓸 때
d.text((40, 1010), "③ 반복 → ④ 쓸 때", font=F(36), fill=B3)
상자(40, 1060, 1060, 380, "7 반복", B3)
for i, t in enumerate(["1~6 을 합성 부품 수천 쌍으로 몇천 번", "가끔 「얼린 시험 부품」으로 채점:", "   레시피 실행 → 정답 3D 와 모양이 겹치나(IoU)", "   + 실제 오메가몬 원화 부품은 눈으로 판정", "점수가 안 오르면 멈추고 데이터(생성기)를 고침"]):
    d.text((70, 1120 + i * 56), t, font=F(28), fill=(40, 40, 40))
상자(1210, 1060, 950, 380, "8 쓸 때 (오메가몬)", B3)
for i, t in enumerate(["TripoSG 머리 → 부품으로 나눔", "부품마다: 원화 크롭 + TripoSG 점 → LoRA 붙인 cadrille", "→ 레시피 → 실행 → 부품 솔리드", "→ 머리로 합침 → 후보 몇 개 중 사람이 고름", "고른 기록은 다음 학습 자료가 됨"]):
    d.text((1240, 1120 + i * 56), t, font=F(28), fill=(40, 40, 40))
화살(1110, 1250, 1200, 1250, "")
c.save(os.path.join(O, "학습절차.png")); print("ok", 답[:80])
