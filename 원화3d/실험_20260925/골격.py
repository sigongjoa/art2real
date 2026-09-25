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
p발끝 = 단면중심("L발", d=Y, 기준=mm([0, 86.0, 25.0]))
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
p회L = ps + X * 6.0; p스L = np.array([mm([축i - 8.0, 0, 0])[0], ps[1], ps[2]])   # 스윙 · 회전 · 들기 외피가 안 겹치게 벌림
어깨 = [("어깨스윙", "가슴", "어깨축", "축", p스L, Z, [[Z, -15, 30]], dict(길이=8.0)),
        ("어깨회전", "어깨축", "어깨블록", "축", p회L, -X, [[-X, -180, 180]], dict(길이=6.0))]
for n_, 부, 자, 종, p, a, 범, kw in 어깨:
    j = 관("L" + n_, 부 if 부 == "가슴" else "L" + 부, "L" + 자, 종, p, a, 범, **kw)
    r = dict(j); r.update(이름="R" + n_, 부모=부 if 부 == "가슴" else "R" + 부, 자식="R" + 자, 피벗=거울(p), 축=거울(np.asarray(a, float)),
                        범위=[[축거울(np.asarray(v)), lo, hi] for v, lo, hi in 범])
    관절.append(r)
for s in "LR":
    sg = 1 if s == "L" else -1
    def 축s(a): return np.asarray(a, float) if s == "L" else 축거울(np.asarray(a, float))
    d윗 = 주축(s + "윗팔"); d끝 = 주축(s + "팔끝")
    p들 = 단면중심(s + "윗팔+" + s + "어깨", 어깨z192 - 1.0)
    p윗회 = 단면중심(s + "윗팔", 130.0, d윗)
    p팔1 = 단면중심(s + "윗팔", 123.0, d윗); p팔2 = 단면중심(s + "팔끝", 117.0, d끝)
    p끝회 = 단면중심(s + "팔끝", 108.0 if s == "L" else 112.0, d끝)
    a팔 = 축s(수직(-X, d윗))
    관(s + "어깨들기", s + "어깨블록", s + "윗팔위", "힌지", p들, 축s(Y), [[축s(Y), 0, 90]])
    관(s + "윗팔회전", s + "윗팔위", s + "윗팔", "축", p윗회, d윗, [[d윗, -90, 90]], 길이=6.0)
    관(s + "팔꿈치", s + "윗팔", s + "팔끝", "이중힌지", p팔1, a팔, [[a팔, 0, 150]], 자리=[p팔1, p팔2])
    관(s + "팔끝회전", s + "팔끝", s + "손", "축", p끝회, d끝, [[d끝, -90, 90]], 길이=6.0)
    # 무기 쥠: E13 원통(칼막대 / 대포통) 축 위. 외피 = 꽂이 윗끝(손 뼈가 닿는 곳)에서 축 아래로 회전축 길이만큼, 크기는 그 자리 여유로
    c = 막대["칼" if s == "L" else "대포"]; m_, d_ = np.array(c["점"]), np.array(c["축"])
    a = mm(m_ + d_) - mm(m_); a /= np.linalg.norm(a)
    # 외피 자리: 대포 = 꽂이 가운데 (위는 팔끝회전 자리) · 칼 = 꽂이 윗끝에서 손 속으로 8 mm (꽂이 자리는 겉까지 2.5 mm 뿐 — 칼 꽂이를 손 속 축까지 늘려야)
    mid = mm(m_ + (c["t가름"] + 10.0) * d_) + 8.0 * a if s == "L" else mm(m_ + (c["t가름"] + 5.0) * d_)
    j = 관(s + ("칼쥠" if s == "L" else "대포쥠"), s + "손", s + ("칼" if s == "L" else "대포"), "축", mid, a, [[a, -180, 180]])
    j["끼움"] = "E13 %s 원통(Ø%.1f · 꽂이 10 칸) 축 위 · 손 소켓에서 무기가 돈다. 외피 윗끝 = 꽂이 윗끝" % ("칼막대" if s == "L" else "대포통", 2 * c["반지름"] * C)
J = {j["이름"]: j for j in 관절}

