# 3-9 회전체 경계: 옆선 곡률 최소점(오목이 가장 센 곳) = 고리 경계. 꼭 가장 가는 곳은 아니다.
# python 3-9.py → 3-9.json (3-9.typ 가 읽음)
import json, numpy as np
y = np.linspace(0, 10, 1001)
def bump(c, a, wd, wu):  # 아래 · 위 폭이 다른 혹 → 오목점과 가장 가는 점이 어긋남
    w = np.where(y < c, wd, wu); return a * np.exp(-((y - c) / w) ** 2)
x = 1.25 + bump(2.2, 0.75, 0.6, 0.9) + bump(4.9, 0.6, 0.4, 0.8) + bump(7.5, 0.7, 0.9, 0.6) + 2.4 * np.exp(-((y - 10.4) / 0.9) ** 2) + 2.4 * np.exp(-((y + 0.4) / 0.9) ** 2)
x1 = np.gradient(x, y); x2 = np.gradient(x1, y); k = x2 / (1 + x1 ** 2) ** 1.5
# 기둥이 앞(안쪽이 물체): 오목 = k 의 양의 극대
neck = [i for i in range(20, 981) if x[i] == x[i - 20:i + 21].min()]
crest = [0] + [i for i in range(20, 981) if x[i] == x[i - 20:i + 21].max()] + [1000]
# 마루 사이 골마다 가장 센 오목점 하나
cut = [a + int(np.argmax(k[a:b])) for a, b in zip(crest, crest[1:])]
# 종 모양: z = exp(-r²/2), 곡률 최대(오목) 자리 — z" 최대 √3 보다 조금 바깥
r = np.linspace(0, 4, 401); z = np.exp(-r ** 2 / 2); z2 = np.gradient(np.gradient(z, r), r); kz = z2 / (1 + np.gradient(z, r) ** 2) ** 1.5
rb = float(r[np.argmax(kz)])
assert 3 ** 0.5 < rb < 2.2, rb
json.dump({"pts": [[float(a), float(b)] for a, b in zip(x, y)], "cut": cut, "neck": neck, "rb": rb}, open("3-9.json", "w"))
print("cut", y[cut], "neck", y[neck], "rb", rb)
