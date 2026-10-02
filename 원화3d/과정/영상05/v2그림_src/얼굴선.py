# 얼굴-꽃병 옆선 하나 · 3-1~3-4 공통. x(y) = 꽃병 반지름(오른쪽 선), 얼굴은 x > x(y) 쪽.
# 부품 경계 = 곡률 최소점: 얼굴이 앞이면 x'' 의 음의 극소, 꽃병이 앞이면 x'' 의 양의 극대.
import json, numpy as np
y = np.linspace(0, 10, 801)
g = lambda c, w, a: a * np.exp(-((y - c) / w) ** 2)
base = 1.05 + 2.0 * np.exp(-((y - 10.6) / 3.0) ** 2) + 1.9 * np.exp(-((y + 0.6) / 1.3) ** 2)
x = base - g(8.0, 0.9, 0.42) - g(5.85, 0.48, 0.6) - g(4.75, 0.22, 0.28) - g(4.05, 0.22, 0.30) - g(2.9, 0.45, 0.35)
d2 = np.gradient(np.gradient(x, y), y)
k = d2 / (1 + np.gradient(x, y) ** 2) ** 1.5
def ext(s):  # s*k 의 극대 중 뚜렷한 것
    return [i for i in range(5, len(y) - 5) if s * k[i] == max(s * k[i - 5:i + 6]) and s * k[i] > 0.25]
dd = lambda L: [i for j, i in enumerate(L) if j == 0 or i - L[j - 1] > 16]
face, vase = [i for i in dd(ext(-1)) if y[i] < 9], dd(ext(1))  # 머리 꼭대기 모서리는 판 끝이라 뺌
pts = [[round(float(a), 4), round(float(b), 4)] for a, b in zip(x, y)]
json.dump({"pts": pts, "face": face, "vase": vase, "k": [round(float(v), 3) for v in k]}, open("얼굴선.json", "w"))
print("face", [round(y[i], 2) for i in face]); print("vase", [round(y[i], 2) for i in vase])
