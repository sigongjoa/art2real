# 새 구조 흐름도(10-20 사용자 「코드가 나오고 그 코드에 대해서 설계도를 작성」) — 칸마다 「계산으로 답이 나오나 / 학습 칸」 표시 · 첫 판 할 일 · 10-20
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(20, 10)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 20); W.set_ylim(0, 10); W.axis("off")
칸 = [("① 원화 · 이미지 · 3D", "입력", "#eeeeee", "—"), ("② AI + 기하 처리", "이미지 → CAD 코드\n(기하가 후보를 뽑고\nAI 는 고르기 · 숫자는 기하)", "#fef3c7", "학습 칸\n(정답이 식으로 안 나옴)"),
      ("③ CAD 코드", "스케치 → 돌출 · 회전 ·\n구멍 · 필렛 · 기울인 기준면\n+ 파라미터", "#dcfce7", "결과물"), ("④ 3D + 설계도", "CadQuery 로 3D 계산 ·\n3면도 · 중심선 · 단면 · 치수\n를 코드에서 뽑음", "#dbeafe", "계산 칸\n(학습 없음)"),
      ("⑤ 대조", "다시 그린 설계도 ↔ 원화\n(다시 그리기 · 맞대기 코드\n= 지금까지 만든 것)", "#dbeafe", "계산 칸")]
for k, (t, s, c, 표) in enumerate(칸):
    x = .3 + k * 3.95; W.add_patch(FancyBboxPatch((x, 5.8), 3.4, 3.4, boxstyle="round,pad=.06", fc=c, ec="#555")); W.text(x + 1.7, 8.75, t, ha="center", fontsize=15, weight="bold")
    W.text(x + 1.7, 7.45, s, ha="center", va="center", fontsize=11.5); W.text(x + 1.7, 6.2, 표, ha="center", va="center", fontsize=11, color="#b45309" if "학습" in 표 else "#1d4ed8")
    if k < 4: W.add_patch(FancyArrowPatch((x + 3.45, 7.5), (x + 3.9, 7.5), arrowstyle="-|>", mutation_scale=22, color="#333"))
W.add_patch(FancyArrowPatch((18.2, 5.7), (1.9, 5.7), arrowstyle="-|>", mutation_scale=22, color="#999", connectionstyle="arc3,rad=.18")); W.text(10, 4.55, "안 맞으면 ② 로 되돌아가 후보를 바꿈", ha="center", fontsize=12, color="#666")
W.text(.4, 3.7, "정답 데이터: 우리 부품은 STL 이라 코드가 없음 → 부품 낱말로 CadQuery 코드를 절차 생성 → 코드에서 3D · 렌더 이미지 · 설계도를 뽑음(정답이 공짜 · 정확)", fontsize=12.5)
W.text(.4, 2.9, "첫 판: ⑴ 코드 낱말 정하기(스케치 사각 · 원 · 다각 / 돌출 · 회전 · 구멍 · 필렛 · 기울인 기준면)  ⑵ 생성기: 코드 → 3D → 렌더 + 3면도 · 단면", fontsize=12.5)
W.text(.4, 2.2, "        ⑶ 검산: 생성한 코드의 설계도를 ⑤ 로 대조해 0 오차인지(계산 칸이 맞는지)  ⑷ 그다음에만 ② 학습(이미지 → 코드)", fontsize=12.5)
W.text(.4, 1.2, "안 하는 것: 정답이 계산으로 나오는 칸(③ → ④ → ⑤)에 학습 넣기 · 데이터를 만들며 정보 빼기(먼저 묻기) · 생성 3D", fontsize=12.5, color="#b91c1c")
plt.savefig("G:/art2real/out/설명/캐드부품/흐름115.png", dpi=72); print("저장")
