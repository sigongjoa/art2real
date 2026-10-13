# 1d 학습(판정기준29) — U-Net 이 화소마다 「안 깎음 · 구멍 · 홈」 → 덩어리마다 원 / 직사각형 → 윤곽 바탕에서 CadQuery 로 깎기 · 10-13
# venv python 학습4.py → out/설명/구멍/학습4/스냅.json · 지도_eXX_k.png · 결과.json · 망.pt
import os, json, time, numpy as np, cv2
from multiprocessing import Pool
from PIL import Image
import 캐드점수2 as K, 학습3 as T, 윤곽바탕 as B   # torch 는 main 안에서만
O = "G:/art2real/out/설명/구멍/학습4/"; os.makedirs(O, exist_ok=True)
에폭 = 20

def 정답지도(p, 그림):   # 0 안 깎음 · 1 구멍 · 2 홈 (위에서 본 · 바탕 윤곽 안만)
    m = np.zeros((K.N, K.N), np.uint8); px = K.px
    for t, x, y, a, b in p["칸"]:
        if t == 1: cv2.circle(m, (int(round(px(x))), int(round(px(-y)))), int(round(a / (2 * K.반) * K.N)), 1, -1)
        elif t in (2, 3):
            w, h = (a / 2, b / 2) if t == 2 else (b / 2, a / 2); cv2.rectangle(m, (int(round(px(x - w))), int(round(px(-y - h)))), (int(round(px(x + w))), int(round(px(-y + h)))), 2, -1)
    안, _ = B.바깥(그림); m[~안] = 0; return m
