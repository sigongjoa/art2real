# -*- coding: utf-8 -*-
"""**관절부품** — 오메가몬 PG 급(약 300 mm) 가동 키트의 관절 부품 생성기 + 관절 시험 쿠폰 (2026-09-25).

    python 관절부품.py        -> 규격 표 검사(닫힘 · 가동 범위 · 멈춤) + out/가동/관절부품.png
    python 관절부품.py 쿠폰   -> 위 + out/출력/관절쿠폰/*.stl · 쿠폰.json · 쿠폰.png · 슬라이스 견적

전부 PLA (A1 · 0.4 노즐 · 0.2 층). 틈 숫자는 모두 **한쪽(반지름) mm** 이고 쿠폰 전 가정값이다 → 기본틈 표만 고치면 된다.
조사: claudedocs/research_가동관절_20260925.md (FDM 힌지 0.15–0.30 · 볼 0.2–0.3 은 인쇄-그대로 값, 조립식은 쿠폰이 정한다).

관절 좌표 (모든 함수 공통)
  피벗 = 원점. 부모는 −z 쪽, 자식은 +z 쪽(곧게 편 자세). 힌지 축 = x. 굽힘 +θ = 자식 +z 가 −y 쪽으로 (X회전).
  결합: 관절 부품마다 **D 구멍**(D 면 = +y) 이 뼈 쪽으로 열려 있다. 뼈는 D 촉(구멍 − 2×결합틈)을 꽂는다.
출력 자세 (층 방향)
  눕힘 = −y 면을 바닥으로 (X 축 +90°). 힌지 너클 · 볼 목을 눕혀 층이 뼈 방향을 따라 쌓인다 → 굽힘에 층이 안 갈라진다.
         핀 구멍은 가로 → 물방울(뾰족 끝 +y = 위) · D 구멍은 D 면이 천장(다리 놓기).
  세움 = 그대로 (소켓 입구 위 · 회전축 받이 구멍 위). 소켓 안쪽 윗부분은 수직에서 35° 안쪽 걸침이라 서포트 없이 된다.
  뒤집음 = X 180° (회전축 자식: 받침 바닥, 축이 위). 축 Ø5 는 층을 가로지른다 — 비틀기만 받는 자리라서 허용.
PLA 대책: C 자 소켓(입구 0.85D) + 슬릿(손가락이 벌어져 끼워짐, 부러지면 소켓만 다시 뽑는다) · 볼 목 눕혀 출력 ·
  힌지 핀은 부모에 압입(부모틈), 자식이 핀 위에서 돈다(자식틈) · 크리프로 풀리면 핀(필라멘트)만 굵은 것/새 것으로 바꾼다."""
import json, os, subprocess, sys
import numpy as np, trimesh, manifold3d as M

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 공차쿠폰 import 글자, BBL, ORCA        # 글자 윤곽 · 슬라이서 경로 재사용

SEG = 72
결합틈 = 0.20                 # 뼈 D 촉 한쪽 (공차쿠폰 결과로 바꾼다)
기본틈 = {"볼": 0.10, "힌지자식": 0.10, "힌지부모": 0.00, "회전축": 0.10}   # 쿠폰 전 가정
벽 = 2.4                      # 6 줄

# 이름 → (종류, 매개변수).  PG 300 mm ≈ HG 125 mm × 2.4.
규격 = {
    "볼10":        ("볼소켓", dict(D=10.0, 결합지름=5.0)),     # 목 · 손목 · 발목
    "볼12":        ("볼소켓", dict(D=12.0, 결합지름=6.0)),     # 고관절 · 어깨
    "힌지3":       ("힌지", dict(핀=3.0)),                      # 출력 핀 Ø3
    "힌지1.75":    ("힌지", dict(핀=1.75)),                     # 필라멘트 핀
    "이중힌지3":   ("이중힌지", dict(핀=3.0)),                  # 팔꿈치 · 무릎
    "이중힌지1.75": ("이중힌지", dict(핀=1.75)),
    "회전축5":     ("회전축", dict(d=5.0)),                     # 손목 비틀기 · 허벅지 비틀기
    "회전축8":     ("회전축", dict(d=8.0, 결합지름=6.0)),       # 허리
}


# ─────────────── 기하 도구 ───────────────
def 상자(x0, x1, y0, y1, z0, z1):
    return M.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def 원기둥z(r, z0, z1, r1=None):
    return M.Manifold.cylinder(z1 - z0, r, r if r1 is None else r1, SEG).translate([0, 0, z0])


def 원기둥x(r, x0, x1, y=0.0, z=0.0):
    return M.Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, y, z])


def 물방울x(r, x0, x1, z=0.0):
    """x 방향 가로 구멍. 뾰족 끝 +y (눕힘 출력 때 위) → 천장 45°."""
    s = r / np.sqrt(2)
    cs = M.CrossSection.circle(r, SEG) + M.CrossSection([np.array([[0, 0], [s, s], [0, r * np.sqrt(2)], [-s, s]])], M.FillRule.EvenOdd)
    m = M.Manifold.extrude(cs, x1 - x0).rotate([0, 90, 0])
    b = m.bounding_box(); return m.translate([x0 - b[0], 0, z])


def D구멍z(지름, z0, z1, 컷=None):
    """z 방향 D 구멍 (D 면 = +y). 뼈 촉 돌기 방지."""
    r = 지름 / 2; 컷 = 0.15 * 지름 if 컷 is None else 컷
    cs = M.CrossSection.circle(r, SEG) ^ M.CrossSection.square([2 * r, 2 * r - 컷]).translate([-r, -r])
    return M.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def X회전(m, 각, 축z=0.0):
    return m.translate([0, 0, -축z]).rotate([각, 0, 0]).translate([0, 0, 축z])


def 겹침(a, b):
    return (a ^ b).volume()


def 결합정보(지름, 깊이, 입구, 방향):
    return {"구멍지름": 지름, "D컷": round(0.15 * 지름, 2), "깊이": 깊이, "입구xyz": [round(v, 2) for v in 입구], "방향": 방향,
            "뼈촉지름": round(지름 - 2 * 결합틈, 2), "뼈촉D면(축에서 +y)": round(지름 / 2 - 0.15 * 지름 - 결합틈, 2)}


def 트(m):
    g = m.to_mesh(); t = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
    return t


