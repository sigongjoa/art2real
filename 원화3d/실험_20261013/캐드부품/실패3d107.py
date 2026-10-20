# 실패 3D 보기 자료 — 시험 부품마다 48³ 칸: 정답 · 천장(정답 층으로 깎음) · 판0 · 부드러움(판정기준106) — 평가69 와 같은 깎기 · 10-20
# 사용(venv · ART_MEM_GB=10): 실패3d107.py → out/설명/캐드부품/실패3d/실패3d.html (틀 실패3d_틀.html)
import os, json, base64, numpy as np, cv2
import 천장쪼개기52 as C, 울퉁67 as U, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; D = O + "실패3d/"; os.makedirs(D, exist_ok=True)
te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]; 층 = np.load(O + "층32.npy", mmap_mode="r")
P = {k: np.load(O + f"학습69_{k}/예측.npy", mmap_mode="r") for k in ("판0", "부드러움")}
d0 = np.load(O + "데이터.npz"); X = d0["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
def 도면(a, b):   # 실선 검정 · 숨은선 파랑 → png data URI (입력 그대로 128²)
    img = np.full((128, 128, 3), 255, np.uint8); img[b > 0] = (232, 160, 90); img[a > 0] = 0; return "data:image/png;base64," + base64.b64encode(cv2.imencode(".png", img)[1].tobytes()).decode()
def 깎(i, t):   # 평가69.하나 와 같은 깎기
    h = [float(x) for x in 반[i]]; w = {d: np.where(t[j] == 32, np.nan, hh - t[j] * (2 * hh / 32)) for j, (d, hh) in enumerate(zip(S6.방향, h))}
    return C.깎(U.풀(틀[i]), w, 48, False, h)
iou = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
out = {}
for i in [59, 6004, 5411, 5924, 5700, 8519, 8380, 7838, 6064, 3861, 7307, 2435, 325, 1569]:
    t = int(np.nonzero(te == i)[0][0]); g = U.풀(정[i]).astype(bool)
    팔 = {"정답": g, "틀": U.풀(틀[i]), "천장": 깎(i, np.array(층[i])), "판0": 깎(i, np.array(P["판0"][t])), "부드러움": 깎(i, np.array(P["부드러움"][t]))}
    팔 = {k: v.astype(bool) for k, v in 팔.items()}
    out[str(i)] = {k: {"칸": base64.b64encode(np.packbits(v.ravel())).decode(), "IoU": round(iou(v, g), 3), "남음": int((v & ~g).sum()), "모자람": int((g & ~v).sum())} for k, v in 팔.items()}
    out[str(i)]["도면"] = {"위": 도면(X[i], HX[i]), "앞": 도면(F[i], HF[i]), "옆": 도면(S[i], HS[i])}
    print(i, {k: (v["IoU"], v["남음"], v["모자람"]) for k, v in out[str(i)].items() if k != "도면"}, flush=True)
틀h = open("실패3d_틀.html", encoding="utf-8").read(); open(D + "실패3d.html", "w", encoding="utf-8").write(틀h.replace("__DATA__", json.dumps(out, ensure_ascii=False))); print("html")
