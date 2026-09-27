# -*- coding: utf-8 -*-
"""**나사 쿠폰** — PLA 관절을 틈이 아니라 나사로 조여 세운다 (2026-09-27).

09-26 관절 쿠폰 결과(사용자): 「설계는 고무로 한 건데 실제로는 플라스틱이니 잘 안 들어가고, 포징도 안 되고,
넣고 나면 힘이 없어 세우지 못하고, 핀은 너무 작아 안 들어간다」. PLA 는 안 휘므로 스냅 · 틈 마찰을 버리고
**나사 조임으로 마찰을 만든다**(헐거워지면 더 조인다). 사용자: 「당분간은 나사 같은 걸로」.

    python 나사쿠폰.py  ->  out/출력/나사쿠폰/*.stl · 나사쿠폰.png · 쿠폰.json · 슬라이스 견적

나사 = M2 (가정 — 다른 규격이면 나사 = 만 바꾼다).
  구멍판      자가태핑 밑구멍 Ø1.5~1.9 · 통과 구멍 Ø2.2~2.6 · 너트 자리(맞변 4.1~4.4) — 새김 = ×10 / ×100
  나사힌지 ×2 포크(너클 둘) + 혀(팔) — 나사가 너클을 혀 쪽으로 조인다(너클 틈 0.25 = 휠 몫).
              T = 둘째 너클에 밑구멍(나사가 PLA 에 탭) · N = 둘째 너클에 너트 자리
  클램프볼    반쪽 둘이 볼 Ø10 을 감싸고 나사 둘로 조인다. 가름면 틈 0.3 씩 = 멈춤(볼을 부수기 전에 면이 닿는다)
시험: 팔을 수평으로 세우고 거는 구멍(축에서 30 mm)에 31 g(500 원 4 개). 나사를 조여 가며 「버팀 · 손으로는 움직임」이 되는지."""
import json, os, sys
import numpy as np, manifold3d as M
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "실험_20260925"))
from 관절부품 import 상자, 원기둥z, 물방울x, 자세, 새김, 트, 칠, 겹침, 색, SEG
import 출력판

OUT = r"G:\art2real\원화3d\out\출력\나사쿠폰"
나사 = 2.0                                  # M2
통과 = 나사 + 0.4                           # 통과 구멍 Ø (구멍판 결과로 바꾼다)
밑구멍 = 1.7                                # 자가태핑 · 기계나사도 PLA 에 탭 된다 (구멍판 결과로 바꾼다)
너트맞변 = 4.0 + 0.2                        # M2 너트 맞변 4.0
너트두께 = 1.6 + 0.2
거는구멍 = 30.0


def 육각x(맞변, x0, x1):
    """x 방향 육각 기둥 · 꼭짓점 +y (눕힘 출력 때 천장 60°)."""
    R = 맞변 / np.sqrt(3); a = np.radians(90 + 60 * np.arange(6))
    cs = M.CrossSection([np.c_[R * np.cos(a), R * np.sin(a)]])
    return M.Manifold.extrude(cs, x1 - x0).rotate([0, 90, 0]).translate([x0, 0, 0])


# ─────────────── 구멍판 ───────────────
def 구멍판():
    줄 = [("T", [1.5, 1.6, 1.7, 1.8, 1.9], "밑"), ("C", [2.2, 2.3, 2.4, 2.6], "통"), ("N", [4.1, 4.2, 4.3, 4.4], "너트")]
    간격, 높 = 8.0, 8.0; 폭 = 10 + 5 * 간격; 깊 = 6 + len(줄) * 11
    판 = 상자(0, 폭, 0, 깊, 0, 높); 칼 = []; 글 = []
    for j, (머리, 값들, 종) in enumerate(줄):
        y = 깊 - 6 - j * 11
        for i, v in enumerate(값들):
            x = 12 + i * 간격
            if 종 == "너트":
                R = v / np.sqrt(3); a = np.radians(60 * np.arange(6))
                칼.append(M.Manifold.extrude(M.CrossSection([np.c_[R * np.cos(a), R * np.sin(a)]]), 너트두께 + 0.1).translate([x, y, 높 - 너트두께]))
                칼.append(원기둥z(통과 / 2, -1, 높 + 1).translate([x, y, 0]))
            else:
                칼.append(원기둥z(v / 2, 1.0 if 종 == "밑" else -1, 높 + 1).translate([x, y, 0]))    # 밑구멍은 막힘(깊이 7)
            글.append(("%d" % round(v * 10), x, y - 4.3))
        글.append((머리, 4.0, y))
    판 = 판 - M.Manifold.batch_boolean(칼, M.OpType.Add)
    for s, x, y in 글: 판 = 새김(판, s, 2.4, x, y)
    return 판