def 자세(m, 방식):
    """출력 자세로 돌려 바닥 z=0."""
    if 방식 == "눕힘": m = m.rotate([90, 0, 0])          # −y → −z
    elif 방식 == "뒤집음": m = m.rotate([180, 0, 0])
    b = m.bounding_box(); return m.translate([0, 0, -b[2]])


# ─────────────── 볼 소켓 ───────────────
def 볼소켓(D=10.0, 틈=None, 입구=0.85, 목비=0.5, 슬릿=3, 슬릿폭=1.0, 평면=0.3, 결합지름=5.0, 깊이=6.0, 결합=True):
    """부모 = C 자 소켓 (입구 위 · 세움 출력). 자식 = 볼 + 목 + 깃 (눕힘 출력: 볼 옆 평면 0.3 이 바닥, 목은 다리 놓기).
    가동 = 입구 원뿔 반각 β − 목 반각 (전방향) · 비틀기 360°. 슬릿 = 입구에서 적도 아래까지 세로 틈 → 손가락이 벌어져 끼움."""
    틈 = 기본틈["볼"] if 틈 is None else 틈
    R = D / 2; Rin = R + 틈; Ro = Rin + 벽; rn = 목비 * D / 2
    β = np.degrees(np.arcsin(입구 * D / 2 / Rin))
    바닥 = -Rin - 1.2 - (깊이 if 결합 else 0.0); 바닥 = min(바닥, -Ro)
    몸 = (M.Manifold.sphere(Ro, SEG) + 원기둥z(Ro, 바닥, 0)) ^ 상자(-Ro - 1, Ro + 1, -Ro - 1, Ro + 1, 바닥, Ro + 1)
    h = Ro + 2; 원뿔 = M.Manifold.cylinder(h, 0, h * np.tan(np.radians(β)), SEG)
    칼 = [M.Manifold.sphere(Rin, SEG), 원뿔]
    for k in range(슬릿):
        칼.append(상자(0, Ro + 1, -슬릿폭 / 2, 슬릿폭 / 2, -0.2 * Rin, Ro + 1).rotate([0, 0, 90 + 360 * k / 슬릿]))
    if 결합: 칼.append(D구멍z(결합지름, 바닥 - 0.1, 바닥 + 깊이))
    소켓 = 몸 - M.Manifold.batch_boolean(칼, M.OpType.Add)
    # 볼: 깃은 소켓 바깥에서 시작, 최대 흔들림에서 깃이 소켓에 안 닿을 때까지 민다
    Rc = max(R - 평면, 결합지름 / 2 + 1.2); 깃길이 = (깊이 + 1.2) if 결합 else 4.0
    흔들 = β - np.degrees(np.arcsin(rn / Rin))
    for zc in np.arange(Ro * np.cos(np.radians(β)) + 1.0, Ro + 8, 0.5):
        볼 = M.Manifold.sphere(R, SEG) + 원기둥z(rn, 0, zc + 0.5) + 원기둥z(Rc, zc, zc + 깃길이)
        볼 = 볼 ^ 상자(-Ro, Ro, -(R - 평면), Ro, -Ro, zc + 깃길이 + 1)
        if 결합: 볼 = 볼 - D구멍z(결합지름, zc + 깃길이 - 깊이, zc + 깃길이 + 0.1)
        if all(겹침(소켓, X회전(볼, 흔들 - 1).rotate([0, 0, a])) < 1e-3 for a in (0, 90, 180, 270)):
            break
    return {"종류": "볼소켓", "부모": 소켓, "자식": 볼, "자세": {"부모": "세움", "자식": "눕힘"},
            "외피반지름": round(Ro, 2), "틈": 틈, "가동": {"흔들(전방향)": round(float(흔들), 1), "비틀기": 360},
            "치수": {"볼지름": D, "목지름": round(2 * rn, 2), "입구지름": round(입구 * D, 2), "소켓벽": 벽, "슬릿": 슬릿, "원뿔반각": round(float(β), 1), "볼평면": 평면},
            "결합": {"부모": 결합정보(결합지름, 깊이, (0, 0, 바닥), "+z"), "자식": 결합정보(결합지름, 깊이, (0, 0, zc + 깃길이), "−z")} if 결합 else None,
            "_검사": ("볼", 흔들)}


# ─────────────── 힌지 ───────────────
def _너클치수(핀, a, b, g):
    rk = 핀 / 2 + 벽; W = 2 * a + b + 2 * g; return rk, W


def _혀(rk, b, z1):
    """x 폭 b · 축에서 +z 로 z1 까지 · 끝 둥근 너클."""
    return 원기둥x(rk, -b / 2, b / 2) + 상자(-b / 2, b / 2, -rk, rk, 0, z1)


def _포크(rk, W, b, g, cr, t, Lp, 혀길이, 가동):
    """부모 포크: 바깥 너클 둘 + 몸(−z) + 멈춤 벽(+y, t 두께). 가운데 홈 = 너클 틈 원 ∪ 틈만큼 부푼 혀를 가동 범위로 쓸어낸 부피.
    쓸어내고 남은 곳이 곧 멈춤 턱 (Calì 2012 식 쓸린 부피 빼기)."""
    몸 = 원기둥x(rk, -W / 2, W / 2) + 상자(-W / 2, W / 2, -rk, rk, -Lp, 0) + 상자(-W / 2, W / 2, 0, rk + t, -Lp, rk)
    혀c = _혀(rk + cr, b + 2 * g, 혀길이)
    각 = list(np.arange(가동[0], 가동[1], 2.0)) + [가동[1]]
    홈 = M.Manifold.batch_boolean([원기둥x(rk + cr, -(b / 2 + g), b / 2 + g)] + [X회전(혀c, a) for a in 각], M.OpType.Add)
    return 몸 - 홈


