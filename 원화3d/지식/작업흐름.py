# -*- coding: utf-8 -*-
"""작업흐름도 그리기 → 그림/작업흐름.png.  python 작업흐름.py"""
import os
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.abspath(__file__))
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", s)
f1, f2, f3 = F(24), F(17), F(15)
# (제목, 설명, 종류) 종류: 사람 · 나 · 자동 · 검사
단계 = [("요청", "사용자 말", "사람"),
        ("① 시작 카드 읽기", "부위 쪽 · 규칙 · 미학 표  ← 훅이 문맥에 넣음", "자동"),
        ("② 레퍼런스 보기", "원화 3 배 확대 + 격자 → 단면표 · 특징 목록", "나"),
        ("③ 소체 · 프레임", "관절 자리(원화 px) · 링크 · 볼 · 경첩", "나"),
        ("④ 겹 입히기", "속 → 갑주 · 갑주 ∩ 소체 = 0 (assert)", "검사"),
        ("⑤ 디테일 네 단계", "덩어리 → 나누기 → 겹치기 → 작은 것 · 원화 특징만", "나"),
        ("⑥ 렌더 직접 보기", "레퍼런스와 같은 각도 3 개 · 미학 표 번호로 판정", "나"),
        ("⑦ 사용자 판정", "없으면 내 판정 · 「사용자 미확인」", "사람"),
        ("⑧ 적기 + 커밋", "log · 바퀴 표 · 규칙  ← 없으면 커밋 막힘", "자동"),
        ("⑨ 출력 전 검사", "벽 · 틈 · 핀 · 서포트 · 조립 · 끄덕", "검사"),
        ("⑩ 슬라이스 → 프린터", "보내기 전에 사용자 확인", "사람")]
색 = {"사람": (255, 226, 190), "나": (214, 228, 250), "자동": (205, 240, 210), "검사": (250, 214, 214)}
W, bw, bh, gap, x0, y0 = 1300, 560, 74, 26, 60, 90
H = y0 + len(단계) * (bh + gap) + 90
im = Image.new("RGB", (W, H), (250, 250, 248)); d = ImageDraw.Draw(im)
d.text((x0, 26), "작업흐름 — 원화 → 키트 (지식 위키 09-28)", font=F(30), fill=(20, 20, 20))
중 = []
for i, (t, s, k) in enumerate(단계):
    y = y0 + i * (bh + gap); d.rounded_rectangle([x0, y, x0 + bw, y + bh], 12, fill=색[k], outline=(60, 60, 60), width=2)
    d.text((x0 + 16, y + 8), t, font=f1, fill=(20, 20, 20)); d.text((x0 + 16, y + 42), s, font=f3, fill=(50, 50, 50))
    중.append(y + bh / 2)
    if i: d.line([x0 + bw / 2, y - gap, x0 + bw / 2, y - 4], fill=(60, 60, 60), width=3); d.polygon([(x0 + bw / 2 - 7, y - 12), (x0 + bw / 2 + 7, y - 12), (x0 + bw / 2, y - 2)], fill=(60, 60, 60))
# 되돌이
def 되돌이(a, b, x, 글, c):
    ya, yb = 중[a], 중[b]
    d.line([x0 + bw, ya, x, ya, x, yb, x0 + bw + 8, yb], fill=c, width=3); d.polygon([(x0 + bw, yb), (x0 + bw + 12, yb - 7), (x0 + bw + 12, yb + 7)], fill=c)
    d.text((x0 + bw + 290, ya - 12), 글, font=f2, fill=c)   # 글은 선들 오른쪽 바깥, 시작 높이에
되돌이(7, 5, x0 + bw + 60, "안 읽힘 → 디테일 · 겹 다시", (200, 90, 40))
되돌이(6, 2, x0 + bw + 150, "같은 곳 두 판 안 읽힘\n→ 멈추고 「실물로 무엇인가」 조사\n→ 규칙 후보", (170, 40, 40))
되돌이(9, 4, x0 + bw + 250, "출력 · 조립 실패\n→ 겹 · 틈 고침", (120, 60, 160))
# 범례
y = H - 60
for i, (k, c) in enumerate(색.items()):
    x = x0 + i * 250; d.rounded_rectangle([x, y, x + 30, y + 30], 6, fill=c, outline=(60, 60, 60)); d.text((x + 40, y + 3), {"사람": "사람이 정함", "나": "Claude", "자동": "훅이 강제", "검사": "스크립트 assert"}[k], font=f2, fill=(30, 30, 30))
p = os.path.join(R, "그림", "작업흐름.png"); im.save(p); print(p, im.size)

