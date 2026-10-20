# 판0(학습69_판0) 손실이 어디서 나오나 — 학습과 같은 손실(CE + .1 L1 · 화소마다)을 시험 300 · 학습 300 에서 재고 갈래별 몫 · 10-20
# 갈래: 윤곽 밖 / 통째(32) / 껍질 그대로 / 껍질 + 1 / 깎인 속(≥ 껍질 + 2) · 선에서 거리 · 면 꼴(7×7 정답 창) · 얇은 판 · 방향 · 부품 쏠림
# 사용(venv · ART_MEM_GB=10): 손실103.py → out/설명/캐드부품/손실103/결과.json · 화소손실.npy(시험 300 × 6 × 128² float16)
import os, json, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn, cv2
import 학습 as T, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; D = O + "손실103/"; os.makedirs(D, exist_ok=True); dev = "cuda"; K = 32
입 = np.load(O + "입력51.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r"); 껍32 = np.load(O + "껍질32.npy", mmap_mode="r"); z = np.load(O + "데이터51.npz"); ok, 반 = z["ok"], z["반"]
시 = np.load(O + "데이터.npz")["시험"]; 찬 = z["정답"].any(1); 부 = np.arange(len(ok)); tr = 부[~시 & ok & 찬]
class 모(nn.Module):
    def __init__(s): super().__init__(); s.u = T.U만들기(10, 1)(); s.u.o = nn.Conv2d(32, 33, 1)
    def forward(s, x):
        u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
        c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
m = 모().to(dev); m.load_state_dict(torch.load(O + "학습69_판0/망.pt")); m.eval(); 눈 = torch.eye(6, device=dev); 칸값 = torch.arange(33, device=dev).float()
def 손실(i):   # → (6, N, N) 화소 손실 · 예측(껍질로 막은 argmax)
    a = torch.tensor(np.array(입[i]), device=dev).float(); 껍 = torch.where(a[:, 2] == 17, 32., a[:, 2] * 2)   # 학습69 입력() 과 같음
    x = torch.cat([a[:, :1], a[:, 1:2], 껍[:, None] / 32, 껍[:, None] / 32, 눈[:, :, None, None].expand(-1, -1, 128, 128)], 1)
    with torch.no_grad():
        lo = m(x); y = torch.tensor(np.array(층[i]), device=dev).long(); 기대 = (torch.softmax(lo, 1) * 칸값[None, :, None, None]).sum(1)
        l = Fn.cross_entropy(lo, y, reduction="none") + .1 * (기대 - y.float()).abs()   # 학습: ce 평균 + .1 · l1 평균 · 화소마다 같은 무게
        p = torch.maximum(lo.argmax(1), 껍.long())
    return l.cpu().numpy(), p.cpu().numpy()
def 갈래(i, l, p):
    g = np.array(층[i]).astype(int); s = np.array(껍32[i]).astype(int); 안 = np.array(입[i][:, 1]) > 0; 선 = np.array(입[i][:, 0]) > 0; r = {}
    def 더(k, m_): m_ = np.broadcast_to(m_, l.shape); e = r.setdefault(k, [0., 0, 0]); e[0] += float(l[m_].sum()); e[1] += int(m_.sum()); e[2] += int((p[m_] == g[m_]).sum())
    더("전체", np.ones_like(안))
    더("영역: 윤곽 밖", ~안); 더("영역: 안 · 통째(32)", 안 & (g == K)); 더("영역: 안 · 껍질 그대로", 안 & (g < K) & (g <= s)); 더("영역: 안 · 껍질 + 1", 안 & (g < K) & (g == s + 1)); 더("영역: 안 · 깎인 속(≥ 껍질+2)", 안 & (g < K) & (g >= s + 2))
    거 = np.stack([cv2.distanceTransform((~선[n]).astype(np.uint8), cv2.DIST_L2, 3) for n in range(6)])
    for lo_, hi_ in ((0, .5), (.5, 2.5), (2.5, 5.5), (5.5, 999)): 더(f"선에서 거리 {lo_}~{hi_}", 안 & (거 >= lo_) & (거 < hi_))
    g7 = np.stack([cv2.dilate(g[n].astype(np.uint8), np.ones((7, 7), np.uint8)).astype(int) - cv2.erode(g[n].astype(np.uint8), np.ones((7, 7), np.uint8)).astype(int) for n in range(6)])
    for nm, m_ in (("면: 평평(7×7 창 한 층)", g7 == 0), ("면: 비탈(창 1~3 층)", (g7 >= 1) & (g7 <= 3)), ("면: 벽 옆 · 급한 면(창 > 3 층)", g7 > 3)): 더(nm, 안 & (g < K) & m_)
    얇 = np.array([(2 * 반[i][n] / K) / S6.칸 < .5 for n in range(6)])[:, None, None]; 더("얇은 판(층 < 0.5 화소)", 안 & 얇); 더("보통 두께", 안 & ~얇)
    for n, k in enumerate(S6.방향): 더(f"방향: {k}", np.arange(6)[:, None, None] == n)
    return r
if __name__ == "__main__":
    결 = {}; 화 = np.zeros((300, 6, 128, 128), np.float16); 부품손 = []
    for 꼴, 부품 in (("시험", 부[시][:300]), ("학습", tr[:300])):
        합 = {}
        for t, i in enumerate(부품):
            l, p = 손실(i); r = 갈래(i, l, p)
            if 꼴 == "시험": 화[t] = l; 부품손.append(float(l.sum()))
            for k, v in r.items(): e = 합.setdefault(k, [0., 0, 0]); e[0] += v[0]; e[1] += v[1]; e[2] += v[2]
        전 = 합["전체"][0]
        결[꼴] = {k: {"손실 몫": round(v[0] / 전, 4), "화소 몫": round(v[1] / 합["전체"][1], 4), "화소당 손실": round(v[0] / max(v[1], 1), 4), "층 맞음": round(v[2] / max(v[1], 1), 4)} for k, v in 합.items()}
        print(꼴, json.dumps(결[꼴], ensure_ascii=False, indent=0), flush=True)
    b = np.sort(np.array(부품손))[::-1]; 결["시험 부품 쏠림"] = {"위 10 % 부품의 손실 몫": round(b[:30].sum() / b.sum(), 3), "위 30 %": round(b[:90].sum() / b.sum(), 3)}
    np.save(D + "화소손실.npy", 화); np.save(D + "부품손실.npy", np.array(부품손)); json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결["시험 부품 쏠림"])
