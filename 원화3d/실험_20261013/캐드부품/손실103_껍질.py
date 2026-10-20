import numpy as np, 손실103 as L
시부 = L.부[L.시][:300]; a = np.zeros(6)
for i in 시부[:150]:
    l, p = L.손실(i); g = np.array(L.층[i]).astype(int); s = np.array(L.껍32[i]).astype(int); 안 = np.array(L.입[i][:, 1]) > 0; 옛 = np.where(L.입[i][:, 2] == 17, 32, L.입[i][:, 2].astype(int) * 2)
    m = 안 & (g < 32) & (g <= s); 다름 = 옛 != s
    a += [l[m].sum(), l[m & 다름].sum(), (m & 다름).sum() , m.sum(), (m & (p != g)).sum(), (m & (p != g) & 다름).sum()]
print("껍질 그대로 화소: 입력 16단 껍질 ≠ 32단 껍질 몫 %.3f · 손실 중 그 화소 몫 %.3f · 틀린 것 중 그 화소 몫 %.3f" % (a[2] / a[3], a[1] / a[0], a[5] / a[4]))
