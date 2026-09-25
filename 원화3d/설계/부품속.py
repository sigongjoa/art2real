"""분할안(기본안_<c>.json)의 상자 하나하나 안에 실제로 나올 부품을 짓는다 — out/부품속_<c>.html

  몸 = 정면 · 옆 원화 실루엣의 교집합 (3 px = 0.4 mm 칸 · 노즐 한 줄)
  칸 주인 = 그 칸이 가장 깊이 들어가 있는 상자 (겹친 곳을 나눠 갖는다)
  몸통 · 머리 · 허리 = 왼 반을 거울로 · 다리 등 거울 짝 = L 을 지어 R 은 뒤집기 · 팔은 원화 그대로
  나누는 부품 = 벽 1.2 mm 껍질로 속을 비우고 가르는 면에서 반쪽 둘 (가르는 면 쪽이 열린 컵)
               + 보스 둘 (속 기둥) · 한쪽 보스에 핀 · 다른 쪽 보스에 구멍
  관절 = 볼 · 폴리캡 · 플러그를 따로 조각으로 (회색)
이건 보기용이다. 출력 STL 은 같은 규칙을 메시 불리언으로 다시 짓는다 (0.4 mm 칸으로는 틈 0.2 mm 를 못 담는다)."""
import base64, json, os, sys
import numpy as np, trimesh
from PIL import Image
from scipy import ndimage
from skimage.measure import marching_cubes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hull as H  # noqa

V = 3                    # 원화 화소 → 칸
벽mm, 보스mm, 핀mm, 구멍mm, 핀길이mm = 1.2, 1.6, 0.9, 1.15, 2.4

def 마스크(path, 청소=False):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 10
    if 청소:   # 옆 그림의 가로 줄 같은 얇은 잡선을 떼고 가장 큰 덩어리만
        a = ndimage.binary_opening(a, iterations=3)
        lab, n = ndimage.label(a); a = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    return a

def 메시(M, mmv, 원점):
    if M.sum() < 8: return None
    P = np.pad(M, 2).astype(np.float32)
    v, f, _, _ = marching_cubes(ndimage.gaussian_filter(P, 0.7), 0.5)
    v = (v - 2) * V                       # 칸 → 원화 화소 [y, x, z]
    y, x, z = v[:, 0] + 원점[0], v[:, 1] + 원점[1], v[:, 2] + 원점[2]
    m = trimesh.Trimesh(np.c_[x, -y, -z], f[:, ::-1], process=True)   # 화소 → 보기 좌표 (위 +y · 앞 +z)
    if len(m.faces) > 4000:                                             # 보기용 — 삼각형 1/4 (닫힘은 아래서 다시 센다)
        s = m.simplify_quadric_decimation(percent=0.75)
        if s.is_watertight: m = s
    return m

def 원기둥(shape, c, 축, r, a0, a1):
    """칸 격자에서 축 방향 원기둥 (c 는 다른 두 축 좌표, a0..a1 는 축 위 구간)"""
    I = np.indices(shape); 나머지 = [k for k in range(3) if k != 축]
    d2 = (I[나머지[0]] - c[0]) ** 2 + (I[나머지[1]] - c[1]) ** 2
    return (d2 <= r * r) & (I[축] >= a0) & (I[축] < a1)

