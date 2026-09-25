# -*- coding: utf-8 -*-
"""오메가몬 PG 급(전고 300 mm) 가동 골격 — 관절 목록 · 이너 프레임 뼈 · 관절 외피 (2026-09-25).

    python 골격.py   -> out/가동/관절.json · out/가동/프레임/*.stl · out/가동/골격.png

좌표 = mm · 원점 발바닥 중앙 · [x 좌우(거울 면 x=0), y 깊이(**작은 y 가 앞**), z 높이] (입력.npz 와 같은 축).
L/R 는 E13 이름 그대로 (L = 작은 x = 칼 팔). E13 이름의 앞/뒤는 뒤집혀 있어 부위 묶음에만 쓰고 방향은 y 로 본다.
몸 = 384³ 연속 장(field_default n=384) ∩ 192³ 키트 몸 O (둘 다 안인 곳 — 장갑이 올라갈 몸보다 크지 않게).
안쪽 오프셋 = 겉에서 장갑 2.0 + 틈 0.4 = 2.4 mm 안. 뼈는 이 안에 · 관절 외피는 J2 가 채울 빈자리.
축 = 기하 방향(볼·회전축은 자식 쪽 · R 은 L 의 점 거울 (-x,y,z)). 범위 = [축 벡터, 최소°, 최대°] · 양수 = 그 벡터 둘레 오른손 회전.
R 쪽 범위 벡터는 L 의 유사벡터 거울(a → -M a, M=diag(-1,1,1))이라
같은 숫자가 같은 뜻(예: 고관절 벌림 + = 바깥)이다."""
import os, sys, json
os.environ.setdefault("OMP_NUM_THREADS", "4"); os.environ.setdefault("INK_W", "1")
import numpy as np
from scipy import ndimage
import manifold3d as mf

ROOT = r"G:\art2real\원화3d"
OUT = os.path.join(ROOT, "out", "가동"); os.makedirs(os.path.join(OUT, "프레임"), exist_ok=True)
E13 = os.path.join(ROOT, "out", "분할후보", "E13")
d192 = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz"))
O = d192["O"]; 축i = float(d192["축i"])
lab = np.load(os.path.join(E13, "lab.npy"))
이름 = {v: int(k) for k, v in json.load(open(os.path.join(E13, "이름.json"), encoding="utf-8")).items()}
막대 = {}
for e in json.load(open(os.path.join(E13, "평면.json"), encoding="utf-8")):
    if "원통" in e: 막대["칼" if 이름["L칼"] in e["짝"] else "대포"] = e["원통"]

# ── 척도 · 좌표 ───────────────────────────────────────────────
zs = np.nonzero(O.any((0, 1)))[0]
C = 300.0 / (zs[-1] - zs[0] + 1)            # 192 칸 = C mm
바닥 = O[:, :, zs[0]:zs[0] + 2]; y0 = np.argwhere(바닥)[:, 1].mean()
def mm(p):                                   # 192 색인(실수) → mm
    p = np.asarray(p, float); return np.stack([(p[..., 0] - 축i) * C, (p[..., 1] - y0) * C, (p[..., 2] - (zs[0] - 0.5)) * C], -1)
장 = os.path.join(OUT, "장384.npz")
if not os.path.exists(장):
    sys.path[:0] = [ROOT] + [ROOT + r"\실험_202609%02d" % d for d in (21, 22, 23, 24, 25)]
    import hull as H, 부품분할 as BB
    raw, masks, bs, p = BB.판("오메가몬"); g, ax = H.field_default(masks, back_sign=bs, n=384)
    np.savez_compressed(장, g=g.astype(np.float32))
up = lambda a: a.repeat(2, 0).repeat(2, 1).repeat(2, 2)
B = (np.load(장)["g"] > 0) & up(O)          # 384 몸
h = C / 2                                    # 384 칸 mm
q = np.arange(384); ax_mm = [((q - 0.5) / 2 - 축i) * C, ((q - 0.5) / 2 - y0) * C, ((q - 0.5) / 2 - (zs[0] - 0.5)) * C]
깊 = ndimage.distance_transform_edt(B) * h - h / 2     # 겉까지 거리 (mm, 칸 중심 → 겉 반 칸 보정)
두께 = 2.4
안 = 깊 >= 두께
lab4 = up(lab)
def 칸(p):                                    # mm → 384 색인
    return tuple(int(np.clip(np.rint((p[k] - ax_mm[k][0]) / h), 0, 383)) for k in range(3))
def 깊이(p): return float(깊[칸(p)])

부위 = dict(머리=["머리앞", "머리뒤"], 가슴=["가슴앞", "가슴뒤", "가슴판"], 복부=["복부앞", "복부뒤"], 허리=["허리앞", "허리뒤"],
          L허벅지=["L허벅지앞", "L허벅지뒤"], L무릎=["L무릎"], L정강이=["L정강이앞", "L정강이뒤"], L발=["L발앞", "L발뒤"],
          L윗팔=["L윗팔앞", "L윗팔뒤"], L어깨=["색38"], R어깨=["R어깨"], L팔끝=["L팔끝앞", "L팔끝뒤"], R윗팔=["R윗팔앞", "R윗팔뒤"], R팔끝=["R늑대앞", "R늑대뒤"])
_점 = {}
def 점들(k):                                  # 부위 → 384 칸 mm 좌표
    if k not in _점:
        ks = sum((부위[s] for s in k.split("+")), [])
        w = np.argwhere(np.isin(lab4, [이름[n] for n in ks]) & B)
        _점[k] = np.stack([ax_mm[i][w[:, i]] for i in range(3)], 1); _점[k + "_깊"] = 깊[tuple(w.T)]
    return _점[k]
def 주축(k, 아래=True):
    P = 점들(k); d = np.linalg.svd(P - P.mean(0), full_matrices=False)[2][0]
    return d * (-1 if (d[2] > 0) == 아래 else 1)
