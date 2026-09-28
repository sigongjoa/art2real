# -*- coding: utf-8 -*-
"""관절 쿠폰 — Figuarts 관절 세트(볼 · 이중경첩 · 흔들 · 경첩)를 PLA 로 번역한 한 판 (2026-09-28).

    python 관절쿠폰.py  ->  out/소체/관절쿠폰/  조립/*.stl(조립 좌표 · 검사용) · 출력/*.stl(출력 자세 · 판 배치)
                            관절쿠폰.png(Blender 조립 그림) · 관절쿠폰.3mf(슬라이스) · 쿠폰.json

관절 목록 = out/소체/이족_메카_남/관절.json (PG 급 300 mm). 09-27 교훈([[pla-joints-not-rubber]]):
PLA 는 안 휜다 → 스냅 · 틈 마찰 안 씀. 자세는 **나사 조임(M2)** 과 **래칫(면 톱니)** 으로 버틴다.
  볼      갈라진 소켓 두 반쪽이 볼을 감싸고 M2 두 개로 조인다. Ø10(어깨 · 고관절) · Ø6(목 · 손목) × 틈 0.10 / 0.15
  이중경첩 아래 포크 · 링크 · 위 포크(3 부품 — 축 둘이라 둘로는 안 됨). 축 = M2 나사(통과 2.4 · 탭 1.8).
          아래 축에 면 톱니 20 개(18°) — 나사를 조이면 톱니가 물려 딸깍 멈춤, 풀면 헐겁다.
  흔들    정강이 포크(앞뒤 · x 축) · 십자 블록 · 발(좌우 흔들 · y 축 = 발 길이 방향). 축 = M2 나사 둘.
  경첩    발 앞 포크 · 발끝 · 출력 핀 Ø3. 면 톱니 24 개(15°) = 0 · 15 · 30° 멈춤. 스프링 = 얇은 너클(1.6) 휨.
나사 = M2 × 10~12 (자가태핑 또는 기계나사 · 밑구멍 1.8 에 탭). 출력 금지 — 사용자 OK 뒤 send.py.
"""
import os, sys, json, shutil, subprocess
import numpy as np, manifold3d as M, trimesh
R_ = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R_)
sys.path.insert(0, os.path.join(원화3d, "실험_20260925"))
from 관절부품 import 상자, 원기둥z, 물방울x, 출력핀, 겹침, 트, 새김, 선반쌓기, SEG
import 출력판
sys.path.insert(0, R_)
from 생성기 import 블, BLENDER          # Blender 4.0 헤드리스 렌더 재사용

OUT = os.path.join(원화3d, "out", "소체", "관절쿠폰")
관절표 = json.load(open(os.path.join(원화3d, "out", "소체", "이족_메카_남", "관절.json"), encoding="utf-8"))["관절"]

# ── 치수 (mm · 틈은 한쪽 반지름) ──
통과, 밑, 나사 = 2.4, 1.8, 2.0     # M2: 통과 구멍 · 탭 밑구멍 (1.8~2.0) · 나사 지름
벽 = 1.2                           # 최소 벽 (막힌 구멍 바닥 포함)
핀 = 3.0; 핀틈포크, 핀틈혀 = 0.10, 0.15
볼틈들 = (0.10, 0.15)
rk, b, g = 4.5, 5.0, 0.25          # 너클 반지름 · 혀 두께 · 너클 틈
a통, a탭 = 2.4, 4.0                 # 통과 쪽 너클(얇아 휜다 = 래칫 스프링) · 탭 쪽 너클(나사산 물림 4 − 1.2)
이높, 이틈 = 0.4, 0.10             # 래칫 톱니 높이 · 축방향 틈


def 틀(m, 축, 끝):
    """x 축 · +y 끝 기준으로 만든 것을 축 → 축, +y → 끝 으로 돌린다."""
    a, t = np.array(축, float), np.array(끝, float); R = np.c_[a, t, np.cross(a, t)]
    return m.transform(np.c_[R, np.zeros(3)])


