# 공통 자 — 방법이 무엇을 내든(화소 지도 · 선 목록 · 도형 목록) 「정답 모서리마다 찾았나 · 종류(직선 / 곡선) 맞혔나 · 어떤 상황의 모서리인가」로 잰다 · 비교판의 주지표 · 10-23
# 정답 모서리: out/하네스/겹침/<부품>.npz (겹침그림.모서리들 — CAD 를 다시 투영해 모서리마다 1 화소 마스크 · 종류 · 꼭짓점)
# 상황: 모서리 화소 가운데 다른 모서리가 2 화소 안으로 붙어 지나는 몫이 20 % 넘으면 그 짝의 종류로(직선-곡선 > 곡선-곡선 > 직선-직선), 아니면 홀로
import os, sys, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
상황이름 = ["홀로 직선", "홀로 곡선", "직선-직선", "직선-곡선", "곡선-곡선"]
def 모서리(부품, v):   # → [(마스크 bool 128², 종류 1 · 2, 상황 0~4)]
    import cv2, 겹침그림 as Q
    z = np.load(Q.저장 + f"{부품}.npz"); ms = z[f"m{v}"]; ks = z[f"k{v}"]
    if not len(ms): return []
    ms = np.unpackbits(ms, axis=1)[:, :128 * 128].reshape(-1, 128, 128).astype(bool); u = Q.유형지도(z, v); out = []
    for m, k in zip(ms, ks):
        if m.sum() < 3: continue
        t = u[m]; t = t[t >= 0]
        if len(t) == 0: 상 = 0 if k == 1 else 1
        else:
            몫 = {s: (t == s).mean() for s in (2, 3, 4)}
            상 = 3 if 몫[3] > .2 else 4 if 몫[4] > .2 else 2 if 몫[2] > .2 else (0 if k == 1 else 1)
        out.append((m, int(k), 상))
    return out
def 화소채점(예, 모서리들):   # 예: 지도 (128, 128) 0 없음 · 1 직선 · 2 곡선 · 3 곡면테 | (있음 bool, 직선 확률, 곡선 확률) → 모서리마다 (찾음, 맞음, 상황)
    import cv2
    있, p직, p곡 = (예 > 0, 예 == 1, 예 == 2) if np.ndim(예) == 2 else 예
    결과 = []
    for m, k, 상 in 모서리들:
        곁 = (cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & 있
        찾음 = 곁.sum() >= .6 * m.sum()
        a, b = float(np.mean(p직[곁])) if 곁.any() else 0., float(np.mean(p곡[곁])) if 곁.any() else 0.   # 곡면테는 종류 표에서 뺌(사람도 못 가름) · 둘이 같으면(다 테 · 둘 다 켬) 틀림
        맞음 = bool(찾음 and (a > b if k == 1 else b > a))
        결과.append((bool(찾음), 맞음, 상))
    return 결과
def 모음(결과들):   # 모서리 결과 목록 → 공통 지표
    a = np.array([(f, c, s) for f, c, s in 결과들], dtype=int)
    r = {"모서리_수": int(len(a)), "모서리_찾음": round(float(a[:, 0].mean()), 4), "모서리_종류": round(float(a[:, 1].mean()), 4)}
    for s, n in enumerate(상황이름):
        m = a[:, 2] == s; r[f"틀림_{n}"] = round(float(1 - a[m, 1].mean()), 4) if m.any() else None; r[f"수_{n}"] = int(m.sum())
    m = a[:, 2] == 3; r["모서리_종류_직곡"] = round(float(a[m, 1].mean()), 4) if m.any() else None
    return r
def 선지도판(판, net=None, 자료=None):   # 자료 = (X, vx, 이) 를 주면 다시 읽지 않음(시드 반복에서 다시 읽다 메모리 상한 두 번)   # 선지도(화소) 판 어댑터: 시험 부품마다 모델 예측 → 모서리 채점 · net 을 주면 그 망(비교판 시드 반복)
    import torch, 과제선지도 as G, 분석그림 as A
    from omegaconf import OmegaConf
    import 겹침그림 as Q
    c = OmegaConf.load(f"{뿌리}/하네스/판/{판}/설정.yaml"); X, vx, 이 = 자료 or (lambda t: (t[0], t[4], t[5]))(G.자료("cuda", c))
    n = (net or A.불러(판)).cuda(); pr = G.예측(n, X[vx])[:, :, :4].float().softmax(2)   # 다중 판은 예측이 이미 같은 꼴로 읽음
    있 = (1 - pr[:, :, 0] > .5).cpu().numpy(); p = pr[:, :, 1:3].cpu().numpy(); 예 = np.where(있, p.argmax(2) + 1, 0)
    결과 = []; 부품들 = [이[int(j)] for j in vx.tolist()]
    for k, 부품 in enumerate(부품들):
        if not os.path.exists(Q.저장 + f"{부품}.npz"): continue
        for v in range(3): 결과 += 화소채점((있[k, v], p[k, v, 0], p[k, v, 1]), 모서리(부품, v))
    return 모음(결과), 예, 부품들
if __name__ == "__main__":   # 자체 시험: 완벽한 지도는 종류 1 · 빈 지도는 찾음 0
    m = np.zeros((128, 128), bool); m[40, 10:60] = True; m2 = np.zeros((128, 128), bool); yy, xx = np.mgrid[:128, :128]; m2[np.abs(np.hypot(xx - 80, yy - 80) - 20) < .6] = True
    ms = [(m, 1, 0), (m2, 2, 1)]; 완 = np.zeros((128, 128), int); 완[m] = 1; 완[m2] = 2
    r = 모음(화소채점(완, ms)); assert r["모서리_종류"] == 1 and r["모서리_찾음"] == 1, r
    r = 모음(화소채점(np.zeros((128, 128), int), ms)); assert r["모서리_찾음"] == 0 and r["모서리_종류"] == 0, r
    뒤 = 완.copy(); 뒤[m] = 2; r = 모음(화소채점(뒤, ms)); assert r["모서리_종류"] == .5 and r["틀림_홀로 직선"] == 1, r
    둘 = np.ones((128, 128)); r = 모음(화소채점((완 > 0, 둘, 둘), ms)); assert r["모서리_종류"] == 0, r   # 둘 다 켜면 이득 없음
    print("공통자 시험 통과")
