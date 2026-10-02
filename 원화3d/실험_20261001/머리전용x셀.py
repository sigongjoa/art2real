# -*- coding: utf-8 -*-
"""정면 52 셀 × 머리 전용 TripoSG (10-02 · 사용자 「내가 확인한 tripo 는 얼굴 형태 잘 가져왔어 · 코드 다시 봐」).
메시 = 트레일/trail4_gen3d/out/knights/h_Omegamon_main.glb (02 정면 캡처 한 장 → TripoSG · 73.7만 점 · 닫힘).
10-01 밤 실험(#9~#15)이 쓴 것은 head_build6.blend 의 「TripoSG참고」 = **전신** TripoSG(omega_front_clean.glb · 51만 점)에서 머리만 잘라 8,284 점으로 줄인 사본 + 스무딩 25 → 「투구를 못 잡는다 · 사람 얼굴 덩어리」는 그 사본 탓(틀린 결론).
절차: ① 자세 맞춤(yaw/pitch/roll · 배율 · 이동 · 정면 셀 실루엣 IoU) → cut/h_fit.json (IoU 0.72 · yaw −5 · roll −2 · 배율 50)
      ② trimesh voxelized(0.5).fill() (닫힌 메시라 정확) → 셀 마스크 × 복셀 → 마칭큐브 → cut/hullobjH/C_<n>.obj
      ③ hullH_render.py (헤드리스.py) — 결과 out/오메가몬2/지표/곱연산/머리전용/
결과: 50/52 셀(빈 것 뿔 끝 · 턱 끝 — 입력 캡처가 뿔 끝을 잘랐고 자세 맞춤이 턱에서 조금 샘) · 투구 돔 · 뒤통수 · 눈구멍이 TripoSG 곡면 그대로 부품이 됨."""