def 구멍(r, 축, lo, hi, 위=None):
    """축 방향 구멍 [lo, hi] (원점 지남). 위 = 출력 때 위쪽 방향 → 물방울(천장 45°). 위 ∥ 축 이면 둥근 구멍."""
    축 = np.array(축, float)
    if 위 is None or abs(np.dot(축, 위)) > 0.9:
        t = np.array([0, 0, 1.0]) if abs(축[2]) < 0.9 else np.array([0, 1.0, 0])
        return 틀(M.Manifold.cylinder(hi - lo, r, r, SEG).rotate([0, 90, 0]).translate([lo, 0, 0]), 축, t)
    return 틀(물방울x(r, lo, hi), 축, 위)


def 이빨(n, r0, r1, h, x면, 방향, 넓=1.0):
    """x 축 둘레 면 톱니 n 개: x = x면 에서 방향(±1) 으로 h 솟음. 삼각 단면."""
    p = 넓 * np.pi / n; 톱 = []
    for k in range(n):
        q = 2 * np.pi * k / n; pts = []
        for r in (r0, r1):
            for (각, x) in ((q - p, x면), (q + p, x면), (q, x면 + 방향 * h)):
                pts.append([x, r * np.cos(각), r * np.sin(각)])
        톱.append(M.Manifold.hull_points(np.array(pts)))
    return M.Manifold.batch_boolean(톱, M.OpType.Add)


def 너클(x0, x1, r, 쪽, 받침):
    """x 축 원기둥 + 받침 쪽(±z)으로 네모 — 받침까지 이어진다."""
    c = M.Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, 0, 0])
    return c + 상자(x0, x1, -r, r, min(0, 쪽 * 받침), max(0, 쪽 * 받침))


def 포크(쪽, L, 위, 래칫=None, r=rk, 혀=b, 틈=g, a1=a통, a2=a탭, 축구멍=None, r0=1.8):
    """x 축 · 받침 쪽(±z) 에 팔 L. 래칫 = (n, h) 면 톱니(−x 너클 안쪽). 축구멍 = (포크 구멍 r) 이면 핀, 없으면 M2(통과 · 탭)."""
    x2 = 혀 / 2 + 틈 + a2
    if 래칫:
        n, h = 래칫; 안1 = -혀 / 2 - 이틈; x1 = 안1 - h - a1
    else:
        안1 = -혀 / 2 - 틈; x1 = 안1 - a1
    z0 = r + 0.5
    m = 너클(x1, 안1, r, 쪽, z0) + 너클(혀 / 2 + 틈, x2, r, 쪽, z0) + 상자(x1, x2, -r, r, min(쪽 * z0, 쪽 * (z0 + L)), max(쪽 * z0, 쪽 * (z0 + L)))
    if 래칫:
        m = m - 이빨(n, r0 - 0.3, r, h, -혀 / 2, -1, 넓=1.04).translate([-이틈, 0, 0])      # 홈은 반지름 0.3 · 각 4 % 넓게 (톱니 끝 현이 안쪽 · 이웃 홈이 모서리로만 닿으면 안 닫힘)
        m = max(m.decompose(), key=lambda q: q.volume())      # 홈 바깥 현 끝의 부피 0 부스러기 버림
    if 축구멍:
        m = m - 구멍(축구멍, [1, 0, 0], x1 - 1, x2 + 1, 위)
    else:
        m = m - 구멍(통과 / 2, [1, 0, 0], x1 - 1, 안1 + 0.1, 위) - 구멍(밑 / 2, [1, 0, 0], 혀 / 2 + 틈 - 0.1, x2 - 벽, 위)
    return m, dict(x1=x1, x2=x2, 나사길이=round(x2 - x1, 1), 탭물림=round(a2 - 벽, 1))




def 혀(쪽, L, 위, 래칫=None, r=rk, 두께=b, 구멍r=통과 / 2, r0=1.8):
    """x 축 혀 (두께 · 가운데) + 몸 쪽(±z) L. 래칫 = −x 면 톱니."""
    m = 너클(-두께 / 2, 두께 / 2, r, 쪽, L)
    if 래칫:
        n, h = 래칫; m = m + 이빨(n, r0, r - 0.3, h, -두께 / 2, -1)
    return m - 구멍(구멍r, [1, 0, 0], -두께 / 2 - 1 - (래칫[1] if 래칫 else 0), 두께 / 2 + 1, 위)


