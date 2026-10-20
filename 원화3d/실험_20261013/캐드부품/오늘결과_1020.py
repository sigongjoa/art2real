# 10-20 결과 한 장 — 구조(원화 → 고르기 → 코드 → 설계도 → 대조) 위에 오늘 판들의 점수 · 통과/실패 · 남은 결정 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; E = O + "임베딩117/"
r116 = json.load(open(O + "설계116/결과b.json", encoding="utf-8")); r117 = json.load(open(E + "결과.json", encoding="utf-8")); r118 = json.load(open(E + "회전118b_재채점.json", encoding="utf-8"))
초, 빨, 회, 금 = "#28a050", "#d8262b", "#9aa3ad", "#e0a020"
fig = plt.figure(figsize=(20, 11)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 20); W.set_ylim(0, 11); W.axis("off")
칸 = [("입력", "원화 · 3D · 글", "#eeeeee"), ("고르기 (학습 칸)", "종류: Gemma 인코더\n수치: 시점 맞추기 + 화소 비교", "#fef3c7"), ("CAD 코드", "돌출 · 회전 · 구멍 · 홈", "#dcfce7"), ("설계도 (계산)", "3면도 + 중심선 + 단면", "#dbeafe"), ("대조 (계산)", "다시 그려 원래 그림과", "#dbeafe")]
for k, (t, s, c) in enumerate(칸):
    x = .4 + k * 3.95; W.add_patch(FancyBboxPatch((x, 8.9), 3.3, 1.6, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + 1.65, 10.05, t, ha="center", fontsize=15, weight="bold"); W.text(x + 1.65, 9.35, s, ha="center", va="center", fontsize=11)
    if k < 4: W.add_patch(FancyArrowPatch((x + 3.35, 9.7), (x + 3.9, 9.7), arrowstyle="-|>", mutation_scale=20, color="#333"))
def 판(ax, 제목, 막, 기준, 통과, 주):
    ax.set_title(제목, fontsize=13, color=초 if 통과 else 빨, weight="bold")
    nm = [m[0] for m in 막]; v = [m[1] for m in 막]; c = [m[2] for m in 막]; ax.barh(range(len(v))[::-1], v, color=c, height=.6)
    for y, (n, vv) in zip(range(len(v))[::-1], zip(nm, v)): ax.text(vv + .01, y, f"{vv:.3f}" if vv < .1 else f"{vv:.2f}", va="center", fontsize=12); ax.text(-.02, y, n, va="center", ha="right", fontsize=11)
    if 기준 is not None: ax.axvline(기준, color=빨, ls="--"); ax.text(기준, len(v) - .3, f" 기준 {기준}", color=빨, fontsize=10)
    ax.set_xlim(0, 1.15); ax.set_yticks([]); ax.spines[["top", "right", "left"]].set_visible(False); ax.text(0, -1.25, 주, fontsize=10.5, color="#444", va="top")
판(fig.add_axes([.12, .38, .2, .38]), "116b 설계도 · 비교기 → 통과", [("실행(코드 200)", r116["실행"], 초), ("결정성", r116["결정성"], 초), ("구별 못 함 · 전체", r116["구별 못 함(전체)"], 초), ("구별 못 함 · 3면도만", r116["구별 못 함(3면도만)"], 회)], None, True,
   "기준: 실행 ≥ 0.95 · 구별 못 함 ≤ 0.05\n3면도만이면 5 배 많이 놓침 —\n그릇 두께 · 컵 바닥 · 상자 높이(깊이)")
판(fig.add_axes([.45, .38, .2, .38]), "117 Gemma 종류 고르기 → 통과", [("이미지(다른 시점)", r117["T1"]["이미지(다른 시점)→렌더"], 초), ("턴테이블 영상(3D)", r117["T1"]["영상→렌더"], 초), ("글 설명", r117["T1"]["글→코드"], 초), ("수치 변형(T2) · 이미지", r117["T2"]["이미지(다른 시점)→렌더"], 회)], .8, True,
   "학습 없이 · 부품 100 · 찍기 0.167\n종류는 고르고, 수치 차이는 못 가림\n(그건 비교기 몫)")
판(fig.add_axes([.77, .38, .2, .38]), "118b 시점 맞추기 + 화소 → 실패", [("시점 ±15° 안(비대칭)", r118["시점 방위 ≤ 15° 몫(비대칭)"], 초), ("T2 엄격", r118["T2 엄격(동점 = 틀림)"], 빨), ("T2 동점 1/k", r118["T2 나눔(동점 1/k)"], 회), ("(버그 판) T2 동점=정답", r118["T2"], "#dddddd")], .8, False,
   "시점은 맞춤(오차 중앙 0°)\n동점 34 부품 = 겉에 안 보이는 깊이\n(그릇 두께 14 · 막힌 깊이 9 · 컵 바닥 8)")
W.text(.4, 2.55, "남은 결정: 겉 이미지 한 장에 없는 깊이를 어떻게 정하나 —  ① 단면 · 다른 시점을 입력으로 더 받기   ② 「모름」 + 표준값   ③ 그 수 하나만 사람에게 묻기", fontsize=14, weight="bold")
W.text(.4, 1.75, "오늘 그 밖: 조사 3 건(선만 3면도는 곡면 깊이를 못 정함 · 실무는 단면 · 기호 · 특징) · 구조 재정의(결과물 = CAD 코드 · 설계도는 코드에서 계산 · 학습은 고르기만)\n쇼츠 84 「곡면」 · 85 「정답」 서재용 공개 · 학습 장치 그림 + mp4 · 제 실수 바로잡음: 116 시험 버그 3 · 118b 동점 채점 버그 · 한글 경로 cv2", fontsize=11.5, va="top", color="#333")
fig.suptitle("10-20 결과 — 계산 칸(설계도 · 비교기)과 종류 고르기는 됨 · 겉 이미지 한 장으로 속 깊이를 고르는 건 안 됨", fontsize=17, y=.99)
plt.savefig(O + "오늘결과_1020.png", dpi=75); print("저장")
