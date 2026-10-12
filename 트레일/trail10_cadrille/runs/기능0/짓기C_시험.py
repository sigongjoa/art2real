# 짓기C 자체 검사 — 합성 구는 공으로 · 정사각 막대는 원기둥 구간으로 안 걸려야 · python 짓기C_시험.py
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x", "모델T_검증뺌"]
import numpy as np
from 짓기C import 공찾기, 원기둥구간
n = 256; yy, xx = np.mgrid[:n, :n]
def 원(cy, cx): return ((yy - cy) ** 2 + (xx - cx) ** 2 < 40 ** 2) | ((yy > cy - 8) & (yy < cy + 8) & (xx > cx) & (xx < cx + 120))   # 구 + 옆으로 뻗은 목
# 구 중심 (X, Y, Z) = (128, 128, 100) · 축 a 그림은 행 = o[0] · 열 = o[1]
S = np.stack([원(128, 100), 원(128, 100), 원(128, 100), 원(128, 100), 원(128, 128), 원(128, 128)]).astype(float); b = 공찾기(S); print("구", b); assert len(b) >= 1 and abs(b[0][1] - 40) < 6 and len(b[0][2]) == 2
네 = np.zeros((n, n)); 네[60:200, 100:156] = 1; 단 = np.zeros((n, n)); 단[100:156, 100:156] = 1
S2 = np.stack([단, 단, 네, 네, 네.T, 네.T]).astype(float); print("막대", 원기둥구간(S2)); assert not 원기둥구간(S2)
print("ok 자체 검사")