def 힌지(핀=3.0, 틈=None, 부모틈=None, a=3.5, b=4.0, g=0.3, cr=0.3, t=1.5, 가동=(0.0, 90.0), 결합지름=None, 깊이=6.0, 결합=True):
    """부모 = 포크(너클 2) · 자식 = 혀(너클 1) + 깃. 핀은 부모 구멍에 압입(부모틈), 자식 구멍에서 돈다(자식틈).
    핀 = 1.75 이면 필라멘트 토막을 꽂고, 아니면 `핀` 부품(눕힘 · 아래 D 면 0.3)을 함께 돌려준다. 둘 다 눕힘 출력."""
    틈 = 기본틈["힌지자식"] if 틈 is None else 틈; 부모틈 = 기본틈["힌지부모"] if 부모틈 is None else 부모틈
    rk, W = _너클치수(핀, a, b, g)
    결합지름 = 결합지름 or np.floor((2 * rk - 2.4) * 2) / 2
    Lp = 깊이 + rk + cr + 1.2
    부모 = _포크(rk, W, b, g, cr, t, Lp, rk + 60, 가동) - 물방울x(핀 / 2 + 부모틈, -W / 2 - 1, W / 2 + 1)
    if 결합: 부모 = 부모 - D구멍z(결합지름, -Lp - 0.1, -Lp + 깊이)
    Lc = (깊이 + 1.2) if 결합 else 4.0
    for zw in np.arange(rk + cr + 0.5, rk + 20, 0.5):     # 깃(넓은 부분)이 최대 굽힘에서 부모에 안 닿는 가장 짧은 혀
        자식 = _혀(rk, b, zw + 0.5) + 상자(-W / 2, W / 2, -rk, rk, zw, zw + Lc) - 물방울x(핀 / 2 + 틈, -W / 2 - 1, W / 2 + 1)
        if 결합: 자식 = 자식 - D구멍z(결합지름, zw + Lc - 깊이, zw + Lc + 0.1)
        if 겹침(부모, X회전(자식, 가동[1])) < 1e-3 and 겹침(부모, X회전(자식, 가동[0])) < 1e-3: break
    j = {"종류": "힌지", "부모": 부모, "자식": 자식, "자세": {"부모": "눕힘", "자식": "눕힘"},
         "외피반지름": round(float(np.hypot(rk + t, rk)), 2), "틈": {"자식": 틈, "부모(압입)": 부모틈, "너클 축방향": g, "너클 반지름": cr},
         "가동": {"굽힘": list(가동)},
         "치수": {"핀": 핀, "핀종류": "필라멘트" if abs(핀 - 1.75) < 1e-6 else "출력", "너클지름": round(2 * rk, 2), "폭W": W, "바깥너클폭": a, "가운데너클폭": b, "멈춤벽": t},
         "결합": {"부모": 결합정보(결합지름, 깊이, (0, 0, -Lp), "+z"), "자식": 결합정보(결합지름, 깊이, (0, 0, zw + Lc), "−z")} if 결합 else None,
         "_검사": ("힌지", [가동])}
    if j["치수"]["핀종류"] == "출력":
        j["핀"] = 출력핀(핀, W + 1.0); j["자세"]["핀"] = "눕힘"
    return j


def 출력핀(d, 길이, 평면=0.3):
    """x 방향 핀, −y 에 D 면(바닥) · 양끝 모따기 0.3."""
    r = d / 2
    m = M.Manifold.cylinder(길이, r, r, SEG).translate([0, 0, 0])
    m = m ^ (M.Manifold.cylinder(0.3, r - 0.3, r, SEG) + M.Manifold.cylinder(길이 - 0.6, r, r, SEG).translate([0, 0, 0.3])
             + M.Manifold.cylinder(0.3, r, r - 0.3, SEG).translate([0, 0, 길이 - 0.3]))
    m = m.rotate([0, 90, 0]); b = m.bounding_box(); m = m.translate([-b[0] - 길이 / 2, 0, 0])
    return m ^ 상자(-길이, 길이, -r + 평면, r + 1, -r - 1, r + 1)


def 이중힌지(핀=3.0, 틈=None, 부모틈=None, a=3.5, b=4.0, g=0.3, cr=0.3, t=1.5, 가동=((0.0, 80.0), (0.0, 80.0)), 결합지름=None, 깊이=6.0, 결합=True):
    """부모 포크(축1, z=0) – 링크(혀 둘) – 자식 포크(축2, z=s, 부모 포크를 z 로 뒤집은 것). 합 가동 = 가동1 + 가동2.
    축 사이 s 는 두 포크가 최대 굽힘에서 안 닿는 가장 짧은 값."""
    틈 = 기본틈["힌지자식"] if 틈 is None else 틈; 부모틈 = 기본틈["힌지부모"] if 부모틈 is None else 부모틈
    rk, W = _너클치수(핀, a, b, g)
    결합지름 = 결합지름 or np.floor((2 * rk - 2.4) * 2) / 2
    Lp = 깊이 + rk + cr + 1.2
    구멍p = 물방울x(핀 / 2 + 부모틈, -W / 2 - 1, W / 2 + 1)
    for s in np.arange(2 * (rk + t) + 1.0, 4 * rk + 20, 0.5):
        혀길이 = s + rk + cr + 1
        부모 = _포크(rk, W, b, g, cr, t, Lp, 혀길이, 가동[0]) - 구멍p
        자식 = (_포크(rk, W, b, g, cr, t, Lp, 혀길이, 가동[1]) - 구멍p).mirror([0, 0, 1]).translate([0, 0, s])
        if 결합:
            부모 = 부모 - D구멍z(결합지름, -Lp - 0.1, -Lp + 깊이)
            자식 = 자식 - D구멍z(결합지름, s + Lp - 깊이, s + Lp + 0.1)
        링크 = (원기둥x(rk, -b / 2, b / 2) + 상자(-b / 2, b / 2, -rk, rk, 0, s) + 원기둥x(rk, -b / 2, b / 2, z=s)
               - 물방울x(핀 / 2 + 틈, -b / 2 - 1, b / 2 + 1) - 물방울x(핀 / 2 + 틈, -b / 2 - 1, b / 2 + 1, z=s))
        끝 = X회전(X회전(자식, 가동[1][1], s), 가동[0][1])
        if 겹침(부모, 끝) < 1e-3: break
    j = {"종류": "이중힌지", "부모": 부모, "링크": 링크, "자식": 자식, "자세": {"부모": "눕힘", "링크": "눕힘", "자식": "눕힘"},
         "외피반지름": round(float(np.hypot(rk + t, rk)), 2), "틈": {"자식(링크)": 틈, "부모(압입)": 부모틈, "너클 축방향": g, "너클 반지름": cr},
         "가동": {"굽힘1": list(가동[0]), "굽힘2": list(가동[1]), "합": 가동[0][1] + 가동[1][1]},
         "치수": {"핀": 핀, "핀종류": "필라멘트" if abs(핀 - 1.75) < 1e-6 else "출력", "너클지름": round(2 * rk, 2), "폭W": W, "축사이": float(s)},
         "결합": {"부모": 결합정보(결합지름, 깊이, (0, 0, -Lp), "+z"), "자식": 결합정보(결합지름, 깊이, (0, 0, s + Lp), "−z")} if 결합 else None,
         "_검사": ("이중힌지", [가동[0], 가동[1], s])}
    if j["치수"]["핀종류"] == "출력":
        j["핀"] = 출력핀(핀, W + 1.0); j["핀2"] = 출력핀(핀, W + 1.0); j["자세"].update({"핀": "눕힘", "핀2": "눕힘"})
    return j


