"""2단계 부품을 실물 척도로 — j1 0.17 mm/px 체계가 실물의 약 0.53 배였다.

근거(커팅매트 격자 · 국소 척도): 정강이 46~49 mm / 체계 23.8 → 1.93~2.06 · 방패 흰 판 76.6 × 35.5 / 39.8 × 16.8 → 1.92 · 2.11 ·
발바닥 28~32 × 17 / 16.7 × 8.8 → 1.8 · 1.9. 전신 옆(gb_005) 정강이 ≈ 전고 125 의 0.33 → 41 mm → 1.72. 가운데 값 1.9.
부품 안 Z 가정도 0.17 체계에 맞춰 잡았으니 고르게 키운다 — 끼움 틈 0.1~0.15 도 0.19~0.29 가 된다(PLA 출력엔 오히려 가깝다).
ponytail: 한 배율 — 캘리퍼 실측이 오면 K 만 바꾼다. 틈을 절대값으로 되돌리려면 각 스크립트에서 척도를 받아 다시 지어야 한다.
결과: out/키트/EG_RX78/2단계/실척/부품_NN.stl (부품마다 가장 새 판 _vN)."""
import glob, os, re
import trimesh

K = 1.9
D = os.path.join(os.path.dirname(__file__), "..", "out", "키트", "EG_RX78", "2단계")
OUT = os.path.join(D, "실척"); os.makedirs(OUT, exist_ok=True)

고른 = {}
for p in sorted(glob.glob(os.path.join(D, "부품_*.stl"))):
    m = re.match(r"부품_(\d+)(?:_v(\d+))?\.stl", os.path.basename(p))
    if m: 고른.setdefault(m[1], []).append((int(m[2] or 2), p))
고른 = {n: max(v)[1] for n, v in 고른.items()}          # 가장 새 판

for n, p in sorted(고른.items()):
    t = trimesh.load(p); t.apply_scale(K)
    assert t.is_watertight, p
    t.export(os.path.join(OUT, f"부품_{n}.stl"))
    print(n, os.path.basename(p), "x".join(f"{v:.1f}" for v in t.extents))
print(len(고른), "개 · K =", K)
