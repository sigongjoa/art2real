# 판정기준51 루프 이음새 — (가) 칸 ↔ (나) 층 · 10-15
# 칸에서층: 48³ [x, y, z](짓기.점유_캐드 격자) → 128³ 가장 가까운 칸 → 지역틀.깊이층 방향마다 → (6, 128, 128) uint8 · (가) 출력을 (나) 앞 판으로
# CAD에서칸: CadQuery 고체 → 짓기.점유_캐드 48³ · (나) CAD 를 (가) 앞 판으로(부품당 OCC 광선 · 비쌈)
# 층에서칸: 층 + 반 + 틀 칸 → 여섯방향.칸깎기 와 같은 칸 깎기(CAD 안 지음 · 싼 대용 · 천장51 「CAD 대 칸」 0.866 만큼만 CAD 와 같다)
# 사용(venv): 변환51.py [부품 수 20] → 정답 칸 → 층 이 정답 층과 얼마나 맞나 · 128 메시 칸으로 해상도 몫을 가른다
import sys, numpy as np
import 여섯방향 as S6, 지역틀 as T
O = "G:/art2real/out/설명/캐드부품/"
_j = np.floor((np.arange(128) + .5) * 48 / 128).astype(int)   # 128 칸 가운데 → 그 점을 담은 48 칸(두 격자 모두 [−.55, .55])
def 칸에서층(칸48, 반):
    c = np.asarray(칸48, bool)[np.ix_(_j, _j, _j)]
    return np.stack([T.깊이층(c, k, float(반[n])) if 반[n] > 0 else np.full((128, 128), 17, np.uint8) for n, k in enumerate(S6.방향)])
def CAD에서칸(고체):
    import 짓기 as J; return J.점유_캐드(고체)
_G = (np.arange(48) + .5) / 48 * 1.1 - .55; _P = np.stack(np.meshgrid(_G, _G, _G, indexing="ij"), -1).reshape(-1, 3)
def 층에서칸(층, 반, 틀칸):   # 여섯방향.칸깎기 와 같은 셈 · 반높이를 몸 대신 데이터51 「반」에서
    q = np.asarray(틀칸, bool).reshape(-1).copy()
    for n, (k, (축, 도)) in enumerate(S6.방향.items()):
        h = float(반[n]); r = S6.R(축, 도); 깊 = np.where(층[n] == 17, 2 * h + .1, 층[n] * 2 * h / S6.층수); L = _P @ r
        x = np.clip(np.round((L[:, 0] + .55) / S6.칸 - .5).astype(int), 0, 127); y = np.clip(np.round((-L[:, 1] + .55) / S6.칸 - .5).astype(int), 0, 127)
        q &= ~(L[:, 2] > h - 깊[y, x])
    return q.reshape(48, 48, 48)
if __name__ == "__main__":
    import json, 짓기 as J
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    z = np.load(O + "데이터51.npz"); ok = z["ok"]; idx = np.nonzero(np.load(O + "데이터.npz")["시험"] & ok)[0][:k]
    풀 = lambda a: np.unpackbits(a, axis=-1).reshape(-1, 48, 48, 48).astype(bool)
    정칸, 틀칸, 정층, 반 = 풀(z["정답"][idx]), 풀(z["틀"][idx]), z["층"][idx], z["반"][idx]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1)
    def 비교(층):   # (일치 · ±1 안 · 통째 어긋남 · 둘 다 맞은 화소 층 차 평균)
        a, b = 층.astype(int), 정층_.astype(int); 맞 = (a < 17) & (b < 17)
        return (a == b).mean(), (np.abs(a - b) <= 1).mean(), ((a == 17) != (b == 17)).mean(), np.abs(a - b)[맞].mean() if 맞.any() else np.nan
    줄 = {"48 → 128": [], "128 메시 칸": []}; 칸점 = {"정답 층": [], "48 → 128 층": [], "128 메시 칸 층": []}
    for n, i in enumerate(idx):
        정층_ = 정층[n]; 가 = 칸에서층(정칸[n], 반[n]); v, f, _ = J.정규메시(L[i]); 나 = np.stack([T.깊이층(J.점유_메시(v, f, 128), kk, float(반[n][m])) for m, kk in enumerate(S6.방향)])
        줄["48 → 128"].append(비교(가)); 줄["128 메시 칸"].append(비교(나))
        for 이, 층 in (("정답 층", 정층_), ("48 → 128 층", 가), ("128 메시 칸 층", 나)): 칸점[이].append(iou(층에서칸(층, 반[n], 틀칸[n]), 정칸[n]))
        if n == 0:   # 자기 검사: 칸에서층 → 층에서칸 이 틀 ∩ 정답 칸 을 되살리는가(같은 격자 · 같은 회전이면 ≥ 0.9)
            print("자기 검사 · 층에서칸(칸에서층(정답)) 대 정답 칸 IoU %.3f" % iou(층에서칸(가, 반[n], 틀칸[n]), 정칸[n] & 틀칸[n]))
    print("부품 %d (시험 · ok 앞에서)" % len(idx))
    for 이, r in 줄.items():
        r = np.array(r); print("%-10s 화소 일치 %.3f · ±1 층 안 %.3f · 통째 어긋남 %.4f · 층 차 평균 %.3f (최소 일치 %.3f)" % (이, *np.nanmean(r, 0), r[:, 0].min()))
    print("정답 칸 빈 부품 %d (층 차 평균에서 빠짐)" % int((정칸.sum((1, 2, 3)) == 0).sum()))
    for 이, r in 칸점.items(): print("층에서칸(%s) 대 정답 칸 IoU 평균 %.3f" % (이, np.mean(r)))
    고 = J.몸통37((np.load(O + "데이터.npz")["X"][idx[0]], np.load(O + "데이터_앞옆.npz")["F"][idx[0]], np.load(O + "데이터_앞옆.npz")["S"][idx[0]]), J.정규메시(L[idx[0]])[2])[0]
    print("CAD에서칸(몸통37 틀) 대 데이터51 틀 칸 같음 %.4f" % (CAD에서칸(고) == 틀칸[0]).mean())
