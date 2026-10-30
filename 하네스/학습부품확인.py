# 학습한 부품에서도 못 하나 — 지난 판 LoRA 로 학습 부품 N 개를 생성해 새 자(부피 IoU)로 · 시험 부품 값(재채점 부피.json)과 나란히
# 10-30: 145~155 모두 시험 부피 IoU 0.15~0.21(바닥 원기둥 0.151) · 학습 부품도 ≈ 0.2 면 외우지도 못함(형식 · 입력 · 구조) · 높으면 일반화 문제
# 사용: python 학습부품확인.py 154MLP포함 [50] → out/하네스/<판>/학습부품/ (생성 글 · 부피.json)
import os, sys, json, numpy as np
뿌리 = "G:/art2real"; sys.path[:0] = [뿌리 + "/하네스", 뿌리 + "/원화3d/실험_20261013/캐드부품"]
if __name__ == "__main__":
    import torch, 과제코드 as K, 코드글, 모델124 as B, 데이터117 as Q
    from omegaconf import OmegaConf; from peft import set_peft_model_state_dict; from safetensors.torch import load_file
    판 = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 50; 원 = f"{뿌리}/out/하네스/{판}/"; 밖 = 원 + "학습부품/"; os.makedirs(밖, exist_ok=True)
    s = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml").코드; 토큰 = str(s.get("토큰", "기존")); 입력 = str(s.입력)
    목 = K.자료(선입력=str(s.get("선입력", "CNN")), 좌표계=str(s.get("좌표계", "mm")))
    목 = K.서식바꿈(목, s); 학 = [x for x in 목 if not x[1]]
    if s.get("학습부품"): 고 = set(json.load(open(f"{뿌리}/out/하네스/{s.학습부품}/부품.json"))); 학 = [x for x in 학 if x[0] in 고]
    학 = 학[:: max(1, len(학) // N)][:N]   # 학습 부품을 고르게 N 개
    생경 = 밖 + "생성.json"; 생 = json.load(open(생경, encoding="utf-8")) if os.path.exists(생경) else {}
    if len(생) < len(학):
        model, proc = K.모델(int(s.get("랭크", 16)), 토큰, str(s.get("LoRA대상", "어텐션"))); set_peft_model_state_dict(model, load_file(원 + "lora/adapter_model.safetensors", device="cuda"))
        if 토큰 == "좌표":
            with torch.no_grad(): model.get_base_model().model.embed_tokens.새.copy_(torch.load(원 + "lora/좌표임베딩.pt"))
        model.eval(); 남 = [x for x in 학 if x[0] not in 생]
        for b in range(0, len(남), 8):
            for (n, *_), g in zip(남[b:b + 8], K.생성(model, proc, [K.항목(n, l, g, 입력, 정답=False) for n, _, l, g in 남[b:b + 8]], 제약=str(s.get("디코딩", "탐욕")) == "제약")): 생[n] = g
            json.dump(생, open(생경, "w", encoding="utf-8"), ensure_ascii=False); print(f"생성 {len(생)}/{len(학)}", flush=True)
        del model; torch.cuda.empty_cache()
    색 = {f"{r['i']:05d}": r for r in B.색인()}; 이 = [x[0] for x in 학]
    렌 = B.병렬렌더([("글", 생[n], 1) for n in 이] + [("조립", 색[n]["코드"], 1) for n in 이]); k = len(이)
    부 = lambda r: None if r is None else r[2]
    줄 = {n: {"부피IoU": round(Q.부피겹(부(렌[t]), 부(렌[k + t])), 4), "실행": 렌[t] is not None, "정답실패": 렌[k + t] is None, "몸맞음": K.몸수(생[n]) == K.몸수(g)} for t, (n, _, _, g) in enumerate(학)}
    assert not any(z["정답실패"] for z in 줄.values()), "정답 렌더 실패 — 판정 안 함"
    시 = json.load(open(원 + "부피.json", encoding="utf-8"))["요약"]["부피IoU"] if os.path.exists(원 + "부피.json") else None
    요 = {"학습부품수": k, "학습 부피IoU": round(float(np.median([z["부피IoU"] for z in 줄.values()])), 4), "학습 실행률": round(float(np.mean([z["실행"] for z in 줄.values()])), 3),
          "학습 몸개수맞음": round(float(np.mean([z["몸맞음"] for z in 줄.values()])), 3), "시험 부피IoU(재채점)": 시}
    json.dump({"요약": 요, "부품": 줄}, open(밖 + "부피.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(판, 요, flush=True)
