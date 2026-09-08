# -*- coding: utf-8 -*-
"""캡 + 뿔을 한 파일로 조립하고 **뿌리가 캡 안에 박혔는지** 잰다.

    blender -b --python assemble.py -- out/pauldron_v3.blend

조립을 파이썬 한 줄짜리 즉석 명령으로 하다가 뿔의 깊이(y)가 전부 뒤바뀐 걸
놓쳤다. 조립도 부품처럼 스크립트로 둔다 — 그래야 다시 잴 수 있다.
"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def load(path):
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    return [o for o in dst.objects if o.type == "MESH"]


def bb(o):
    co = np.array([v.co[:] for v in o.data.vertices])
    return co.min(0), co.max(0)


def main():
    out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.join(OUT, "pauldron_v3.blend")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # cap_c1.blend 는 pauldron() 을 통째로 지은 파일이라 **옛 뿔이 딸려 온다.**
    # 새 뿔을 그 위에 얹으면 뿔이 두 벌(8개)이 된다 — 원화는 4개다. 여기서 버린다.
    cap = load(os.path.join(OUT, "cap_c1.blend"))
    drop = [o for o in cap if o.name.startswith("sh_horn")]
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    cap = [o for o in cap if o not in drop]
    print("캡 파일의 옛 뿔 %d개 버림 -> 남은 %s" % (len(drop), [o.name for o in cap]))
    horns = load(os.path.join(OUT, "horns.blend"))
    clo, chi = bb(cap[0])
    print("캡   x %+.4f..%+.4f  y %+.4f..%+.4f  z %.4f..%.4f" % (clo[0], chi[0], clo[1], chi[1], clo[2], chi[2]))
    for o in sorted(horns, key=lambda o: o.name):
        lo, hi = bb(o)
        # 뿌리 = 캡에 가까운 끝. z 최저 고리를 뿌리로 본다
        co = np.array([v.co[:] for v in o.data.vertices])
        root = co[co[:, 2] <= co[:, 2].min() + 1e-4].mean(0)
        inside = all(clo[k] - 1e-4 <= root[k] <= chi[k] + 1e-4 for k in (0, 1, 2))
        print("  %-6s 뿌리(%+.4f,%+.4f,%.4f)  y %+.4f..%+.4f  캡 bbox 안: %s"
              % (o.name, root[0], root[1], root[2], lo[1], hi[1], "예" if inside else "**아니오**"))
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("ASSEMBLE OK objects=%d faces=%d -> %s"
          % (len(cap) + len(horns), sum(len(o.data.polygons) for o in cap + horns), out))


if __name__ == "__main__":
    main()