def 단면중심(k, z192=None, d=(0, 0, 1), 판=1.0, 기준=None):
    """부위 k 를 d 에 수직인 판(두께 ±판 mm)으로 자른 단면의 **속 중심** = 단면 안에서 겉까지 거리가 최대의 80 % 이상인
    칸들의 무게중심 (그냥 무게중심은 얇은 날개 · 비대칭 단면에서 겉으로 끌려 무릎이 여유 2 mm 였다). 판 위치 = z192 높이(주축 위)."""
    P = 점들(k); d = np.asarray(d, float); d /= np.linalg.norm(d); c = P.mean(0) if 기준 is None else np.asarray(기준, float)
    if z192 is not None:
        zm = mm([0, 0, z192])[2]; c = c + d * (zm - c[2]) / d[2]
    s = np.abs((P - c) @ d) <= 판
    assert s.sum() > 20, (k, z192, s.sum())
    dd = _점[k + "_깊"][s]; return P[s][dd >= 0.8 * dd.max()].mean(0)

X = np.array([1.0, 0, 0]); Y = np.array([0, 1.0, 0]); Z = np.array([0, 0, 1.0])
def 거울(p): return np.array([-p[0], p[1], p[2]])
def 축거울(a): return np.array([a[0], -a[1], -a[2]])          # 축벡터(유사벡터) 거울 = -M a
def 수직(a, d): a = a - (a @ d) * d; return a / np.linalg.norm(a)

# ── 관절 외피 규격 = J2 카탈로그 out/가동/관절규격.json (이름 · 외피반지름 · 폭W · 축사이 · 뼈촉) 에서 고른다 ──
# 자리의 여유(겉까지 − 2.4) 안에 외피반지름이 드는 가장 큰 것. 없으면 가장 작은 것 + 「여유부족」 표시.
# 볼 = 외피 구 · 회전축 = 원기둥(길이 축길이+1) · 힌지 = 원기둥(폭 W) · 이중힌지 = 두 원기둥 볼록 껍질(축사이 고정).
_규 = json.load(open(os.path.join(OUT, "관절규격.json"), encoding="utf-8"))
_종 = {"볼소켓": "볼", "회전축": "축", "힌지": "힌지", "이중힌지": "이중힌지"}
후보 = {}
for k, v in _규.items():
    if v.get("종류") in _종:
        c_ = v.get("치수", {}); 후보.setdefault(_종[v["종류"]], []).append(dict(이름=k, R=v["외피반지름"], W=c_.get("폭W"), 축사이=c_.get("축사이"),
                                                                           길이=c_.get("축길이", 7.0) + 1.0, 결합=v.get("결합", {})))
for v in 후보.values(): v.sort(key=lambda e: -e["R"])

관절 = []
def 관(이름_, 부모, 자식, 종류, p, a, 범위, 자리=None, 최대R=99.0, **_):
    """자리 = 여유를 재는 점들 (없으면 피벗). 이중힌지는 자리[1] 방향으로 J2 축사이만큼 떨어진 곳이 둘째 축."""
    p = np.asarray(p, float); a = np.asarray(a, float) / np.linalg.norm(a)
    자리 = [p] if 자리 is None else [np.asarray(s, float) for s in 자리]
    여유1 = min(깊이(s) for s in 자리) - 두께
    for e in 후보[종류]:
        if e["R"] > 최대R: continue
        자 = 자리
        if 종류 == "이중힌지": u = 자리[1] - p; u -= (u @ a) * a; 자 = [p, p + e["축사이"] * u / np.linalg.norm(u)]
        여유 = min(깊이(s) for s in 자) - 두께
        if e["R"] <= 여유: break
    j = dict(이름=이름_, 부모=부모, 자식=자식, 종류=종류, 규격=e["이름"] + ("" if e["R"] <= 여유 else "(여유부족)"),
             피벗=p, 축=a, 범위=범위, 외피R=e["R"], 여유=여유, 결합=e["결합"])
    if 종류 == "축": j["외피길이"] = e["길이"]
    if 종류 in ("힌지", "이중힌지"): j["외피폭"] = e["W"]
    if 종류 == "이중힌지": j["피벗2"] = 자[1]
    관절.append(j); return j

# ── 몸통 · 목 · 머리 (가운데 · x=0 에 붙임) ──────────────────────
def 가운(p): p = np.array(p, float); p[0] = 0.0; return p
p허회 = 가운(단면중심("복부", 121.0))
p가복 = 가운(단면중심("복부", 130.5))
p목아 = 가운(단면중심("가슴+머리", 146.0))
p목위 = 가운(단면중심("머리", 154.0))                    # 두 볼 사이 16 mm — 볼12 둘이면 외피가 겹쳐 목뼈가 없어진다 → 목 볼은 10 까지
관("목아래", "가슴", "목", "볼", p목아, Z, [[X, -15, 15], [Y, -15, 15], [Z, -30, 30]], 최대R=7.9)
관("목위", "목", "머리", "볼", p목위, Z, [[X, -25, 20], [Y, -15, 15], [Z, -45, 45]], 최대R=7.9)   # 볼 27° 한계 · 위로 = 목위 25 + 목아래 15 = 40
관("가슴복부", "복부", "가슴", "볼", p가복, Z, [[X, -15, 20], [Y, -15, 15], [Z, -30, 30]])
관("복부허리", "허리", "복부", "축", p허회, Z, [[Z, -45, 45]], 길이=8.0)

