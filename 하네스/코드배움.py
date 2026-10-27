# 코드생성 판의 「배웠나」 — 정답 글을 그대로 넣어 줄 때(teacher forcing) 결정 자리에서 다음 토큰을 맞히나 · 학습 부품 · 시험 부품 따로
# 자리: 원뿔 시작(「.add」) · 원뿔 갈래(「cq.」 다음 「.Solid」) · 몸 줄 끝 괄호 · layout 줄 · 나머지
# 10-26 사용자 「그게 문제가 아니라 학습을 못한 거는 아니고?」 · 147 · 151 모두 「.Solid」 0/35(logit 8 대 「.Work」 18) · 학습 = 시험 0.85 → 덜 배움
# 판마다 점검 끝에서 학습된 모델로 바로 잼(과제코드.점검) · 지난 판은 python 코드배움.py <판> 으로 LoRA 를 읽어 잼
import os, sys, re, json
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
def 칸이름(앞, 이것, 뒤줄, 덮):
    if 덮: return 덮
    if 앞.rsplit("\n", 1)[-1].startswith("layout"): return "layout 줄"
    if ")" in 이것 and 뒤줄.strip(") ") == "": return "몸 줄 끝 괄호"
    return "나머지"
def 재기(model, proc, 묶음, 입력="선글"):   # 묶음 = [(부품, 입력 글, 정답 글)] (서식 · 좌표글 바꾼 뒤) → {칸: {수, 맞음, CE}}
    import torch, torch.nn.functional as F, 과제코드 as K
    tok = proc.tokenizer; 칸 = {}; model.eval()
    for n, l, g in 묶음:
        b = K.묶([K.항목(n, l, g, 입력)], proc)
        with torch.no_grad():
            base = model.get_base_model(); head = base.lm_head; base.lm_head = torch.nn.Identity()
            try: h = base(**{k: v for k, v in b.items() if k != "labels"}).logits
            finally: base.lm_head = head
            y = b["labels"][0, 1:]; m = y != -100; lo = head(h[0, :-1][m]).float(); y = y[m]
            맞 = (lo.argmax(-1) == y).tolist(); ce = F.cross_entropy(lo, y, reduction="none").tolist()
        ids = y.tolist(); 글 = ""; 자 = []
        for i in ids: 자.append(len(글)); 글 += tok.decode([i])
        표 = {}
        for x in re.finditer(r"\.add\(cq\.Solid", 글): 표[x.start() + 1] = "원뿔 시작 .add"; 표[x.start() + 8] = "원뿔 갈래 .Solid"
        for j, s0 in enumerate(자):
            이것 = tok.decode([ids[j]]); 덮 = next((v for q, v in 표.items() if s0 <= q < s0 + len(이것)), None)
            칸.setdefault(칸이름(글[:s0], 이것, 글[s0:].split("\n", 1)[0], 덮), []).append((맞[j], ce[j]))
    return {k: {"수": len(v), "맞음": round(sum(a for a, _ in v) / len(v), 3), "CE": round(sum(c for _, c in v) / len(v), 2)} for k, v in sorted(칸.items())}
def 저장(폴더, model, proc, 학, 시, 입력="선글", N=80):   # 학 · 시 = [(부품, 입력 글, 정답 글)] → 배움.json
    r = {"부품수": N, "학습": 재기(model, proc, 학[:N], 입력), "시험": 재기(model, proc, 시[:N], 입력)}
    json.dump(r, open(폴더 + "배움.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); return r
if __name__ == "__main__":   # 지난 판 소급: python 코드배움.py 151배치먼저 [147좌표토큰 …] · 자체 시험: 칸이름
    assert 칸이름("b0 = at(0, x", "))", "))", None) == "몸 줄 끝 괄호" and 칸이름("layout = [(", "1", ")]", None) == "layout 줄" and 칸이름("b0 = ", "cq", ".Solid", "원뿔 갈래 .Solid") == "원뿔 갈래 .Solid"
    print("코드배움 칸 시험 통과")
    import torch, 과제코드 as K, 코드글
    from omegaconf import OmegaConf; from peft import set_peft_model_state_dict; from safetensors.torch import load_file
    for 판 in sys.argv[1:]:
        s = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml").코드; 토큰 = str(s.get("토큰", "기존")); 원 = f"{뿌리}/out/하네스/{판}/lora/"
        model, proc = K.모델(int(s.get("랭크", 16)), 토큰, str(s.get("LoRA대상", "어텐션"))); set_peft_model_state_dict(model, load_file(원 + "adapter_model.safetensors", device="cuda"))
        if 토큰 == "좌표":
            with torch.no_grad(): model.get_base_model().model.embed_tokens.새.copy_(torch.load(원 + "좌표임베딩.pt"))
        목 = K.자료()
        if 토큰 == "좌표": 목 = [(n, t, K.좌표글(l), g) for n, t, l, g in 목]
        if str(s.get("서식", "기존")) == "배치먼저": 목 = [(n, t, l, 코드글.배치먼저(g)) for n, t, l, g in 목]
        print(판, json.dumps(저장(f"{뿌리}/out/하네스/{판}/", model, proc, [(n, l, g) for n, t, l, g in 목 if not t], [(n, l, g) for n, t, l, g in 목 if t], str(s.입력)), ensure_ascii=False), flush=True)
        del model; torch.cuda.empty_cache()
