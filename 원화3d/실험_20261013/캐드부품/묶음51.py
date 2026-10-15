# 판정기준51 다섯 묶음 — 부품 번호 i → 조립 폴더 이름 해시로 0 ~ 4 · 같은 조립의 형제 부품은 같은 묶음(감사: 부품 번호 해시는 형제를 다른 묶음에 갈랐다) · 10-15
# 시험 분할(데이터.py)은 md5(폴더) % 10 == 0 — 묶음은 같은 해시의 다른 자리(// 10 % 5)를 써서 시험 분할과 엮이지 않게 · 사용(venv): 묶음51.py → 검사
import json, hashlib, numpy as np
O = "G:/art2real/out/설명/캐드부품/"
폴더 = [p.rstrip("/").split("/")[-2] for p in json.load(open(O + "목록.json", encoding="utf-8"))]   # .../parts/<조립 폴더>/<부품>.stl
_해 = [int(hashlib.md5(f.encode()).hexdigest(), 16) for f in 폴더]
def 묶음(i): return _해[int(i)] // 10 % 5
if __name__ == "__main__":
    import collections
    시, ok = np.load(O + "데이터.npz")["시험"], np.load(O + "데이터51.npz")["ok"]; n = len(시)
    assert len(폴더) >= n and all((_해[i] % 10 == 0) == bool(시[i]) for i in range(n)), "목록 순서 ≠ 데이터 순서"
    tr = np.nonzero(~시 & ok)[0]; b = np.array([묶음(i) for i in tr])
    print("학습 부품", len(tr), "· 묶음 크기", np.bincount(b, minlength=5).tolist())
    조 = collections.defaultdict(set); [조[폴더[i]].add(int(k)) for i, k in zip(tr, b)]
    걸침 = sum(len(s) > 1 for s in 조.values()); print("조립", len(조), "· 두 묶음에 걸친 조립", 걸침)
    옛 = collections.defaultdict(set); [옛[폴더[i]].add((i * 2654435761 % 2 ** 32) % 5) for i in tr]
    print("참고 · 옛 부품 번호 묶음이면 걸친 조립", sum(len(s) > 1 for s in 옛.values()))
    assert 걸침 == 0