# ─────────────── 볼 ───────────────
def 볼클램프(D, c, s=0.3, 원뿔=60.0):
    """볼 중심 = 원점 · 목 +z · 가름면 y = 0. 반쪽 둘(y ≥ s 통과 / y ≤ −s 탭)을 M2 둘로 조이면 볼을 (s − c) 누르고 면이 닿아 멈춘다."""
    R = D / 2; Rc = R + c; T = Rc + 1.4; nx = Rc + 벽 + 통과 / 2; X = nx + 통과 / 2 + 벽 + 0.2
    zb, zt = -Rc - 1.4, 0.6 * R; zs = (zb + zt) / 2 - 0.5
    속 = M.Manifold.sphere(Rc, SEG) + M.Manifold.cylinder(20, 0, 20 * np.tan(np.radians(원뿔)), SEG)
    위 = 상자(-X, X, s, T, zb, zt) - 속; 아래 = 상자(-X, X, -T, -s, zb, zt) - 속
    for sx in (-nx, nx):
        위 = 위 - 구멍(통과 / 2, [0, 1, 0], -20, 20).translate([sx, 0, zs])
        아래 = 아래 - 구멍(밑 / 2, [0, 1, 0], -(T - 벽), 0).translate([sx, 0, zs])
    rn = 0.5 * R; z목 = zt + 4; Lt = min(12.0, 29 - R - z목)
    볼 = (M.Manifold.sphere(R, SEG) + 원기둥z(rn, 0, z목 + 0.5) + 상자(-0.7 * R, 0.7 * R, -(R - 0.3), rn, z목, z목 + Lt)) ^ 상자(-50, 50, -(R - 0.3), 50, -50, 100)
    흔들 = 0
    for 각 in range(5, 60, 5):
        if all(겹침(위 + 아래, 볼.rotate(r)) < 1e-3 for r in ([각, 0, 0], [-각, 0, 0], [0, 각, 0], [0, -각, 0])): 흔들 = 각
        else: break
    # 벽 · 틈 검사 (해석)
    assert T - Rc >= 벽 and nx - 통과 / 2 - Rc >= 벽 - 1e-9 and X - nx - 통과 / 2 >= 벽 and -zb - Rc >= 벽, "볼 소켓 벽"
    assert T - 벽 - s >= 2.0, "탭 물림"
    # 틈 검사 (수치): R + c − 0.02 공은 안 닿고, R + c + 0.02 공은 닿아야
    assert 겹침(위 + 아래, M.Manifold.sphere(Rc - 0.02, SEG)) < 1e-4 < 겹침(위 + 아래, M.Manifold.sphere(Rc + 0.03, SEG)), ("볼 틈", D, c)
    return 위, 아래, 볼, dict(볼지름=D, 틈=c, 가름틈=s, 누름=round(s - c, 2), 흔들=흔들, 목지름=round(2 * rn, 1), 나사="M2×%d · 두 개" % (8 if D < 8 else 10),
                         반쪽=[round(2 * X, 1), round(T - s, 1), round(zt - zb, 1)])


