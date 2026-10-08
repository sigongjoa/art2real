# -*- coding: utf-8 -*-
"""교사 데이터 (10-08 · 판정은 runs/교사1/판정기준.json — 학습 전에 고정)
3 바퀴 학습 코드(runs/자가3/data/train) 그대로 + Claude 가 짠 통과 코드(결과*.json 의 통과 · 눈판정 O)를 REP 번 반복해 붙인다.
차이는 교사 코드뿐 → 3 바퀴 LoRA 가 대조군.
python s0/교사데이터.py <교사 폴더=runs/교사1> <출력 폴더> [REP=3]"""
import os, sys, glob, json, shutil, trimesh
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
import s0 as S
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"

if __name__ == "__main__":
    T, O = sys.argv[1], sys.argv[2]; REP = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    src = "runs/자가3/data/train"; os.makedirs(O + "/train", exist_ok=True)
    for f in glob.glob(src + "/*"): shutil.copy(f, O + "/train/")
    n = len(glob.glob(O + "/train/*.py")); k = 0
    from transformers import AutoTokenizer; TOK = AutoTokenizer.from_pretrained("weights/qwen2vl2b"); MAXT = 768   # 평가 때 max_new_tokens 768 — 그보다 긴 정답은 배워도 못 쓴다(10-08 1 만 토큰 덤프 둘이 메모리 부족을 냄)
    X = set(json.load(open(T + "/제외.json", encoding="utf-8"))) if os.path.exists(T + "/제외.json") else set()   # 단면을 베낀 흔적 코드 — 점수는 통과해도 CAD 설계가 아니다
    for jf in sorted(glob.glob(T + "/결과*.json")):
        i = os.path.basename(jf)[2:-5]   # 결과0.json → "0"
        for j, r in enumerate(json.load(open(jf, encoding="utf-8"))):
            if not (r.get("통과") and r.get("눈판정") == "O") or "%s_%02d" % (i, j) in X: continue
            code = open("%s/%s_%02d.py" % (T, i, j), encoding="utf-8").read()
            if len(TOK(code)["input_ids"]) > MAXT: continue
            _, g = S.item_img(S.unit(trimesh.load(R + r["부품"], force="mesh")))
            for _ in range(REP):
                open("%s/train/%04d.py" % (O, n), "w", encoding="utf-8").write(code); g.save("%s/train/%04d.png" % (O, n)); n += 1
            k += 1
    assert k > 0, "통과한 교사 코드가 없다"
    print("교사 부품", k, "· 학습 코드 합계", n)
