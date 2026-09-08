#!/bin/sh
# 평활 창을 훑어 거칠기와 실루엣 IoU 를 같이 잰다. 창은 재서 고른다, 취향으로 고르지 않는다.
BL="/c/Program Files/Blender Foundation/Blender 4.0/blender.exe"
for W in 0 5 7 11 15 21; do
  SMOOTH=$W python depth.py --nocheck >/dev/null 2>&1 || SMOOTH=$W python -c "
import os; os.environ['SMOOTH']='$W'
import depth; depth.build()" >/dev/null
  "$BL" -b --python buildpad.py -- out/workbench.blend >/dev/null 2>&1
  NOHORN=1 TAG=sw "$BL" -b out/workbench.blend --python ab_front.py >/dev/null 2>&1
  W=$W python - <<'PY'
import json, os, numpy as np
from PIL import Image, ImageDraw
R=1024; cw=lambda u:(u+0.6)/1.2*(R-1); rw=lambda z:(1.1-z)/1.2*(R-1)
s=json.load(open("parts/sh_pauldron.json",encoding="utf-8"))
def mask(p):
    im=Image.new("L",(R,R),0); ImageDraw.Draw(im).polygon([(cw(a[0]),rw(a[1])) for a in p],fill=255)
    return np.array(im)>128
mf,ms=mask(s["front"]["poly_xz"]),mask(s["side"]["poly_yz"])
def iou(f,r):
    a=np.array(Image.open(f).convert("RGBA"))[...,3]>128
    return (a&r).sum()/(a|r).sum()
D=json.load(open("parts/depth.json")); b=D["bands"]
z=np.array([x["z"] for x in b]); yf=np.array([x["yf"] for x in b]); dz=np.diff(z).mean()
r2=float(np.sqrt(((np.diff(yf,2)/dz**2)**2).mean()))
fl=int((np.diff(np.sign(np.diff(yf)))!=0).sum())
print("창 %-3s  yf거칠기 %7.1f  부호바뀜 %2d   정면 IoU %.3f  측면 IoU %.3f"
      % (os.environ["W"], r2, fl, iou("out/sw_front.png",mf), iou("out/sw_side.png",ms)))
PY
done
