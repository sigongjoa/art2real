# 쇼츠 59 재료 — 시험 131 번(브래킷 · ① 0.14 ③ 0.90): 정답 · ① 위에서만 · ② 세 실루엣 · ③ 위앞옆 파기 렌더 600² · 10-14
import json, os, numpy as np
from PIL import Image
import 천장34 as T, 그림34 as G
O = "G:/art2real/out/영상05/대화/59_천장/자료/"; os.makedirs(O, exist_ok=True)
if __name__ == "__main__":
    d = np.load(T.O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; L = json.load(open(T.O + "목록.json", encoding="utf-8")); R = np.load(T.O + "부피IoU_34.npy")
    sc, v, f, H = T.장면(L[te[131]]); 정, 판 = T.복셀(sc, v, f, H, 48)
    for 이름, m in (("정답", 정), ("1", 판["①"]), ("2", 판["②"]), ("3", 판["③"])): Image.fromarray(G.그리기(m, 600)).save(O + "브래킷_%s.png" % 이름)
    print("131:", np.round(R[131, :5], 3))
