# -*- coding: utf-8 -*-
"""쇼츠 49 재료 — 메카2 삼면.png(자체 디자인) 머리 · 발 → 앞 판 · 옆 판 · 겹침 · 교차 돌림 프레임 · 10-13
python 자료49.py → out/영상05/대화/49_진짜그림/자료/"""
import os, sys, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import 도구 as T, 그림짓기 as G
from 윤곽 import 메시로
from render import render
IMG = "G:/art2real/원화3d/out/도안생성/메카2/삼면.png"; O = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; os.makedirs(O, exist_ok=True)
부위 = {"머리": (20, 160, 200, 350, 670, 800), "발": (815, 975, 60, 250, 610, 850)}
색 = {"앞": (0.35, 0.55, 0.95), "옆": (0.95, 0.6, 0.25), "교차": (0.55, 0.8, 0.5)}
N = 36

def 정사각(a, s=420):   # 그림 조각 → 흰 정사각
    im = Image.fromarray(a); k = s / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    c = Image.new("RGB", (s, s), "white"); c.paste(im, ((s - im.width) // 2, (s - im.height) // 2)); return c
def 돌림(메시들, 이름, 고정=None, 중=0, 크=2.2):   # [(trimesh, 색)] → N 장 · [-1,1] 상자 기준 같은 크기 · Z 위
    V, F, C, o = [], [], [], 0
    for m, c in 메시들:   # 메시로 = [-1, 1]
        v = (np.asarray(m.vertices) - 중) / 크 * 0.75; V.append(v[:, [0, 2, 1]] * [1, 1, -1] + .5); F.append(np.asarray(m.faces) + o); C.append(np.tile(c, (len(m.faces), 1))); o += len(v)
    V, F, C = np.concatenate(V), np.concatenate(F), np.concatenate(C)
    for k in range(N if 고정 is None else 1):
        t = 2 * np.pi * k / N + .6 if 고정 is None else 고정
        Image.fromarray(np.asarray(render(V, F, [np.cos(t), -.45, np.sin(t)], dist=-1.05, img_size=420, cols=C))).save(O + "%s_%02d.png" % (이름, k))

for 이름, b in 부위.items():
    fa, fb, S, X = G.넣기(IMG, *b, i=-1)
    정사각(fa).save(O + 이름 + "_앞그림.png"); 정사각(fb).save(O + 이름 + "_옆그림.png")
    앞, 옆 = T.돌출(-1, 0), T.돌출(-1, 1); 교 = 앞.intersect(옆).intersect(T.돌출(-1, 2)); bb = 교.val().BoundingBox()
    앞 = 앞.intersect(T.상자(bb.xmin - 12, bb.xmax + 12, -10, 110, -10, 110)); 옆 = 옆.intersect(T.상자(-10, 110, bb.ymin - 12, bb.ymax + 12, -10, 110))   # 판은 물건 앞뒤로만(쿠키 판)
    m앞, m옆, m교 = 메시로(앞), 메시로(옆), 메시로(교); 중 = m교.bounds.mean(0); 크 = m교.extents.max() * 1.5
    if 이름 == "머리":
        돌림([(m앞, 색["앞"])], "머리_앞판", 중=중, 크=크); 돌림([(m옆, 색["옆"])], "머리_옆판", 중=중, 크=크); 돌림([(m앞, 색["앞"]), (m옆, 색["옆"])], "머리_겹침", 중=중, 크=크)
    돌림([(m교, 색["교차"])], 이름 + "_교차", 중=중, 크=크)
    print(이름, "ok", flush=True)
Image.open(IMG).convert("RGB").save(O + "삼면.png")