def 다각깎기(바, 지도):   # 고침(학습 전): 지도의 구멍(관통) · 홈(깊이 4) 덩어리 윤곽을 그대로 다각형으로 깎음 — 원/직사각형 맞춤은 천장 0.922 라 버림
    import cadquery as cq
    s = T.짓기(바, [])
    for 값, 깊 in ((1, None), (2, K.홈깊이)):
        cs, _ = cv2.findContours((지도 == 값).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cs:
            if cv2.contourArea(c) < 4: continue
            p = cv2.approxPolyDP(c, .8, True)[:, 0, :]
            if len(p) < 3: continue
            pts = [(float(B.화소mm(x + .5)), float(-B.화소mm(y + .5))) for x, y in p]
            try: s = s.cut(cq.Workplane("XY").polyline(pts).close().extrude(K.높 + 2 if 깊 is None else 깊 + 1).translate((0, 0, -1 if 깊 is None else K.높 - 깊)))
            except Exception: pass
    return s
def 점수지도(job):
    바, 지도, m = job
    try: c = K.윗면(다각깎기(바, 지도))
    except Exception: return 0.0
    return float((c & m).sum() / max((c | m).sum(), 1))
def 지도칸(m):   # 지도 → 칸 목록(개수 제한 없음): 구멍 덩어리 → 원 · 홈 덩어리 → 축 맞춘 직사각형
    out = []; mm = lambda v: v / K.N * 2 * K.반
    for 종, 값 in ((1, 1), (2, 2)):
        n, lab, st, cen = cv2.connectedComponentsWithStats((m == 값).astype(np.uint8), connectivity=4)
        for i in range(1, n):
            if st[i, 4] < 6: continue
            cx, cy = B.화소mm(cen[i][0] + .5), -B.화소mm(cen[i][1] + .5)   # 화소 번호 → 화소 가운데
            if 종 == 1: out.append((1, float(cx), float(cy), float(mm(np.sqrt(st[i, 4] / np.pi))), 0.0))
            else:
                w, h = mm(st[i, 2]), mm(st[i, 3]); x0 = B.화소mm(st[i, 0] + st[i, 2] / 2); y0 = -B.화소mm(st[i, 1] + st[i, 3] / 2)
                out.append((2, float(x0), float(y0), float(w), float(h)) if w >= h else (3, float(x0), float(y0), float(h), float(w)))
    return out

if __name__ == "__main__":
    import torch, torch.nn as nn
    torch.manual_seed(29); dev = "cuda"
    class U(nn.Module):
        def __init__(s):
            super().__init__(); b = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU())
            s.e1, s.e2, s.e3, s.e4 = b(1, 32), b(32, 64), b(64, 128), b(128, 192); s.p = nn.MaxPool2d(2)
            s.u3, s.d3 = nn.ConvTranspose2d(192, 128, 2, 2), b(256, 128); s.u2, s.d2 = nn.ConvTranspose2d(128, 64, 2, 2), b(128, 64); s.u1, s.d1 = nn.ConvTranspose2d(64, 32, 2, 2), b(64, 32); s.o = nn.Conv2d(32, 3, 1)
        def forward(s, x):
            x = x[:, None]; a = s.e1(x); b_ = s.e2(s.p(a)); c = s.e3(s.p(b_)); d = s.e4(s.p(c))   # 128 → 64 → 32 → 16 (줄이기)
            c2 = s.d3(torch.cat([s.u3(d), c], 1)); b2 = s.d2(torch.cat([s.u2(c2), b_], 1)); a2 = s.d1(torch.cat([s.u1(b2), a], 1)); return s.o(a2)   # 16 → 32 → 64 → 128 (키우기)
    with Pool(6) as pool:
        Ptr, Xtr, Mtr, Btr = T.묶음(pool, 3000, 27); Pte, Xte, Mte, Bte = T.묶음(pool, 200, 2027)
        Ytr = np.stack([정답지도(p, x) for p, x in zip(Ptr, Xtr)]); Yte = np.stack([정답지도(p, x) for p, x in zip(Pte, Xte)])
        지 = [next(i for i, p in enumerate(Pte) if T.범주of(p) == c) for c in T.범주]
        바탕만 = float(np.mean(pool.map(T.점수, [(b, [], m) for b, m in zip(Bte, Mte)])))
        for k, i in enumerate(지): Image.fromarray((Yte[i] * 120).astype(np.uint8)).save(O + "정답지도_%d.png" % k)
        m = U().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); w = torch.tensor([1., 4., 4.], device=dev)   # 깎을 자리가 적어서 무게를 더 줌
        Xt, Yt = torch.tensor(Xtr, device=dev), torch.tensor(Ytr, dtype=torch.long, device=dev); 스냅 = []; t0 = time.time()
        for ep in range(에폭 + 1):
            m.eval()
            with torch.no_grad(): pred = torch.cat([m(torch.tensor(Xte[i:i + 50], device=dev)).argmax(1) for i in range(0, len(Xte), 50)]).cpu().numpy().astype(np.uint8)
            C = [지도칸(p) for p in pred]; s = pool.map(점수지도, [(b, p, mm) for b, p, mm in zip(Bte, pred, Mte)])   # 점수는 다각형 깎기 · 칸 목록은 개수 기록용
            맞 = float(np.mean([len(c) == T.개수(p["칸"]) for c, p in zip(C, Pte)])); 깎 = (Yte > 0); 예 = (pred > 0); 화소IoU = float((깎 & 예).sum() / max((깎 | 예).sum(), 1))
            for k, i in enumerate(지): Image.fromarray((pred[i] * 120).astype(np.uint8)).save(O + "지도_e%02d_%d.png" % (ep, k))
            스냅.append({"에폭": ep, "시험IoU": float(np.mean(s)), "개수맞힘": 맞, "화소IoU": 화소IoU, "지켜볼": [{"범주": T.범주[k], "바탕": Bte[i], "칸": C[i], "IoU": s[i]} for k, i in enumerate(지)]})
            json.dump({"윤곽바탕만": 바탕만, "범주": T.범주, "정답": [Pte[i] for i in 지], "스냅": 스냅}, open(O + "스냅.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            print("에폭 %2d  시험 IoU %.3f  개수 %.2f  지도 화소 IoU %.3f  (윤곽 바탕만 %.3f)  %.0f 초" % (ep, 스냅[-1]["시험IoU"], 맞, 화소IoU, 바탕만, time.time() - t0), flush=True)
            if ep == 에폭: break
            m.train(); perm = torch.randperm(len(Xt), device=dev)
            for k in range(0, len(Xt), 32):
                i = perm[k:k + 32]; l = nn.functional.cross_entropy(m(Xt[i]), Yt[i], weight=w); opt.zero_grad(); l.backward(); opt.step()
    끝 = 스냅[-1]; 통과 = 끝["시험IoU"] >= .95 and 끝["시험IoU"] > 바탕만 and 끝["화소IoU"] >= .8
    json.dump({"시험IoU_처음": 스냅[0]["시험IoU"], "시험IoU_끝": 끝["시험IoU"], "개수맞힘_끝": 끝["개수맞힘"], "화소IoU_끝": 끝["화소IoU"], "윤곽바탕만": 바탕만, "통과": 통과}, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    torch.save(m.state_dict(), O + "망.pt"); print("끝 · IoU %.3f → %.3f · 개수 %.2f · 화소 IoU %.3f · 윤곽 바탕만 %.3f · 통과 %s" % (스냅[0]["시험IoU"], 끝["시험IoU"], 끝["개수맞힘"], 끝["화소IoU"], 바탕만, 통과))
