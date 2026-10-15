# 판정기준51 루프 오케스트레이터 — 나 → 가 → 나 → 가 → 나 · 앞 판은 「그 묶음을 안 본 모델」로 · 마지막은 (나) · 판마다 오름 < 0.003 이면 멈춤 · 10-15
# 사용(venv): 루프51.py --마른 [판 3]  → 무엇을 어떤 순서로 돌릴지 출력만
#            루프51.py [판 3]          → 차례로 돌림(⚠ 학습51나 · 학습51가 의 묶음이 묶음51 로 바뀐 뒤에만 · 아래 묶음확인 이 막는다)
#            루프51.py 모으기 <나|가> <판>  → 묶음 다섯 + 전체 예측을 다음 쪽 앞 판 파일 하나로(부품 번호 자리)
# 앞 판 파일: out/설명/캐드부품/루프51/판<r>/가_앞판.npy (부품, 48, 48, 48) uint8 ← (나) 판 r · 나_앞판.npy (부품, 6, 128, 128) uint8 ← (가) 판 r−1
# (나) → (가) 는 변환51.층에서칸(칸 깎기 · 싼 대용). CAD 를 지어 CAD에서칸 으로 하면 학습 9 천 부품 × 깎기(최대 120 초) — 일꾼 2 로 수십 시간
import sys, os, json, subprocess, numpy as np
O = "G:/art2real/out/설명/캐드부품/"; 루 = O + "루프51/"; 여기 = os.path.dirname(os.path.abspath(__file__))
PY = "G:/art2real/트레일/trail10_cadrille/venv/Scripts/python.exe"; 오름문턱 = .003; 일꾼 = 2
def 이름(쪽, r, b): return "루프51_판%d_%s%s" % (r, 쪽, "전체" if b < 0 else "b%d" % b)
def 앞판(쪽, r): return 루 + "판%d/%s_앞판.npy" % (r, 쪽)
def 순서(판수):   # → [(판, 쪽, 일, 명령 | None)] · 명령 None = 이 파일 안의 일
    s = []
    for r in range(판수):
        for 쪽 in ("나", "가"):
            if 쪽 == "가" and r == 판수 - 1: break   # 마지막은 (나)
            앞 = ("-" if r == 0 else 앞판("나", r)) if 쪽 == "나" else 앞판("가", r)
            학 = "학습51나.py" if 쪽 == "나" else "학습51가.py"
            for b in list(range(5)) + [-1]:
                s.append((r, 쪽, "학습 " + ("전체 → 시험 예측" if b < 0 else "묶음 %d 뺌 → 묶음 %d 예측(앞 판용)" % (b, b)), [PY, 학, 이름(쪽, r, b), 앞, str(b)]))
            if 쪽 == "나":
                전 = 이름("나", r, -1)
                s.append((r, 쪽, "평가 712 CAD", [PY, "평가51나.py", 전, "0", "712", str(일꾼)]))
                s.append((r, 쪽, "판정 → CAD 평균", [PY, "평가51나.py", 전, "판정"]))
                if r > 0: s.append((r, 쪽, "멈춤 검사: CAD(판 %d) − CAD(판 %d) < %.3f 이면 여기서 끝(마지막이 (나))" % (r, r - 1, 오름문턱), None))
                if r < 판수 - 1: s.append((r, 쪽, "모으기 → " + 앞판("가", r), [PY, "루프51.py", "모으기", "나", str(r)]))
            else:
                s.append((r, 쪽, "칸 IoU(시험 712 · 범위46)", None))
                s.append((r, 쪽, "모으기 → " + 앞판("나", r + 1), [PY, "루프51.py", "모으기", "가", str(r)]))
    return s
def CAD점(r): return json.load(open(O + "학습51나_%s/결과.json" % 이름("나", r, -1), encoding="utf-8"))["CAD 평균"]
def 칸점(r):   # 학습51가 전체 모델 예측 → 범위46 712 부피 IoU(틀 밖 0 · 예측 없는 부품 0)
    import 학습51가 as A
    D = O + "학습51가_%s/" % 이름("가", r, -1); P = np.load(D + "예측.npy"); 자 = {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}
    te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 범 = json.load(open(O + "범위46.json")); 정 = np.load(O + "데이터51.npz")["정답"]; r_ = []
    for k in 범:
        i = int(te[k]); a, b = A.풀기(P[자[i]]) if i in 자 else None, A.풀기(정[i])
        r_.append(0.0 if a is None else float((a & b).sum() / max((a | b).sum(), 1)))
    return float(np.mean(r_))
