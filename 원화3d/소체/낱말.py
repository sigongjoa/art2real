# -*- coding: utf-8 -*-
"""단위 부품 낱말 (2026-09-28 다시 씀) — 프레임과 갑주를 기본 도형으로만 짓는다.

규칙: claudedocs/notes_우리문법_단위부품_20260914.md (옛 `메카/단위부품.py` 는 이 저장소에 없다 → manifold 로 다시).
  프레임  링크(막대) · 볼(구) · 경첩(핀 원통)
  갑주    소매(링크를 감싸는 속 빈 통) · 상자(닫힌 블록 · 테이퍼 · 모따기) · 덧판(매달린 판) · 쐐기(뿔 · 발톱 · 가시)
원화는 정면 폭 · 길이만 정한다. 깊이는 규칙(폭 × 비) 에서. 앞 = −y · 위 = +z · 단위 mm.
    python 낱말.py  -> 자기 검사
"""
import numpy as np, manifold3d as M

def _틀(a, b):
    """a → b 를 로컬 +z 로 보내는 3×4. 로컬 x 는 되도록 세계 x(정면 폭 방향)."""
    a, b = np.asarray(a, float), np.asarray(b, float); z = (b - a) / np.linalg.norm(b - a)
    x = np.array([1.0, 0, 0]) - z[0] * z
    if np.linalg.norm(x) < 1e-6: x = np.array([0, 1.0, 0]) - z[1] * z
    x /= np.linalg.norm(x); y = np.cross(z, x)
    return np.column_stack([x, y, z, a])
def _팔각(w, d, z, c):
    """z 높이의 w × d 사각(모서리 c 모따기) 꼭짓점 8."""
    c = min(c, 0.45 * min(w, d)); hw, hd = w / 2, d / 2
    return [(sx * (hw - (c if k else 0)), sy * (hd - (0 if k else c)), z) for sx in (1, -1) for sy in (1, -1) for k in (0, 1)]
def 뿔대(w0, d0, w1, d1, L, 모=0.6, 밑=0.0):
    """로컬 z 0 → L 로 단면이 (w0 × d0) → (w1 × d1) 로 바뀌는 모따기 상자. 밑 = 시작 z."""
    return M.Manifold.hull_points(_팔각(w0, d0, 밑, 모) + _팔각(w1, d1, 밑 + L, 모))

# ── 프레임 ──
def 링크(a, b, w=6.0, d=None, 여유=0.0):
    L = float(np.linalg.norm(np.subtract(b, a))); d = w if d is None else d
    return 뿔대(w + 2 * 여유, d + 2 * 여유, w + 2 * 여유, d + 2 * 여유, L + 2 * 여유, 모=0.8, 밑=-여유).transform(_틀(a, b))
def 볼(c, r=4.0, 여유=0.0): return M.Manifold.sphere(r + 여유, 40).translate(list(map(float, c)))
def 경첩(c, r=3.5, 길이=10.0, 축=(1, 0, 0), 여유=0.0):
    축 = np.asarray(축, float) / np.linalg.norm(축); c = np.asarray(c, float); h = 길이 / 2 + 여유
    return M.Manifold.cylinder(2 * h, r + 여유, r + 여유, 40).transform(_틀(c - 축 * h, c + 축 * h))

# ── 갑주 ──
def 소매(a, b, w0, w1, 깊이비=1.0, 덮음=0.85, 밀=0.0, 모=1.0):
    """링크 a → b 를 감싸는 통. 정면 폭 w0(a 쪽) → w1(b 쪽) · 깊이 = 폭 × 깊이비 · 길이 = 덮음 × L(양 끝에 관절이 보임). 밀 = 로컬 y(앞뒤) 로 민 양."""
    L = float(np.linalg.norm(np.subtract(b, a))); 밑 = (1 - 덮음) / 2 * L
    return 뿔대(w0, w0 * 깊이비, w1, w1 * 깊이비, 덮음 * L, 모, 밑).translate([0, 밀, 0]).transform(_틀(a, b))
def 상자(c, W, H, D, 위W=None, 위D=None, 모=1.0):
    """가운데 c · 아래 폭 W · 높이 H · 깊이 D. 위W · 위D = 윗면(테이퍼)."""
    return 뿔대(W, D, W if 위W is None else 위W, D if 위D is None else 위D, H, 모, -H / 2).translate(list(map(float, c)))
def 덧판(P, 두께=1.6, 방향=(0, -1, 0)):
    """점들 P(같은 평면 근처)의 볼록 판. 방향 쪽으로 두께만큼."""
    P = np.asarray(P, float); n = np.asarray(방향, float) / np.linalg.norm(방향)
    return M.Manifold.hull_points(np.vstack([P, P + n * 두께]))
def 쐐기(밑점들, 끝):
    """밑면 다각형 + 끝점 → 뿔 · 발톱 · 가시."""
    return M.Manifold.hull_points(np.vstack([np.asarray(밑점들, float), np.asarray([끝], float)]))

if __name__ == "__main__":
    a, b = (0, 0, 0), (10, 5, 40); l = 링크(a, b, 6); s = 소매(a, b, 14, 10) - 링크(a, b, 6, 여유=0.3)
    assert len(s.decompose()) == 1 and (s ^ l).volume() < 1e-6, "소매가 링크를 파고듦"
    assert abs(l.volume() - 6 * 6 * np.linalg.norm(b)) / l.volume() < 0.1
    assert 상자((0, 0, 0), 20, 10, 12, 위W=10).volume() < 20 * 10 * 12 and 쐐기([(0, 0, 0), (4, 0, 0), (0, 4, 0)], (0, 0, 9)).volume() > 0
    assert (경첩((0, 0, 0), 3, 10) ^ 볼((20, 0, 0), 4)).volume() == 0
    print("낱말 자기 검사 통과")