def main(c="오메가몬"):
    here = os.path.dirname(os.path.abspath(__file__))
    안 = json.load(open(os.path.join(here, "기본안_%s.json" % c), encoding="utf-8"))
    src, base = H.CASES[c]["src"], H.art_dir(c)
    F = 마스크(os.path.join(base, src["front"])); S = 마스크(os.path.join(base, src["side"]), 청소=True)
    mmpx = 125 / (968 - 45); ax = 안["axis"]
    Fv, Sv = F[::V, ::V], S[::V, ::V]
    몸 = Fv[:, :, None] & Sv[:, None, :]                    # [y, x, z]
    print("몸 칸 %d · 격자 %s" % (몸.sum(), 몸.shape))

    부품 = 안["parts"]; 상자 = []                              # (이름, 부품, 거울R?)
    for p in 부품:
        상자.append((p["id"], p, False))
        if p["거울"]: 상자.append((p["id"] + "#R", p, True))
    def 칸상자(p, R):
        x = 2 * ax - p["x"] - p["w"] if R else p["x"]
        return (slice(p["y"] // V, (p["y"] + p["h"]) // V + 1), slice(x // V, (x + p["w"]) // V + 1),
                slice(p["sx"] // V, (p["sx"] + p["sw"]) // V + 1))
    # 칸 주인 = 그 칸이 가장 깊이 들어가 있는 상자 (상자 중심에서 반폭으로 나눈 거리의 최대 성분이 가장 작은 것)
    주인 = np.full(몸.shape, -1, np.int16); 최선 = np.full(몸.shape, np.inf, np.float32)
    for k, (_, p, R) in enumerate(상자):
        sl = 칸상자(p, R); I = np.indices(몸[sl].shape).astype(np.float32)
        d = np.max([np.abs(I[a] + sl[a].start - (sl[a].start + sl[a].stop - 1) / 2) / max((sl[a].stop - sl[a].start) / 2, 1) for a in range(3)], axis=0)
        더 = 몸[sl] & (d < 최선[sl]); 최선[sl][더] = d[더]; 주인[sl][더] = k

    axv = ax / V; xs = np.arange(몸.shape[1])
    def 거울(M): j = np.round(2 * axv - xs).astype(int); ok = (j >= 0) & (j < len(xs)); o = np.zeros_like(M); o[:, ok] = M[:, j[ok]]; return o
    벽, 보스r, 핀r, 구멍r, 핀길이 = [round(v / (mmpx * V)) for v in (벽mm, 보스mm, 핀mm, 구멍mm, 핀길이mm)]
    대칭블록 = {"몸통", "머리", "허리"}
    조각들, 표 = [], []
    for k, (이름, p, R) in enumerate(상자):
        if R: continue                                       # R 은 L 메시를 뒤집어 만든다
        M = 주인 == k
        if p["블록"] in 대칭블록:
            왼 = M & (xs[None, :, None] < axv); M = 왼 | 거울(왼)
        if M.sum() == 0: continue
        # 부품 둘레 상자로 잘라 계산을 줄인다
        idx = np.argwhere(M); lo = np.maximum(idx.min(0) - 3, 0); hi = idx.max(0) + 4
        m = M[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        원점 = lo * V                                         # 화소 [y, x, z]
        반 = {"통": None, "앞뒤": 2, "좌우": 1, "위아래": 0}[p["분할"]]
        낼 = []                                                # (조각 이름, 칸, 종류, 벌림 방향)
        if 반 is None:
            낼.append((이름, m, "통", None))
        else:
            경계화소 = {2: p["sx"] + p["sw"] * p["비"], 1: p["x"] + p["w"] * p["비"], 0: p["y"] + p["h"] * p["비"]}[반]
            s = int(round(경계화소 / V)) - lo[반]
            속 = ndimage.binary_erosion(m, iterations=벽)
            껍 = m & ~속
            I = np.indices(m.shape)[반]
            # 보스 자리: 가르는 면에서 속이 가장 두꺼운 두 곳 (긴 축 양쪽)
            면 = np.take(속, min(max(s, 0), m.shape[반] - 1), axis=반)
            보스 = np.zeros_like(m); 핀 = np.zeros_like(m); 구멍 = np.zeros_like(m)
            if 면.sum() > 20:
                q = np.argwhere(면); e = ndimage.distance_transform_edt(면)
                u = np.linalg.svd(q - q.mean(0), full_matrices=False)[2][0]; t = (q - q.mean(0)) @ u
                for 몫 in (0.2, 0.8):
                    가 = np.abs(t - np.quantile(t, 몫)) < max(3, 0.08 * np.ptp(t))
                    c2 = q[가][np.argmax(e[tuple(q[가].T)])]
                    보스 |= 원기둥(m.shape, c2, 반, 보스r, 0, m.shape[반]) & m
                    핀 |= 원기둥(m.shape, c2, 반, 핀r, s, s + 핀길이)
                    구멍 |= 원기둥(m.shape, c2, 반, 구멍r, s, s + 핀길이 + 1)
            몸체 = 껍 | 보스
            이름둘 = {2: ("앞", "뒤"), 1: ("왼", "오"), 0: ("위", "아래")}[반]
            A = 몸체 & (I < s); B = 몸체 & (I >= s) & ~구멍
            dA = [0, 0, 0]; dA[반] = -1
            낼.append((이름 + " " + 이름둘[0], A | 핀, "반쪽", dA))
            낼.append((이름 + " " + 이름둘[1], B, "반쪽", [-v for v in dA]))
        for 조각, 칸, 종류, d in 낼:
            me = 메시(칸, mmpx, 원점)
            if me is None: continue
            me.apply_translation([-ax, 0, 0]); me.apply_scale(mmpx)
            if d is not None: d = [d[1], -d[0], -d[2]]                 # [y,x,z] → 보기 좌표
            조각들.append((p, 조각, 종류, d, me))
            if p["거울"]:
                r = me.copy(); r.apply_transform(np.diag([-1, 1, 1, 1])); r.invert()
                rd = None if d is None else [-d[0], d[1], d[2]]
                조각들.append((p, 조각.replace(p["id"], p["id"][:-1] + "R" if p["id"].endswith("L") else p["id"] + "R"), 종류, rd, r))
        # 관절 부품 (회색) — 붙는 자리에서 부모와 자식 사이
        if p.get("jx") is not None and p["방식"] in ("볼 조인트", "축(폴리캡)", "끼움 플러그"):
            zc = p["sx"] + p["sw"] / 2
            if p["방식"] == "볼 조인트": j = trimesh.util.concatenate([trimesh.creation.icosphere(2, 2.5), trimesh.creation.cylinder(1.2, 4, transform=trimesh.transformations.translation_matrix([0, -2.5, 0]) @ trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))])
            elif p["방식"] == "축(폴리캡)": j = trimesh.creation.annulus(1.2, 2.6, 4, transform=trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            else: j = trimesh.creation.cylinder(1.3, 5, transform=trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            j.apply_translation([(p["jx"] - ax) * mmpx, -p["jy"] * mmpx, -zc * mmpx])
            조각들.append((p, p["id"] + " — " + p["방식"], "관절", None, j))
            if p["거울"]:
                r = j.copy(); r.apply_transform(np.diag([-1, 1, 1, 1])); r.invert()
                조각들.append((p, 조각들[-1][1].replace(p["id"], p["id"][:-1] + "R"), "관절", None, r))

    # 보기 파일
    색표 = ["#e8590c", "#1c7ed6", "#2f9e44", "#ae3ec9", "#f59f00", "#0c8599", "#d6336c", "#5c940d", "#6741d9", "#495057"]
    블록들 = list(dict.fromkeys(p["블록"] for p in 부품))
    전체 = trimesh.util.concatenate([t[4] for t in 조각들]); 중심 = 전체.bounds.mean(0)
    데 = []
    for p, 조각, 종류, d, me in 조각들:
        me = me.copy(); me.apply_translation(-중심)
        b = me.extents
        데.append({"부품": p["id"], "조각": 조각, "블록": p["블록"], "종류": 종류, "벌림": d,
                  "색": "#9a9a92" if 종류 == "관절" else 색표[블록들.index(p["블록"]) % len(색표)],
                  "치수": [round(float(x), 1) for x in b], "닫힘": bool(me.is_watertight), "부피": round(float(abs(me.volume)) / 1000, 2),
                  "v": base64.b64encode(me.vertices.astype(np.float32).tobytes()).decode(),
                  "f": base64.b64encode(me.faces.astype(np.uint32).tobytes()).decode()})
    n반 = sum(1 for x in 데 if x["종류"] != "관절"); n관 = len(데) - n반
    print("조각 %d (관절 %d) · 삼각형 %d · 닫힘 %d/%d" % (n반, n관, sum(len(t[4].faces) for t in 조각들), sum(x["닫힘"] for x in 데), len(데)))
    t = open(os.path.join(here, "부품속.src.html"), encoding="utf-8").read().replace("__DATA__", json.dumps(데, ensure_ascii=False))
    t = t.replace("__THREE__", open(os.path.join(here, "three.iife.js"), encoding="utf-8").read())
    out = os.path.join(H.OUT, "부품속_%s.html" % c); open(out, "w", encoding="utf-8").write(t)
    print(out, "%.1f MB" % (os.path.getsize(out) / 2 ** 20))

if __name__ == "__main__":
    main(*sys.argv[1:])