# ─────────────── 나사 힌지 ───────────────
def 나사힌지(종류="T", rk=4.5, a=2.4, b=5.0, g=0.25, L=10.0):
    """축 = x, 부모 −z · 자식 +z (관절부품 좌표). 반환 (부모, 자식)."""
    a2 = 4.0 if 종류 == "T" else a                     # 탭 쪽 너클은 두껍게 (나사산 물림 4 mm)
    x1, x2 = -b / 2 - g - a, b / 2 + g + a2
    둥근 = lambda x0, x1_: (원기둥z(rk, x0, x1_).rotate([0, 90, 0]) ^ 상자(x0, x1_, -rk, rk, 0, rk)) + 상자(x0, x1_, -rk, rk, -rk - L, 0)
    부모 = 둥근(x1, -b / 2 - g) + 둥근(b / 2 + g, x2) + 상자(x1, x2, -rk, rk, -rk - L, -rk - 0.5)
    부모 = 부모 - 물방울x(통과 / 2, x1 - 1, -b / 2 - g + 0.1)
    if 종류 == "T":
        부모 = 부모 - 물방울x(밑구멍 / 2, b / 2 + g - 0.1, x2 - 0.8)          # 막힌 밑구멍 (바깥 0.8 남김)
    else:
        부모 = 부모 - 물방울x(통과 / 2, b / 2 + g - 0.1, x2 + 1) - 육각x(너트맞변, x2 - 너트두께, x2 + 0.1)
    팔길이 = 거는구멍 + 4
    자식 = (원기둥z(rk, -b / 2, b / 2).rotate([0, 90, 0]) + 상자(-b / 2, b / 2, -rk, rk, 0, 팔길이)
          - 물방울x(통과 / 2, -b / 2 - 1, b / 2 + 1) - 원기둥z(1.6, -20, 20).rotate([90, 0, 0]).translate([0, 0, 거는구멍]))
    return 부모, 자식, dict(종류=종류, 나사길이=round(x2 - x1, 1), 너클틈=g, 탭물림=a2 - 0.8 if 종류 == "T" else None)