# ─────────────── 회전축 (스냅) ───────────────
def _마름모고리(r0, e, zc, 반높이):
    """반지름 r0 에서 e 만큼 튀어나온 45° 마름모 고리 (z 축 둘레)."""
    cs = M.CrossSection([np.array([[r0 - 0.01, zc - 반높이], [r0 + e, zc - 반높이 + e], [r0 + e, zc + 반높이 - e], [r0 - 0.01, zc + 반높이]])], M.FillRule.EvenOdd)
    return M.Manifold.revolve(cs, SEG)


def 회전축(d=5.0, 틈=None, 걸림=0.4, Ls=7.0, 슬릿폭=1.0, 축틈=0.2, 결합지름=5.0, 깊이=6.0, 결합=True):
    """자식 = 깃 + 축(−z 로 Ls) · 축 끝 근처 마름모 턱(걸림) · 끝에서 0.7 Ls 까지 슬릿 → 턱이 오므라들며 받이 홈에 딸깍.
    부모 = 받이 원통 · 구멍 d + 2틈 · 같은 높이에 홈(턱 + 틈). 비틀기 360°, 빠짐은 턱이 막는다. 틈 < 0 이면 슬릿 축이 조여 마찰."""
    틈 = 기본틈["회전축"] if 틈 is None else 틈
    rs = d / 2; Rb = rs + max(틈, 0) + 벽; 깃높이 = (깊이 + 1.2) if 결합 else 2.5
    z턱 = -Ls + 1.2 + 걸림
    자식 = 원기둥z(Rb, 0, 깃높이) + 원기둥z(rs - 0.4, -Ls, -Ls + 0.4, rs) + 원기둥z(rs, -Ls + 0.4, 0.01) + _마름모고리(rs, 걸림, z턱, 걸림 + 0.3)
    자식 = 자식 - 상자(-슬릿폭 / 2, 슬릿폭 / 2, -rs - 1, rs + 1, -Ls - 1, -Ls + 0.7 * Ls)
    if 결합: 자식 = 자식 - D구멍z(결합지름, 깃높이 - 깊이, 깃높이 + 0.1)
    바닥 = -Ls - 0.5 - 1.2 - (깊이 if 결합 else 0.0)
    부모 = 원기둥z(Rb, 바닥, -축틈)
    부모 = 부모 - (원기둥z(rs + 틈, -Ls - 0.5, 1) + 원기둥z(rs + 틈, -축틈 - 0.4, -축틈 + 0.01, rs + 틈 + 0.4)
                  + _마름모고리(rs + 틈 - 0.01, 걸림 + 틈 + 0.01, z턱, 걸림 + 0.3 + 틈))
    if 결합: 부모 = 부모 - D구멍z(결합지름, 바닥 - 0.1, 바닥 + 깊이)
    return {"종류": "회전축", "부모": 부모, "자식": 자식, "자세": {"부모": "세움", "자식": "뒤집음"},
            "외피반지름": round(Rb, 2), "틈": 틈, "가동": {"비틀기": 360},
            "치수": {"축지름": d, "축길이": Ls, "걸림": 걸림, "슬릿폭": 슬릿폭, "받이지름": round(2 * Rb, 2), "축방향틈": 축틈},
            "결합": {"부모": 결합정보(결합지름, 깊이, (0, 0, 바닥), "+z"), "자식": 결합정보(결합지름, 깊이, (0, 0, 깃높이), "−z")} if 결합 else None,
            "_검사": ("회전축", 걸림)}


함수 = {"볼소켓": 볼소켓, "힌지": 힌지, "이중힌지": 이중힌지, "회전축": 회전축}


def 만들기(이름, **덮어쓰기):
    종류, p = 규격[이름]; return 함수[종류](**{**p, **덮어쓰기})


def 부품들(j):
    return {k: j[k] for k in ("부모", "링크", "자식", "핀", "핀2") if k in j}


# ─────────────── 검사 (문턱은 질 수 있어야 한다) ───────────────
def 검사(j):
    """닫힘 · 곧은 자세 겹침 0 · 범위 안 겹침 0 · 범위 밖 6° 에서 겹침 > 0 (멈춤이 실제로 막는다)."""
    for k, m in 부품들(j).items():
        t = 트(m); assert t.is_watertight and t.is_volume and m.genus() >= 0, (j["종류"], k, "닫히지 않음")
    P, C = j["부모"], j["자식"]; 종, 값 = j["_검사"]; 결과 = {}
    if 종 == "볼":
        안 = max(겹침(P, X회전(C, 값 - 2).rotate([0, 0, a])) for a in (0, 45, 90, 180, 270))
        밖 = min(겹침(P, X회전(C, 값 + 5).rotate([0, 0, a])) for a in (0, 90, 180, 270))
        결과 = {"곧음": 겹침(P, C), "흔들-2°": 안, "흔들+5°": 밖}
        assert 결과["곧음"] < 1e-3 and 안 < 1e-3 and 밖 > 1e-3, 결과
        R = j["치수"]["볼지름"] / 2; assert j["치수"]["입구지름"] < 2 * R    # 볼이 입구보다 커야 안 빠진다
    elif 종 == "힌지":
        (a0, a1), = 값
        안 = max(겹침(P, X회전(C, a)) for a in np.linspace(a0, a1, 10))
        결과 = {"범위안": 안, "위멈춤°": 멈춤각(lambda a: 겹침(P, X회전(C, a)), a1, +1), "아래멈춤°": 멈춤각(lambda a: 겹침(P, X회전(C, a)), a0, -1)}
        assert 안 < 1e-3 and 결과["위멈춤°"] and 결과["아래멈춤°"], 결과
    elif 종 == "이중힌지":
        g1, g2, s = 값; L = j["링크"]
        안 = 0.0
        for a in np.linspace(*g1, 5):
            for b in np.linspace(*g2, 5):
                Lr = X회전(L, a); Cr = X회전(X회전(C, b, s), a)
                안 = max(안, 겹침(P, Lr), 겹침(Cr, Lr), 겹침(P, Cr))
        결과 = {"범위안": 안, "1위멈춤°": 멈춤각(lambda a: 겹침(P, X회전(L, a)), g1[1], +1), "1아래멈춤°": 멈춤각(lambda a: 겹침(P, X회전(L, a)), g1[0], -1),
              "2위멈춤°": 멈춤각(lambda a: 겹침(L, X회전(C, a, s)), g2[1], +1), "2아래멈춤°": 멈춤각(lambda a: 겹침(L, X회전(C, a, s)), g2[0], -1)}
        assert 안 < 1e-3 and all(v for k, v in 결과.items() if k != "범위안"), 결과
    elif 종 == "회전축":
        결과 = {"곧음": 겹침(P, C), "비틀기45°": 겹침(P, C.rotate([0, 0, 45]))}
        # 턱이 받이 입구보다 크다 = 슬릿이 오므라들어야 들어간다 = 빠지지 않는다
        결과["걸림-틈"] = j["치수"]["걸림"] - j["틈"]
        결과["1mm 뽑음"] = 겹침(P, C.translate([0, 0, 1.0]))            # 턱이 홈 윗면에 걸려야 > 0
        assert 결과["곧음"] < 1e-3 and 결과["비틀기45°"] < 1e-3 and 결과["걸림-틈"] > 0 and 결과["1mm 뽑음"] > 1e-3, 결과
    return {k: round(float(v), 3) for k, v in 결과.items()}


