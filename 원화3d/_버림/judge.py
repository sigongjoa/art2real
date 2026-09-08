# -*- coding: utf-8 -*-
"""**애니 원화 → 3D 벤치마크.** 어느 모델이 와도 같은 자로 잰다.

    python judge.py                 # cases.tsv 전부 재고 board.md 를 다시 쓴다
    python judge.py 견갑 스탠드      # case 이름 일부로 거른다
    python judge.py --demo          # 자체검사 (메시 없이 돈다)

trail7 venv 로 돌린다 — `5_blender/trail7_part3d/venv/Scripts/python.exe judge.py`

## 자를 새로 안 짠다

`trail7_part3d/judge_stand.py` 가 이미 항 넷을 갖고 있다 — 실루엣 IoU · 덮음/삐져나감 ·
두께비 · 파트 붙음률. 그걸 빌리고 **한 항만 더한다.**

## 더하는 한 항 — 시점 낙차

빌려온 판정기는 **정면만 잰다.** 그런데 지금 생성 모델이 무너지는 자리가 정확히 거기다.
정면 한 장을 넣으니 정면은 맞고 나머지 시점은 **지어내진다** — TripoSG 가 정면 0.827 인데
측면 0.611 이었다. 사람이 「기괴하다」고 느끼는 건 이 낙차다.

    낙차 = max(시점별 IoU) - min(시점별 IoU)

낙차가 안 잡히면 **정면만 맞춘 판이 1등으로 올라온다.** 실제로 trail7 에서
OmniPart cfg12 가 cfg7.5 보다 IoU 가 높았는데 형태가 나아서가 아니었다.

파일은 안 옮긴다. trail4/6/7 의 원화와 메시를 경로로 가리키기만 한다.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "5_blender", "trail7_part3d"))
import judge_stand as J                      # noqa: E402  자 본체

VIEWS = ("front", "side", "back")
FLAT = 0.15                                  # 두께비가 이 밑이면 접시 (judge_stand 주석의 통과선)


def view_axis(ax, view):
    """(투영에 쓸 가로축, 부호). 위축은 언제나 ax[1].

    front 는 가로축 그대로, back 은 좌우가 뒤집히고, side 는 **깊이축이 가로가 된다** —
    시점이 무너졌는지는 여기서 드러난다. 깊이가 없는 판은 side 에서 선이 된다."""
    h, _u, d = ax
    return {"front": (h, 1), "back": (h, -1), "side": (d, 1)}[view]


def mesh_mask(parts, ax, view):
    """`judge_stand.mesh_mask` 와 같되 시점을 고른다. 삼각형을 칠한다(정점만 찍으면 성글다)."""
    import cv2
    a, sign = view_axis(ax, view)
    u = ax[1]
    allV = np.vstack([np.asarray(p.vertices) for p in parts])
    lo, hi = allV.min(0), allV.max(0)
    span = max(hi[a] - lo[a], hi[u] - lo[u], 1e-9)
    g = np.zeros((J.RES * 2, J.RES * 2), np.uint8)
    for p in parts:
        V = np.asarray(p.vertices)
        x = (V[:, a] - lo[a]) if sign > 0 else (hi[a] - V[:, a])
        px = x / span * (J.RES * 2 - 4) + 2
        py = (hi[u] - V[:, u]) / span * (J.RES * 2 - 4) + 2
        P = np.stack([px, py], 1).astype(np.int32)
        for tri in P[np.asarray(p.faces)]:
            # 하나씩 칠한다. cv2 에 여러 개를 한 번에 넘기면 **짝수-홀수**라 앞뒤가 서로를
            # 지운다 (판때기 12면: 한꺼번에 5,533 화소 / 하나씩 744,309). 91.8만 면 1.0초.
            # ponytail: 파이썬 반복문. 면이 1,000만을 넘으면 바리센트릭 벡터화로 간다
            cv2.fillConvexPoly(g, tri, 1)
    return J.fit_box(g.astype(bool))


def judge(row):
    """한 줄 = 모델 하나 × 케이스 하나. 없는 시점은 건너뛴다."""
    mesh = os.path.join(ROOT, row["mesh"])
    if not os.path.exists(mesh):
        return dict(row, miss="메시 없음")
    sc = trimesh.load(mesh)
    parts = list(sc.geometry.values()) if isinstance(sc, trimesh.Scene) else [sc]
    V = np.vstack([np.asarray(p.vertices) for p in parts])
    # 축은 **짐작하지 않는다.** judge_stand 의 `제일 짧은 축이 깊이` 어림은 두께비가 1 에
    # 가까운 덩어리에서 깨진다 (op_s23: 두께 0.948 -> 정면과 측면이 뒤바뀌었다).
    # 시점을 재는 자가 시점을 짐작하면 안 된다. GLB 는 glTF 규약이라 y-up = `xyz`.
    ax = tuple("xyz".index(c) for c in row["axes"]) if row.get("axes", "auto") != "auto" else J.axes(V)

    ious = {}
    for v in VIEWS:
        png = row.get("art_" + v, "")
        if not png or not os.path.exists(os.path.join(ROOT, png)):
            continue
        A = J.art_mask(os.path.join(ROOT, png))
        M = mesh_mask(parts, ax, v)
        ious[v] = float((M & A).sum()) / max(int((M | A).sum()), 1)

    r = dict(row, parts=len(parts), faces=int(sum(len(p.faces) for p in parts)),
             thickness=J.thickness(V, ax), attached=J.attached(parts),
             axes="".join("xyz"[i] for i in ax), **{"iou_" + k: v for k, v in ious.items()})
    # **머리 숫자는 최저 시점이다.** 낙차만 보면 「전부 똑같이 틀린 판」이 1등이 된다 —
    # 견갑 PartCrafter 가 정/측/후 0.08 로 나란해서 낙차 0.082 를 찍었다. 제일 못 맞춘
    # 시점이 그 모델의 실력이고, 낙차는 그 실패가 **시점 붕괴인지 아닌지**를 말해준다.
    r["worst"] = min(ious.values()) if ious else None
    r["gap"] = (max(ious.values()) - min(ious.values())) if len(ious) > 1 else None
    return r


# ----------------------------------------------------------------- 목록과 표

def read_cases(path=None):
    """cases.tsv — `#` 로 시작하는 줄은 주석, 첫 비주석 줄이 열 이름."""
    lines = [l.rstrip("\n") for l in open(path or os.path.join(HERE, "cases.tsv"), encoding="utf-8")]
    lines = [l for l in lines if l.strip() and not l.lstrip().startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def fmt(v, w=6):
    if v is None or v == "":
        return "—".rjust(w)
    return ("%.3f" % v).rjust(w) if isinstance(v, float) else str(v).rjust(w)


def board(rows):
    """모델 × 케이스 표. **낙차 오름차순** — 시점을 제일 잘 지킨 판이 위로."""
    out = ["| 케이스 | 모델 | 정면 | 측면 | 후면 | **낙차** | 두께비 | 붙음 | 파트 | 면 |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    ok = [r for r in rows if "miss" not in r]
    for r in sorted(ok, key=lambda r: (r["case"], r["gap"] if r["gap"] is not None else 9)):
        out.append("| %s | %s | %s | %s | %s | **%s** | %s | %s | %d | %s |" % (
            r["case"], r["model"],
            fmt(r.get("iou_front")), fmt(r.get("iou_side")), fmt(r.get("iou_back")),
            fmt(r["gap"]), fmt(r["thickness"]), fmt(r["attached"]),
            r["parts"], "{:,}".format(r["faces"])))
    for r in rows:
        if "miss" in r:
            out.append("| %s | %s | — | — | — | — | — | — | — | *%s* |"
                       % (r["case"], r["model"], r["miss"]))
    return "\n".join(out)


def demo():
    """메시 없이 도는 자체검사. 시점 축 고르기와 표 그리기만 본다 — 자 본체는 J.demo() 가 본다."""
    ax = (0, 1, 2)                                   # 가로 x · 위 y · 깊이 z
    assert view_axis(ax, "front") == (0, 1)
    assert view_axis(ax, "back") == (0, -1), "후면은 좌우가 뒤집혀야"
    assert view_axis(ax, "side") == (2, 1), "측면은 깊이축이 가로가 돼야"

    # 판때기: 정면은 맞고 측면은 선이 된다 -> 낙차가 커야 한다
    plate = trimesh.creation.box((1.0, 1.4, 0.02))
    a = J.fit_box(np.ones((100, 70), bool))
    m_f = mesh_mask([plate], J.axes(np.asarray(plate.vertices)), "front")
    m_s = mesh_mask([plate], J.axes(np.asarray(plate.vertices)), "side")
    iou_f = (m_f & a).sum() / max((m_f | a).sum(), 1)
    iou_s = (m_s & a).sum() / max((m_s | a).sum(), 1)
    assert iou_f > 0.9, "판때기 정면은 사각 마스크와 거의 같아야 (%.3f)" % iou_f
    assert iou_f - iou_s > 0.3, "판때기는 시점 낙차가 커야 (%.3f -> %.3f)" % (iou_f, iou_s)

    rows = [dict(case="시험", model="가짜", parts=2, faces=10, thickness=0.5,
                 attached=1.0, gap=0.2, iou_front=0.8, iou_side=0.6),
            dict(case="시험", model="없는것", miss="메시 없음")]
    t = board(rows)
    assert "0.200" in t and "메시 없음" in t
    J.demo()
    print("자체검사 통과")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); raise SystemExit
    pick = [a for a in sys.argv[1:] if not a.startswith("-")]
    cases = [c for c in read_cases() if not pick or any(p in c["case"] for p in pick)]
    rows = []
    for c in cases:
        r = judge(c)
        rows.append(r)
        print("  %-14s %-16s %s" % (r["case"], r["model"],
              r.get("miss") or "정 %s 측 %s 후 %s | 낙차 %s | 두께 %s | 붙음 %s"
              % (fmt(r.get("iou_front")), fmt(r.get("iou_side")), fmt(r.get("iou_back")),
                 fmt(r["gap"]), fmt(r["thickness"]), fmt(r["attached"]))))
    md = open(os.path.join(HERE, "board.md"), encoding="utf-8").read().split("<!-- 표 -->")[0]
    open(os.path.join(HERE, "board.md"), "w", encoding="utf-8").write(
        md + "<!-- 표 -->\n\n" + board(rows) + "\n")
    print("\nboard.md 다시 씀 — %d 줄" % len(rows))
