# -*- coding: utf-8 -*-
"""**전체 매핑** — 정면 18 + 측면 16 + 후면 23 판을 면 723개에 배정한다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python remap_all.py

지금까지는 front 18 + side 1(뭉뚱그림) 뿐이었고 그 하나가 아틀라스의 55.8% 였다.
71k 파이프라인(tri_paint)을 다시 돌리지 않는다 — 칠할 대상은 723 쿼드고
판 배정은 면 중심 하나로 끝나는 일이라 여기서 바로 한다.

    라벨 공간   front 0..17 · side 100+ · back 200+ · 미배정 -1
    배정        면 법선으로 판을 고르고(가장 정면인 판), 그 판의 마스크 안이면
                크롭 픽셀의 알베도 라벨을 읽는다. 밖이면 다음으로 정면인 판.
    색          그 판 영역의 원화 중앙색 (평면 알베도)
    전파        어느 판도 못 읽은 면은 이웃 다수결 (판이 아니라 라벨을 옮긴다)
"""
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mask2d
from mask2d import topix

OUT = os.path.join(HERE, "out"); T4 = os.path.join(HERE, "..", "trail4_gen3d")
VW = json.load(open(os.path.join(HERE, "parts", "views.json"), encoding="utf-8"))
MINPX = 40

# 판 정의: (이름, 법선 점수, 월드축->화면 u 의 부호와 축, 라벨 오프셋)
DEF = [("front", lambda n: -n[:, 1], (0,  1.0),   0),
       ("side",  lambda n:  n[:, 0], (1,  1.0), 100),
       ("side",  lambda n: -n[:, 0], (1,  1.0), 100),
       ("back",  lambda n:  n[:, 1], (0, -1.0), 200)]

# 판별 라벨맵 · 마스크 · 창
Lm, Mk, Win, Art = {}, {}, {}, {}
Win["front"] = [612, 726, 98, 277]
Lm["front"] = np.load(os.path.join(OUT, "_L_alb.npy"))
Mk["front"] = np.ones_like(Lm["front"], bool)
for v in ("side", "back"):
    Lm[v] = np.load(os.path.join(OUT, "_L_alb_%s.npy" % v))
    Mk[v] = np.load(os.path.join(OUT, "mask_%s.npy" % v))
    keep = set(int(x) for x in np.load(os.path.join(OUT, "keep_%s.npy" % v)))
    Mk[v] = Mk[v] & np.isin(Lm[v], list(keep))
    Win[v] = VW[v]["win"]
for v in ("front", "side", "back"):
    Art[v] = np.load(os.path.join(T4, "rgb_%s.npy" % v))

# ── 팔레트 게이트 ────────────────────────────────────────────────────────────
# 마스크를 조여도 적갈색이 남는다 — 그 화소는 실루엣 **안쪽**이다 (방패에 가려
# 뒤의 남의 부품이 그 자리에 있다). 위치로는 못 거르니 색으로 거른다.
# 견갑 실측 팔레트에서 먼 판은 직접 배정에서 빼고 전파로 돌린다.
PAL = np.array([[87., 92., 124.], [131., 139., 176.],     # 라벤더 (그늘/밝음)
                [158., 138., 76.], [194., 180., 107.],    # 금 (그늘/밝음)
                [41., 42., 44.], [42., 43., 53.]])        # 어두움
GATE = 62.0
for v in ("side", "back"):
    x0, x1, y0, y1 = Win[v]
    sub = Art[v][y0:y1, x0:x1]
    drop = []
    for L in np.unique(Lm[v]):
        if L <= 1: continue
        m = (Lm[v] == L) & Mk[v] & (sub[..., 3] >= 128)
        if m.sum() < MINPX: continue
        c = np.median(sub[..., :3][m], 0)
        if np.linalg.norm(PAL - c, axis=1).min() > GATE:
            Mk[v][Lm[v] == L] = False
            drop.append((int(L), c, float(np.linalg.norm(PAL - c, axis=1).min())))
    print("%-5s 팔레트 게이트로 뺀 판 %d개" % (v, len(drop)))
    for L, c, d in sorted(drop, key=lambda t: -t[2])[:6]:
        print("    판 %-4d RGB(%3.0f,%3.0f,%3.0f)  거리 %.0f" % (L, c[0], c[1], c[2], d))

