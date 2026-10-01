# -*- coding: utf-8 -*-
"""정면 셀 × TripoSG 교집합 (10-02 새벽 · 사용자 「TripoSG 랑 교집합하라고 했는데 옆 원화랑 했다」 정정).
C = 정면 셀 기둥 ∩ TripoSG 전체(깊이맵 채움)  → 셀마다 머리 깊이를 꿰뚫는 기둥(= #9 쿠키 커터와 같음)
D = 정면 셀 기둥 ∩ TripoSG 앞 껍질(앞면에서 겹 두께 d 만큼: 투구 6 · 마스크 5 · 눈 1.5 · 뿔 10) → 「앞뒤로 늘린 부품을 TripoSG 로 깎은」 것
TripoSG 는 머리 단위 틀에서 정면 실루엣(뿔 행 제외)으로 다시 맞춤(tripo_fit2.json · IoU 0.35 — 닮지 않아 낮다).
스크래치패드 원본: hullC_render.py · hullD_render.py (헤드리스.py 사용) · 결과 out/오메가몬2/지표/곱연산/곱연산_ACD.png"""
