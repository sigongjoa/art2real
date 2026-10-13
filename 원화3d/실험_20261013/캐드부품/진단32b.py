import json, numpy as np, trimesh
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0][:200]; L = json.load(open(O + "목록.json", encoding="utf-8"))
for j in (3, 17, 75, 135, 154, 196, 199, 28):
    v, f, H = J.정규메시(L[te[j]]); m = trimesh.Trimesh(v, f, process=False); 정 = J.점유_메시(v, f)
    print(j, "정답 점유", int(정.sum()), "· 닫힘", m.is_watertight, "· 면", len(f), "· 메시 부피 %.4f" % abs(m.volume), "· H %.3f" % H)