# ─────────────── 이중경첩 (팔꿈치 · 무릎) ───────────────
def 이중경첩(P=2 * rk + 1.0, L=12.0):
    """아래 축 z = 0 (래칫) · 위 축 z = P. 부모(아래 팔) 아래 · 링크 · 자식(위 팔) 위. 출력: −y 면이 바닥 → 물방울 끝 +y."""
    위y = [0, 1, 0]; 래 = (20, 이높)
    아래, i1 = 포크(-1, L, 위y, 래칫=래)
    링크 = (혀(+1, P, 위y, 래칫=래) + 혀(-1, P, 위y).translate([0, 0, P]))
    위팔, i2 = 포크(+1, L, 위y); 위팔 = 위팔.translate([0, 0, P])
    assert 겹침(아래, 링크) < 1e-3 and 겹침(링크, 위팔) < 1e-3 and 겹침(아래, 위팔) < 1e-3, "이중경첩 조립 겹침"
    for 각 in (36, 90):     # 톱니 18° 배수에서만 물림
        assert 겹침(아래, 링크.rotate([-각, 0, 0])) < 1e-3, ("아래 축 %d°" % 각)
    for 각 in (45, 90):
        assert 겹침(링크, 위팔.translate([0, 0, -P]).rotate([-각, 0, 0]).translate([0, 0, P])) < 1e-3, ("위 축 %d°" % 각)
    assert a통 >= 벽 and a탭 - 벽 >= 2.0 and rk - 통과 / 2 * np.sqrt(2) >= 벽
    return [("팔꿈치_아래_파랑", 아래, [0, -1, 0]), ("팔꿈치_링크_초록", 링크, [0, -1, 0]), ("팔꿈치_위_노랑", 위팔, [0, -1, 0])], \
        dict(축간=P, 래칫="면 톱니 20 × 18° · 높이 %.1f · 축방향 틈 %.2f" % (이높, 이틈), 나사="M2×%d 둘" % round(i1["나사길이"]), 아래=i1, 위=i2,
             가동="축마다 0~90 검사(합 180) · 아래 축 18° 딸깍")


# ─────────────── 흔들 (발목) ───────────────
def 흔들(P2=2 * rk + 1.5):
    """앞뒤 = x 축(z = 0, 정강이 포크 위) · 좌우 흔들 = y 축(z = −P2, 발 포크 아래). 십자 블록이 둘을 잇는다."""
    정강이, _ = 포크(+1, 10.0, [0, 1, 0])
    십 = (너클(-b / 2, b / 2, rk, -1, P2 / 2) - 구멍(통과 / 2, [1, 0, 0], -b, b, [0, 1, 0])
         + 틀(너클(-b / 2, b / 2, rk, -1, P2 / 2), [0, 1, 0], [1, 0, 0]).translate([0, 0, -P2]))     # 틀: 로컬 +z → −z
    십 = 십 - 구멍(통과 / 2, [0, 1, 0], -b, b).translate([0, 0, -P2])       # 출력 −y 바닥 → y 구멍은 세로(둥근)
    발포, _ = 포크(-1, 0.1, [0, 0, 1])        # x 축으로 만들고 y 축으로 돌림
    발포 = 발포.rotate([0, 0, 90])
    z판 = -rk - 0.5 - 0.1
    발 = 발포 + 상자(-10, 10, -14, 14, z판 - 3.0, z판 + 0.01)
    발 = 발.translate([0, 0, -P2])
    assert 겹침(정강이, 십) < 1e-3 and 겹침(십, 발) < 1e-3 and 겹침(정강이, 발) < 1e-3, "흔들 조립 겹침"
    for 각 in (-30, 30):
        assert 겹침(정강이.rotate([각, 0, 0]), 십) < 1e-3, ("앞뒤 %d°" % 각)
    for 각 in (-20, 20):
        assert 겹침(십, 발.translate([0, 0, P2]).rotate([0, 각, 0]).translate([0, 0, -P2])) < 1e-3, ("흔들 %d°" % 각)
    return [("발목_정강이_파랑", 정강이, [0, -1, 0]), ("발목_십자_초록", 십, [0, -1, 0]), ("발목_발_노랑", 발, [0, 0, -1])], \
        dict(축간=P2, 앞뒤="±30 검사", 흔들="±20 검사", 나사="M2×12 둘", 발판="20 × 28 × 3")