# ── 다리 (왼쪽을 짓고 거울) ──────────────────────────────────────
d허 = 주축("L허벅지"); d정 = 주축("L정강이")
p고 = 단면중심("L허벅지", 103.0, d허)
p허벅회 = 단면중심("L허벅지", 94.0, d허)
p무1 = 단면중심("L무릎+L허벅지+L정강이", 84.0); p무2 = 단면중심("L무릎+L정강이", 77.0)
p발목 = 단면중심("L정강이", 35.0, d정); p발목[2] = mm([0, 0, 30.0])[2]
p발끝 = 단면중심("L발", d=Y, 기준=mm([0, 90.0, 25.0]))    # 3바퀴: +4 칸 뒤 — 힌지 자식 혀+깃(12) 이 발끝 밖으로 안 나가게
p발앞 = 단면중심("L발", d=Y, 기준=mm([0, 79.0, 25.0])); p뒤꿈 = 단면중심("L발", d=Y, 기준=mm([0, 110.0, 25.0]))
a무 = 수직(X, d정)
다리 = [
    # J2: 볼 소켓 전방향 흔들림은 기하상 27° 한계 → 27° 넘는 볼은 건프라식 조합으로.
    # 고관절 = 벌림 힌지(골반 속, 피벗 16 mm 위 · 3 mm 안쪽) + 앞차기 힌지(고관절 자리) · 비틀기는 허벅지회전이 맡는다.
    ("L고관절벌림", "허리", "L고관절블록", "힌지", p고 + Z * 16.0 + X * 3.0, Y, [[Y, -10, 45]], {}),
    ("L고관절", "L고관절블록", "L허벅지위", "힌지", p고, -X, [[-X, -30, 90]], {}),
    ("L허벅지회전", "L허벅지위", "L허벅지", "축", p허벅회, d허, [[d허, -45, 45]], dict(길이=8.0)),
    ("L무릎", "L허벅지", "L정강이", "이중힌지", p무1, a무, [[a무, 0, 150]], dict(자리=[p무1, p무2])),
    # 발목 = 볼(옆 ±25 · 비틀기 ±15 · 앞뒤 ±10, 27° 안) 을 정강이 속 17 mm 위에 + 앞뒤 힌지 ±30 (발목 자리)
    ("L발목볼", "L정강이", "L발목블록", "볼", p발목 - d정 * 17.0, d정, [[X, -10, 10], [Y, -25, 25], [d정, -15, 15]], {}),
    ("L발목", "L발목블록", "L발", "힌지", p발목, X, [[X, -30, 30]], {}),
    ("L발끝", "L발", "L발끝", "힌지", p발끝, X, [[X, -30, 20]], {}),
]
for n_, 부, 자, 종, p, a, 범, kw in 다리:
    j = 관(n_, 부, 자, 종, p, a, 범, **kw)
    r = dict(j); r.update(이름="R" + n_[1:], 부모=부.replace("L", "R", 1) if 부.startswith("L") else 부, 자식="R" + 자[1:],
                        피벗=거울(j["피벗"]), 축=거울(j["축"]), 범위=[[축거울(np.asarray(v)), lo, hi] for v, lo, hi in 범])
    if "피벗2" in j: r["피벗2"] = 거울(j["피벗2"])
    관절.append(r)

# ── 어깨 (몸통 안이라 좌우 같게) · 팔 (좌우 따로) ───────────────────
# 어깨 높이 = 가슴과 윗팔이 붙는 다리(x 색인 83 세로면)에서 겉까지 가장 먼 곳 (z 138~152). 윗팔은 z 140 아래에서 가슴과 떨어져 있다.
xq = 칸(mm([축i - 17.0, 0, 0]))[0]; 면 = 깊[xq].copy(); zq = [칸(mm([0, 0, z]))[2] for z in (138.0, 152.0)]
면[:, :zq[0]] = -9; 면[:, zq[1]:] = -9; yq, zq_ = np.unravel_index(np.argmax(면), 면.shape)
ps = np.array([ax_mm[0][xq], ax_mm[1][yq], ax_mm[2][zq_]]); 어깨z192 = (zq_ - 0.5) / 2
print("어깨 다리: x %.1f mm 에서 겉까지 최대 %.1f mm (z %.1f mm · 192 색인 %.1f)" % (ps[0], 면.max(), ps[2], 어깨z192))
# 3바퀴: J2 실물 길이로 배치 — 스윙(z 축 · 받이 R 6.5) 은 x −12.5 · 회전(x 축) 은 x −29.5 · z +7.5 (스윙 자식 깃 위로 링크가 넘어가게)
p회L = np.array([-13.5 - 17.0, ps[1], ps[2] + 5.5]); p스L = np.array([-13.5, ps[1], ps[2]])   # 스윙 깃(R 6.5) 이 목 소켓(R 7.5) 에 안 닿게 13.5
어깨 = [("어깨스윙", "가슴", "어깨축", "축", p스L, Z, [[Z, -15, 30]], dict(길이=8.0)),
        ("어깨회전", "어깨축", "어깨블록", "축", p회L, -X, [[-X, -180, 180]], dict(길이=6.0))]
for n_, 부, 자, 종, p, a, 범, kw in 어깨:
    j = 관("L" + n_, 부 if 부 == "가슴" else "L" + 부, "L" + 자, 종, p, a, 범, **kw)
    r = dict(j); r.update(이름="R" + n_, 부모=부 if 부 == "가슴" else "R" + 부, 자식="R" + 자, 피벗=거울(p), 축=거울(np.asarray(a, float)),
                        범위=[[축거울(np.asarray(v)), lo, hi] for v, lo, hi in 범])
    관절.append(r)
# 팔: 어깨들기 ~ 팔끝회전은 L 을 짓고 R 은 거울 (1바퀴 비평 공통 3 — 좌우 피벗 2~6 mm · 축 ~10° 어긋남). 무기 쥠만 좌우 따로.
d윗 = 주축("L윗팔"); d끝 = 주축("L팔끝")
p들 = 단면중심("L윗팔+L어깨", 어깨z192 - 1.0)
p팔1 = 단면중심("L윗팔", 126.0, d윗); p팔2 = 단면중심("L팔끝", 120.0, d끝)      # 3바퀴: +3 칸 위 — 팔꿈치 자식 포크(11.4) 가 팔끝회전 받이에 안 닿게
d윗 = (p팔1 - p들) / np.linalg.norm(p팔1 - p들)                # 윗팔회전 축 = 윗팔 원통 축 (들기 피벗 → 팔꿈치 피벗) (D3)
# 피벗 = 그 축 위에서 좌우 둘 다 겉까지 가장 먼 곳 (들기 · 팔꿈치 외피와 안 겹치는 구간 안)
p윗회 = p들 + d윗 * 21.5        # 3바퀴: 들기 자식 혀(≈12) + 윗팔회전 받이(8.7) 가 안 겹치는 거리 (J2 실물)
p끝회 = 단면중심("L팔끝", 108.0, d끝)
a팔 = 수직(-X, d윗)
팔 = [("어깨들기", "어깨블록", "윗팔위", "힌지", p들, Y, [[Y, 0, 90]], {}),
      ("윗팔회전", "윗팔위", "윗팔", "축", p윗회, d윗, [[d윗, -90, 90]], {}),
      ("팔꿈치", "윗팔", "팔끝", "이중힌지", p팔1, a팔, [[a팔, 0, 150]], dict(자리=[p팔1, p팔2])),
      ("팔끝회전", "팔끝", "손", "축", p끝회, d끝, [[d끝, -90, 90]], {})]
