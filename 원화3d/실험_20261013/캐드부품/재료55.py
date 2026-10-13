# 쇼츠 55 재료 — 얕은 홈 · 깊은 구멍(위에서 보면 같은 원) · 계단 부품 CadQuery → EEVEE · 10-13
import cadquery as cq, subprocess
A = "G:/art2real/out/설명/구멍/"
W = cq.Workplane
for n, s in (("55_얕은홈", W("XY").box(20, 20, 10).faces(">Z").workplane().circle(5).cutBlind(-2)),
             ("55_깊은구멍", W("XY").box(20, 20, 10).faces(">Z").workplane().circle(5).cutBlind(-8)),
             ("55_계단", W("XY").box(22, 16, 4).union(W("XY").box(14, 16, 4).translate((-4, 0, 4))).union(W("XY").box(6, 16, 4).translate((-8, 0, 8))))):
    cq.exporters.export(s, A + "r%s.stl" % n, tolerance=0.01, angularTolerance=0.05)
subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--", "55_얕은홈", "55_깊은구멍", "55_계단"], check=True, stdout=subprocess.DEVNULL); print("ok")
