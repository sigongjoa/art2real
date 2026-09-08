# -*- coding: utf-8 -*-
"""생성 견갑에 원화 색을 칠한다 — **화소가 아니라 판(panel)을.**

    blender -b --python tri_seg.py                  # 먼저. 부품 그래프를 만든다
    MODE=v0|v1|v2|v3|v4 blender -b --python tri_paint.py    # v4 가 기본

어제 판(v1)은 면마다 정면 한 판의 **화소**를 찍고, 남의 색을 손으로 찍은 색상 규칙
(`b-r>5`, `r-b>20`)으로 막았다. 경계·그래프로 그 반창고를 떼도(v2) 3/4 에서 무너졌다 —
정면 먹선이 옆구리로 길게 끌리고 뿔 하나가 통째로 검었다.

원인은 투영이 아니라 **무엇을 찍었나**였다. 원화는 셀이다. 먹선은 재질이 아니라 그리는
관습이고 안티에일리어싱 화소는 아무 재질도 아닌데, v2 는 그걸 표면색으로 발랐다
(찍을 수 있는 색이 661개였다).

이 판은 **판 라벨**을 찍는다. panels.json 에 18개가 이미 라벨링돼 커밋돼 있다
(lav 10 · gold 5 · dark 2 · white 1). 판마다 평면색 하나를 그 판 안에서 재고,
면은 그중 하나만 받는다. **19색 팔레트 밖으로 나갈 수가 없다** — 검은 뿔이 원리적으로 불가능하다.

    1) 판 라벨   면 -> (법선 순위 + 자기 가림 광선) -> 그 판에서 어느 panel 인가
    2) 라벨 전파 못 받은 면은 부품 그래프 안에서 **정수를 옮긴다** (색이 아니라)
    3) 라벨 다수결 이웃과 다 다른 고립 면을 이웃 판으로
    4) 뿔 계급   생성 뿔은 좌우 대칭 쌍둥이라 하나가 원화의 라벤더 자리를 찍는다(119).
                낱개 투표로는 못 고친다. 넷은 같은 물건이니 재질을 공유한다 —
                **계급으로 표를 모은다** (gold 57%). 뿔을 가리는 건 두께가 아니라
                단면 모양이다: 원뿔은 e2/e3 ~ 1.0~1.25, 앞판은 2.1 (앞판도 얇다).
                세어 보니 4개, 원화 실측 뿔 개수와 같다 — 이게 검사다

두 가지 함정을 밟았다.
  - `sh_pauldron.side.gold` 는 **판이 아니라 경계상자**다. 안의 중앙색이 (129,136,172)
    라벤더지 실측 금 (158,138,76) 이 아니다. 판으로 쓰면 뿔이 통째로 라벤더가 된다
  - 측면은 라벨이 하나뿐이라 무엇을 물어도 라벤더라고 답한다.
    **재질을 구분 못 하는 판은 표를 못 던진다**

그리고 라벨은 재질이지 판별 색이 아니다 — 측면 라벤더에 정면 라벤더의 색을 준다.
그것만으로 두 판의 조명 불일치(127)가 이 부품에서 없어진다.

판정: 정면·측면 지표는 **순환이다**(그 판 원화로 칠하고 그 판에서 잰다). 갈리는 건
3/4 뿐이고 거기엔 원화가 없다 — 눈이 판정이다 (57). out/tripaint_*_q.png
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tri_look                                  # bring() 재사용 (같은 배치여야 비교가 된다)
import tri_seg                                   # adjacency() 재사용
import mask2d                                    # 경계 (bpy 없이도 도는 모듈. 자체검사 붙어 있다)
from mask2d import inside, UAX

T4 = os.path.join(HERE, "..", "trail4_gen3d")    # 블렌더엔 PIL 이 없다. npy 로 읽는다
OUT = os.path.join(HERE, "out")
RES, U0, U1, Z0, Z1 = mask2d.RES, mask2d.U0, mask2d.U1, mask2d.Z0, mask2d.Z1

SH = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
SHELL = np.array(SH["color"]["shell"], float)    # 원화 실측 (87,92,124)
GOLD = np.array(SH["color"]["gold"], float)      # (158,138,76)

# 판마다 (원화, 그 판에서 견갑이 차지하는 폴리곤, 월드축->화면 u)
#   front  u = x   panels.json 의 lav+gold 판 전부 = 견갑 + 뿔
#   side   u = y   sh_pauldron.json 의 측면 윤곽 (뿔 포함)
ART = {k: np.load(os.path.join(T4, "rgb_%s.npy" % k)).astype(float) for k in ("front", "side")}
MODE = os.environ.get("MODE", "v4")   # v0 맨투영 / v1 색규칙 / v2 경계+그래프 / v3 부품투표 / v4 판라벨

# 판 후보: (이름, 광선 진행방향, 법선 점수). bake_art.py 와 같은 규약 — 앞이 -y
VIEWS = [("front", Vector((0., 1., 0.))), ("side", Vector((-1., 0., 0.))),
         ("side", Vector((1., 0., 0.)))]
SCORE = lambda n: np.stack([-n[:, 1], n[:, 0], -n[:, 0]], 1)


# 판별 이득으로 밝기를 맞추는 건 **재 보고 버렸다** — 정면 6.3->6.2 로 안 움직이고
# 측면이 2.8->14.5 로 무너졌다. 두 판의 불일치는 밝기 배율이 아니라 음영 자체다 (127).
def sample(key, P):
    """면 중심을 그 판의 화소로 바로 꽂는다 (UV 도 굽기도 안 쓴다)."""
    py, px = mask2d.topix(P[:, UAX[key]], P[:, 2])     # 변환은 mask2d 하나만 안다
    a = ART[key][py, px]
    return a[:, :3], a[:, 3] >= 128


def assign(o, ctr, nrm, POLY):
    """면마다 판 하나. 순위대로 보되 **가려지지 않고 경계 안**인 판에서 멈춘다."""
    nf = len(ctr)
    sc = SCORE(nrm)
    order = np.argsort(-sc, 1)

    ok, col = [], []                       # 판별 유효성·색을 미리 벡터로 (광선만 루프)
    for name, _ in VIEWS:
        c, alpha = sample(name, ctr)
        ins = mask2d.lookup(POLY[name], ctr[:, UAX[name]], ctr[:, 2])
        ok.append(alpha & ins)
        col.append(c)

    # 스쳐 읽는 면을 문턱으로 자르는 건 **재 보고 버렸다** (MINCOS 0.05~0.7 스윕).
    # 오독이 2.1->2.0 으로 안 움직이고 L1 만 오른다. 메시가 조밀해서 스쳐 읽어도
    # 화소가 제 자리 근처다 — 투영의 손실은 각도가 아니라 **면적**에서 난다 (128)
    view = np.full(nf, -1, np.int8)
    out = np.zeros((nf, 3))
    blocked = np.zeros(nf, bool)           # 경계 밖이라 물린 면 = 어제 오독으로 칠했을 면
    for i in range(nf):
        c = Vector(ctr[i])
        rejected = False
        for slot in range(3):
            v = int(order[i, slot])
            if sc[i, v] <= 0.05:
                break
            dv = VIEWS[v][1]
            hit, loc, _, _ = o.ray_cast(c - dv * 4.0, dv)
            if not (hit and (loc - c).length <= 0.004):
                continue                   # 자기 메시에 가렸다
            if not ok[v][i]:
                rejected = True
                continue                   # 남의 부품 화소다. 색 규칙이 아니라 경계로 거른다
            view[i] = v
            out[i] = col[v][i]
            break
        if view[i] < 0 and rejected:
            blocked[i] = True

    # v0 이 정면색을 주던 면(앞을 보는 면) 중 이 판이 왜 안 주는지 계수한다
    f0 = nrm[:, 1] < -0.15
    lost = f0 & (view != 0)
    occl = np.zeros(nf, bool)
    for i in np.nonzero(lost)[0]:
        dv = VIEWS[0][1]
        hit, loc, _, _ = o.ray_cast(Vector(ctr[i]) - dv * 4.0, dv)
        occl[i] = not (hit and (loc - Vector(ctr[i])).length <= 0.004)
    print("  진단: 앞을 보는 면 %d 중 정면 배정 %d.  놓친 %d = 가림 %d + 경계밖 %d"
          % (f0.sum(), (f0 & (view == 0)).sum(), lost.sum(),
             occl[lost].sum(), (lost & ~occl & ~ok[0]).sum()))
    return view, out, blocked


def spread(lab, pairs, have, col):
    """부품 그래프로 색을 넓힌다. **부품 경계를 못 넘는다.**"""
    und = np.concatenate([pairs, pairs[:, ::-1]])
    und = und[lab[und[:, 0]] == lab[und[:, 1]]]
    nf = len(have)
    filled = 0
    for _ in range(400):
        m = (~have)[und[:, 0]] & have[und[:, 1]]
        if not m.any():
            break
        tgt, src = und[m, 0], und[m, 1]
        o = np.argsort(-src, kind="stable")      # 큰 것부터 덮어써 **최소 인덱스**가 남는다
        pick = np.full(nf, -1, np.int64)
        pick[tgt[o]] = src[o]
        s = pick >= 0
        col[s] = col[pick[s]]                    # 평균이 아니라 복사 — 셀은 평면색이다
        have[s] = True
        filled += int(s.sum())
    return filled


def spread_median(lab, have, col):
    """부품마다 **배정된 면들의 중앙값 하나.** 이웃 복사와 달리 부품 안이 평면색이 된다.
    LESSONS 74 의 "중앙값이면 소수는 못 이긴다" 를 면이 아니라 **부품** 단위로 올린 것."""
    filled = 0
    for pid in np.unique(lab[~have]):
        m = lab == pid
        src = m & have
        if not src.any():
            continue
        tgt = m & ~have
        col[tgt] = np.median(col[src], 0)
        have[tgt] = True
        filled += int(tgt.sum())
    return filled


def labels(POLY):
    """**화소가 아니라 판을 찍는다.** 원화는 셀이다 — 먹선은 재질이 아니라 그리는 관습이고,
    안티에일리어싱 화소는 아무 재질도 아니다. 그런데 v2 는 그걸 표면색으로 발랐고
    (661색을 찍을 수 있었다) 3/4 에서 먹선이 옆구리로 끌리고 뿔이 검게 나왔다.

    판은 이미 라벨링돼 커밋돼 있다 — panels.json 18개(lav 10 · gold 5 · dark 2 · white 1).
    판마다 **평면색 하나**를 그 판 안에서 재고, 면은 그중 하나만 받는다.
    18색 팔레트 밖으로는 나갈 수가 없다.

    측면은 판 분해가 없다. 있는 건 금 상자 하나뿐이라 gold/lav 둘로만 가른다."""
    pn = json.load(open(os.path.join(HERE, "parts", "panels.json"), encoding="utf-8"))
    ps = sorted(pn["panels"], key=lambda p: -p["px"])      # 큰 것부터. 작은 판이 위에 앉는다
    lbl = {k: np.full((RES, RES), -1, np.int16) for k in ART}
    cols, meta = [], []

    # **먹선(dark)·하이라이트(white) 는 재질이 아니라 그리는 관습이다** — 배정 대상에서 뺀다.
    # 색표에는 남긴다(판정이 원화 화소를 분류할 때 쓴다). 다만 면이 그걸 물지는 못한다.
    # 안 빼면 저폴리 메시에서 갑판 한 장이 통째로 새까매진다 (판 하나 = 면 한 장이라)
    nconv = 0
    for p in ps:
        m = mask2d.raster([np.array(p["poly"], float)]) & (ART["front"][..., 3] >= 128)
        if m.sum() < 20:
            continue
        if p["hue"] in ("lav", "gold"):
            lbl["front"][m] = len(cols)
        else:
            nconv += 1
        cols.append(np.median(ART["front"][m][:, :3], 0))
        meta.append("front/%s%d" % (p["hue"], p["id"]))
    print("  재질 판 %d개 · 관습 판(먹선·하이라이트) %d개는 배정에서 뺀다"
          % (len(cols) - nconv, nconv))

    # **음영 톤을 재질로 합친다** (TONE=albedo, 기본). 원화의 라벤더는 판마다 밝기가 다른데
    # (lav10 V=235 ~ lav12 V=115) 그건 재질이 아니라 그 판에 빛이 어떻게 앉았나다.
    # 셀 셰이더가 렌더 때 다시 얹으므로 텍스처는 **평면 알베도**여야 한다.
    # TONE=keep 이면 판별 톤을 그대로 둔다 (원화의 칠한 맛은 남지만 조명이 두 번 얹힌다)
    if os.environ.get("TONE", "albedo") == "albedo":
        lit = {p["id"]: p["lit"] for p in ps}
        for h in ("lav", "gold"):
            idx = [i for i, t in enumerate(meta)
                   if t.startswith("front/" + h) and lit.get(int(t[len("front/") + len(h):]), False)]
            if not idx:
                continue
            base = np.median([cols[i] for i in idx], 0)
            for i, t in enumerate(meta):
                if t.startswith("front/" + h):
                    cols[i] = base
            print("  %s 알베도 = 밝은 판 %d개의 중앙 %s" % (h, len(idx), base.round().astype(int)))

    # 측면은 판 분해가 없다. sh_pauldron 의 side.gold 는 **판이 아니라 경계상자**라
    # 그 안의 중앙색이 (129,136,172) — 실측 금 (158,138,76) 이 아니라 라벤더다.
    # 판으로 쓰면 뿔이 통째로 라벤더가 된다. 상자는 안 쓴다. 측면은 라벤더 한 장이다
    m = POLY["side"] & (ART["side"][..., 3] >= 128)
    lbl["side"][m] = len(cols)
    # **라벨은 재질이지 판별 색이 아니다.** 측면 라벤더를 측면 원화에서 재면 (128,135,166) 인데
    # 같은 재질을 정면에서 재면 (91,95,123) 이다 (127). 재질이 같으니 색도 하나여야 한다 —
    # 제일 큰 정면 라벤더 판의 색을 쓴다. 이것만으로 두 판의 조명 불일치가 없어진다
    base_lav = next(i for i, t in enumerate(meta) if t.startswith("front/lav"))
    cols.append(cols[base_lav])
    meta.append("side/lav")

    print("  판 %d개 (측면 라벤더는 %s 의 색을 쓴다): %s"
          % (len(cols), meta[base_lav], " ".join(meta)))
    return lbl, np.array(cols), meta


def paint_labels(o, ctr, nrm, POLY, lab, pairs, thin):
    """면마다 판 라벨 하나. 못 받으면 **색이 아니라 라벨을** 그래프로 전파한다 —
    없는 색이 만들어질 수가 없다 (v2 의 검은 뿔이 원리적으로 불가능해진다)."""
    LBL, COLS, meta = labels(POLY)
    nf = len(ctr)
    sc = SCORE(nrm)
    order = np.argsort(-sc, 1)
    seen = [mask2d.lookup(LBL[n], ctr[:, UAX[n]], ctr[:, 2]) for n, _ in VIEWS]

    lid = np.full(nf, -1, np.int32)
    for i in range(nf):
        c = Vector(ctr[i])
        for slot in range(3):
            v = int(order[i, slot])
            if sc[i, v] <= 0.05:
                break
            dv = VIEWS[v][1]
            hit, loc, _, _ = o.ray_cast(c - dv * 4.0, dv)
            if not (hit and (loc - c).length <= 0.004):
                continue
            if seen[v][i] < 0:
                continue                         # 어느 판에도 안 들어간다 (먹선 밖·경계 밖)
            lid[i] = seen[v][i]
            break
    have = lid >= 0
    direct0 = have.copy()
    print("  판 라벨 직접 %d/%d (%.1f%%)" % (have.sum(), nf, have.mean() * 100))

    lidf = lid.astype(float)[:, None]            # spread 는 (n,3) 을 기대한다. 라벨을 실어 보낸다
    spread(lab, pairs, have, np.repeat(lidf, 3, 1))
    und = np.concatenate([pairs, pairs[:, ::-1]])
    und = und[lab[und[:, 0]] == lab[und[:, 1]]]
    for _ in range(400):                         # 라벨 전파 (색이 아니라 정수를 옮긴다)
        m = (lid < 0)[und[:, 0]] & (lid >= 0)[und[:, 1]]
        if not m.any():
            break
        t, s2 = und[m, 0], und[m, 1]
        o2 = np.argsort(-s2, kind="stable")
        pick = np.full(nf, -1, np.int64); pick[t[o2]] = s2[o2]
        k = pick >= 0
        lid[k] = lid[pick[k]]
    print("  전파 뒤 %.1f%%.  판별 면 수: %s" % ((lid >= 0).mean() * 100,
          " ".join("%s=%d" % (meta[j], (lid == j).sum()) for j in np.unique(lid[lid >= 0]))))

    # **라벨 다수결로 얼룩을 지운다.** 색이 아니라 정수를 옮기므로 없는 색이 못 생긴다.
    # 판 경계에서 면 하나가 이웃과 다른 판을 찍은 것들이 뿔 뿌리에 점점이 남았다
    und2 = np.concatenate([pairs, pairs[:, ::-1]])
    und2 = und2[lab[und2[:, 0]] == lab[und2[:, 1]]]
    for it in range(2):
        keep = lid[und2[:, 0]] == lid[und2[:, 1]]
        agree = np.bincount(und2[keep, 0], minlength=nf)
        deg = np.bincount(und2[:, 0], minlength=nf)
        lone = (deg >= 3) & (agree == 0)              # 이웃 중 같은 판이 하나도 없다
        if not lone.any():
            break
        o3 = np.argsort(-und2[:, 1], kind="stable")
        pick = np.full(nf, -1, np.int64); pick[und2[o3, 0]] = und2[o3, 1]
        k = lone & (pick >= 0)
        lid[k] = lid[pick[k]]
        print("  라벨 다수결 %d회: 고립된 면 %d개를 이웃 판으로" % (it + 1, k.sum()))

    # 부품별 표 — 그래프 덩어리 하나가 원화의 무슨 색을 골랐나
    hue = np.array([m.split("/")[1].rstrip("0123456789") for m in meta])
    sizes = np.bincount(lab)
    print("  부품별 표 (>=200면):")
    for pid in np.argsort(-sizes):
        if sizes[pid] < 200:
            break
        m = (lab == pid) & (lid >= 0)
        v2 = lid[m]; v2 = v2[np.array([meta[j].startswith("front/") for j in v2], bool)] if m.sum() else v2
        if not len(v2):
            continue
        h, n = np.unique(hue[v2], return_counts=True)
        o2 = np.argsort(-n)
        c = ctr[lab == pid]
        e = np.sqrt(np.linalg.eigvalsh(np.cov((c - c.mean(0)).T)))[::-1]
        print("    #%-5d %6d면 %-8s  주축 %.3f/%.3f/%.3f  가늘기 %.2f   %s"
              % (pid, sizes[pid], "얇음" if thin[lab == pid][0] else "두꺼움",
                 e[0], e[1], e[2], e[0] / max(e[1], 1e-9),
                 " ".join("%s %.0f%%" % (h[j], n[j] / n.sum() * 100) for j in o2)))

    # **뿔은 계급으로 표를 모은다.** 생성 뿔은 방향이 좌우 대칭 쌍둥이로 나와서(119)
    # 한 개는 원화의 라벤더 자리를 찍는다 — 낱개 투표로는 못 고친다. 그런데 넷은 같은
    # 종류의 물건이니 재질을 공유한다. 뿔을 가려내는 건 두께가 아니라 **단면 모양**이다:
    #   원뿔은 단면이 원형(e2/e3 ~ 1.0~1.25), 앞판은 납작하다(2.1). 앞판도 얇아서 두께로는 못 뗀다
    horn = np.zeros(len(lab), bool)
    nhorn = 0
    for pid in np.unique(lab):
        m = lab == pid
        if m.sum() < 200 or not thin[m][0]:
            continue
        c = ctr[m]
        e = np.sqrt(np.linalg.eigvalsh(np.cov((c - c.mean(0)).T)))[::-1]
        if e[1] / max(e[2], 1e-9) < 1.5:               # 단면이 원형이다
            horn |= m
            nhorn += 1
    want = len(SH["horns"])
    print("  뿔 판정: 단면 원형인 얇은 부품 %d개 (원화 실측 %d개)%s"
          % (nhorn, want, "" if nhorn == want else "   <- 개수가 안 맞는다. 의심하라"))

    prov = np.where(lid >= 0, 1, 3).astype(np.int8)    # 0 직접 / 1 전파 / 2 뿔계급 / 3 못받음
    prov[direct0] = 0
    out = np.where(thin[:, None], GOLD[None, :], SHELL[None, :])
    out[lid >= 0] = COLS[lid[lid >= 0]]
    # **재질을 구분 못 하는 판은 표를 못 던진다.** 측면은 라벨이 하나뿐(라벤더)이라
    # 무엇을 물어도 라벤더라고 답한다 — 그건 정보가 아니라 잡음이다
    view_of = np.array([m.split("/")[0] for m in meta])
    informative = np.array([len(set(hue[view_of == v])) > 1 for v in view_of])
    print("  표를 던질 수 있는 판: %s (재질을 구분하는 판만)"
          % " ".join(sorted(set(view_of[informative]))) or "없음")

    if nhorn:
        v = lid[horn & (lid >= 0)]
        v = v[informative[v]]
        h, n = np.unique(hue[v], return_counts=True)
        win = h[np.argmax(n)]
        cand = v[hue[v] == win]
        best = np.bincount(cand).argmax()               # 그 반에서 제일 많이 뽑힌 판
        print("  뿔 계급 표: %s -> %s 전부 %s"
              % (" ".join("%s %.0f%%" % (h[j], n[j] / n.sum() * 100) for j in np.argsort(-n)),
                 "뿔 %d개" % nhorn, meta[best]))
        out[horn] = COLS[best]
        prov[horn] = 2
    np.save(os.path.join(OUT, "tri_lid.npy"), lid.astype(np.int32))
    np.save(os.path.join(OUT, "tri_prov.npy"), prov.astype(np.int8))
    json.dump(meta, open(os.path.join(OUT, "tri_meta.json"), "w"), ensure_ascii=False)
    print("  출처 저장: 직접 %d · 전파 %d · 뿔계급 %d · 못받음 %d"
          % ((prov == 0).sum(), (prov == 1).sum(), (prov == 2).sum(), (prov == 3).sum()))
    return out


def paint_parts(lab, direct, col, thin):
    """**투영을 위치가 아니라 투표로만 쓴다.** 셀 원화는 평면색이니 원화가 주는 건
    "이 화소가 무슨 색"이 아니라 "이 부품이 무슨 재질"이다. 부품마다 직접 읽은 면들의
    중앙색 하나로 통째로 칠한다 — 화소를 면에 붙이지 않으므로 **번짐이 원리적으로 없다.**

    두께로 정하면 안 된다(재 봤다): tri_seg 의 "얇음" 26,179면에는 금뿔뿐 아니라
    앞판 14,999면(라벤더)이 들어 있어 두께 != 금이다. 정면 L1 18.5% 로 크게 진다."""
    out = np.where(thin[:, None], GOLD[None, :], SHELL[None, :])   # 표 없는 부품의 대체
    voted = 0
    for pid in np.unique(lab):
        m = lab == pid
        src = m & direct
        if src.sum() < 8:                        # 표가 너무 적으면 두께 대체를 쓴다
            continue
        out[m] = np.median(col[src], 0)
        voted += 1
    print("v3  부품 -> 재질.  부품 %d 중 %d개를 원화가 투표로 정했다 (투영은 투표에만)"
          % (lab.max() + 1, voted))
    return out


def paint_old(ctr, nrm, rule):
    """어제 판을 **그대로** 되살린다 — 같은 자로 재야 비교가 된다 (git 580c730).
    정면 한 판, 나머지는 평면색.  rule=False 면 색 규칙 반창고를 뗀 맨 투영(v0)이다."""
    raw, _ = sample("front", ctr)
    ok = nrm[:, 1] < -0.15                       # 앞을 보는 면만
    if rule:                                     # LESSONS 74 의 손으로 찍은 색상 규칙
        r, g, b = raw[:, 0], raw[:, 1], raw[:, 2]
        ok &= ((r - b > 20) & (r - g < 60)) | (b - r > 5)
    print("%s  색 받은 면 %d/%d (%.1f%%)  — 나머지는 평면색"
          % ("v1" if rule else "v0", ok.sum(), len(ok), ok.sum() / len(ok) * 100))
    return np.where(ok[:, None], raw, np.array([89., 93., 126.])[None, :])


def paint(o, lab, thin, pairs, POLY):
    me = o.data
    nf = len(me.polygons)
    ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
    nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)

    view, col, blocked = assign(o, ctr, nrm, POLY)
    have = view >= 0
    direct = have.copy()                         # 전파 전에 원화를 직접 읽은 면
    print("판 배정  %d/%d (%.1f%%)   정면 %d · 측면 %d   경계로 거른 면 %d"
          % (have.sum(), nf, have.sum() / nf * 100,
             (view == 0).sum(), (view >= 1).sum(), blocked.sum()))

    how = os.environ.get("SPREAD", "graph")
    filled = (spread(lab, pairs, have, col) if how == "graph"
              else spread_median(lab, have, col))
    print("전파[%s]  +%d면 -> %.1f%%" % (how, filled, have.sum() / nf * 100))

    surface(me, view, direct, lab)

    rest = ~have                                 # 색을 한 번도 못 만난 부품
    if rest.any():
        col[rest] = np.where(thin[rest, None], GOLD[None, :], SHELL[None, :])
        parts = np.unique(lab[rest])
        print("두께 대체  %d면 (부품 %d개: 얇음 %d · 두꺼움 %d)"
              % (rest.sum(), len(parts), (rest & thin).sum(), (rest & ~thin).sum()))
    return col


def surface(me, view, direct, lab):
    """**표면 공간 판정.** 화면 화소로 세면 99% 가 칠해진 걸로 보이지만, 원화는 투영이라
    면이 비스듬할수록 그 면에 배당된 화소가 cos 로 줄어든다. UV 전개도 위에서는
    그 면이 원래 넓이를 되찾으므로 **화면에서 1화소로 읽은 색이 전개도에서는 넓은 판**이 된다.

    그래서 면 수도 화소도 아니고 **면적**으로, 그리고 그 면적이 원화에 얼마나
    정면으로 놓였는지(cos)로 잰다. 이게 "단면으로 전개도를 못 채운다" 의 숫자다."""
    nf = len(me.polygons)
    ar = np.empty(nf); me.polygons.foreach_get("area", ar)
    nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
    cos = np.abs(SCORE(nrm)).max(1)              # 제일 정면인 판에서의 cos
    tot = ar.sum()
    print("  표면 공간 — 면적 %.4f 중" % tot)
    print("    원화를 직접 읽은 면적   %5.1f%%   (면 수로는 %.1f%%)"
          % (ar[direct].sum() / tot * 100, direct.mean() * 100))
    print("    그 면적의 cos 가중      %5.1f%%   <- **원화가 실제로 본 표면**"
          % ((ar[direct] * cos[direct]).sum() / tot * 100))
    for lo, hi in ((0.7, 1.01), (0.35, 0.7), (0.0, 0.35)):
        m = direct & (cos >= lo) & (cos < hi)
        print("      cos %.2f~%.2f  면적 %5.1f%%  (전개도에서 %.1f 배로 펴진다)"
              % (lo, hi, ar[m].sum() / tot * 100,
                 1 / max(np.median(cos[m]) if m.any() else 1, 1e-6)))


def write_attr(me, col):
    lin = np.where(col / 255.0 <= 0.04045, col / 255.0 / 12.92,
                   ((col / 255.0 + 0.055) / 1.055) ** 2.4)
    nf = len(me.polygons)
    at = me.color_attributes.get("art") or me.color_attributes.new("art", 'FLOAT_COLOR', 'CORNER')
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    buf = np.ones((len(me.loops), 4))
    for i in range(nf):
        buf[ls[i]:ls[i] + lt[i], :3] = lin[i]    # 면 하나 = 색 하나
    at.data.foreach_set("color", buf.ravel())
    me.color_attributes.active_color = at
    me.color_attributes.default_color_name = at.name
    return at.name


def judge(o, POLY):
    """부품 지표. **정면만 보지 않는다** (123). 견갑 경계 안에서만 잰다."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'VERTEX'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Standard'
    cd = bpy.data.cameras.new("j"); cd.type = 'ORTHO'; cd.ortho_scale = U1 - U0
    cam = bpy.data.objects.new("j", cd); sc.collection.objects.link(cam); sc.camera = cam

    # 팔레트는 **두 판 합집합**이다. 판별로 만들면 측면 마스크에 금뿔이 없어서
    # 금색이 통째로 "남의 색"으로 잡힌다 — 지표가 뷰 차이를 오독으로 오인한다
    q = lambda a: (a.astype(np.int32) >> 3)
    PAL = set()
    for k in ("front", "side"):
        m = POLY[k] & (ART[k][..., 3] >= 128)
        PAL |= set(map(tuple, np.unique(q(ART[k][m][:, :3]), axis=0)))

    # **재질 일치율** — 음영에 안 흔들리는 자. 화소를 판 중앙색으로 분류해 hue 만 본다.
    # 색 L1 은 평면 알베도를 내는 판(v3·v4)에 구조적으로 불리하다 — 원화엔 음영이 구워져
    # 있으니까. 셀 셰이더는 그 음영을 렌더 때 다시 얹는다. 지금 물어야 할 건 "금이 금
    # 자리에 있나"지 "밝기가 같나"가 아니다
    _, PCOL, PMETA = labels(POLY)
    PHUE = np.array([t.split("/")[1].rstrip("0123456789") for t in PMETA])
    tohue = lambda c: PHUE[np.argmin(((c[:, None, :] - PCOL[None]) ** 2).sum(2), 1)]

    print("\n부품 지표 [%s]   팔레트 %d색 = 색공간의 %.1f%%" % (MODE, len(PAL), len(PAL) / 32768 * 100))
    for key, loc, rot in (("front", (0, -2, 0.5), (90, 0, 0)),
                          ("side", (2, 0, 0.5), (90, 0, 90))):
        cam.location = loc
        cam.rotation_euler = tuple(math.radians(a) for a in rot)
        p = os.path.join(OUT, "tripaint_%s_%s.png" % (MODE, key))
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p)
        px = np.array(im.pixels[:]).reshape(RES, RES, 4)[::-1]
        bpy.data.images.remove(im)
        got = px[..., 3] > 0.5
        ref = ART[key]
        msk = POLY[key] & (ref[..., 3] >= 128)
        both = got & msk
        l1 = np.abs(px[both][:, :3] * 255.0 - ref[both][:, :3]).mean() / 255.0
        iou = (got & msk).sum() / max((got | msk).sum(), 1)

        # **오독** — 원화의 견갑이 한 번도 안 쓴 색을 칠했나. 문턱을 눈으로 안 찍는다:
        # 팔레트는 원화가 그 경계 안에서 실제로 쓴 색 전부다 (셀 2톤·먹선 포함, 색공간의 2%).
        # **마스크 안이 아니라 렌더 실루엣 전체**에서 잰다 — 오독은 정의상 경계 밖에 떨어진다
        mine = q(np.clip(px[got][:, :3] * 255.0, 0, 255))
        foreign = np.array([tuple(c) not in PAL for c in mine])
        # 먹선(dark 16.3%)·하이라이트(white 3.1%)는 **그리는 관습이지 재질이 아니다** —
        # 텍스처가 아니라 Freestyle·능선 형태가 낼 몫이다. 실재질만 놓고 센다
        ah = tohue(ref[both][:, :3].astype(float))
        mh = tohue(px[both][:, :3] * 255.0)
        real = (ah == "lav") | (ah == "gold")
        print("  %-5s  IoU %.3f   색 L1 %5.1f%%   오독 %4.1f%%   "
              "재질 일치 %5.1f%%   **실재질(라벤더·금)만 %5.1f%%**"
              % (key, iou, l1 * 100, foreign.mean() * 100, (ah == mh).mean() * 100,
                 (ah[real] == mh[real]).mean() * 100))
    look34(cam, sc)