def 모으기(쪽, r):   # 묶음 모델 다섯(학습 부품) + 전체 모델(시험) → 다음 쪽 앞 판 · 학습 부품은 정확히 한 번씩만 채워져야 한다
    import 변환51 as V, 묶음51 as B
    z = np.load(O + "데이터51.npz"); 반, ok = z["반"], z["ok"]; 시 = np.load(O + "데이터.npz")["시험"]; n = len(ok); 틀 = np.unpackbits(z["틀"], axis=-1).reshape(n, 48, 48, 48)
    os.makedirs(os.path.dirname(앞판("가", r)), exist_ok=True); os.makedirs(os.path.dirname(앞판("나", r + 1)), exist_ok=True)
    if 쪽 == "나": M = np.lib.format.open_memmap(앞판("가", r), mode="w+", dtype=np.uint8, shape=(n, 48, 48, 48)); M[:] = 틀   # 예측 없는 부품 = 틀
    else: M = np.lib.format.open_memmap(앞판("나", r + 1), mode="w+", dtype=np.uint8, shape=(n, 6, 128, 128)); M[:] = np.load(O + "입력51.npy", mmap_mode="r")[:, :, 2]   # = 껍질 층
    본 = np.zeros(n, int)
    for b in list(range(5)) + [-1]:
        D = O + "학습51%s_%s/" % (쪽, 이름(쪽, r, b)); P = np.load(D + "예측.npy", mmap_mode="r"); 부 = np.load(D + "예측부품.npy")
        assert b < 0 or all(B.묶음(i) == b and not 시[i] for i in 부), "묶음 %d 예측 부품이 묶음51 과 다름 — 학습 스크립트 묶음 고침 전" % b
        for j, i in enumerate(부):
            본[i] += 1
            M[i] = V.층에서칸(P[j], 반[i], 틀[i]) if 쪽 == "나" else V.칸에서층(np.unpackbits(P[j]).reshape(48, 48, 48).astype(bool), 반[i])
    assert (본[~시 & ok] == 1).all(), "학습 부품이 한 번씩 채워지지 않음"; M.flush(); print("모으기", 쪽, r, "→", M.filename, flush=True)
def 묶음확인():
    import 학습51나 as N, 묶음51 as B
    if any(N.묶음(i) != B.묶음(i) for i in range(200)): sys.exit("학습51나.묶음 이 아직 부품 번호 해시 — 고침안(diff)을 먼저 적용")
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--마른"]; 마른 = "--마른" in sys.argv
    if a and a[0] == "모으기": 모으기(a[1], int(a[2])); sys.exit()
    판수 = int(a[0]) if a else 3; s = 순서(판수)
    if 마른:
        for n, (r, 쪽, 일, 명) in enumerate(s): print("%2d · 판 %d (%s) · %s%s" % (n + 1, r, 쪽, 일, "" if 명 is None else "\n      " + " ".join(명[1:])))
        print("※ 모든 명령에 ART_MEM_GB=4 · 작업 폴더", 여기); sys.exit()
    묶음확인(); env = dict(os.environ, ART_MEM_GB=os.environ.get("ART_MEM_GB", "4")); 점 = []
    for r, 쪽, 일, 명 in s:
        if 명 is not None: print("▶", 일, flush=True); subprocess.run(명, cwd=여기, env=env, check=True); continue
        if 쪽 == "가": print("칸 IoU 판 %d = %.3f" % (r, 칸점(r)), flush=True); continue
        점.append(CAD점(r)); print("CAD 판 %d = %.3f" % (r, 점[-1]), flush=True)
        if len(점) > 1 and 점[-1] - 점[-2] < 오름문턱: print("멈춤: 오름 %.4f < %.3f · 마지막 (나) = 판 %d" % (점[-1] - 점[-2], 오름문턱, r)); break
    json.dump({"CAD": 점}, open(루 + "점수.json", "w", encoding="utf-8"), ensure_ascii=False)