# ── 뼈 (캡슐 토막들) ─────────────────────────────────────────────
def P(n, k="피벗"): return J[n][k]
def 끝(n): j = J[n]; return j["피벗"] + j["축"] * (j["외피길이"] / 2 + 1.0)
뼈 = {
    "허리": [(P("복부허리"), 가운(단면중심("허리", 106.0))), (P("L고관절벌림"), 가운(단면중심("허리", 106.0))), (가운(단면중심("허리", 106.0)), P("R고관절벌림"))],
    "복부": [(P("복부허리"), P("가슴복부"))],
    "가슴": [(P("가슴복부"), P("목아래")), (P("L어깨스윙"), P("R어깨스윙"))],
    "목": [(P("목아래"), P("목위"))],
    "머리": [(P("목위"), P("목위") + Z * 12)],
}
for s in "LR":
    뼈[s + "허벅지위"] = [(P(s + "고관절"), P(s + "허벅지회전"))]
    뼈[s + "허벅지"] = [(P(s + "허벅지회전"), P(s + "무릎"))]
    뼈[s + "정강이"] = [(P(s + "무릎", "피벗2"), P(s + "발목볼"))]
    뼈[s + "고관절블록"] = [(P(s + "고관절벌림"), P(s + "고관절"))]
    뼈[s + "발목블록"] = [(P(s + "발목볼"), P(s + "발목"))]
    fx = (lambda p: p) if s == "L" else 거울
    뼈[s + "발"] = [(fx(p뒤꿈), P(s + "발끝")), (P(s + "발목"), (fx(p뒤꿈) + P(s + "발끝")) / 2)]   # 뒤꿈치–발끝 막대 + 발목에서 내려오는 기둥
    뼈[s + "발끝"] = [(P(s + "발끝"), fx(p발앞))]
    뼈[s + "어깨축"] = [(P(s + "어깨스윙"), P(s + "어깨회전"))]
    뼈[s + "어깨블록"] = [(P(s + "어깨회전"), P(s + "어깨들기"))]
    뼈[s + "윗팔위"] = [(P(s + "어깨들기"), P(s + "윗팔회전"))]
    뼈[s + "윗팔"] = [(P(s + "윗팔회전"), P(s + "팔꿈치"))]
    뼈[s + "팔끝"] = [(P(s + "팔꿈치", "피벗2"), P(s + "팔끝회전"))]
    쥠 = J[s + ("칼쥠" if s == "L" else "대포쥠")]
    뼈[s + "손"] = [(P(s + "팔끝회전"), 끝(쥠["이름"]))]

