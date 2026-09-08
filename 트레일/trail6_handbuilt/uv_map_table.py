# -*- coding: utf-8 -*-
"""**알베도 분할 번호 ↔ UV 섬 번호** 대응표. 일대다 허용.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python uv_map_table.py

판 경계를 이음선으로 박았으니 섬 하나는 반드시 판 하나에 속한다(순도 100%).
반대로 판 하나는 여러 섬으로 갈릴 수 있다 — 그게 일대다다.
산출: out/uv_map_table.json  (판 -> 섬 목록, 면수, 면적%, 색)
"""
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "panel_q800.blend"))
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nf = len(me.polygons)
# 라벨은 메시에 박혀 있다 (uv_panel.py 가 후면 보정까지 반영해 넣었다).
# 여기서 다시 transfer 하면 보정 전 라벨이 나와 섬이 판 둘을 문 것처럼 보인다.
at = me.attributes["panel"]
lab = np.empty(nf, np.int32); at.data.foreach_get("value", lab)
import retopo_paint as rp
col, _, _ = rp.transfer(me)

area = np.empty(nf); me.polygons.foreach_get("area", area)
uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)

_, inv = np.unique(np.round(uv * 20000).astype(np.int64), axis=0, return_inverse=True)
par = np.arange(inv.max() + 1)
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for i in range(nf):
    r = find(inv[ls[i]])
    for k in range(1, lt[i]):
        t = find(inv[ls[i] + k])
        if r != t: par[t] = r
_, isl = np.unique(np.array([find(inv[ls[i]]) for i in range(nf)]), return_inverse=True)

tot = area.sum()
table = {}
print("%-6s %6s %7s  %-16s %s" % ("판", "면", "면적%", "색 RGB", "UV 섬 (면적% 내림차순)"))
for L in sorted(np.unique(lab)):
    m = lab == L
    ss = sorted(np.unique(isl[m]), key=lambda s: -area[m & (isl == s)].sum())
    parts = ["%d(%.1f%%)" % (s, area[m & (isl == s)].sum() / tot * 100) for s in ss]
    c = col[m].mean(0)
    print("%-6d %6d %6.1f%%  RGB(%3.0f,%3.0f,%3.0f)  %s"
          % (L, m.sum(), area[m].sum() / tot * 100, c[0], c[1], c[2], " ".join(parts)))
    table[int(L)] = {"면": int(m.sum()), "면적%": round(float(area[m].sum() / tot * 100), 2),
                     "색": [int(round(v)) for v in c],
                     "섬": [{"id": int(s), "면적%": round(float(area[m & (isl == s)].sum() / tot * 100), 2)}
                            for s in ss]}

# 역방향 검사 — 섬 하나가 판 둘을 물면 실패다
bad = [int(s) for s in range(isl.max() + 1) if len(np.unique(lab[isl == s])) > 1]
print("\n판 %d개 -> UV 섬 %d개 (일대다).  섬이 판 둘을 문 경우: %s"
      % (len(np.unique(lab)), isl.max() + 1, bad if bad else "없음"))
json.dump({"판수": int(len(np.unique(lab))), "섬수": int(isl.max() + 1),
           "섞인섬": bad, "표": table},
          open(os.path.join(OUT, "uv_map_table.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("out/uv_map_table.json")
