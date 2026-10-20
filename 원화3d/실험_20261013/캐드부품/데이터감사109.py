# 데이터 감사 — 정답 48³ 이 틀(도면 세 장 몸통37) 밖으로 나가는 부품: 정답 칸이 틀렸나(메시 부피와 칸 수) · 틀이 잘라먹나(메시 표면 점이 틀 밖) · 10-20
# 사용(venv · ART_MEM_GB=10): 데이터감사109.py → out/설명/캐드부품/데이터감사109.json
import json, numpy as np, trimesh, 짓기 as J, 울퉁67 as U
O = "G:/art2real/out/설명/캐드부품/"; L = json.load(open(O + "목록.json", encoding="utf-8")); z = np.load(O + "데이터51.npz"); 틀, 정 = z["틀"], z["정답"]
te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 범 = json.load(open(O + "범위46.json")); 예 = te[범]; n = 48; 칸 = 1.1 / n
def 하나(i):
    g = U.풀(정[i]).astype(bool); t = U.풀(틀[i]).astype(bool); v, f, _ = J.정규메시(L[i]); m = trimesh.Trimesh(v, f, process=False)
    기대 = abs(m.volume) / 칸 ** 3 if m.is_watertight else np.nan   # 부피가 차지할 칸 수
    p = trimesh.sample.sample_surface(m, 4000, seed=0)[0]; ix = np.clip(((p + .55) / 칸).astype(int), 0, n - 1)
    밖 = ~t[ix[:, 0], ix[:, 1], ix[:, 2]]   # 표면 점이 들어간 칸이 틀 밖 (정답 칸과 같은 좌표: g = (arange + .5)/n·1.1 − .55)
    return dict(부품=int(i), 닫힘=bool(m.is_watertight), 정답칸=int(g.sum()), 부피칸=float(기대), 정답틀밖=float((g & ~t).sum() / max(g.sum(), 1)), 표면점틀밖=float(밖.mean()))
r = [하나(i) for i in 예]; json.dump(r, open(O + "데이터감사109.json", "w", encoding="utf-8"), ensure_ascii=False)
a = np.array([[x["정답틀밖"], x["표면점틀밖"], x["정답칸"], x["부피칸"], x["닫힘"]] for x in r], float); b = a[:, 0] > .05
print("정답이 틀 밖 5 % 넘는 부품", b.sum(), "/", len(a))
print("  그중 메시 표면 점이 틀 밖 5 % 넘음(틀이 잘라먹음)", int((b & (a[:, 1] > .05)).sum()), "· 표면 점 틀 밖 중앙값 %.3f" % np.median(a[b, 1]))
c = b & (a[:, 4] > 0); print("  그중 닫힌 메시", int(c.sum()), "· 정답칸 / 부피칸 중앙값 %.2f" % np.median(a[c, 2] / np.maximum(a[c, 3], 1)), "(1 이면 정답 칸 수는 맞음)")
d = ~b & (a[:, 4] > 0); print("나머지 닫힌 메시: 표면 점 틀 밖 중앙값 %.3f · 정답칸/부피칸 중앙값 %.2f" % (np.median(a[d, 1]), np.median(a[d, 2] / np.maximum(a[d, 3], 1))))
