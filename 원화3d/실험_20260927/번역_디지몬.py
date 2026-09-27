"""번역_디지몬.py — 원작(애니·공식 일러스트) → 피규어(키트) 「번역 규칙」을 오메가몬 정면 비율로 잰다.

python 번역_디지몬.py   -> out/번역/디지몬/비율.json · 비교.png

점은 손으로 찍었다(격자 덮은 확대 그림에서 읽음 · ±3~5 %). 좌표는 아래 표 = 비율.json 의 "점".
모든 길이 ÷ 전고(가운데 뿔 끝 → 발바닥). 우리 모델은 STL 경계(mm), 나머지는 사진·그림 px.
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
ROOT = r"G:\art2real\원화3d"; OUT = os.path.join(ROOT, "out", "번역", "디지몬"); 원작 = os.path.join(OUT, "원작")
키트 = os.path.join(ROOT, "out", "키트")

# ── 손 점 ──  top/sole = 뿔 끝·발바닥 y · head = (투구 윗단 y, 턱 y) · crotch = 골반 V 끝 y · 길이값은 같은 단위(px 또는 mm)
# None = 그 그림에선 못 잰다(가림 · 포즈 · 없음). 0 = 없음(생략).
점 = {
 "원작_tri": dict(file=os.path.join(원작, "Omegamon_tri.png"), crop=[0, 0, 597, 650], top=5, sole=640, head=[50, 95], crotch=330,
    L=dict(head_h=45, head_w=50, horn=45, shoulder=None, chest=105, waist=65, leg=310, garuru=243, war=205, arm=270, cape_w=560, cape_l=470, shield=115, foot=None),
    주="tri. 공식 설정(3/4 · 낮은 앵글) · 어깨 폭은 3/4 라 못 잼 · 발은 원근으로 벌어짐"),
 "원작_설정화": dict(file=os.path.join(원작, "Omegamon1.png"), crop=[180, 60, 660, 860], top=85, sole=800, head=[150, 195], crotch=525,
    L=dict(head_h=45, head_w=55, horn=65, shoulder=265, chest=135, waist=75, leg=275, garuru=190, war=None, arm=320, cape_w=None, cape_l=None, shield=150, foot=None),
    주="2000 극장판 決定稿 선화(초기 · 원근 섞임) · 발톱은 과하게 벌어져 못 잼"),
 "FRA": dict(file=os.path.join(키트, "FRA_오메가몬", "dalong", "frs45_01.jpg"), crop=[320, 0, 880, 750], top=38, sole=700, head=[80, 128], crotch=345,
    L=dict(head_h=48, head_w=45, horn=42, shoulder=285, chest=135, waist=50, leg=355, garuru=217, war=250, arm=450, cape_w=365, cape_l=425, shield=150, foot=145),
    주="Figure-rise Amplified 완성 정면(전고 183 mm · 3.62 px/mm) · 가루루 머리 = 앞 조사 60 mm · 워그 머리는 흰 뿔 뺀 상자"),
 "D-Arts": dict(file=os.path.join(원작, "Darts_omegamon.jpg"), crop=[60, 230, 700, 1000], top=245, sole=955, head=[300, 335], crotch=590,
    L=dict(head_h=35, head_w=35, horn=55, shoulder=None, chest=None, waist=None, leg=365, garuru=200, war=None, arm=None, cape_w=None, cape_l=None, shield=None, foot=None),
    주="D-Arts 공식 사진 — 포즈 · 낮은 앵글이라 다리는 늘고 머리는 줄어 보인다(참고만)"),
 "우리_원화": dict(file=r"G:\art2real\트레일\trail7_part3d\in\omega_front_clean.png", crop=[180, 30, 850, 975], top=45, sole=968, head=[100, 180], crotch=505,
    L=dict(head_h=80, head_w=68, horn=55, shoulder=362, chest=166, waist=100, leg=463, garuru=277, war=285, arm=490, cape_w=0, cape_l=0, shield=150, foot=210),
    주="omega_front_clean.png(망토 없음) · ⚠ 좌우 반전: 원작·키트·D-Arts 는 보는 쪽 왼팔이 가루루"),
 "우리_모델": dict(file=os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인", "조립_3바퀴.png"), crop=[505, 175, 960, 930], top=199, sole=899,
    head=[899 - 293 * 700 / 310, 899 - 263 * 700 / 310], crotch=899 - 152 * 700 / 310,
    L=dict(head_h=30, head_w=28, horn=17, shoulder=111, chest=58, waist=30, leg=152, garuru=81, war=80, arm=182, cape_w=0, cape_l=0, shield=50, foot=60),
    H_mm=310, 주="STL 경계(mm · 전고 310) — 투구 263~293 · 어깨돔 −51~60 · 가슴앞 58 · 복부 30 · V 끝 152 · R팔끝 160~241 · L팔끝 160~240(뿔) · 돔 274→대포 92 · 방패 50 · 발(발톱 포함) 60"),
}
이름 = dict(head_h="머리 높이", head_w="머리 폭", horn="뿔(투구 위)", shoulder="어깨 폭(돔 포함)", chest="가슴 폭", waist="허리 폭",
          leg="다리 길이(V→바닥)", garuru="가루루 팔머리 길이", war="워그 팔머리 길이", arm="팔 길이(돔→끝)", cape_w="망토 폭", cape_l="망토 길이",
          shield="방패 길이", foot="발 폭(발톱 포함)")


def 비율(k):
    d = 점[k]; H = d.get("H_mm") or (d["sole"] - d["top"])
    return {m: (None if v is None else round(v / H, 3)) for m, v in d["L"].items()}


R = {k: 비율(k) for k in 점}
# 자기 검사: 전고 비는 0~1, 다리 + 머리 < 1
for k, r in R.items():
    assert all(v is None or 0 <= v < 1 for v in r.values()), k
    assert r["leg"] + r["head_h"] < 1, k

# 분류(과장 / 생략 / 생산) — 원작(tri·설정화) → FRA
분류 = {
 "leg": ("과장", "원작 0.39~0.49 → FRA 0.54 · 긴 다리 = 영웅 비례(D-Arts 도 0.51)"),
 "waist": ("과장", "원작 0.10 → FRA 0.076 · 허리를 25 % 조여 가슴·어깨가 넓어 보이게"),
 "shoulder": ("과장", "설정화 0.37 → FRA 0.43 · 어깨돔을 키워 역삼각"),
 "chest": ("유지", "0.17~0.19 → 0.20 · 차이 작다"),
 "head_h": ("유지(작게)", "원작 0.06~0.07 = FRA 0.073 · 키트는 원작의 작은 머리를 그대로 둔다"),
 "horn": ("생산", "tri 0.071 · 설정화 0.091 → FRA 0.063 · 뾰족한 끝을 짧게(파손·안전)"),
 "garuru": ("유지~약간 과장", "원작 0.27~0.38 → FRA 0.33 · 원작부터 팔머리가 크다 — 키트가 새로 키운 게 아니다"),
 "war": ("유지", "tri 0.32 → FRA 0.38(흰 뿔 빼고) · 잡는 법 오차 안"),
 "cape_w": ("생략", "tri 0.88 → FRA 0.55 · 펄럭이는 천을 몸 뒤 판 넷으로 접음"),
 "cape_l": ("생략", "tri 0.74 → FRA 0.64 · 바닥까지 안 끌림(자립·출력)"),
 "arm": ("생산(포즈)", "원작은 팔을 굽혀 0.42~0.45 · 키트는 곧게 내려 0.68 — 비율보다 차렷 포즈 탓"),
 "shield": ("과장", "tri 0.18 → FRA 0.23 · 등 뒤로 돌려 실루엣을 키움"),
 "foot": ("생산", "FRA 0.22 · 자립 면적(원작 발은 원근으로 못 잼)"),
}

json.dump(dict(설명="정면 · 전고(뿔 끝→발바닥)로 나눈 비 · 손 점 ±3~5 % · 포즈 탓 항목은 분류에 적음", 비율=R, 분류=분류,
               점={k: {kk: vv for kk, vv in d.items() if kk != "file"} | {"file": d["file"]} for k, d in 점.items()}),
          open(os.path.join(OUT, "비율.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ──
fig = plt.figure(figsize=(26, 16))
열 = list(점)
FW, FH, h_in = 26, 16, 5.6   # 윗줄 높이(인치) 같게 → 전고 맞춤
xl = 0.004
for i, k in enumerate(열):
    d = 점[k]; x0, y0, x1, y1 = d["crop"]; im = Image.open(d["file"]).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
    # 전고 맞춤: 뿔 끝 = 0, 발바닥 = 1 · 칸 너비 = 자른 폭 비례
    H = d["sole"] - d["top"]; wf = (x1 - x0) / H / 1.06 * h_in / FW
    ax = fig.add_axes([xl, 0.52, wf, h_in / FH]); xl += wf + 0.004
    ax.imshow(im, extent=(0, im.width / H, (im.height - d["top"]) / H, -d["top"] / H))
    ax.set_xlim((x0) / H, x1 / H); ax.set_ylim(1.03, -0.03); ax.set_xticks([])
    for y, c, t in [(d["top"], "k", "뿔끝"), (d["head"][0], "b", "투구"), (d["head"][1], "b", "턱"), (d["crotch"], "r", "V"), (d["sole"], "k", "바닥")]:
        yy = (y - d["top"]) / H; ax.axhline(yy, color=c, lw=0.8, ls="--"); ax.text(x0 / H, yy, t, color=c, fontsize=8, va="bottom")
    ax.set_title(f"{k}\n머리 {R[k]['head_h']} · 다리 {R[k]['leg']} · 허리 {R[k]['waist']}", fontsize=10)
    if i: ax.set_yticks([])
ax = fig.add_axes([0.04, 0.05, 0.94, 0.38])
항 = ["head_h", "horn", "chest", "waist", "shoulder", "leg", "garuru", "war", "arm", "shield", "foot", "cape_w"]
색 = ["#b22222", "#e07b7b", "#555555", "#aaaaaa", "#1f5fbf", "#e8a33d"]
w = 0.8 / len(열); xs = np.arange(len(항))
for i, k in enumerate(열):
    v = [R[k][m] if R[k][m] is not None else np.nan for m in 항]
    ax.bar(xs + (i - len(열) / 2 + 0.5) * w, v, w, label=k, color=색[i])
ax.set_xticks(xs); ax.set_xticklabels([이름[m] for m in 항], fontsize=10); ax.set_ylabel("÷ 전고"); ax.legend(ncol=6, fontsize=10)
ax.set_title("정면 비율 (빈 칸 = 못 잼 · 0 = 없음) — 빨강 계열 원작 · 회색 키트/완성품 · 파랑 우리 원화 · 주황 우리 모델", fontsize=11)
ax.grid(axis="y", alpha=0.3)
fig.savefig(os.path.join(OUT, "비교.png"), dpi=90); print("끝", os.path.join(OUT, "비교.png"))
for m in 항 + ["head_w", "cape_l"]:
    print(f"{이름[m]:<14}", "  ".join(f"{k}={R[k][m]}" for k in 열))
