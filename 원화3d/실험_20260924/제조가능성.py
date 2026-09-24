# -*- coding: utf-8 -*-
"""**제조 게이트** — 점수판을 유사도에서 제조 제약으로 바꾼다 (2026-09-24).

    python 제조가능성.py 검사        자가검사 (속 찬 상자 · 벽 1.2mm 상자)
    python 제조가능성.py            실제 키트(대조군) + 우리 부품

부품마다 넷을 본다. 통과 / 전체 한 줄이 점수판이다.

    ① 얇은 면적 몫 <= 0.10 (두께 0.8mm 미만)   ② 얇기 <= 0.25 (껍질인가)
    ③ 서포트 면적 몫 <= 0.35 (가장 좋은 방향)  ④ A1 판 250mm 안

**09-24 1 회차에서 대조군이 자를 깨뜨렸다.** 실제 키트 통과율이 0.07 이었다. 세 가지가 틀렸다:
  · 최소 벽 두께(5 분위)는 **껍질의 가장자리 살**을 잡는다 — 진짜 키트도 다 떨어진다. 면적 몫으로 바꾼다.
  · 「탈형 방향 존재」는 **속 빈 껍질이면 원리상 통과할 수 없다**(기둥이 벽·공동·벽 세 토막). 금형 이야기이고 우리는 출력한다. 서포트로 바꾼다.
  · 키트를 전고 125mm 로 **다시 배율 조정한 것이 잘못**이다. 설계자가 정한 크기 그대로 재야 한다.

**대조군이 자를 검증한다** — 실제 키트 부품이 떨어지면 키트가 아니라 게이트가 틀린 것이다.
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 원형사 as WH

전고 = 125.0
벽하한, 얇은몫상한, 얇기상한, 서포트상한, 판크기 = 0.8, 0.10, 0.25, 0.35, 250.0
피치 = 0.4          # 벽 두께를 재는 복셀 크기 (0.8mm 벽이 2 칸)


광선수 = 900


def 국소두께(m, n=광선수):
    """**벽 두께** — 겉면에서 안쪽으로 광선을 쏘아 다음 면까지의 거리를 잰다. 그게 벽 두께의 정의다.

    복셀로 재려 했다가 `voxelized().fill()` 이 **속 빈 껍질의 공동까지 메워** 껍질이 덩어리로 잡혔다
    (09-24 자가검사가 잡았다). 바깥에서 채우는 방식은 닫힌 공동을 구별하지 못한다.
    광선은 그 문제가 없고 정의 그대로다. 속이 꽉 찬 부품은 «반대쪽 벽까지» 거리가 나와 자연히 크다."""
    g = m
    if len(g.faces) > 20000:
        import fast_simplification
        vv, ff = fast_simplification.simplify(np.asarray(g.vertices, np.float32),
                                              np.asarray(g.faces, np.int32), 1 - 20000 / len(g.faces))
        g = trimesh.Trimesh(vv, ff, process=False)
    if len(g.faces) < 4: return None
    pts, fid = g.sample(n, return_index=True)
    nrm = np.asarray(g.face_normals)[fid]
    눈 = max(float(g.extents.max()) * 1e-5, 1e-4)
    출발 = pts - nrm * 눈
    loc, ray, _ = g.ray.intersects_location(출발, -nrm, multiple_hits=False)
    if len(loc) < n * 0.2: return None
    d = np.linalg.norm(loc - 출발[ray], axis=1) + 눈
    return float(np.mean(d < 벽하한)), float(np.median(d))


def 서포트몫(m):
    """**서포트가 필요한 면적 몫** — 쌓는 방향 여섯 중 가장 좋은 것.
    아래를 보는 면이 수평에서 45° 안쪽이면 서포트가 붙는다. 금형의 탈형이 아니라 **우리가 실제로 하는 공정**이다."""
    n = np.asarray(m.face_normals); a = m.area_faces; 합 = a.sum()
    좋 = 1.0
    for ax in range(3):
        for 위 in (1, -1):
            u = np.zeros(3); u[ax] = 위
            좋 = min(좋, float(a[(n @ -u) > 0.7071].sum() / max(합, 1e-9)))
    return 좋


def 부품재기(m, 배율=1.0):
    m = m.copy()
    if 배율 != 1.0: m.apply_scale(배율)
    m.merge_vertices()
    V, A = abs(float(m.volume)), float(m.area)
    if V <= 0 or A <= 0: return None
    t = 국소두께(m)
    if t is None: return None
    얇기 = (2 * V / A) / V ** (1 / 3)
    서포트 = 서포트몫(m)
    r = {"얇은몫": round(t[0], 3), "벽두께중앙mm": round(t[1], 2), "서포트몫": round(서포트, 3),
         "얇기": round(얇기, 3), "부피cm3": round(V / 1000, 2),
         "크기mm": [round(float(x), 1) for x in m.extents]}
    r["①벽"] = t[0] <= 얇은몫상한
    r["②껍질"] = 얇기 <= 얇기상한
    r["③서포트"] = 서포트 <= 서포트상한
    r["④판"] = max(m.extents) <= 판크기
    r["통과"] = all(r[k] for k in ("①벽", "②껍질", "③서포트", "④판"))
    return r


def 한벌(경로들, 이름, 배율=None):
    ms = []
    for p in 경로들:
        try:
            m = trimesh.load(p, force="mesh"); m.merge_vertices()
        except Exception:
            continue
        if len(m.faces) and m.is_watertight and m.volume > 0: ms.append(m)
    if len(ms) < 3: return None
    if 배율 is None:
        모두 = trimesh.util.concatenate([m.copy() for m in ms])
        배율 = 전고 / max(float(모두.extents.max()), 1e-9)
    줄 = [r for r in (부품재기(m, 배율) for m in ms) if r]
    if not 줄: return None
    통 = lambda k: round(sum(r[k] for r in 줄) / len(줄), 3)
    return {"이름": 이름, "부품": len(줄), "배율": round(배율, 4),
            "통과율": 통("통과"), "①벽": 통("①벽"), "②껍질": 통("②껍질"), "③서포트": 통("③서포트"), "④판": 통("④판"),
            "얇은몫 중앙": round(float(np.median([r["얇은몫"] for r in 줄])), 3),
            "서포트몫 중앙": round(float(np.median([r["서포트몫"] for r in 줄])), 3),
            "벽두께mm 중앙": round(float(np.median([r["벽두께중앙mm"] for r in 줄])), 2),
            "얇기 중앙": round(float(np.median([r["얇기"] for r in 줄])), 3),
            "합계 부피cm3": round(sum(r["부피cm3"] for r in 줄), 1)}


def 검사():
    """속 찬 상자는 두껍고, 벽 1.2mm 상자는 1.2mm 로 나와야 한다."""
    상자 = trimesh.creation.box((20, 20, 20))
    안 = trimesh.creation.box((20 - 2.4, 20 - 2.4, 20 - 2.4))
    껍질 = trimesh.boolean.difference([상자, 안])
    a, b = 국소두께(상자), 국소두께(껍질)
    print("속 찬 20mm 상자   최소 %.2f 중앙 %.2f  (기대: 20mm 근처 — 반대쪽 벽까지)" % a)
    print("벽 1.2mm 상자     최소 %.2f 중앙 %.2f  (기대: 1.2 언저리)" % b)
    print("얇기  속 찬 상자 %.3f  (기대 0.333)   껍질 %.3f  (기대 << 0.25)" % (
        (2 * 상자.volume / 상자.area) / 상자.volume ** (1 / 3),
        (2 * abs(껍질.volume) / 껍질.area) / abs(껍질.volume) ** (1 / 3)))
    assert b[1] < 2.0 and a[1] > 8.0, "벽 두께가 껍질과 덩어리를 못 가른다"
    assert a[0] == 0.0 and b[0] == 0.0, "얇은 몫이 두꺼운 벽에서 0 이 아니다"
    print("자가검사 통과")


def main():
    조립좌표 = ("680191", "529483", "813280", "529278", "588149")
    줄 = []
    for kit in 조립좌표:
        d = os.path.join(H.OUT, "키트정답", kit)
        fs = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(".stl")]
        r = 한벌(fs, "키트 " + kit, 배율=1.0)   # 설계자가 정한 크기 그대로 — 다시 맞추면 벽 두께가 거짓이 된다
        if r: 줄.append(r)
    d = os.path.join(H.OUT, "출력", "mech_Mech_4UvIHxnoSR")
    fs = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(".stl")]
    r = 한벌(fs, "우리 mech", 배율=1.0)
    if r: 줄.append(r)
    for r in 줄:
        print("  %-14s 부품%3d  통과 %.2f | ①벽 %.2f ②껍질 %.2f ③서포트 %.2f ④판 %.2f | 얇은몫 %.3f 서포트 %.2f 벽 %.2fmm 얇기 %.3f 합계 %6.1fcm³" % (
            r["이름"], r["부품"], r["통과율"], r["①벽"], r["②껍질"], r["③서포트"], r["④판"],
            r["얇은몫 중앙"], r["서포트몫 중앙"], r["벽두께mm 중앙"], r["얇기 중앙"], r["합계 부피cm3"]))
    키 = [r for r in 줄 if r["이름"].startswith("키트")]
    요약 = {"키트 통과율 중앙": round(float(np.median([r["통과율"] for r in 키])), 3),
           **{"키트 %s 중앙" % k: round(float(np.median([r[k] for r in 키])), 3) for k in ("①벽", "②껍질", "③서포트", "④판")}}
    print("\n" + json.dumps(요약, ensure_ascii=False))
    p = os.path.join(H.OUT, "기록", "제조게이트_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "줄": 줄}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    (검사 if len(sys.argv) > 1 and sys.argv[1] == "검사" else main)()
