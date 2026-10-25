# 보류 집합 — 시험 299 는 140~147 동안 결과를 보며 규칙 · 문턱을 정해 검증 집합이 됨(10-25 감사) → 한 번도 안 본 새 부품을 따로 만들어 봉인 · 10-25 사용자 「데이터는 더 구축」
# 같은 생성기(조립124.무작위 · rng 124000 + i)에서 처음 나오는 번호 12300~12599 · 개발 판은 읽지 않는다 — 기말(마지막 한 번 채점)에서만
# 산출: out/하네스/보류/ 사양/<i>.json · 도면/<i>_<뷰>.png · 선정답/<i>.npz · 그림.npz(CNN 입력 · 모델127.그림 과 같은 꼴) · 봉인.json
# 사용(cadrille venv · 메모리 상한): python 하네스/보류.py [일꾼=3]   — 이어 하기 됨(있는 파일은 건너뜀)
import os, sys, json, time, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
HD = f"{뿌리}/out/하네스/보류/"; 번호 = range(12300, 12600)
def _사양(i):
    import 모델124 as B; B.D = HD; B._하나(i)   # 같은 짓기 · 같은 도면 · 폴더만 보류
def _선(i):
    import 모델124 as B, 선정답 as L; B.D = HD; L.저장 = HD + "선정답/"; L._하나(i)
def 돌기(함수, 일, 일꾼, 초):   # 부품마다 새 프로세스 · 시간 넘으면 죽임(선정답.모두 와 같은 꼴 · OCC 가 걸려도 안 멈춤)
    import multiprocessing as mp
    도는 = {}
    while 일 or 도는:
        while 일 and len(도는) < 일꾼: i = 일.pop(0); p = mp.Process(target=함수, args=(i,)); p.start(); 도는[i] = (p, time.time())
        for i, (p, t) in list(도는.items()):
            if not p.is_alive(): p.join(); del 도는[i]
            elif time.time() - t > 초: p.kill(); p.join(); del 도는[i]; print("시간 넘음", i, flush=True)
        time.sleep(.2)
def 만들기(일꾼=3):
    import cv2
    for d in ("사양", "도면", "선정답"): os.makedirs(HD + d, exist_ok=True)
    돌기(_사양, [i for i in 번호 if not os.path.exists(HD + f"사양/{i:05d}.json")], 일꾼, 300)
    된 = [i for i in 번호 if os.path.exists(HD + f"사양/{i:05d}.json") and "코드" in json.load(open(HD + f"사양/{i:05d}.json", encoding="utf-8"))]; print("사양", len(된), "/", len(번호), flush=True)
    돌기(_선, [i for i in 된 if not os.path.exists(HD + f"선정답/{i:05d}.npz") and not os.path.exists(HD + f"선정답/{i:05d}.npz.err")], 일꾼, 120)
    이 = [f"{i:05d}" for i in 된 if os.path.exists(HD + f"선정답/{i:05d}.npz")]; X = np.zeros((len(이), 3, 128, 128), np.uint8)
    for k, n in enumerate(이):
        for v, nm in enumerate(("위", "앞", "옆")): X[k, v] = 255 - cv2.resize(cv2.imdecode(np.fromfile(HD + f"도면/{n}_{nm}.png", np.uint8), 0), (128, 128), interpolation=cv2.INTER_AREA)
    np.savez(HD + "그림.npz", X=X, 이름=np.array(이))
    json.dump({"번호": [번호.start, 번호.stop - 1], "부품": len(이), "만든 날": time.strftime("%Y-%m-%d %H:%M"), "생성기": "조립124.무작위(rng 124000 + i)",
               "규칙": "개발 판 · 비교판은 읽지 않는다. 기말(마지막 한 번 채점)에서만 연다. 연 날 · 판을 여기 「열람」에 적는다.", "열람": []}, open(HD + "봉인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("보류 집합", len(이), "부품 →", HD, flush=True)
if __name__ == "__main__":
    assert 12300 > max(int(f[:5]) for f in os.listdir("G:/art2real/out/설명/캐드부품/모델124/사양")), "보류 번호가 기존 사양과 겹침"
    만들기(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
