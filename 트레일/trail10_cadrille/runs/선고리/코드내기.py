# -*- coding: utf-8 -*-
"""선 고리 결과를 사람이 읽는 CadQuery 코드로 내보내기 · 코드를 다시 실행해 부피가 같은지 확인
python runs/선고리/코드내기.py <번호>  →  코드_NN_A.py · 코드_NN_B.py (단위: 부품 긴 변 = 100)"""
import os, sys, json, pickle, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "윤곽0"), os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 선고리 import 세계, N as NL, 포켓, TH
from 윤곽 import 다각형들, PL
from 실물보기 import 실물보기
from s0 import unit
i = int(sys.argv[1]); D = pickle.load(open(os.path.join(H, "단계_%02d.pkl" % i), "rb")); fs = D["fs"]
m = unit(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + D["부품"], force="mesh")); Sr, _ = 실물보기(m, 256)
f1 = lambda v: "%.1f" % v
def 점들(p): return "[" + ", ".join("(%s, %s)" % (f1(a * 100), f1(b * 100)) for a, b in p) + "]"
for 판 in ("A", "B"):
    L = ['# 부품 #%d %s — 선 고리 시험 (%s 깊이) · 자동 생성 · 단위: 긴 변 = 100' % (i, D["부품"], "정답" if 판 == "A" else "AI"),
         'import cadquery as cq', '',
         'def 제자리(s, ax, lo):   # 밀어낸 기둥을 축 ax 방향으로 lo 에서 시작하게 옮김 (작업면 법선 방향과 상관없이)',
         '    bb = s.val().BoundingBox(); t = [0, 0, 0]; t[ax] = lo - (bb.xmin, bb.ymin, bb.zmin)[ax]; return s.translate(tuple(t))', '',
         '# ── 1 바탕: 앞 · 옆 · 위 윤곽을 밀어서 교차 ──']
    이름 = {0: "앞(YZ)", 1: "옆(XZ)", 2: "위(XY)"}
    for ax in range(3):
        L.append('판%d = None   # %s' % (ax, 이름[ax]))
        for outer, holes in 다각형들(Sr[2 * ax]):
            L.append('f = cq.Workplane("%s").polyline(%s).close()' % (PL[ax], 점들(outer)))
            for h in holes: L.append('f = f.polyline(%s).close()' % 점들(h))
            t = "(0, 50, 0)" if PL[ax] == "XZ" else str(tuple(50 if k == ax else 0 for k in range(3)))
            L.append('s = f.extrude(80, both=True).translate(%s); 판%d = s if 판%d is None else 판%d.union(s)' % (t, ax, ax, ax))
    L += ['바탕 = 판0.intersect(판1).intersect(판2)', '', '# ── 2 포켓: 그림의 닫힌 선 고리 = 스케치 → 그 깊이까지 빼기 ──', 'r = 바탕']
    n = 0
    for f in fs:
        if f["종"] != "고리" or 판 not in f.get("판것", []): continue
        ax = f["쪽"] // 2; 종, v = f["벡터"]; n += 1
        깊 = (f[판] * 1.1 - .05 + .2) * 100
        if 종 == "원":
            rr, cc, rad = v; u, w = 세계(rr, cc)
            L.append('# 포켓 %d · %s 쪽 · 원 Ø%s · 깊이 %s (바탕보다 %s 더)' % (n, 이름[ax], f1(2 * rad / NL * 110), f1(f[판] * 110), f1((f[판] - f["바탕"]) * 110)))
            L.append('r = r.cut(제자리(cq.Workplane("%s").center(%s, %s).circle(%s).extrude(%s), %d, -20))' % (PL[ax], f1(u * 100), f1(w * 100), "%.2f" % (rad / NL * 110), f1(깊), ax))
        else:
            L.append('# 포켓 %d · %s 쪽 · 다각형 %d 꼭짓점 · 깊이 %s (바탕보다 %s 더)' % (n, 이름[ax], len(v), f1(f[판] * 110), f1((f[판] - f["바탕"]) * 110)))
            L.append('r = r.cut(제자리(cq.Workplane("%s").polyline(%s).close().extrude(%s), %d, -20))' % (PL[ax], 점들([세계(a, b) for a, b in v]), f1(깊), ax))
    L += ['', 'cq.exporters.export(r, "부품%02d_%s.step")' % (i, 판)]
    p = os.path.join(H, "코드_%02d_%s.py" % (i, 판)); open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
    # 확인: 코드를 실행한 결과 부피 = 선고리.py 결과 부피
    g = {}; exec(compile(open(p, encoding="utf-8").read().replace('cq.exporters.export', '_ = (lambda *a: None) or print if False else (lambda *a: None)\n# cq.exporters.export'), p, "exec"), g)
    from 윤곽 import 메시로
    v_code = g["r"].val().Volume(); m_run = trimesh.load(os.path.join(H, "결과_" + 판, "%02d_선고리.stl" % i)); v_run = m_run.volume * 50 ** 3
    print(판, "포켓", n, "개 · 코드 부피 %.0f · 돌린 결과 부피 %.0f · 차 %.2f%%" % (v_code, v_run, 100 * abs(v_code - v_run) / v_run), "·", p)
