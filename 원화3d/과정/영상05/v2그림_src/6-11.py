# -*- coding: utf-8 -*-
"""6-11 두 사람 뒤의 집을 여러 번 완성: 보이는 곳은 같고 가려진 곳(문 · 창 · 현관)이 저마다 다른 집 셋 (Ozguroglu 외 2024 Fig.8 의 생각)
python 6-11.py → ../6-11.png · 세 집의 입력 그림이 같은지 assert 로 확인한다."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _bl as B
D = B.passdir("6-11")
WALL, TRIM, DARK = (0.9, 0.85, 0.7), (0.98, 0.98, 0.96), (0.25, 0.28, 0.32)

if B.bpy:
    import bpy
    def prism(name, color):
        v = [(-2.4, -1.7, 3.2), (2.4, -1.7, 3.2), (0, -1.7, 5.0), (-2.4, 1.7, 3.2), (2.4, 1.7, 3.2), (0, 1.7, 5.0)]
        f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.color = (*color, 1); return o
    def win(x, z, w=0.55, h=0.8):
        return [B.box("창틀", (x, -1.52, z), (w + 0.12, 0.06, h + 0.12), TRIM), B.box("창", (x, -1.56, z), (w, 0.06, h), DARK)]
    def house(v):
        P = [B.box("벽", (0, 0, 1.6), (4.2, 3.0, 3.2), WALL), prism("지붕", (0.55, 0.3, 0.25))]
        P += win(0, 4.0, 0.45, 0.6)                       # 박공 창 (보인다 · 모두 같음)
        P += win(-1.75, 1.9, 0.45) + win(1.75, 1.9, 0.45)  # 옆 창 (보인다 · 모두 같음)
        # 가려진 가운데 (x -1.2..1.2 · z < 3) 만 다르다
        if v == 1:
            P += [B.box("문", (0, -1.55, 0.85), (0.7, 0.06, 1.7), (0.45, 0.25, 0.18))] + win(-0.85, 1.9, 0.4) + win(0.85, 1.9, 0.4)
        if v == 2:
            P += [B.box("문", (-0.75, -1.55, 0.85), (0.6, 0.06, 1.7), (0.2, 0.35, 0.55))] + win(0.55, 1.6, 0.9, 1.2)
        if v == 3:
            P += [B.box("현관", (0, -1.9, 0.12), (2.3, 0.8, 0.24), TRIM), B.box("현관지붕", (0, -1.95, 2.45), (2.3, 0.9, 0.1), TRIM),
                  B.box("문", (0.5, -1.55, 0.95), (0.6, 0.06, 1.6), (0.5, 0.15, 0.15))] + win(-0.6, 1.5, 0.6, 0.9)
            for x in (-1.15, 1.15):
                P.append(B.cyl("기둥", (x, -2.2, 1.3), 0.06, 2.3, TRIM, verts=16))
            for i in range(9):
                P.append(B.box("난간", (-1.15 + i * 0.12 if i < 5 else 0.67 + (i - 5) * 0.12, -2.2, 0.55), (0.04, 0.04, 0.6), TRIM))
        return P
    def people():
        P = []
        for x, y, c in ((-0.62, -4.0, (0.3, 0.26, 0.28)), (0.62, -4.3, (0.12, 0.13, 0.18))):   # 몸통이 땅까지 · 둘이 겹쳐 가운데를 다 가린다
            P += [B.cyl("몸", (x, y, 1.3), 0.74, 2.6, c), B.ell("어깨", (x, y, 2.6), (0.74, 0.35, 0.4), c),
                  B.ell("머리", (x, y, 3.3), (0.3, 0.3, 0.38), (0.86, 0.72, 0.62))]
        return P
    for v in (1, 2, 3):
        B.scene((720, 720)); h = house(v); people()
        B.camera((0, -16, 2.5), (0, 0, 2.5), ortho=6.4)
        B.passes(D, [h], tag=str(v))
else:
    B.run(os.path.abspath(__file__))
    import numpy as np
    ins = [B.on_white(B.load(D, f"beauty{v}.png")) for v in (1, 2, 3)]
    d = max(np.abs(ins[0] - ins[k]).max() for k in (1, 2))
    assert d < 0.02, "입력이 집마다 다르다(%.3f) — 다른 곳이 사람 밖으로 나왔다" % d
    cv = B.canvas(); S = 380; gap = 30; X0 = (1920 - 4 * S - 3 * gap - 40) // 2; Y = 300
    cv.paste(B.to_img(ins[0]).resize((S, S)), (X0, Y)); B.label(cv, (X0 + S // 2, Y + S + 50), "입력", 32)
    for v in (1, 2, 3):
        al = B.load(D, f"alone{v}_1.png"); fade = ins[0] * 0.25 + 0.75
        comp = al[..., :3] * al[..., 3:4] + fade * (1 - al[..., 3:4])
        x = X0 + 40 + v * (S + gap); cv.paste(B.to_img(comp).resize((S, S)), (x, Y))
        B.label(cv, (x + S // 2, Y + S + 50), f"완성 {v}", 32)
    B.arrow(cv, (X0 + S + 8, Y + S // 2), (X0 + S + 60, Y + S // 2), w=5)
    cv.save(os.path.join(B.OUT, "6-11.png"))