def 선거리(G, a, b, 매개=False):                # 점들 G(…,3) 에서 선분 ab 까지 거리 (매개=True 면 t 도)
    ab = b - a; t = np.clip(((G - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    d = np.linalg.norm(G - a - t[..., None] * ab, axis=-1); return (d, t) if 매개 else d
def 외피안(j, G):                             # 관절 외피 안인 점
    p, a, R = j["피벗"], j["축"], j["외피R"]
    if j["종류"] == "볼": return np.linalg.norm(G - p, axis=-1) <= R
    t = (G - p) @ a
    if j["종류"] == "이중힌지":
        q2 = j["피벗2"]; Gp = G - t[..., None] * a
        return (선거리(Gp, p, q2 - ((q2 - p) @ a) * a) <= R) & (np.abs(t) <= j["외피폭"] / 2)
    L = j.get("외피길이", j.get("외피폭"))
    return (np.linalg.norm(G - p - t[..., None] * a, axis=-1) <= R) & (np.abs(t) <= L / 2)

# 뼈 = 토막마다 마디 9 개의 로프트(이웃 마디 구의 볼록 껍질). 마디 반지름 = 앞뒤 1/8 구간 축 위 점에서 (겉까지 − 2.4 − 0.2) 최소,
# 관절 외피 안 점은 가장 가까운 밖 점 값으로. [2, 7] mm 로 자른다 (2 로 올라간 곳 = 여유 부족 → 검사에서 드러난다).
def 마디(a, b):
    ts = np.linspace(0, 1, 41); g = a + ts[:, None] * (b - a)
    r = np.array([np.nan if any(외피안(j, x[None])[0] for j in 관절) else 깊이(x) - 두께 - 0.2 for x in g])
    ok = ~np.isnan(r); 원 = float(np.nanmin(r)) if ok.any() else None
    r = np.interp(np.arange(41), np.nonzero(ok)[0], r[ok]) if ok.any() else np.full(41, 7.0)
    return [(g[i], float(np.clip(r[max(0, i - 5):i + 6].min(), 2.0, 7.0))) for i in range(0, 41, 5)], 원
뼈마디 = {}; 뼈원여유 = {}
거울뼈 = ("허벅지위", "허벅지", "정강이", "발", "발끝", "어깨축", "어깨블록", "고관절블록", "발목블록")
for n, 토막 in 뼈.items():
    if n[0] == "R" and n[1:] in 거울뼈:                     # 거울 뼈는 왼쪽 마디를 뒤집어
        뼈마디[n] = [[(거울(p), r) for p, r in 줄] for 줄 in 뼈마디["L" + n[1:]]]; 뼈원여유[n] = 뼈원여유["L" + n[1:]]; continue
    ms = [마디(a, b) for a, b in 토막]; 뼈마디[n] = [m for m, _ in ms]
    원 = [o for _, o in ms if o is not None]; 뼈원여유[n] = min(원) if 원 else None

# ── 384 칸으로 칠하기 (검사 · 그림) ──────────────────────────────
def 칠(fn, lo, hi):                           # 상자 안 384 칸을 시험 → 칸 번호(평탄) 배열
    sl = [np.arange(max(0, 칸(lo)[k] - 1), min(384, 칸(hi)[k] + 2)) for k in range(3)]
    I = np.stack(np.meshgrid(*sl, indexing="ij"), -1).reshape(-1, 3)
    g = np.stack([ax_mm[k][I[:, k]] for k in range(3)], 1)
    return np.ravel_multi_index(tuple(I[fn(g)].T), (384,) * 3)
def 판(ix): M = np.zeros(384 ** 3, bool); M[ix] = True; return M.reshape((384,) * 3)
관M = {}
for j in 관절:
    R = j["외피R"] + max(j.get("외피길이", 0), j.get("외피폭", 0)) / 2 + (np.linalg.norm(j["피벗2"] - j["피벗"]) if "피벗2" in j else 0)
    관M[j["이름"]] = 칠(lambda g, j=j: 외피안(j, g), j["피벗"] - R, j["피벗"] + R)
외피M = 판(np.concatenate(list(관M.values())))
뼈M = {}
def 로프트안(g, a, b, ra, rb, A, Bp):          # A→Bp = 토막 전체: 양 끝은 토막에 수직인 평면으로 자른다(외피 너머로 삐져나온 머리 없게)
    d, t = 선거리(g, a, b, True); u = (g - A) @ (Bp - A) / ((Bp - A) @ (Bp - A)); return (d <= ra + t * (rb - ra)) & (u >= 0) & (u <= 1)
for n, 줄들 in 뼈마디.items():
    ix = np.unique(np.concatenate([칠(lambda g, a=a, b=b, ra=ra, rb=rb, A=줄[0][0], Bp=줄[-1][0]: 로프트안(g, a, b, ra, rb, A, Bp), np.minimum(a, b) - 7, np.maximum(a, b) + 7)
                                   for 줄 in 줄들 for (a, ra), (b, rb) in zip(줄[:-1], 줄[1:])]))
    뼈M[n] = ix[~외피M.ravel()[ix]]

# ── 메시 (manifold3d) ────────────────────────────────────────────
SEG = 32
def 돌림(a):                                  # z → a 회전 행렬
    a = a / np.linalg.norm(a); v = np.cross(Z, a); c = a @ Z
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def 놓기(m, R, t): return m.transform(np.hstack([R, np.asarray(t, float)[:, None]]).tolist())
def 캡슐(a, b, ra, rb): return mf.Manifold.batch_hull([mf.Manifold.sphere(ra, SEG).translate(tuple(a)), mf.Manifold.sphere(rb, SEG).translate(tuple(b))])
def 외피메시(j):
    p, a, R = j["피벗"], j["축"], j["외피R"]
    if j["종류"] == "볼": return mf.Manifold.sphere(R, SEG).translate(tuple(p))
    L = j.get("외피길이", j.get("외피폭"))
    cy = lambda c: 놓기(mf.Manifold.cylinder(L, R, R, SEG, True), 돌림(a), c)
    if j["종류"] == "이중힌지": return mf.Manifold.batch_hull([cy(p), cy(j["피벗2"])])
    return cy(p)
import trimesh
def 저장(m, path):
    t = m.to_mesh(); trimesh.Trimesh(np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts)).export(path)
외피합 = mf.Manifold.batch_boolean([외피메시(j) for j in 관절], mf.OpType.Add)
저장(외피합, os.path.join(OUT, "관절외피.stl"))
뼈부피 = {}; 뼈메시 = {}
for n, 토막 in 뼈.items():
    if n[0] == "R" and n[1:] in 거울뼈:
        m = 뼈메시["L" + n[1:]].mirror((1, 0, 0))            # 다리 · 어깨축/블록 = 왼쪽 거울
    else:
        def 줄메시(줄):
            A, Bp = 줄[0][0], 줄[-1][0]; d = (Bp - A) / np.linalg.norm(Bp - A)
            m = mf.Manifold.batch_boolean([캡슐(a, b, ra, rb) for (a, ra), (b, rb) in zip(줄[:-1], 줄[1:])], mf.OpType.Add)
            return m.trim_by_plane(tuple(d), float(d @ A)).trim_by_plane(tuple(-d), float(-d @ Bp))
        m = mf.Manifold.batch_boolean([줄메시(줄) for 줄 in 뼈마디[n]], mf.OpType.Add) - 외피합
    if not m.is_empty():                                        # 외피가 잘라 남긴 부스러기(가장 큰 조각의 5 % 미만) 버림
        cs = m.decompose(); vm = max(c.volume() for c in cs); m = mf.Manifold.batch_boolean([c for c in cs if c.volume() >= 0.05 * vm], mf.OpType.Add)
    뼈메시[n] = m; 뼈부피[n] = m.volume()
    if not m.is_empty(): 저장(m, os.path.join(OUT, "프레임", n + ".stl"))

# ── 검사 ─────────────────────────────────────────────────────────
v = h ** 3
검 = {}
안f = 안.ravel(); Bf = B.ravel()
for n, ix in 뼈M.items():
    rs = [r for 줄 in 뼈마디[n] for _, r in 줄]
    s = len(ix); 검[n] = dict(최소지름=round(2 * min(rs), 1), 최대지름=round(2 * max(rs), 1), 축여유=None if 뼈원여유[n] is None else round(뼈원여유[n] + 0.2, 2),
                              칸=int(s), 안쪽몫=round(float(안f[ix].sum() / max(s, 1)), 3), 몸밖mm3=round(float((~Bf[ix]).sum() * v), 1),
                              조각=len(뼈메시[n].decompose()) if not 뼈메시[n].is_empty() else 0, 부피mm3=round(뼈부피[n], 1))
전뼈 = 판(np.concatenate(list(뼈M.values())))
외검 = {n: dict(부피mm3=round(float(len(ix) * v), 1), 장갑층mm3=round(float((Bf[ix] & ~안f[ix]).sum() * v), 1), 몸밖mm3=round(float((~Bf[ix]).sum() * v), 1))
        for n, ix in 관M.items()}
요약 = dict(뼈_안쪽몫=round(float((전뼈 & 안).sum() / 전뼈.sum()), 4), 뼈_몸밖mm3=round(float((전뼈 & ~B).sum() * v), 1),
          뼈_최소지름=min(검[n]["최소지름"] for n in 뼈), 뼈_여유부족=[n for n in 뼈 if 뼈원여유[n] is not None and 뼈원여유[n] < 2.0], 뼈_외피사이만=[n for n in 뼈 if 뼈원여유[n] is None],
          외피_몸밖mm3=round(float((외피M & ~B).sum() * v), 1), 외피_장갑층mm3=round(float((외피M & B & ~안).sum() * v), 1),
          외피_부피mm3=round(float(외피M.sum() * v), 1), 칸mm=round(h, 3), 몸높이mm=300.0)
외피겹침 = []
ns = list(관M)
for i in range(len(ns)):
    for k in range(i + 1, len(ns)):
        o = len(np.intersect1d(관M[ns[i]], 관M[ns[k]], assume_unique=True))
        if o: 외피겹침.append([ns[i], ns[k], round(float(o * v), 1)])
요약["외피_겹침"] = 외피겹침

# ── 관절.json ───────────────────────────────────────────────────
r3 = lambda a: [round(float(x), 2) for x in a]
def 꽂이(n, p, 결):                            # 뼈 끝 = J2 뼈촉(D 컷 돌기)이 관절 부품 구멍에 들어간다. 뼈 끝 마디 지름이 촉+1.2 보다 작으면 표시
    if n not in 뼈마디: return None
    D = 2 * min(((np.linalg.norm(q - p), r) for 줄 in 뼈마디[n] for q, r in 줄), key=lambda t: t[0])[1]
    촉 = 결.get("뼈촉지름")
    return dict(뼈끝지름=round(D, 1), 뼈촉지름=촉, 구멍지름=결.get("구멍지름"), 깊이=결.get("깊이"), 판정="됨" if 촉 and D >= 촉 + 1.2 else "뼈끝 가늚")
out = []
for i, j in enumerate(관절, 1):
    e = dict(번호=i, 이름=j["이름"], 부모뼈=j["부모"], 자식뼈=j["자식"], 종류=j["종류"], 규격=j["규격"], 피벗mm=r3(j["피벗"]), 축=r3(j["축"]),
             범위=[dict(축=r3(a), 최소=lo, 최대=hi) for a, lo, hi in j["범위"]],
             외피=dict(모양={"볼": "구", "축": "원기둥", "힌지": "원기둥", "이중힌지": "두 원기둥 껍질"}[j["종류"]], 반지름mm=round(j["외피R"], 2),
                     **({"길이mm": round(j["외피길이"], 2)} if "외피길이" in j else {}), **({"폭mm": round(j["외피폭"], 2)} if "외피폭" in j else {}),
                     **({"둘째축피벗mm": r3(j["피벗2"])} if "피벗2" in j else {})),
             피벗여유mm=round(j["여유"], 2), 부모끝=꽂이(j["부모"], j["피벗"], j["결합"].get("부모", {})), 자식끝=꽂이(j["자식"], j.get("피벗2", j["피벗"]), j["결합"].get("자식", {})),
             거울짝=(("R" + j["이름"][1:]) if j["이름"].startswith("L") else ("L" + j["이름"][1:]) if j["이름"].startswith("R") else None),
             검사=외검[j["이름"]])
    if j["이름"][1:] in ("칼쥠", "대포쥠"): e["거울짝"] = None; e["메모"] = j["끼움"]
    if "무릎" in j["이름"]: e["메모"] = "무릎 장갑 연동(굽히면 무릎 장갑이 따라 들림) — 기록만, J4"
    if "팔끝회전" in j["이름"]: e["메모"] = "짐승 머리 입 벌림은 선택 — 이번 판 없음"
    out.append(e)
규격표 = dict(출처="out/가동/관절규격.json (J2) — 이름 · 외피반지름 · 폭W · 축사이 · 뼈촉 그대로",
           외피="볼 = 구 R · 회전축 = 원기둥 R × (축길이+1) · 힌지 = 원기둥 R × W · 이중힌지 = 피벗 · 둘째축피벗 두 원기둥 볼록 껍질",
           뼈끝="J2 결합: 뼈 쪽 D 컷 촉(뼈촉지름)이 관절 부품 구멍에 들어간다. 촉은 아직 뼈 메시에 안 붙였다(J2 깊이·D 면 방향 확정 뒤)",
           여유부족="자리 여유(겉까지 − 2.4) 안에 드는 J2 규격이 없어 가장 작은 것을 넣음 — 외피가 장갑층으로 들어간다")
json.dump(dict(설명=__doc__, 척도=dict(mm_per_192칸=round(C, 4), 원점="발바닥 중앙 (x 거울 면 · y 바닥 두 칸 평균 · z 바닥)"),
               규격표=규격표, 관절=out, 뼈={n: dict(마디=[[r3(list(p) + [2 * r]) for p, r in 줄] for 줄 in 뼈마디[n]], 파일="프레임/%s.stl" % n, **검[n]) for n in 뼈}, 요약=요약),
          open(os.path.join(OUT, "관절.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ────────────────────────────────────────────────────────
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
fig, axs = plt.subplots(1, 3, figsize=(22, 12), gridspec_kw=dict(width_ratios=[5, 2.2, 1.3]))
bw = np.argwhere(B.any((1, 2)))[[0, -1], 0]; bd = np.argwhere(B.any((0, 2)))[[0, -1], 0]
색 = plt.cm.tab20(np.linspace(0, 1, 20))
for ax_, (i, k, nm) in zip(axs[:2], ((0, 1, "앞 (x-z · 작은 y 쪽에서)"), (1, 0, "옆 (y-z · 작은 y = 앞 = 왼쪽)"))):
    e = (ax_mm[i][0], ax_mm[i][-1], ax_mm[2][0], ax_mm[2][-1])
    ax_.imshow(B.any(k).T, origin="lower", extent=e, cmap="Greys", alpha=0.18)
    ax_.contour(ax_mm[i], ax_mm[2], 안.any(k).T, [0.5], colors="0.55", linewidths=0.6)
    for c_, (n, ix) in enumerate(뼈M.items()):
        im = np.zeros((384, 384, 4)); I = np.unravel_index(ix, (384,) * 3); pr = np.zeros((384, 384), bool); pr[I[i], I[2]] = True; pr = pr.T
        im[pr] = list(색[c_ % 20][:3]) + [0.85]; ax_.imshow(im, origin="lower", extent=e)
    pr = 외피M.any(k).T; im = np.zeros((384, 384, 4)); im[pr] = [1, 0.2, 0.1, 0.45]; ax_.imshow(im, origin="lower", extent=e)
    for n_, j in enumerate(관절, 1):
        p, a = j["피벗"], j["축"]
        ax_.plot(p[i], p[2], "k.", ms=4)
        ax_.annotate("", xy=(p[i] + 14 * a[i], p[2] + 14 * a[2]), xytext=(p[i], p[2]), arrowprops=dict(arrowstyle="->", color="b", lw=1.0))
        dx = (-1 if p[0] < -1 else 1) * 7 if i == 0 else 5
        ax_.text(p[i] + dx, p[2] + 1.5, str(n_), fontsize=8, color="darkred", ha="center")
    ax_.set_title(nm); ax_.set_aspect("equal"); ax_.set_xlabel("mm"); ax_.grid(alpha=0.2)
    ax_.set_ylim(-5, 305); lim = (bw if i == 0 else bd); ax_.set_xlim(ax_mm[i][lim[0]] - 5, ax_mm[i][lim[1]] + 5)
axs[2].axis("off")
axs[2].text(0, 1, chr(10).join("%2d %s  %s" % (i, j["이름"], j["규격"]) for i, j in enumerate(관절, 1)), transform=axs[2].transAxes, fontsize=10, va="top")

fig.suptitle("오메가몬 PG 골격 · 뼈(색) · 관절 외피(빨강) · 축(파랑) · 회색 선 = 겉에서 2.4 mm 안쪽", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "골격.png"), dpi=90)

print("관절 %d · 뼈 %d · 칸 %.3f mm" % (len(관절), len(뼈), h))
for e in out: print("%2d %-8s %-4s %-8s 여유 %5.1f 외피R %4.1f 몸밖 %6.1f 장갑층 %7.1f" % (e["번호"], e["이름"], e["종류"], e["규격"], e["피벗여유mm"], e["외피"]["반지름mm"], e["검사"]["몸밖mm3"], e["검사"]["장갑층mm3"]))
for n, d in 검.items(): print("  뼈 %-8s Ø%4.1f~%4.1f 축여유 %s 안쪽몫 %.3f 몸밖 %.1f 조각 %d 부피 %.0f" % (n, d["최소지름"], d["최대지름"], d["축여유"], d["안쪽몫"], d["몸밖mm3"], d["조각"], d["부피mm3"]))
print(json.dumps(요약, ensure_ascii=False))