def 멈춤각(f, 끝, 방향, 한=12):
    """설계 끝각에서 1° 씩 더 돌려 처음 닿는 각 (놀이 = 틈 탓). 한° 안에 안 닿으면 None → 멈춤 없음."""
    for d in range(1, 한 + 1):
        if f(끝 + 방향 * d) > 1e-3: return 끝 + 방향 * d
    return None


def 표(j):
    return {k: v for k, v in j.items() if k not in ("부모", "링크", "자식", "핀", "핀2", "_검사")}


# ─────────────── 그림 (칠하기 순서 투영) ───────────────
색 = {"부모": (0.45, 0.55, 0.70), "자식": (0.93, 0.55, 0.25), "링크": (0.40, 0.70, 0.45), "핀": (0.85, 0.25, 0.25), "핀2": (0.85, 0.25, 0.25), "판": (0.70, 0.70, 0.72)}


def 칠(ax, 목록, 방위=-50, 앙각=25, 높이색=False):
    """목록 = [(trimesh, rgb)]. 정사영 · 뒤에서 앞으로 칠한다."""
    from matplotlib.collections import PolyCollection
    az, el = np.radians(방위), np.radians(앙각)
    Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.sin(el), np.cos(el)], [0, -np.cos(el), np.sin(el)]])   # 눈 = −y 쪽 위
    V = Rx @ Rz; 빛 = np.array([0.3, -0.5, 0.8]); 빛 /= np.linalg.norm(빛)
    폴, 색들, 깊 = [], [], []
    zs = np.concatenate([t.vertices[:, 2] for t, _ in 목록]); z0, z1 = zs.min(), zs.max() + 1e-9
    for t, c in 목록:
        P = t.vertices @ V.T; F = t.faces; n = t.face_normals @ V.T
        보임 = n[:, 2] > -0.05 if not 높이색 else np.ones(len(F), bool)
        밝 = 0.35 + 0.65 * np.clip(n[보임] @ 빛, 0, 1)
        cc = np.array(c)[None] * 밝[:, None]
        if 높이색:
            h = (t.vertices[F[보임]].mean(1)[:, 2] - z0) / (z1 - z0); cc = cc * (0.55 + 0.45 * h[:, None])
        폴.append(P[F[보임]][:, :, :2]); 색들.append(np.clip(cc, 0, 1)); 깊.append(P[F[보임]].mean(1)[:, 2])
    폴, 색들, 깊 = np.concatenate(폴), np.concatenate(색들), np.concatenate(깊)
    o = np.argsort(깊)
    ax.add_collection(PolyCollection(폴[o], facecolors=색들[o], edgecolors=색들[o], linewidths=0.2))
    xy = 폴.reshape(-1, 2); ax.set_xlim(xy[:, 0].min() - 2, xy[:, 0].max() + 2); ax.set_ylim(xy[:, 1].min() - 2, xy[:, 1].max() + 2)
    ax.set_aspect("equal"); ax.axis("off")


def 부품그림(경로):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
    보기 = [("볼12", 20), ("힌지3", 60), ("이중힌지3", (50, 50)), ("회전축5", 0)]
    fig, axs = plt.subplots(len(보기), 3, figsize=(15, 5 * len(보기)))
    for i, (이름, 각) in enumerate(보기):
        j = 만들기(이름); 조 = {}
        for k, m in 부품들(j).items():
            if j["종류"] == "이중힌지":
                s = j["치수"]["축사이"]
                m = {"링크": X회전(m, 각[0]), "자식": X회전(X회전(m, 각[1], s), 각[0])}.get(k, m)
            elif k == "자식" and j["종류"] in ("볼소켓", "힌지"): m = X회전(m, 각)
            if k == "핀" and j["종류"] == "이중힌지": pass
            if k == "핀2": m = X회전(m.translate([0, 0, j["치수"]["축사이"]]), 각[0])
            조[k] = m
        단 = {k: m ^ 상자(-100, 0, -100, 100, -100, 100) for k, m in 조.items()}
        벌림 = {"부모": [0, 0, -12], "자식": [0, 0, 14], "링크": [0, 0, 2], "핀": [-18, 0, 0], "핀2": [18, 0, 0]}
        분 = {k: m.translate(벌림[k]) for k, m in 부품들(j).items()}
        if "핀2" in 분: 분["핀2"] = 부품들(j)["핀2"].translate([18, 0, j["치수"]["축사이"]])
        for c, (제목, 모음, 방위) in enumerate((("조립", 조, -50), ("단면 (x<0 반)", 단, -90), ("분해", 분, -50))):
            칠(axs[i, c], [(트(m), 색[k]) for k, m in 모음.items() if not m.is_empty()], 방위=방위)
            axs[i, c].set_title("%s · %s" % (이름, 제목), fontsize=12)
        g = j["가동"]; axs[i, 0].text(0.0, -0.02, "외피 R %.1f · 가동 %s" % (j["외피반지름"], g), transform=axs[i, 0].transAxes, fontsize=9, va="top")
    fig.suptitle("관절 부품 (PG 300mm · PLA) — 파랑 부모 · 주황 자식 · 초록 링크 · 빨강 출력 핀", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.975]); fig.savefig(경로, dpi=110); plt.close(fig)