# ─────────────── 클램프 볼 ───────────────
def 클램프볼(D=10.0, c=0.1, s=0.3, T=6.4, 원뿔=70.0, 나사x=7.8):
    """볼 중심 = 원점, 목 = +z. 가름면 y = 0. 위 반쪽 y ≥ s (통과 구멍) · 아래 반쪽 y ≤ −s (밑구멍).
    조이면 반쪽이 s 만큼 다가올 때까지 볼을 (s − c) 누른다 → 면이 닿아 멈춤."""
    R = D / 2; Rc = R + c; zb, zt = -R - 2.4, 4.0; X = 나사x + 2.7
    속 = M.Manifold.sphere(Rc, SEG) + M.Manifold.cylinder(20, 0, 20 * np.tan(np.radians(원뿔)), SEG)     # 목 나가는 원뿔
    위 = 상자(-X, X, s, T, zb, zt) - 속
    아래 = 상자(-X, X, -T, -s, zb, zt) + 상자(-5, 5, -T, -s, zb - 10, zb + 0.1) - 속        # 아래 반쪽에 쥘 꼬리
    for sx in (-나사x, 나사x):
        위 = 위 - 원기둥z(통과 / 2, -20, 20).rotate([90, 0, 0]).translate([sx, 0, -1.0])
        아래 = 아래 - 원기둥z(밑구멍 / 2, 0, T - 0.8).rotate([90, 0, 0]).translate([sx, 0.1, -1.0])  # −y 로 T−0.8 깊이
    rn = 0.5 * R; 목끝 = zt + 5
    볼 = (M.Manifold.sphere(R, SEG) + 원기둥z(rn, 0, 목끝 + 0.5) + 상자(-3, 3, -rn, rn, 목끝, 목끝 + 거는구멍)
         - 원기둥z(1.6, -20, 20).rotate([90, 0, 0]).translate([0, 0, 거는구멍 + 4]))
    볼 = 볼 ^ 상자(-50, 50, -(R - 0.3), 50, -50, 100)                                       # 눕힘 바닥 평면 0.3
    흔들 = 0
    for 각 in range(5, 60, 5):
        if all(겹침(위 + 아래, 볼.rotate([각, 0, 0]).rotate([0, 0, q])) < 1e-3 for q in (0, 90, 180, 270)): 흔들 = 각
        else: break
    return 위, 아래, 볼, dict(볼지름=D, 볼틈=c, 가름틈=s, 누름최대=round(s - c, 2), 흔들=흔들, 나사길이="M2×10~12 (위 %.1f 통과 + 아래 물림 ≤ %.1f)" % (T - s, T - 0.8 - s))


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".stl"): os.remove(os.path.join(OUT, f))
    낼, 기록 = [], {"나사": "M2", "통과": 통과, "밑구멍": 밑구멍, "너트자리": [너트맞변, 너트두께]}
    낼.append(("구멍판", 구멍판()))
    조 = {}
    for k in ("T", "N"):
        부, 자, j = 나사힌지(k); 기록["힌지" + k] = j
        assert 겹침(부, 자) < 1e-3, "힌지 부모 · 자식 겹침"
        for 각 in (45, 90):
            assert 겹침(부, 자.rotate([각, 0, 0])) < 1e-3, "힌지 %d° 에서 걸림" % 각
        낼 += [("힌지%s_포크" % k, 새김(자세(부, "눕힘"), k, 3.0, 0, 9.75)), ("힌지%s_팔" % k, 자세(자, "눕힘"))]
        조["힌지" + k] = (부, 자)
    위, 아래, 볼, j = 클램프볼(); 기록["클램프볼"] = j
    assert 겹침(위 + 아래, 볼) < 1e-3 and j["흔들"] >= 20, j
    낼 += [("볼_위", 자세(위.rotate([180, 0, 0]), "눕힘")), ("볼_아래", 자세(아래, "눕힘")), ("볼_막대", 자세(볼, "눕힘"))]
    경로 = []
    for 이름, m in 낼:
        t = 트(m); assert t.is_watertight and t.is_volume, 이름
        p = os.path.join(OUT, 이름 + ".stl"); t.export(p); 경로.append(p)
        기록.setdefault("부품", {})[이름] = [round(float(v), 1) for v in t.extents]
    # 그림: 조립(팔 60°) · 분해
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.5))
    부, 자 = 조["힌지N"]
    칠(axs[0], [(트(부), 색["부모"]), (트(자.rotate([60, 0, 0])), 색["자식"])]); axs[0].set_title("나사 힌지 (N = 너트) · 팔 60°")
    칠(axs[1], [(트(위.translate([0, 8, 0])), 색["부모"]), (트(아래.translate([0, -8, 0])), 색["부모"]), (트(볼.rotate([25, 0, 0])), 색["자식"])], 방위=-30)
    axs[1].set_title("클램프 볼 (반쪽 벌림) · 흔들 %d°" % j["흔들"])
    칠(axs[2], [(트(m), 색["판"]) for 이름, m in 낼[:1]], 방위=0, 앙각=90, 높이색=True); axs[2].set_title("구멍판  T 밑구멍 · C 통과 · N 너트 (×10)")
    fig.suptitle("나사 쿠폰 — PLA 는 안 휜다: 마찰은 틈이 아니라 나사 조임으로", fontsize=14)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "나사쿠폰.png"), dpi=110); plt.close(fig)
    출력판.main("나사쿠폰", 경로, 눕히기=False)
    json.dump(기록, open(os.path.join(OUT, "쿠폰.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(기록, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