def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "panel_q800.blend"))
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
    me = o.data; nf = len(me.polygons)
    N = np.empty(nf*3); me.polygons.foreach_get("normal", N); N = N.reshape(-1, 3)
    C = np.empty(nf*3); me.polygons.foreach_get("center", C); C = C.reshape(-1, 3)
    area = np.empty(nf); me.polygons.foreach_get("area", area)

    sc = np.stack([f(N) for _, f, _, _ in DEF], 1)
    order = np.argsort(-sc, 1)
    lab = np.full(nf, -1, np.int32)
    src = np.full(nf, -1, np.int32)
    for i in range(nf):
        for k in order[i]:
            if sc[i, k] <= 0.15:
                break
            name, _, (ax, sgn), off = DEF[k]
            x0, x1, y0, y1 = Win[name]
            py, px = topix(sgn*C[i, ax], C[i, 2])
            cy, cx = py - y0, px - x0
            if not (0 <= cy < y1-y0 and 0 <= cx < x1-x0):
                continue
            if not Mk[name][cy, cx]:
                continue
            v = int(Lm[name][cy, cx])
            if v <= 1:
                continue
            lab[i] = off + v; src[i] = k
            break

    print("직접 배정 %d/%d 면 (면적 %.1f%%)" % ((lab >= 0).sum(), nf, area[lab >= 0].sum()/area.sum()*100))
    for k, (name, _, _, _) in enumerate(DEF):
        m = src == k
        if m.any():
            print("   %-5s(%d)  %4d면  면적 %5.1f%%  판 %d개" % (name, k, m.sum(), area[m].sum()/area.sum()*100, len(np.unique(lab[m]))))

    # 전파 — 엣지를 공유하는 이웃 다수결, 배정될 때까지
    e2f = {}
    for pi, p in enumerate(me.polygons):
        vv = p.vertices[:]
        for a in range(len(vv)):
            e = (min(vv[a], vv[(a+1) % len(vv)]), max(vv[a], vv[(a+1) % len(vv)]))
            e2f.setdefault(e, []).append(pi)
    adj = [[] for _ in range(nf)]
    for f in e2f.values():
        for a in f:
            for b in f:
                if a != b: adj[a].append(b)
    for _ in range(60):
        miss = np.where(lab < 0)[0]
        if not len(miss): break
        new = lab.copy()
        for i in miss:
            nb = [lab[j] for j in adj[i] if lab[j] >= 0]
            if nb: new[i] = max(set(nb), key=nb.count)
        if (new == lab).all(): break
        lab = new
    print("전파 뒤 미배정 %d면" % (lab < 0).sum())

    # 라벨별 색 = 그 판 영역의 원화 중앙색
    colmap = {}
    for L in np.unique(lab):
        if L < 0: continue
        name = "front" if L < 100 else ("side" if L < 200 else "back")
        off = 0 if L < 100 else (100 if L < 200 else 200)
        x0, x1, y0, y1 = Win[name]
        m = (Lm[name] == L - off) & Mk[name]
        sub = Art[name][y0:y1, x0:x1]
        px = sub[..., :3][m & (sub[..., 3] >= 128)]
        colmap[int(L)] = np.median(px, 0) if len(px) else np.array([128., 128., 128.])
    col = np.array([colmap[int(L)] if L >= 0 else [110., 110., 118.] for L in lab])

    at = me.attributes.get("panel") or me.attributes.new("panel", 'INT', 'FACE')
    at.data.foreach_set("value", lab.astype(np.int32).tolist())
    np.save(os.path.join(OUT, "remap_lab.npy"), lab)
    np.save(os.path.join(OUT, "remap_col.npy"), col)
    np.save(os.path.join(OUT, "remap_src.npy"), src)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "panel_q800.blend"))
    print("\n라벨 %d개 (front %d · side %d · back %d)  색 %d종"
          % (len(np.unique(lab)), (np.unique(lab) < 100).sum(),
             ((np.unique(lab) >= 100) & (np.unique(lab) < 200)).sum(),
             (np.unique(lab) >= 200).sum(), len(np.unique(col, axis=0))))


if __name__ == "__main__":
    main()