# ─────────────── 쿠폰 ───────────────
OUT = r"G:\art2real\원화3d\out\출력\관절쿠폰"
힌지틈들 = [-0.05, 0.0, 0.05, 0.10, 0.15, 0.20]
볼틈들 = [0.0, 0.05, 0.10, 0.15, 0.20]
축칸 = [(e, c) for e in (0.3, 0.5) for c in (0.0, 0.10, 0.20)]
팔길이, 거는구멍 = 34.0, 30.0          # 축에서 매다는 구멍까지 30 mm


def 새김(m, s, 높이, cx, cy, 깊이=0.4, top=None):
    """출력 자세 메시 윗면(z 최대)에 글자를 판다."""
    p = 글자(s, 높이, (cx, cy)); polys = list(p.geoms) if hasattr(p, "geoms") else [p]
    링 = []
    for q in polys:
        링.append(np.asarray(q.exterior.coords)[:-1]); 링 += [np.asarray(r.coords)[:-1] for r in q.interiors]
    칼 = M.Manifold.extrude(M.CrossSection(링, M.FillRule.EvenOdd), 깊이 + 0.5)
    top = m.bounding_box()[5] if top is None else top
    return m - 칼.translate([0, 0, top - 깊이])


def 라벨(c):
    return "%d" % round(c * 100)