for n_, 부, 자, 종, p, a, 범, kw in 팔:
    j = 관("L" + n_, "L" + 부, "L" + 자, 종, p, a, 범, **kw)
    r = dict(j); r.update(이름="R" + n_, 부모="R" + 부, 자식="R" + 자, 피벗=거울(j["피벗"]), 축=거울(j["축"]),
                        범위=[[축거울(np.asarray(v)), lo, hi] for v, lo, hi in 범])
    if "피벗2" in j: r["피벗2"] = 거울(j["피벗2"])
    r["여유"] = min(깊이(r["피벗"]), 깊이(r.get("피벗2", r["피벗"]))) - 두께        # R 몸에서 다시 잰 여유
    관절.append(r)
for s in "LR":
    # 무기 쥠: E13 원통(칼막대 / 대포통) 축 위. 외피 = 꽂이 윗끝(손 뼈가 닿는 곳)에서 축 아래로 회전축 길이만큼, 크기는 그 자리 여유로
    c = 막대["칼" if s == "L" else "대포"]; m_, d_ = np.array(c["점"]), np.array(c["축"])
    a = mm(m_ + d_) - mm(m_); a /= np.linalg.norm(a)
    # 외피 자리: 대포 = 꽂이 아래쪽(t가름+2 칸 · 위는 거울 팔끝회전 자리) · 칼 = 꽂이 윗끝에서 손 속으로 8 mm (꽂이 자리는 겉까지 2.5 mm 뿐 — 칼 꽂이를 손 속 축까지 늘려야)
    mid = mm(m_ + (c["t가름"] + 10.0) * d_) + 8.0 * a if s == "L" else mm(m_ + (c["t가름"] - 8.0) * d_)
    j = 관(s + ("칼쥠" if s == "L" else "대포쥠"), s + "손", s + ("칼" if s == "L" else "대포"), "축", mid, a, [[a, -180, 180]])
    j["끼움"] = "E13 %s 원통(Ø%.1f · 꽂이 10 칸) 축 위 · 손 소켓에서 무기가 돈다. 외피 윗끝 = 꽂이 윗끝" % ("칼막대" if s == "L" else "대포통", 2 * c["반지름"] * C)
J = {j["이름"]: j for j in 관절}








# ════════ 뼈 = J2 관절 부품 사이 링크 (3바퀴 · 09-26) ════════════════════════════
# 관절마다 J2 부품(관절부품.만들기)을 피벗 · 축에 놓고(틀 = J4 장갑.py 관절틀과 같은 규칙), 부모 부품 결합 구멍 ↔ 자식 부품 결합 구멍
# 사이를 캡슐 링크가 잇는다. 양 끝 D 촉(구멍 − 2×0.20). 링크가 안 나오면(부품끼리 닿음 · 입구 사이 < 4) 그 뼈의 J2 부품을
# 결합 없는 판으로 바꿔 뼈 메시에 통합한다(관절 부품 + 링크 한 덩어리). 장갑 결합 = 뼈 쪽 구멍 Ø2.2 × 3 (장갑 보스 촉 Ø2.0).
import trimesh, 관절부품 as JB
J2캐시 = os.path.join(OUT, "_J2캐시"); os.makedirs(J2캐시, exist_ok=True); os.makedirs(os.path.join(OUT, "관절배치"), exist_ok=True)
def 만(v, f): return mf.Manifold(mf.Mesh(vert_properties=np.ascontiguousarray(v, np.float32), tri_verts=np.ascontiguousarray(f, np.uint32)))
def 트(m): g = m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
def 저장(m, path): 트(m).export(path)
r3 = lambda a: [round(float(x), 2) for x in a]
_J2 = {}
def J2(g, 결합=True):
    """규격 g 의 J2 부품 (결합 구멍 있음/없음) — 캐시. 반환 dict(부품={이름: Manifold}, 표)."""
    k = (g, 결합)
    if k in _J2: return _J2[k]
    base = os.path.join(J2캐시, "%s_%s" % (g, "결합" if 결합 else "통합"))
    if os.path.exists(base + ".npz"):
        d = np.load(base + ".npz"); 표 = json.load(open(base + ".json", encoding="utf-8"))
        부품 = {n: 만(d[n + "_v"], d[n + "_f"]) for n in 표["부품이름"]}
    else:
        j = JB.만들기(g, 결합=결합); 부품 = JB.부품들(j); 표 = JB.표(j); 표["부품이름"] = list(부품)
        np.savez_compressed(base + ".npz", **{n + s_: np.asarray(getattr(트(m), a)) for n, m in 부품.items() for s_, a in (("_v", "vertices"), ("_f", "faces"))})
        json.dump(표, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False)
        print("  J2 %s(%s) 만듦" % (g, "결합" if 결합 else "통합"), flush=True)
    _J2[k] = dict(부품=부품, 표=표); return _J2[k]
