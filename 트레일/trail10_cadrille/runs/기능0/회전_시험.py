import sys, os; sys.path.insert(0, os.getcwd()); sys.argv = ["x"]
import numpy as np
from 회전 import 찾기, _돌림
# 자체 검사: 원판 → 걸림 · 정사각 → 안 걸림
n = 256; yy, xx = np.mgrid[:n, :n]; 원 = ((yy - 128) ** 2 + (xx - 128) ** 2 < 60 ** 2).astype(float); 네모 = np.zeros((n, n)); 네모[70:190, 70:190] = 1
옆 = np.zeros((n, n)); 옆[80:180, 68:189] = 1   # 원기둥 옆모습: 행 = 축 방향 · 열 = 지름 (반지름 60)
S = np.stack([원, 원, 옆, 옆, 옆, 옆])   # 축 0(X) 방향은 원 · Y 방향 그림(행 X · 열 Z) · Z 방향 그림(행 X · 열 Y) 은 옆모습
f = 찾기(S); print("원기둥", f["축"], f["돌림"], f["대칭"], f["걸림"]); assert f["걸림"] and f["축"] == 0
assert _돌림(네모 > .5, (129.5, 129.5)) < 0.9, "정사각이 돌림을 넘음"
S2 = np.stack([네모, 네모, 네모, 네모, 네모, 네모]); f2 = 찾기(S2); print("상자", f2["돌림"], f2["대칭"], f2["걸림"]); assert not f2["걸림"]
print("ok 자체 검사")