def 쿠폰부품():
    """[(이름, 출력자세 manifold)]"""
    낼 = []
    # 1. 힌지: 필라멘트 1.75 · 출력 3.0 × 자식틈 6 칸. 부모 포크 6 개를 막대로 이은 빗 + 팔 6 + (출력) 핀 8
    for 핀 in (1.75, 3.0):
        js = [힌지(핀, 틈=c, 부모틈=0.0, 결합=False) for c in 힌지틈들]
        rk, W = _너클치수(핀, 3.5, 4.0, 0.3); Lp = js[0]["치수"] and (6.0 + rk + 0.3 + 1.2); 간격 = W + 4
        빗 = [j["부모"].translate([i * 간격, 0, 0]) for i, j in enumerate(js)]
        빗.append(상자(-W / 2, (len(js) - 1) * 간격 + W / 2, -rk, rk + 1.5, -Lp - 6, -Lp + 0.5))
        m = 자세(M.Manifold.batch_boolean(빗, M.OpType.Add), "눕힘")      # (x, y, z) → (x, −z, y)
        for i, c in enumerate(힌지틈들):
            m = 새김(m, 라벨(c), 2.6, i * 간격, (Lp + rk + 0.3) / 2 + 0.3)
        m = 새김(m, "F1.75" if 핀 < 2 else "P3.0", 3.0, (len(js) - 1) * 간격 / 2, Lp + 3)
        낼.append(("힌지빗_%s" % ("F175" if 핀 < 2 else "P30"), m))
        for i, (c, j) in enumerate(zip(힌지틈들, js)):
            zw = j["자식"].bounding_box()[5]
            팔 = j["자식"] + 상자(-3.5, 3.5, -rk, rk, zw - 1, 팔길이) - 원기둥z(1.6, -20, 20).rotate([90, 0, 0]).translate([0, 0, 거는구멍])
            팔 = 자세(팔, "눕힘")
            팔 = 새김(팔, 라벨(c), 3.0, 0, -(zw + 거는구멍) / 2 - 1)
            낼.append(("힌지팔_%s_%s" % ("F175" if 핀 < 2 else "P30", 라벨(c)), 팔))
        if 핀 > 2:
            for k in range(len(힌지틈들) + 2):
                낼.append(("핀3_%d" % k, 자세(출력핀(3.0, W + 1.0), "눕힘")))
    # 2. 볼 소켓: Ø10 · Ø12 × 틈 5 × 슬릿 3/0 → 소켓판 하나 + 볼 막대 20
    칸 = [(D, sl, c) for D in (10.0, 12.0) for sl in (3, 0) for c in 볼틈들]
    피치x, 피치y = 21.0, 25.0; 소 = []
    for n, (D, sl, c) in enumerate(칸):
        r, k = divmod(n, len(볼틈들))
        j = 볼소켓(D, 틈=c, 슬릿=sl, 결합=False); b = j["부모"].bounding_box()
        소.append(j["부모"].translate([k * 피치x, -r * 피치y, -b[2]]))
    판 = 상자(-13, (len(볼틈들) - 1) * 피치x + 10, -(len(칸) // len(볼틈들) - 1) * 피치y - 16, 10, 0, 1.2)
    m = 자세(M.Manifold.batch_boolean(소 + [판], M.OpType.Add), "세움")
    for n, (D, sl, c) in enumerate(칸):
        r, k = divmod(n, len(볼틈들))
        m = m - 새김판(라벨(c), 3.0, k * 피치x, -r * 피치y - 11.2, 1.2, 깊이=0.6)
    for r in range(len(칸) // len(볼틈들)):
        D, sl, _ = 칸[r * len(볼틈들)]
        m = m - 새김판("%d%s" % (D, "S" if sl else ""), 3.0, -8.5, -r * 피치y + 7.0, 1.2, 깊이=0.6)
    낼.append(("볼소켓판", m))
    for D in (10.0, 12.0):     # 크기마다 5 개: 슬릿 줄을 먼저 시험, 살아남는 줄에 꽂아 하루 둔다
        j = 볼소켓(D, 결합=False); R = D / 2; 바닥y = -(R - 0.3); zc = j["자식"].bounding_box()[5]
        for k in range(len(볼틈들)):
            팔 = j["자식"] + 상자(-3.0, 3.0, 바닥y, 바닥y + 4.0, zc - 2, 팔길이 + 4) - 원기둥z(1.6, -20, 20).rotate([90, 0, 0]).translate([0, 0, 거는구멍 + 4])
            팔 = 자세(팔, "눕힘"); 팔 = 새김(팔, "%d" % D, 3.0, 0, -(zc + 거는구멍) / 2 - 2, top=4.0)
            낼.append(("볼막대%d_%d" % (D, k), 팔))
    # 3. 회전축 스냅: 걸림 0.3 · 0.5 × 틈 0 · 0.1 · 0.2 → 받이판 + 축 6 (손잡이 달림)
    받 = []; 피치 = 20.0
    for i, (e, c) in enumerate(축칸):
        j = 회전축(5.0, 틈=c, 걸림=e, 결합=False); b = j["부모"].bounding_box()
        받.append(j["부모"].translate([i * 피치, 0, -b[2]]))
    m = 자세(M.Manifold.batch_boolean(받 + [상자(-10, (len(축칸) - 1) * 피치 + 10, -16, 10, 0, 1.2)], M.OpType.Add), "세움")
    for i, (e, c) in enumerate(축칸):
        m = m - 새김판("%d-%s" % (round(e * 10), 라벨(c)), 2.6, i * 피치, -12.0, 1.2, 깊이=0.6)
    낼.append(("회전축받이판", m))
    for i, (e, c) in enumerate(축칸):
        j = 회전축(5.0, 틈=c, 걸림=e, 결합=False); Rb = j["외피반지름"]
        축 = j["자식"] + 상자(0, Rb + 16, -4, 4, 0, 2.5)
        축 = 자세(축, "뒤집음")                       # (x, y, z) → (x, −y, −z)
        축 = 새김(축, "%d-%s" % (round(e * 10), 라벨(c)), 2.6, Rb + 8.5, 0)
        낼.append(("회전축_%d-%s" % (round(e * 10), 라벨(c)), 축))
    return 낼


def 새김판(s, 높이, cx, cy, top, 깊이=0.4):
    p = 글자(s, 높이, (cx, cy)); polys = list(p.geoms) if hasattr(p, "geoms") else [p]
    링 = []
    for q in polys:
        링.append(np.asarray(q.exterior.coords)[:-1]); 링 += [np.asarray(r.coords)[:-1] for r in q.interiors]
    return M.Manifold.extrude(M.CrossSection(링, M.FillRule.EvenOdd), 깊이 + 0.5).translate([0, 0, top - 깊이])


def 선반쌓기(낼, 폭=236.0, 사이=3.0):   # 가장자리 10 mm 는 브림 · 스커트 몫
    """아래-왼쪽 채우기 (큰 것부터 · 90° 돌림 허용). 판 폭 안에 못 놓으면 assert."""
    놓인 = []; 결과 = []
    def 빔(x, y, w, h):
        return x + w <= 폭 and y + h <= 폭 and all(x >= a + c + 사이 or a >= x + w + 사이 or y >= b + d + 사이 or b >= y + h + 사이 for a, b, c, d in 놓인)
    for 이름, m in sorted(낼, key=lambda t: -(lambda b: (b[3] - b[0]) * (b[4] - b[1]))(t[1].bounding_box())):
        후보 = []
        for 돌 in (0, 90):
            mm = m.rotate([0, 0, 돌]); b = mm.bounding_box(); w, h = b[3] - b[0], b[4] - b[1]
            for x in [0.0] + [a + c + 사이 for a, b_, c, d in 놓인]:
                for y in [0.0] + [b_ + d + 사이 for a, b_, c, d in 놓인]:
                    if 빔(x, y, w, h): 후보.append((y + h, x, y, w, h, mm, b))
        assert 후보, "한 판(%.0f) 에 안 들어간다: %s" % (폭, 이름)
        _, x, y, w, h, mm, b = min(후보, key=lambda t: (t[0], t[1]))
        놓인.append((x, y, w, h)); 결과.append((이름, mm.translate([x - b[0], y - b[1], 0])))
    return 결과, max(y + h for x, y, w, h in 놓인)


def 평탄(종류, 이름):
    """BBL 프로필의 inherits 사슬을 풀어 한 파일로. CLI 는 inherits 를 안 풀어서 판이 200×200 기본값이 된다 (09-25 확인:
    폭 196 은 되고 235 는 「Nothing to be sliced」). 속도 · 온도도 같은 이유로 기본값이었을 수 있다."""
    d = json.load(open(os.path.join(BBL, 종류, 이름 + ".json"), encoding="utf-8"))
    if d.get("inherits"):
        부 = 평탄(종류, d["inherits"]); 부.update(d); d = 부
    d.pop("inherits", None); return d


def 쿠폰():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".stl", ".gcode", ".3mf")): os.remove(os.path.join(OUT, f))
    놓음, 깊이 = 선반쌓기(쿠폰부품())
    기록 = {"부품": {}}; 경로들 = []
    for 이름, m in 놓음:
        t = 트(m); assert t.is_watertight and t.is_volume, 이름 + " 닫히지 않음"
        os.makedirs(os.path.join(OUT, "부품"), exist_ok=True)
        t.export(os.path.join(OUT, "부품", 이름 + ".stl")); 경로들.append(t)
        기록["부품"][이름] = {"치수mm": [round(float(v), 1) for v in t.extents], "부피cm3": round(float(t.volume) / 1000, 3)}
    합 = os.path.join(OUT, "관절쿠폰판.stl"); 판 = trimesh.util.concatenate(경로들); 판.apply_translation([128 - 판.bounds[:, 0].mean(), 128 - 판.bounds[:, 1].mean(), 0]); 판.export(합); 경로들 = [합]
    기록["배치 깊이mm"] = round(깊이, 1); 기록["총부피cm3"] = round(sum(v["부피cm3"] for v in 기록["부품"].values()), 2)
    기록["칸"] = {
        "힌지": {"핀": ["F1.75 = 필라멘트 토막 (지름 캘리퍼로 재서 적기)", "P3.0 = 출력 핀 (눕힘 · 아래 D 면 0.3)"],
               "자식 구멍 한쪽 틈(새김 = ×100)": 힌지틈들, "부모 구멍 한쪽 틈": 0.0,
               "구성": "빗(부모 포크 6, 새김 = 자식틈) + 팔 6 (같은 숫자 새김) · 너클 Ø%.1f/Ø%.1f · W %.1f" % (2 * (0.875 + 벽), 2 * (1.5 + 벽), 11.6),
               "가동 설계": "0 ~ 90° (멈춤 턱: 0° 는 +y 벽, 90° 는 홈 끝)"},
        "볼소켓": {"볼지름": [10, 12], "슬릿": ["S = 3 개 · 폭 1.0", "없음"], "한쪽 틈(새김 = ×100)": 볼틈들,
                 "줄 머리 새김": "10S · 10 · 12S · 12", "볼 막대": "크기마다 5 개 (슬릿 줄 먼저 → 없음 줄 · 크리프는 부러짐 없는 줄에 꽂아 하루)",
                 "입구": "0.85 D · 벽 2.4 · 목 0.5 D"},
        "회전축스냅": {"축지름": 5.0, "칸(새김 = 걸림×10 - 틈×100)": ["%d-%s" % (round(e * 10), 라벨(c)) for e, c in 축칸],
                    "구성": "받이판(구멍 위) + 손잡이 달린 축 6"},
        "래칫": "안 만듦 (선택 항목 · 쿠폰 결과 뒤)"}
    기록["판정"] = {
        "공통": "뽑은 그대로(후가공 없이) 조립. 끼울 때 부러진 칸은 「부러짐」으로 적고 제외.",
        "힌지": ["팔을 90° (수평) 로 세우고 거는 구멍(축에서 %d mm)에 추를 건다. 추 = 모멘트 ≈ 9.5 N·mm (PG 하완+손 25 g × 38 mm 가정 · J1 무게가 나오면 바꾼다) = %d mm 에 31 g (500 원 동전 4 개)." % (거는구멍, 거는구멍),
               "10 초 안에 처지지 않으면 「버팀」. 버티는 칸 중 가장 큰 틈 = 기본 자식틈 (손으로 움직일 수 있어야 함: 안 움직이면 「꽉」).",
               "하루(24 h) 90° 로 매단 뒤 다시 시험 → 처지면 크리프 탈락, 한 칸 작은 틈으로."],
        "볼소켓": ["볼 막대를 각 칸에 손으로 끼운다: 들어감 / 슬릿 손가락 부러짐 / 안 들어감.",
                 "판을 세워 막대가 수평이 되게 하고 거는 구멍(볼 중심에서 %d mm)에 추: Ø10 = 31 g (≈10 N·mm · 목 · 손목 · 발목), Ø12 = 77 g (500 원 10 개 · ≈26 N·mm · 고관절 · 어깨 가정)." % (거는구멍 + 4),
                 "처짐 없으면 「버팀」. 꽂은 채 하루 두고 재시험 (크리프) → 버팀 유지하는 가장 큰 틈 = 기본 볼 틈. 슬릿 있음/없음 중 부러짐 없는 쪽."],
        "회전축스냅": ["축을 받이에 누른다: 딸깍 들어감 / 슬릿 부러짐 / 안 들어감.",
                   "손잡이를 잡고 비틀어 360° 돌아가는지 · 손을 떼면 그 각에 서는지(마찰).",
                   "당겨서 빠지는지(손 힘) — 안 빠지고 비틀어지는 칸의 (걸림, 틈) 이 기본값."],
        "기록 방법": "칸마다 꽉 / 알맞음 / 헐거움 / 부러짐 · 하루 뒤 같은 표. 결과 → 관절부품.py 기본틈 표만 고친다."}
    # 슬라이스
    if os.path.exists(ORCA):
        풀린 = []
        for 종류, 이름 in (("machine", "Bambu Lab A1 0.4 nozzle"), ("process", "0.20mm Standard @BBL A1"), ("filament", "Bambu PLA Basic @BBL A1")):
            q = os.path.join(OUT, "_%s.json" % 종류); json.dump(평탄(종류, 이름), open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1); 풀린.append(q)
        기록["판 크기(풀린 프로필)"] = 평탄("machine", "Bambu Lab A1 0.4 nozzle").get("printable_area")
        r = subprocess.run([ORCA, "--load-settings", 풀린[0] + ";" + 풀린[1], "--load-filaments", 풀린[2],
                            "--arrange", "0", "--slice", "0", "--outputdir", OUT] + 경로들,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        기록["슬라이스 종료코드"] = r.returncode
        g = sorted(f for f in os.listdir(OUT) if f.endswith(".gcode")); 기록["gcode"] = g
        for f in g:
            for 줄 in open(os.path.join(OUT, f), encoding="utf-8", errors="replace"):
                if "total estimated time" in 줄 or "filament used [cm3]" in 줄 or "filament used [mm]" in 줄:
                    기록.setdefault("견적", []).append(f + ": " + 줄.strip("; \n"))
                    if "[cm3]" in 줄: 기록["무게g(PLA 1.24)"] = round(float(줄.split("=")[1]) * 1.24, 1)
        if r.returncode: 기록["슬라이서 출력 끝"] = (r.stdout + r.stderr)[-800:]
        print("  슬라이스", r.returncode, 기록.get("견적"), 기록.get("무게g(PLA 1.24)"))
    json.dump(기록, open(os.path.join(OUT, "쿠폰.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 미리보기: 위에서 본 판 (높이 음영 → 새김 보임)
    fig, ax = plt.subplots(figsize=(13, 13))
    목록 = []
    for 이름, m in 놓음:
        c = 색["부모"] if ("빗" in 이름 or "판" in 이름) else 색["핀"] if 이름.startswith("핀") else 색["자식"]
        목록.append((트(m), c))
    칠(ax, 목록, 방위=0, 앙각=90, 높이색=True)
    ax.plot([0, 256, 256, 0, 0], [0, 0, 256, 256, 0], "k--", lw=0.8)
    ax.set_xlim(-5, 261); ax.set_ylim(-5, 261)
    시간 = [x.split("total estimated time:")[-1].strip() for x in 기록.get("견적", []) if "total estimated" in x]
    ax.set_title("관절 쿠폰 한 판 (A1 256 mm · PLA 0.2) — %s · %s g · 판 %d 장" % (", ".join(시간) or "슬라이스 없음", 기록.get("무게g(PLA 1.24)"), len(기록.get("gcode", []))), fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "쿠폰.png"), dpi=110); plt.close(fig)
    return 기록


def main():
    결과 = {}
    for 이름 in 규격:
        j = 만들기(이름); 결과[이름] = {**표(j), "검사": 검사(j)}
        print("  %-12s 외피R %5.2f  %s  %s" % (이름, j["외피반지름"], j["가동"], 결과[이름]["검사"]))
    os.makedirs(r"G:\art2real\원화3d\out\가동", exist_ok=True)
    json.dump(결과, open(r"G:\art2real\원화3d\out\가동\관절규격.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    부품그림(r"G:\art2real\원화3d\out\가동\관절부품.png")
    if "쿠폰" in sys.argv: 쿠폰()


if __name__ == "__main__":
    main()