def 단(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def 놓기(m, R, t): return m.transform(np.c_[R, np.asarray(t, float)])
def 돌림(a):                                  # z → a 회전 행렬
    a = 단(a); v = np.cross(Z, a); c = a @ Z
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def 볼록덧(m, d, n=26):
    v = np.asarray(m.to_mesh().vert_properties)[:, :3]
    k = np.arange(n) + 0.5; φ = np.arccos(1 - 2 * k / n); θ = np.pi * (1 + 5 ** 0.5) * k
    dirs = np.c_[np.cos(θ) * np.sin(φ), np.sin(θ) * np.sin(φ), np.cos(φ)]
    return mf.Manifold.hull_points((v[:, None, :] + d * dirs[None]).reshape(-1, 3))
def 캡슐(a, b, ra, rb, seg=32): return mf.Manifold.batch_hull([mf.Manifold.sphere(ra, seg).translate(tuple(a)), mf.Manifold.sphere(rb, seg).translate(tuple(b))])
def 상자겹침(a, b, 여유=0.0):
    A, Bb = a.bounding_box(), b.bounding_box()
    return all(A[i] - 여유 <= Bb[i + 3] and Bb[i] - 여유 <= A[i + 3] for i in range(3))
def 겹침(a, b): return (a ^ b).volume() if 상자겹침(a, b) else 0.0

# ── 틀 (지역 → 세계) : z = 자식 쪽 · 힌지 x = 관절 축 (관절부품.py 좌표 · J4 관절틀과 같은 규칙) ──
뼈이름 = sorted(({j["부모"] for j in 관절} | {j["자식"] for j in 관절}) - {"L칼", "R대포"})
def 자식방향(j):
    다음 = [k["피벗"] for k in 관절 if k["부모"] == j["자식"]]
    if 다음: return 단(np.mean(다음, 0) - j["피벗"])
    return {"머리": Z, "L발끝": -Y, "R발끝": -Y, "L칼": -j["축"], "R대포": -j["축"]}[j["자식"]]
def 틀(j):
    a = j["축"]; 자 = 자식방향(j)
    if j["종류"] in ("볼", "축"):
        z = a if a @ 자 >= 0 else -a
        x = 단(np.cross(Y, z)) if abs(z @ Y) < 0.9 else 단(np.cross(Z, z))
    else:
        x = a; 자 = (j["피벗2"] - j["피벗"]) if j["종류"] == "이중힌지" else 자 * 1.0
        z = 단(자 - (자 @ x) * x)
    return np.c_[x, np.cross(z, x), z]
for j in 관절: j["틀"] = 틀(j); j["규격이름"] = j["규격"].split("(")[0]

# ── 뼈마다 끝(관절 부품 쪽) 모으기 ──
끝 = {n: [] for n in 뼈이름}
for j in 관절:
    for 쪽 in ("부모", "자식"):
        n = j[쪽]
        if n in 끝: 끝[n].append(dict(관절=j, 쪽=쪽))
def 부품놓기(e, 결합):
    j = e["관절"]; d = J2(j["규격이름"], 결합); 표 = d["표"]; R, p = j["틀"], j["피벗"]
    m = d["부품"][e["쪽"]]
    e["m"] = 놓기(m, R, p); e["표"] = 표; e["결합"] = 결합
    b = J2(j["규격이름"], True)["표"]["결합"][e["쪽"]]; e["구멍"] = b
    if 결합:
        sgn = 1 if b["방향"] == "+z" else -1
        e["E"] = R @ np.array(b["입구xyz"], float) + p; e["d_in"] = sgn * R[:, 2]
    else:
        bb = m.bounding_box(); zf = bb[2] if e["쪽"] == "부모" else bb[5]
        e["E"] = R @ np.array([0, 0, zf]) + p; e["d_in"] = (1 if e["쪽"] == "부모" else -1) * R[:, 2]
    e["d_out"] = -e["d_in"]
    return e

# ── 링크 반지름: 축 위 표본에서 (겉까지 − 2.4 − 0.3) 최소 · [하한, 5] ──
def 링크r(a, b, 하한=2.5):
    ts = np.linspace(0, 1, 25); r = min(깊이(a + t * (b - a)) for t in ts) - 두께 - 0.3
    return float(np.clip(r, 하한, 5.0))

뼈메시 = {}; 뼈기록 = {}; 통합표 = {}; 장갑구멍 = {}
모든부품 = []   # (뼈 · 관절 · 쪽 · Manifold) 배치된 J2 부품 (검사용)
for n in 뼈이름:                                   # 1 차: 부품 전부 먼저 놓고 통합 여부 결정
    es = 끝[n]
    for e in es: 부품놓기(e, True)
    통합 = False; 이유 = ""
    for i in range(len(es)):
        for k in range(i + 1, len(es)):
            v = 겹침(es[i]["m"], es[k]["m"]); dist = np.linalg.norm(es[i]["E"] - es[k]["E"])
            if v > 0.01: 통합 = True; 이유 = "부품 닿음 %s·%s %.0f" % (es[i]["관절"]["이름"], es[k]["관절"]["이름"], v)
            elif dist < 4.0: 통합 = True; 이유 = "입구 사이 %.1f" % dist
    if 통합:
        for e in es: 부품놓기(e, False)
    통합표[n] = dict(통합=통합, 이유=이유)
    for e in es:
        e["촉d"] = (e["구멍"]["구멍지름"] - 2 * JB.결합틈) if not 통합 else 0.0
        모든부품.append((n, e["관절"]["이름"], e["쪽"], e["m"]))
for j in 관절:                                    # 링크 · 핀도 놓는다
    d = J2(j["규격이름"], True); s_ = d["표"]["치수"].get("축사이", 0.0)
    for k, m in d["부품"].items():
        if k in ("부모", "자식"): continue
        모든부품.append((None, j["이름"], k, 놓기(m.translate([0, 0, s_]) if k == "핀2" else m, j["틀"], j["피벗"])))
def 남의부품(n, m, 여유=0.5): return [mm_ for (bn, jn, k, mm_) in 모든부품 if bn != n and 상자겹침(mm_, m, 여유)]
for n in 뼈이름:                                   # 2 차: 링크
    es = 끝[n]; 통합, 이유 = 통합표[n]["통합"], 통합표[n]["이유"]
    # A = 링크 시작점: 링크 모드 = 입구에서 r+0.3 밖(구 끝이 입구 면에 닿음) · 통합 = 부품 끝에서 r−1 밖(구가 1 mm 만 부품에 물림 — 소켓 바닥 1.2 를 뚫지 않게)
    def A점(e, r): return e["E"] + e["d_out"] * ((r + 0.3) if not 통합 else (max(r - 1.0, 0.5) if e["쪽"] == "부모" else 0.5))   # 통합 자식 깃은 속이 차 있어 구가 들어가도 된다
    if len(es) == 1:
        e = es[0]; r = max(2.5, e["촉d"] / 2 + 0.6); e["r"] = r; e["A"] = A점(e, r)
        # 토막 방향: 밖(d_out) · 그에 수직한 네 방향 중 겉까지 ≥ 2.4+r 가 가장 길게 이어지는 쪽 (머리 · 발끝은 곧게 뻗으면 몸 밖)
        후보 = [e["d_out"]] + [단(v - (v @ e["d_in"]) * e["d_in"]) * sg for v in (X, Z) for sg in (1, -1) if np.linalg.norm(v - (v @ e["d_in"]) * e["d_in"]) > 0.3]
        def 길이(dv):
            t = 0.0
            while t < 12.0 and 깊이(e["A"] + (t + 0.5) * dv) >= 두께 + r: t += 0.5
            return t
        dv = max(후보, key=길이); 허브 = e["A"] + max(길이(dv), 3.0) * dv
        토막 = [(e["A"], 허브, r, r)]
    else:
        중심 = np.mean([e["E"] for e in es], 0)
        for e in es:
            r = 링크r(e["E"], 중심, max(2.5, e["촉d"] / 2 + 0.6)); e["r"] = r; e["A"] = A점(e, r)
        # 끝 A 들을 최소 신장 트리로 잇는다 (허브를 두면 허브가 부품 속에 들어가 링크가 잘렸다 — 허리)
        토막 = []; 남은 = list(range(1, len(es))); 든 = [0]
        while 남은:
            i, k = min(((i, k) for i in 든 for k in 남은), key=lambda t: np.linalg.norm(es[t[0]]["A"] - es[t[1]]["A"]))
            든.append(k); 남은.remove(k)
            if 통합 and (es[i]["m"] ^ es[k]["m"]).volume() > 0.01: continue     # 통합 부품끼리 이미 물려 있으면 그 사이 링크는 없다
            토막.append((es[i]["A"], es[k]["A"], es[i]["r"], es[k]["r"]))
    링크 = mf.Manifold.batch_boolean([캡슐(a, b, ra, rb) for a, b, ra, rb in 토막], mf.OpType.Add) if 토막 else mf.Manifold()
    빼기 = [볼록덧(m, 0.3) for m in (남의부품(n, 링크) if not 링크.is_empty() else [])] + ([e["m"] for e in es] if not 통합 else [])
    if 빼기: 링크 = 링크 - mf.Manifold.batch_boolean(빼기, mf.OpType.Add)
    # 장갑 구멍 Ø2.2 × 3 : 가장 긴 토막(≥ 6) 의 30 % · 70 % · 앞(−y)/뒤(+y) 겉에서 안으로. 반지름 < 3.6 이면 그 자리에 보스 구(R 3.6) 를 덧대고(몸 안이면) 뚫는다
    구멍들 = []
    if 토막:
        a, b, ra, rb = max(토막, key=lambda t: np.linalg.norm(t[1] - t[0])); L = np.linalg.norm(b - a); 축 = 단(b - a)
        if L >= 3.0:
            for t, 쪽v in (((0.3, -Y), (0.7, Y)) if L >= 6.0 else ((0.5, -Y),)):
                d = 쪽v - (쪽v @ 축) * 축
                if np.linalg.norm(d) < 0.3: d = X - (X @ 축) * 축
                d = 단(d); c = a + t * (b - a); r = ra + t * (rb - ra)
                if r < 3.6:
                    if 깊이(c) < 두께 + 3.6: continue
                    링크 = 링크 + mf.Manifold.sphere(3.6, 32).translate(tuple(c)); r = 3.6
                겉점 = c + d * r
                링크 = 링크 - 놓기(mf.Manifold.cylinder(3.5, 1.1, 1.1, 32), 돌림(-d), 겉점 + d * 0.5)
                구멍들.append(dict(위치mm=r3(겉점), 방향=r3(-d), 지름=2.2, 깊이=3.0))
    if not 구멍들 and 통합:      # 링크가 없는 통합 뼈: 끝마다 부품 옆(앞/뒤)에 보스 구 R 3.6 을 덧대고(몸 안 · 남의 부품과 안 닿을 때만) 뚫는다
        for e in sorted(es, key=lambda e: e["쪽"] != "자식"):
            v = np.asarray(e["m"].to_mesh().vert_properties)[:, :3]; c0 = e["E"] + e["d_in"] * 2.5
            for 쪽v in (-Y, Y):
                lat = 쪽v - (쪽v @ e["d_in"]) * e["d_in"]
                if np.linalg.norm(lat) < 0.3: lat = X - (X @ e["d_in"]) * e["d_in"]
                lat = 단(lat); w = float(((v - c0) @ lat).max()) + 2.0; c = c0 + lat * w
                if 깊이(c) < 두께 + 3.6: continue
                보스 = mf.Manifold.sphere(3.6, 32).translate(tuple(c))
                if any(겹침(보스, m) > 0.01 for m in 남의부품(n, 보스)): continue
                겉점 = c + lat * 3.6
                링크 = 링크 + 보스 - 놓기(mf.Manifold.cylinder(3.5, 1.1, 1.1, 32), 돌림(-lat), 겉점 + lat * 0.5)
                구멍들.append(dict(위치mm=r3(겉점), 방향=r3(-lat), 지름=2.2, 깊이=3.0, 보스="구 R3.6"))
                break
            if len(구멍들) >= 2: break
    장갑구멍[n] = 구멍들
    촉들 = []
    if not 통합:
        for e in es:
            b = e["구멍"]; 면 = b["구멍지름"] / 2 - b["D컷"] - JB.결합틈
            m = JB.D구멍z(e["촉d"], -2.5, b["깊이"] - 0.3, 컷=e["촉d"] / 2 - 면)      # 지역: +z 가 구멍 속 · D 면 +y
            R = e["관절"]["틀"]; sgn = 1 if b["방향"] == "+z" else -1
            Rz = np.c_[sgn * R[:, 0], R[:, 1], sgn * R[:, 2]]                      # 부품 지역 y(D 면) 그대로 · z 를 구멍 속으로
            촉들.append(놓기(m, Rz, e["E"]))
        뼈m = mf.Manifold.batch_boolean([링크] + 촉들, mf.OpType.Add)
    else:
        뼈m = mf.Manifold.batch_boolean([링크] + [e["m"] for e in es], mf.OpType.Add)
    뼈메시[n] = 뼈m
    뼈기록[n] = dict(토막=토막, 촉=촉들, 몸=링크, 끝=es)
    print("  뼈 %-8s 끝 %d %s · 링크 조각 %d · 부피 %.0f" % (n, len(es), "통합(%s)" % 이유 if 통합 else "링크", len(링크.decompose()) if not 링크.is_empty() else 0, 뼈m.volume()), flush=True)

for f in os.listdir(os.path.join(OUT, "관절배치")): os.remove(os.path.join(OUT, "관절배치", f))
for (bn, jn, k, m) in 모든부품: 저장(m, os.path.join(OUT, "관절배치", "관절_%s_%s.stl" % (jn, k)))
for f in os.listdir(os.path.join(OUT, "프레임")): os.remove(os.path.join(OUT, "프레임", f))
for n, m in 뼈메시.items():
    if not m.is_empty(): 저장(m, os.path.join(OUT, "프레임", n + ".stl"))
저장(mf.Manifold.batch_boolean([m for (_, _, _, m) in 모든부품], mf.OpType.Add), os.path.join(OUT, "관절외피.stl"))

# ── 검사 ──
J2겹침 = []
for i in range(len(모든부품)):
    for k in range(i + 1, len(모든부품)):
        (bi, ji, ki, mi), (bk, jk, kk, mk) = 모든부품[i], 모든부품[k]
        if bi is not None and bi == bk and 통합표[bi]["통합"]: continue
        v = 겹침(mi, mk)
        if v > 0.01: J2겹침.append(["%s·%s" % (ji, ki), "%s·%s" % (jk, kk), round(v, 2)])
뼈J2겹침 = []; 촉미접촉 = []; 검 = {}
for n, rec in 뼈기록.items():
    몸 = rec["몸"]
    for (bn, jn, k, m) in 모든부품:
        if bn == n and 통합표[n]["통합"]: continue                    # 통합 부품은 뼈와 한 덩어리 · 링크 모드면 제 부품과도 안 닿아야(촉 빼고)
        v = 겹침(몸, m)
        if v > 0.01: 뼈J2겹침.append([n, "%s·%s" % (jn, k), round(v, 2)])
    for e, 촉 in zip(rec["끝"], rec["촉"]):
        if 겹침(촉, 몸) < 0.5: 촉미접촉.append([n, e["관절"]["이름"]])
    m = 뼈메시[n]; v = np.asarray(m.to_mesh().vert_properties)[:, :3]
    idx = np.array([칸(p) for p in v]); dv = 깊[tuple(idx.T)]
    rs = [ra for _, _, ra, rb in rec["토막"]] + [rb for _, _, ra, rb in rec["토막"]] or [e["r"] for e in rec["끝"]]
    검[n] = dict(최소지름=round(2 * min(rs), 1), 최대지름=round(2 * max(rs), 1), 조각=len(m.decompose()), 부피mm3=round(m.volume(), 1),
                안쪽몫=round(float((dv >= 두께).mean()), 3), 몸밖정점몫=round(float((dv < 0).mean()), 3), 통합=통합표[n]["통합"], 통합이유=통합표[n]["이유"],
                장갑구멍수=len(장갑구멍[n]), 촉=len(rec["촉"]))
뼈끼리 = []
ns = list(뼈메시)
for i in range(len(ns)):
    for k in range(i + 1, len(ns)):
        v = 겹침(뼈메시[ns[i]], 뼈메시[ns[k]])
        if v > 0.01: 뼈끼리.append([ns[i], ns[k], round(v, 2)])
zs_all = np.concatenate([np.asarray(m.to_mesh().vert_properties)[:, 2] for (_, _, _, m) in 모든부품] + [np.asarray(m.to_mesh().vert_properties)[:, 2] for m in 뼈메시.values()])
요약 = dict(J2끼리겹침쌍=len(J2겹침), J2끼리겹침mm3=round(sum(v for _, _, v in J2겹침), 1), 뼈J2겹침쌍=len(뼈J2겹침), 뼈J2겹침mm3=round(sum(v for _, _, v in 뼈J2겹침), 1),
          촉미접촉=촉미접촉, 뼈끼리겹침=뼈끼리, 통합뼈=[n for n in 뼈이름 if 통합표[n]["통합"]], 뼈_최소지름=min(검[n]["최소지름"] for n in 검),
          뼈_안쪽몫=round(float(np.mean([검[n]["안쪽몫"] for n in 검])), 4), 뼈_여러조각=[n for n in 검 if 검[n]["조각"] > 1],
          장갑구멍수=sum(len(v) for v in 장갑구멍.values()), 장갑구멍없는뼈=[n for n in 뼈이름 if not 장갑구멍[n]],
          골격z범위=[round(float(zs_all.min()), 1), round(float(zs_all.max()), 1)], 칸mm=round(h, 3), 몸높이mm=300.0, J2부품수=len(모든부품))
요약["J2끼리겹침"] = J2겹침; 요약["뼈J2겹침"] = 뼈J2겹침

# ── 관절.json (형식 유지 + 장갑구멍 · 통합 · 틀 · 배치파일) ──
def 끝정보(n, 쪽j):
    if n not in 뼈기록: return None
    e = next((e for e in 뼈기록[n]["끝"] if e["관절"] is 쪽j), None)
    if e is None: return None
    if e["결합"]:
        b = e["구멍"]; return dict(뼈끝지름=round(2 * e["r"], 1), 뼈촉지름=round(e["촉d"], 2), 구멍지름=b["구멍지름"], 깊이=b["깊이"], 입구mm=r3(e["E"]), 판정="됨")
    return dict(뼈끝지름=round(2 * e["r"], 1), 뼈촉지름=None, 구멍지름=None, 깊이=None, 입구mm=r3(e["E"]), 판정="통합(부품이 뼈에 한 덩어리)")
out = []
for i, j in enumerate(관절, 1):
    e = dict(번호=i, 이름=j["이름"], 부모뼈=j["부모"], 자식뼈=j["자식"], 종류=j["종류"], 규격=j["규격"], 피벗mm=r3(j["피벗"]), 축=r3(j["축"]),
             범위=[dict(축=r3(a), 최소=lo, 최대=hi) for a, lo, hi in j["범위"]],
             외피=dict(모양={"볼": "구", "축": "원기둥", "힌지": "원기둥", "이중힌지": "두 원기둥 껍질"}[j["종류"]], 반지름mm=round(j["외피R"], 2),
                     **({"길이mm": round(j["외피길이"], 2)} if "외피길이" in j else {}), **({"폭mm": round(j["외피폭"], 2)} if "외피폭" in j else {}),
                     **({"둘째축피벗mm": r3(j["피벗2"])} if "피벗2" in j else {})),
             틀=[r3(j["틀"][:, k]) for k in range(3)],
             피벗여유mm=round(j["여유"], 2), 부모끝=끝정보(j["부모"], j), 자식끝=끝정보(j["자식"], j),
             거울짝=(("R" + j["이름"][1:]) if j["이름"].startswith("L") else ("L" + j["이름"][1:]) if j["이름"].startswith("R") else None),
             배치파일={k: "관절배치/관절_%s_%s.stl" % (j["이름"], k) for (_, jn, k, _) in 모든부품 if jn == j["이름"]})
    if j["이름"][1:] in ("칼쥠", "대포쥠"): e["거울짝"] = None; e["메모"] = j["끼움"]
    if "무릎" in j["이름"]: e["메모"] = "무릎 장갑 연동(굽히면 무릎 장갑이 따라 들림) — 기록만, J4"
    if "팔끝회전" in j["이름"]: e["메모"] = "짐승 머리 입 벌림은 선택 — 이번 판 없음"
    out.append(e)
규격표 = dict(출처="out/가동/관절규격.json (J2) — 이름 · 외피반지름 · 폭W · 축사이 · 뼈촉 그대로",
           틀="관절.json 「틀」 = 지역 x, y, z 축(세계) · 관절부품.py 좌표(피벗 원점 · 부모 −z · 자식 +z · 힌지 축 x). 관절배치/*.stl 은 이 틀로 놓은 J2 부품",
           뼈="뼈 = 부모 부품 결합 구멍 ↔ 자식 부품 결합 구멍 사이 캡슐 링크 + 양 끝 D 촉(구멍 − 2×0.20 · 깊이 5.7 · D 면 = 부품 결합정보). 「통합」 뼈는 J2 부품(결합 없음)이 뼈 메시에 한 덩어리 — 관절배치 STL 도 그 판",
           장갑결합="장갑 보스 촉 Ø2.0 · 뼈 쪽 구멍 Ø2.2 × 깊이 3 (「장갑구멍」 위치 = 뼈 겉점 · 방향 = 뼈 속으로). 반지름 3.6 미만 뼈에는 없음")
json.dump(dict(설명=__doc__, 척도=dict(mm_per_192칸=round(C, 4), 원점="발바닥 중앙 (x 거울 면 · y 바닥 두 칸 평균 · z 바닥)"),
               규격표=규격표, 관절=out,
               뼈={n: dict(마디=[[r3(list(a) + [2 * ra]), r3(list(b) + [2 * rb])] for a, b, ra, rb in 뼈기록[n]["토막"]], 파일="프레임/%s.stl" % n,
                          장갑구멍=장갑구멍[n], **검[n]) for n in 뼈이름}, 요약=요약),
          open(os.path.join(OUT, "관절.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ──
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"
fig, axs = plt.subplots(1, 3, figsize=(22, 12), gridspec_kw=dict(width_ratios=[5, 2.2, 1.3]))
bw = np.argwhere(B.any((1, 2)))[[0, -1], 0]; bd = np.argwhere(B.any((0, 2)))[[0, -1], 0]
색 = plt.cm.tab20(np.linspace(0, 1, 20))
def 그리기(ax_, m, i, fc, alpha):
    t = 트(m); tri = t.vertices[t.faces][:, :, [i, 2]]
    ax_.add_collection(PolyCollection(tri, facecolors=fc, edgecolors="none", alpha=alpha))
for ax_, (i, k, nm) in zip(axs[:2], ((0, 1, "앞 (x-z · 작은 y 쪽에서)"), (1, 0, "옆 (y-z · 작은 y = 앞 = 왼쪽)"))):
    e = (ax_mm[i][0], ax_mm[i][-1], ax_mm[2][0], ax_mm[2][-1])
    ax_.imshow(B.any(k).T, origin="lower", extent=e, cmap="Greys", alpha=0.18)
    ax_.contour(ax_mm[i], ax_mm[2], 안.any(k).T, [0.5], colors="0.55", linewidths=0.6)
    for (_, _, _, m) in 모든부품: 그리기(ax_, mf.Manifold.hull(m), i, (1, 0.2, 0.1), 0.35)
    for c_, (n, m) in enumerate(뼈메시.items()):
        if not m.is_empty(): 그리기(ax_, m, i, 색[c_ % 20][:3], 0.75)
    for n_, j in enumerate(관절, 1):
        p, a = j["피벗"], j["축"]
        ax_.plot(p[i], p[2], "k.", ms=4)
        ax_.annotate("", xy=(p[i] + 14 * a[i], p[2] + 14 * a[2]), xytext=(p[i], p[2]), arrowprops=dict(arrowstyle="->", color="b", lw=1.0))
        dx = (-1 if p[0] < -1 else 1) * 7 if i == 0 else 5
        ax_.text(p[i] + dx, p[2] + 1.5, str(n_), fontsize=8, color="darkred", ha="center")
    ax_.set_title(nm); ax_.set_aspect("equal"); ax_.set_xlabel("mm"); ax_.grid(alpha=0.2)
    ax_.set_ylim(-5, 305); lim = (bw if i == 0 else bd); ax_.set_xlim(ax_mm[i][lim[0]] - 5, ax_mm[i][lim[1]] + 5)
axs[2].axis("off")
axs[2].text(0, 1, "\n".join("%2d %s  %s" % (i, j["이름"], j["규격"]) for i, j in enumerate(관절, 1)) + "\n\n통합 뼈: " + ", ".join(요약["통합뼈"]),
            transform=axs[2].transAxes, fontsize=10, va="top")
fig.suptitle("오메가몬 PG 골격 3바퀴 · 뼈(색 · J2 부품 사이 링크 + D 촉) · J2 부품(빨강 볼록껍질) · 축(파랑) · 회색 선 = 겉에서 2.4 mm 안쪽", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "골격.png"), dpi=90)

print("관절 %d · 뼈 %d · J2 부품 %d" % (len(관절), len(뼈이름), len(모든부품)))
for n, d in 검.items(): print("  뼈 %-8s Ø%4.1f~%4.1f 조각 %d 안쪽몫 %.3f 몸밖 %.3f %s 구멍 %d 촉 %d" % (n, d["최소지름"], d["최대지름"], d["조각"], d["안쪽몫"], d["몸밖정점몫"], "통합(%s)" % d["통합이유"] if d["통합"] else "링크", d["장갑구멍수"], d["촉"]))
print(json.dumps({k: v for k, v in 요약.items() if k not in ("J2끼리겹침", "뼈J2겹침")}, ensure_ascii=False))
print("J2끼리:", J2겹침); print("뼈↔J2:", 뼈J2겹침)
if len(sys.argv) > 1 and sys.argv[1] == "완료":
    open(os.path.join(OUT, "3바퀴_뼈완료.txt"), "w", encoding="utf-8").write("3바퀴 뼈 완료 %s\n%s\n" % (
        __import__("datetime").datetime.now().isoformat(timespec="seconds"), json.dumps({k: v for k, v in 요약.items() if k not in ("J2끼리겹침", "뼈J2겹침")}, ensure_ascii=False)))
