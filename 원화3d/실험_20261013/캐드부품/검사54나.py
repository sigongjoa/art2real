# 판정기준54 (나) 손실 검사 — 시험 부품 20 개 · 10-15
# ① 정답 층 원핫 → 부드러운 칸 깎기(torch) 0.5 자름 ↔ 여섯방향.칸깎기(numpy · 몸통37 틀 · 반높이는 몸에서) 칸 IoU ≥ 0.98
# ② 정답 층 원핫 점 구름 ↔ 정답 표면 점 Chamfer 가 무작위 층 · 껍질 층(입력)보다 확실히 작다
# 사용(venv): 검사54나.py [부품 수 20]
import sys, json, numpy as np, torch
import 여섯방향 as S6, 짓기 as J, 학습54나 as L
from 평가51나 import 지도
O = L.O; dev = "cuda"
k = int(sys.argv[1]) if len(sys.argv) > 1 else 20
z = dict(np.load(O + "데이터51.npz")); idx = np.nonzero(np.load(O + "데이터.npz")["시험"] & z["ok"] & z["정답"].any(1))[0][:k]
목록 = json.load(open(O + "목록.json", encoding="utf-8")); X = np.load(O + "데이터.npz")["X"]; FS = dict(np.load(O + "데이터_앞옆.npz")); 입 = np.load(O + "입력51.npy", mmap_mode="r")
Qs = L.표면점(idx, 목록); 원 = lambda a: torch.nn.functional.one_hot(torch.tensor(a, device=dev).long(), 18).permute(0, 3, 1, 2).float()[None]
iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1); 줄 = []; gen = torch.Generator(device=dev); gen.manual_seed(54); rng = np.random.default_rng(54)
for i in idx:
    층, 반 = z["층"][i], z["반"][i]; 정 = np.unpackbits(z["정답"][i]).reshape(48, 48, 48).astype(bool); 틀 = np.unpackbits(z["틀"][i]).reshape(48, 48, 48).astype(bool)
    _, _, H = J.정규메시(목록[i]); 몸, _ = J.몸통37((X[i], FS["F"][i], FS["S"][i]), H); 반몸 = np.array([S6.반높이(몸, S6.R(*v)) for v in S6.방향.values()])
    numpy칸 = S6.칸깎기(틀, 몸, 지도(층, 반몸))
    h = torch.tensor(반[None], device=dev); p = 원(층); q = L.부드러운칸(p, h, torch.tensor(틀.reshape(1, -1), device=dev).float())
    torch칸 = (q[0] > .5).cpu().numpy().reshape(48, 48, 48)
    윤 = torch.tensor(np.array(입[i, :, 1]) > 0, device=dev)[None]; Q = torch.tensor(Qs[int(i)], device=dev)
    챔 = lambda pp: float(L.챔퍼(*L.점구름(pp, h, 윤, gen)[0], Q))
    무작위 = 원(rng.integers(0, 18, (6, 128, 128))); 껍 = 원(np.array(입[i, :, 2]))
    줄.append([iou(torch칸, numpy칸), float(L.부드러운IoU(q, torch.tensor(정.reshape(1, -1), device=dev).float())[0]), iou(numpy칸, 정), np.abs(반몸 - 반).max(), 챔(p), 챔(무작위), 챔(껍)])
    print("부품 %5d · ① torch↔numpy 칸 IoU %.4f · 부드러운 IoU(정답) %.3f · numpy 칸 IoU(정답) %.3f · 반 차 %.1e · ② Chamfer 정답층 %.4f 무작위 %.4f 껍질 %.4f" % (i, *줄[-1]), flush=True)
a = np.array(줄); print("\n평균 · ① %.4f (최소 %.4f · 문턱 0.98) · 부드러운 IoU %.3f · numpy %.3f · ② 정답층 %.4f · 무작위 %.4f · 껍질 %.4f · 정답층 < 무작위 %d/%d · < 껍질 %d/%d" % (
    a[:, 0].mean(), a[:, 0].min(), a[:, 1].mean(), a[:, 2].mean(), a[:, 4].mean(), a[:, 5].mean(), a[:, 6].mean(), (a[:, 4] < a[:, 5]).sum(), len(a), (a[:, 4] < a[:, 6]).sum(), len(a)))
assert a[:, 0].min() >= .98, "① 실패 — 좌표 · 부호"; assert (a[:, 4] < a[:, 5]).all() and a[:, 4].mean() < .7 * a[:, 5].mean(), "② 실패"
print("① ② 통과")