def look34(cam, sc):
    """3/4. **원화가 없는 각도다** — 잴 게 없으니 눈이 판정이다.
    투영으로 채운 표면의 절반은 여기서 처음 보인다 (128)."""
    r = math.radians(40)
    t = (0.184, 0.027, 0.885)
    cam.data.ortho_scale = 0.26
    cam.location = (t[0] + 1.2 * math.sin(r), t[1] - 1.2 * math.cos(r), t[2])
    cam.rotation_euler = (math.radians(90), 0, r)
    sc.render.filepath = os.path.join(OUT, "tripaint_%s_q.png" % MODE)
    bpy.ops.render.render(write_still=True)
    print("  3/4 -> out/tripaint_%s_q.png  (원화 없음. 눈으로 본다)" % MODE)


def main():
    o = tri_look.bring()
    me = o.data
    lab = np.load(os.path.join(OUT, "tri_lab.npy"))
    thin = np.load(os.path.join(OUT, "tri_thin.npy"))
    pairs = np.load(os.path.join(OUT, "tri_adj.npy"))
    assert len(lab) == len(me.polygons), \
        "tri_seg 와 면 수가 다르다 (%d vs %d) — tri_seg.py 를 다시 돌려라" % (len(lab), len(me.polygons))
    print("부품 %d개 · 엣지쌍 %d" % (lab.max() + 1, len(pairs)))

    print("경계 — 실측 화소 수에 맞춰 팽창을 고른다")
    POLY = mask2d.fitted()
    if MODE == "v4":
        nf = len(me.polygons)
        ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
        nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
        col = paint_labels(o, ctr, nrm, POLY, lab, pairs, thin)
    elif MODE == "v3":
        nf = len(me.polygons)
        ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
        nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
        v, c0, _ = assign(o, ctr, nrm, POLY)
        col = paint_parts(lab, v >= 0, c0, thin)
    elif MODE != "v2":                           # MODE=v0|v1|v3 blender -b --python tri_paint.py
        nf = len(me.polygons)
        ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
        nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
        col = paint_old(ctr, nrm, MODE == "v1")
    else:
        col = paint(o, lab, thin, pairs, POLY)
    attr = write_attr(me, col)
    np.save(os.path.join(OUT, "tri_col.npy"), col.astype(np.uint8))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "tri_paint.blend"))
    judge(o, POLY)
    print("\nattr=%s  ->  out/tri_paint.blend · out/tri_col.npy" % attr)


if __name__ == "__main__":
    main()