# ─────────────── 경첩 (발끝) ───────────────
def 발끝(L=8.0):
    """축 x · 출력 핀 Ø3 · 면 톱니 24 (15°) → 0 · 15 · 30° 멈춤. 스프링 = 얇은 너클 a1 = 1.6 이 휨. 핀 = 포크 0.10 · 혀 0.15."""
    r = 4.0; 래 = (24, 0.3); 위y = [0, 1, 0]; 두께 = 5.0
    부, i = 포크(-1, L, 위y, 래칫=래, r=r, 혀=두께, a1=1.6, a2=2.4, 축구멍=핀 / 2 + 핀틈포크, r0=2.3)
    자 = 혀(+1, 12.0, 위y, 래칫=래, r=r, 두께=두께, 구멍r=핀 / 2 + 핀틈혀, r0=2.3)
    길이 = i["x2"] - i["x1"]; 축핀 = 출력핀(핀, 길이).translate([(i["x1"] + i["x2"]) / 2, 0, 0])
    assert 겹침(부, 자) < 1e-3 and 겹침(부, 축핀) < 1e-3 and 겹침(자, 축핀) < 1e-3, "발끝 조립 겹침"
    for 각 in (15, 30):
        assert 겹침(부, 자.rotate([-각, 0, 0])) < 1e-3, ("발끝 %d°" % 각)
    assert r - (핀 / 2 + 핀틈혀) * np.sqrt(2) >= 벽 and 1.6 >= 벽
    return [("발끝_포크_파랑", 부, [0, -1, 0]), ("발끝_발가락_노랑", 자, [0, -1, 0]), ("발끝_핀_빨강", 축핀, [0, -1, 0])], \
        dict(핀=핀, 핀길이=round(길이, 1), 포크구멍=핀 + 2 * 핀틈포크, 혀구멍=핀 + 2 * 핀틈혀, 톱니="24 × 15° · 높이 0.3", 멈춤="0 · 15 · 30 (30 넘어서도 돎 — 멈춤 턱 없음)")


def 눕(m, 아래):
    T = trimesh.geometry.align_vectors(np.array(아래, float), [0, 0, -1.0])
    m = m.transform(T[:3, :4]); bb = m.bounding_box(); return m.translate([0, 0, -bb[2]])


