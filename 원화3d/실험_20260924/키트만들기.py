# -*- coding: utf-8 -*-
"""**키트 만들기** — 먹선으로 가르고 · 먹선을 새기고 · 다보를 박아 출력 키트로 낸다 (2026-09-24).

    python 키트만들기.py [케이스=오메가몬] [전고=125]
      -> out/출력/<케이스>_키트/부품NN.stl · 키트.json

    ① 먹선 벽으로 부피를 가른다 (`먹선분할`) — 분할선이 곧 먹선이다
    ② 부품마다 장에서 등위면을 뽑고 (0/1 로 안 바꾼다) 창 좌표에서 먹선을 새긴다
    ③ 닿는 부품 짝마다 **다보** — 수(핀)는 −3% · 암(구멍)은 한쪽 0.15mm 틈 (09-23 원형사 조사)
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922",
                r"G:\art2real\원화3d\실험_20260923", r"G:\art2real\원화3d\실험_20260924"]
import hull as H, 부품분할 as BB, 면자르기 as MJ, 지표 as Z
import 먹선분할 as MS, 제조가능성 as MG, 선다듬기 as SD

핀반지름, 핀길이, 틈 = 0.9, 2.5, 0.15        # mm — 1/144 키트의 다보와 비슷하게
홈폭, 홈깊이 = 0.5, 0.35                      # mm — 노즐 0.4 가 들어가는 폭 · V 홈
최소닿음 = 40                                  # 이만큼 안 닿으면 다보를 안 박는다


def 짝찾기(lab, n):
    """부품 짝마다 닿는 칸 수 · 복판 · 법선(경계 칸 주성분의 막내축)."""
    짝 = {}
    for ax in range(3):
        a0 = np.take(lab, range(0, lab.shape[ax] - 1), axis=ax)
        a1 = np.take(lab, range(1, lab.shape[ax]), axis=ax)
        sel = (a0 != a1) & (a0 > 0) & (a1 > 0)
        if not sel.any(): continue
        idx = np.argwhere(sel)
        A = a0[sel]; B = a1[sel]
        for (i, j, k), a, b in zip(idx, A, B):
            key = (int(min(a, b)), int(max(a, b)))
            짝.setdefault(key, []).append((i, j, k))
    낼 = {}
    for key, pts in 짝.items():
        P = np.array(pts, float)
        if len(P) < 최소닿음: continue
        c = P.mean(0)
        u, s, vt = np.linalg.svd(P - c, full_matrices=False)
        낼[key] = (c, vt[-1] / max(np.linalg.norm(vt[-1]), 1e-9), len(P))
    return 낼


def 기둥(중심, 법선, 반지름, 길이):
    m = trimesh.creation.cylinder(radius=반지름, height=길이, sections=20)
    z = np.array([0, 0, 1.0]); v = np.cross(z, 법선); s = np.linalg.norm(v)
    if s > 1e-9:
        cth = float(np.dot(z, 법선)); K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + K + K @ K * ((1 - cth) / (s ** 2))
    else:
        R = np.eye(3) if 법선[2] > 0 else np.diag([1, -1, -1.0])
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = 중심
    m.apply_transform(T); return m


def main():
    c = sys.argv[1] if len(sys.argv) > 1 else "오메가몬"
    전고 = float(sys.argv[2]) if len(sys.argv) > 2 else 125.0
    os.environ.setdefault("INK_W", "1")
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    선들 = MS.창먹선(c, raw, p, bs)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    경 = np.zeros_like(O)
    for a2 in range(3):
        a0 = np.take(부위, range(0, 부위.shape[a2] - 1), axis=a2)
        a1 = np.take(부위, range(1, 부위.shape[a2]), axis=a2)
        d = (a0 != a1) & (a0 > 0) & (a1 > 0)
        경 |= np.pad(d, [(0, 0)] * a2 + [(0, 1)] + [(0, 0)] * (2 - a2))
    lab = MS.가르기(O, MS.먹선벽(O, 선들, ux, z, bs) | (경 & O))
    n = int(lab.max())
    몫 = MS.먹선몫(lab, 선들, ux, z, bs, O)
    print("  부품 %d · 분할선이 먹선 위 %.3f" % (n, 몫))

    전체 = Z.메시로(g, (ux, uy, z))
    배율 = 전고 / float(전체.extents[2])
    판들 = SD.홈판(c, raw, p, bs)               # 다듬은 선 (곧게 편 것)
    # 격자 -> mm 로 옮기는 자리 계산 (부품 중심 · 법선에 쓴다)
    축 = [ux, uy, z]
    def 격자에서창(pt):
        return np.array([np.interp(pt[i], np.arange(len(축[i])), 축[i]) for i in range(3)])

    짝 = 짝찾기(lab, n)
    부품 = {}
    for l in range(1, n + 1):
        안 = ndimage.distance_transform_edt(lab == l)
        밖 = ndimage.distance_transform_edt(lab != l)
        d = ndimage.gaussian_filter(np.where(lab == l, 안 - 0.5, -(밖 - 0.5)).astype(np.float32), 1.0)
        m = Z.메시로(np.minimum(g, d), (ux, uy, z))
        if len(m.faces) < 50: continue
        부품[l] = m                                  # 창 좌표 그대로 — 다보 불리언 뒤에 홈을 판다
    print("  부품 메시 %d 개 · 다보 짝 %d" % (len(부품), len(짝)))

    핀 = {l: [] for l in 부품}; 구멍 = {l: [] for l in 부품}
    for (a, b), (ctr, nrm, cnt) in sorted(짝.items(), key=lambda kv: -kv[1][2]):
        if a not in 부품 or b not in 부품: continue
        C = 격자에서창(ctr)
        N = 격자에서창(ctr + nrm) - C; N = N / max(np.linalg.norm(N), 1e-9)
        # 부피가 작은 쪽에 핀, 큰 쪽에 구멍
        수, 암 = (a, b) if 부품[a].volume < 부품[b].volume else (b, a)
        핀[수].append(기둥(C, N, 핀반지름 * 0.97 / 배율, 핀길이 * 2 / 배율))
        구멍[암].append(기둥(C, N, (핀반지름 + 틈) / 배율, (핀길이 * 2 + 1.0) / 배율))
    out = os.path.join(H.OUT, "출력", c + "_키트"); os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".stl"): os.remove(os.path.join(out, f))
    낼, 실패 = [], []
    for i, (l, m) in enumerate(sorted(부품.items())):
        try:
            if 핀[l]: m = trimesh.boolean.union([m] + 핀[l])
            if 구멍[l]: m = trimesh.boolean.difference([m] + 구멍[l])
        except Exception as e:
            실패.append((l, type(e).__name__))
        # **다보 뒤에 홈을 판다** — 홈을 먼저 파면 잘게 쪼갠 메시라 불리언이 죄다 실패한다 (09-24)
        m, _ = SD.홈파기(m, 판들, bs, 홈폭 / 배율, 홈깊이 / 배율)
        m.apply_scale(배율)
        m.apply_translation(-m.bounds[0])
        fn = os.path.join(out, "부품%02d.stl" % i); m.export(fn)
        r = MG.부품재기(m) or {}
        낼.append({"부품": "부품%02d" % i, "부피cm3": round(abs(m.volume) / 1000, 2),
                   "핀": len(핀[l]), "구멍": len(구멍[l]),
                   "크기mm": [round(float(x), 1) for x in m.extents],
                   "①벽": bool(r.get("①벽", False)), "③서포트": bool(r.get("③서포트", False)), "④판": bool(r.get("④판", False))})
        print("    %s  %5.1f cm³  핀 %d 구멍 %d  %s" % (낼[-1]["부품"], 낼[-1]["부피cm3"], len(핀[l]), len(구멍[l]),
              "".join(k for k in ("①벽", "③서포트", "④판") if not 낼[-1][k]) or "게이트 OK"), flush=True)
    꾸 = {"케이스": c, "전고mm": 전고, "부품": len(낼), "먹선 위 몫": round(몫, 3),
         "다보 짝": len(짝), "핀 합": sum(x["핀"] for x in 낼), "불리언 실패": 실패,
         "합계 부피cm3": round(sum(x["부피cm3"] for x in 낼), 1), "줄": 낼}
    json.dump(꾸, open(os.path.join(out, "키트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  합계 %.1f cm³ · 핀 %d · 불리언 실패 %d" % (꾸["합계 부피cm3"], 꾸["핀 합"], len(실패)))
    print(out)


if __name__ == "__main__":
    main()