def main():
    for d in ("조립", "출력"):
        p = os.path.join(OUT, d); os.makedirs(p, exist_ok=True)
        for f in os.listdir(p):
            if f.endswith(".stl"): os.remove(os.path.join(p, f))
    종류 = sorted({j["종류"] for j in 관절표}); assert 종류 == sorted(["볼", "이중경첩", "흔들", "경첩"]), 종류
    세트, 기록 = [], {"관절표": {k: [j["이름"] for j in 관절표 if j["종류"] == k] for k in 종류}, "나사": "M2", "통과": 통과, "밑구멍": 밑}
    for D in (10.0, 6.0):
        for c in 볼틈들:
            위, 아래, 볼, j = 볼클램프(D, c); assert j["흔들"] >= 20, j
            k = "볼%d_c%02d" % (D, round(c * 100)); 기록[k] = j
            아래출 = 눕(아래, [0, 1, 0]); e = 아래출.bounding_box()
            아래출 = 새김(아래출, "%d" % round(c * 100), 3.0, (e[0] + e[3]) / 2, (e[1] + e[4]) / 2)
            세트.append((k, [(k + "_위_파랑", 위, [0, -1, 0]), (k + "_아래_파랑", 아래, 아래출), (k + "_볼_노랑", 볼, [0, -1, 0])]))
    for k, f in (("이중경첩", 이중경첩), ("흔들", 흔들), ("경첩", 발끝)):
        부들, j = f(); 기록[k] = j; 세트.append((k, 부들))
    # 검사 · 내보내기
    검사, 출력들, x = {}, [], 0.0
    for k, 부들 in 세트:
        for 이름, m, 아래 in 부들:
            assert len(m.decompose()) == 1, 이름 + " 여러 조각"
            t = 트(m); t.merge_vertices(); assert t.is_watertight and t.is_volume, 이름 + " 안 닫힘(꼭짓점 합친 뒤)"
            출 = 아래 if isinstance(아래, M.Manifold) else 눕(m, 아래)
            e = 출.bounding_box(); 크기 = [round(e[3] - e[0], 1), round(e[4] - e[1], 1), round(e[5] - e[2], 1)]
            assert max(크기) <= 30.0 + 1e-6, (이름, 크기)
            검사[이름] = 크기; 출력들.append((이름, 출))
        겹 = max(겹침(a, bb) for i_, (_, a, _) in enumerate(부들) for (_, bb, _) in 부들[i_ + 1:])
        assert 겹 < 1e-3, (k, 겹)
    기록["부품mm(출력 자세)"] = 검사; 기록["검사"] = "전부 한 조각 · 닫힘 · ≤ 30 mm · 조립 겹침 < 0.001 mm³ · 벽 ≥ %.1f · 핀 Ø%.0f · 탭 Ø%.1f · 볼 틈 %s" % (벽, 핀, 밑, 볼틈들)
    # 조립 좌표 STL (세트마다 x 로 벌려 놓음) + 렌더용 자세
    판부품, 색 = [], {"파랑": (0.45, 0.55, 0.70), "초록": (0.40, 0.70, 0.45), "노랑": (0.93, 0.62, 0.25), "빨강": (0.85, 0.25, 0.25)}
    x = 0.0
    for k, 부들 in 세트:
        묶 = []
        for 이름, m, _ in 부들:
            v = m
            if k.startswith("볼") and "_볼_" in 이름: v = m.rotate([20, 0, 0])
            if k == "이중경첩" and "_위_" in 이름: v = m.translate([0, 0, -2 * rk - 1]).rotate([-45, 0, 0]).translate([0, 0, 2 * rk + 1])
            if k == "경첩" and "발가락" in 이름: v = m.rotate([-15, 0, 0])
            if k == "흔들" and "_발_" in 이름: v = m.translate([0, 0, 2 * rk + 1.5]).rotate([0, 12, 0]).translate([0, 0, -2 * rk - 1.5])
            묶.append((이름, v))
        bb = M.Manifold.batch_boolean([v for _, v in 묶], M.OpType.Add).bounding_box(); dx = x - bb[0]
        for 이름, v in 묶:
            트(v.translate([dx, 0, 0])).export(os.path.join(OUT, "조립", 이름 + ".stl"))
            r = v.rotate([0, 0, -35]).rotate([-20, 0, 0]).translate([dx * 1.25, 0, 0])      # 3/4 보기
            p = os.path.join(OUT, "_그림", 이름 + ".stl"); os.makedirs(os.path.dirname(p), exist_ok=True); 트(r).export(p)
            판부품.append((p, next(c for w, c in 색.items() if w in 이름)))
        x += bb[3] - bb[0] + 8
    # Blender 조립 그림
    전 = trimesh.util.concatenate([trimesh.load(p) for p, _ in 판부품]); lo, hi = 전.bounds
    png = os.path.join(OUT, "관절쿠폰.png")
    jf = os.path.join(OUT, "_그림", "판.json")
    json.dump(dict(판=[dict(부품=판부품, 폭=float(hi[0] - lo[0]) + 16, 해상=(2400, int(2400 * (hi[2] - lo[2] + 16) / (hi[0] - lo[0] + 16))), 중심=list(map(float, (lo + hi) / 2)), out=png)]),
              open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(OUT, "_그림", "블.py"); open(pf, "w", encoding="utf-8").write(블)
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0 and os.path.exists(png), r.stderr[-2000:]
    # 판 배치 (가장자리 10 mm) → STL 따로 · 자리 그대로 슬라이스
    놓음, 깊이 = 선반쌓기(출력들, 폭=236.0, 사이=8.0); 경로 = []      # 4 mm 면 좁은 부품 자동 브림끼리 겹쳐 CLI 가 -101; 경로 = []
    전bb = M.Manifold.batch_boolean([m for _, m in 놓음], M.OpType.Add).bounding_box()
    이동 = [128 - (전bb[0] + 전bb[3]) / 2, 128 - (전bb[1] + 전bb[4]) / 2, 0]     # 판 가운데 (앞 가장자리 10 mm 에 두면 --arrange 0 슬라이스가 -101 로 죽음)
    for 이름, m in 놓음:
        p = os.path.join(OUT, "출력", 이름 + ".stl"); 트(m.translate(이동)).export(p); 경로.append(p)
    기록["판깊이mm"] = round(깊이, 1); 기록["부품수"] = len(경로)
    json.dump(기록, open(os.path.join(OUT, "쿠폰.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "--슬라이스" in sys.argv:
        출력판.ROOT = OUT; 출력판.main("관절쿠폰", 경로, 눕히기=False, 자리=True)
        s = os.path.join(OUT, "판", "관절쿠폰", "관절쿠폰.3mf"); shutil.copy(s, os.path.join(OUT, "관절쿠폰.3mf"))
    print(json.dumps(기록, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
