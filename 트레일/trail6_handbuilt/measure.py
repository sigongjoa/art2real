# -*- coding: utf-8 -*-
"""원화에서 +x 어깨 견갑의 실측을 읽는다.

    python measure.py

읽는 것은 trail4 가 이미 만들어 둔 **메시 공간** 자산이다 (rgb_*.npy / cls_*.npy).
좌표창: 1024^2, u in [-0.6,0.6], z in [-0.1,1.1].
front 화면 x = 월드 +x,  side 화면 x = 월드 +y (앞이 화면 왼쪽, 즉 -y).

출력: parts/sh_pauldron.json  +  out/m_*.png (색칠 증명, LESSONS 23)
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1

# 부위를 가두는 실측 박스. 좌표 조건만으로는 부위가 특정되지 않는다 (LESSONS 17)
BOX = dict(u0=0.132, u1=0.320, z0=0.680, z1=1.000)
# 윤곽 폴리곤을 얼마나 굵게 펼지. 둘레 대비 비율 (approxPolyDP).
# 잘게 두면 정점 28개짜리 잔면 덩어리가 되고, 굵게 하면 큰 갑판이 된다.
# 0.004(정점 28) -> 0.018(정점 12) 로 굵혀도 실루엣 IoU 는 0.840 -> 0.838 뿐이다.
# 대신 면이 150 -> 86 으로 줄고 잔면 대신 갑판으로 읽힌다. 굵게 가는 게 공짜다.
POLY_EPS = float(os.environ.get("POLY_EPS", 0.018))

CLS_ARMOR, CLS_DARK, CLS_GOLD = 1, 2, 3


def col(u):  return (u - U0) / (U1 - U0) * (RES - 1)
def row(z):  return (Z1 - z) / (Z1 - Z0) * (RES - 1)
def u_of(c): return U0 + c * (U1 - U0) / (RES - 1)
def z_of(r): return Z1 - r * (Z1 - Z0) / (RES - 1)


def load(view):
    """실루엣은 rgb_*.npy 의 **알파**를 쓴다.

    true_*.npy 는 정렬 변환 전 좌표계라 rgb/cls 와 안 맞는다 (cls>0 의 75%만 담고 IoU 0.612).
    그걸로 가리면 금뿔 끝이 잘린다. rgb 알파는 cls>0 를 100% 담는다. (LESSONS 47)
    """
    raw = np.load(os.path.join(T4, f"rgb_{view}.npy"))
    return raw[..., :3].astype(np.int16), np.load(os.path.join(T4, f"cls_{view}.npy")), raw[..., 3] > 0


def boxmask(u0, u1, z0, z1):
    m = np.zeros((RES, RES), bool)
    m[int(row(z1)):int(row(z0)) + 1, int(col(u0)):int(col(u1)) + 1] = True
    return m


def purple(rgb):
    """라벤더 갑주 = 파랑 우세 + 중간 밝기. 흰 투구(230+)와 갈린다."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    v = rgb.max(2)
    return (b - r > 8) & (v > 60) & (v < 225)


def close(mask, k=5):
    """먹선이 갈라놓은 이웃 면을 붙인다. 안 하면 largest() 가 돌기를 버린다."""
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, ker).astype(bool)


def with_ink(shell, rgb, sil, d=4):
    """**먹선까지 포함해야 원화의 형태다.** 라벤더만 잡으면 선 두께만큼 작아진다.

    경계 밖 3px 띠의 38~49% 가 먹선이고, 포함하면 면적이 정면 x1.122 측면 x1.088 커진다.
    (내 모델이 대상보다 x1.11 / x1.07 컸던 것이 정확히 이 몫이었다 — 모델이 뚱뚱한 게
    아니라 대상이 얇았다.)
    띠 밖의 검정(팔 등)은 넣지 않는다. 안 그러면 팔이 통째로 딸려 온다.
    """
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1))
    band = cv2.dilate(shell.astype(np.uint8), ker).astype(bool) & ~shell
    ink = sil & (rgb.max(2) < 95)
    return largest(shell | (band & ink))


def largest(mask):
    n, lab = cv2.connectedComponents(mask.astype(np.uint8))
    if n <= 1:
        return mask
    sizes = [(lab == i).sum() for i in range(1, n)]
    return lab == (1 + int(np.argmax(sizes)))


def zhang_suen(mask):
    """1px 세선화. `cv2.ximgproc` 이 이 빌드에 없어서 직접 쓴다.

    모폴로지 세선화(open 반복)는 선이 끊긴다. Zhang-Suen 은 연결성을 보존한다.
    """
    I = mask.astype(np.uint8).copy()
    while True:
        removed = False
        for step in (0, 1):
            P = np.pad(I, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            A = sum(((seq[k] == 0) & (seq[k + 1] == 1)).astype(np.uint8) for k in range(8))
            base = (I == 1) & (B >= 2) & (B <= 6) & (A == 1)
            m = (base & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)) if step == 0 else                 (base & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0))
            if m.any():
                I[m] = 0
                removed = True
        if not removed:
            break
    return I > 0


def ink_region(shell, ink, w=6):
    """**그은 선 자체**를 경계로 삼는다.

    색으로 마스크를 뜨면 선 두께만큼 작고(79번), 선 바깥을 쓰면 두께의 흔들림이 섞인다.
    캡 경계 +-w px 안의 먹선만 남겨 획을 뽑고, 1px 로 세선화한 뒤 그 곡선의 내부를 채운다.
    그러면 경계가 **선의 중심**이 된다.
    """
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * w + 1, 2 * w + 1))
    band = (cv2.dilate(shell.astype(np.uint8), ker).astype(bool)
            & ~cv2.erode(shell.astype(np.uint8), ker).astype(bool))
    sk = zhang_suen(largest(ink & band))
    ff = (~sk).astype(np.uint8)
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 0)
    return (ff > 0) | sk


def outline(mask, step=1.5, sigma=1.0, win=6, thr=25.0, tol=1.5):
    """마스크의 바깥 윤곽을 **작가가 그은 모서리** 기준으로 폴리곤화한다.

    `approxPolyDP` 를 래스터 컨투어에 바로 걸면 화소 계단의 모서리를 찍는다
    (29정점 중 대부분이 계단이었다). 그래서 세 단계로 나눈다.

        1) 호 길이로 재표본  -> 화소 격자에서 벗어난다
        2) sigma 1.0 가우스  -> 계단만 지운다 (원본에서 평균 0.17px)
        3) 곡률 국소최대     -> **모서리**를 앵커로 잡고,
           앵커 사이는 편차 tol 넘는 곳만 채운다

    실측: 모서리 13개 + 채움 16개 = 29정점에서 마스크 대비 IoU 0.968.
    """
    c, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(c, key=cv2.contourArea)
    p = c.reshape(-1, 2).astype(float)
    p = np.vstack([p, p[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.linspace(0, d[-1], max(int(d[-1] / step), 16), endpoint=False)
    q = np.stack([np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])], 1)
    n = len(q)
    r = max(int(4 * sigma), 1)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    sp = np.empty_like(q)
    for j in range(2):
        sp[:, j] = np.convolve(np.r_[q[-r:, j], q[:, j], q[:r, j]], k, "same")[r:r + n]
    a = sp - np.roll(sp, win, 0)
    b = np.roll(sp, -win, 0) - sp
    ang = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))))
    anch = []
    for i in range(n):
        w = [(i + j) % n for j in range(-win, win + 1)]
        if ang[i] >= thr and ang[i] >= max(ang[w]) - 1e-9:
            if not anch or min((i - anch[-1]) % n, (anch[-1] - i) % n) > win:
                anch.append(i)
    if len(anch) < 3:
        anch = list(range(0, n, max(n // 8, 1)))
    extra = []

    def fill(i0, i1):
        seg = [(i0 + j) % n for j in range((i1 - i0) % n + 1)]
        A, B = sp[seg[0]], sp[seg[-1]]
        v = B - A
        Lv = np.hypot(*v)
        if Lv < 1e-9 or len(seg) < 3:
            return
        rel = sp[seg] - A
        dist = np.abs(v[0] * rel[:, 1] - v[1] * rel[:, 0]) / Lv
        m = int(np.argmax(dist))
        if dist[m] > tol:
            fill(seg[0], seg[m])
            extra.append(seg[m])
            fill(seg[m], seg[-1])

    for i in range(len(anch)):
        fill(anch[i], anch[(i + 1) % len(anch)])
    idx = sorted(set(anch) | set(extra))
    return sp[idx], len(anch)


def touching(mask, seed):
    """seed 에 닿는 연결성분만 **통째로** 남긴다.

    화소 단위로 자르면 껍데기에서 멀어지는 뿔 끝이 잘린다 (처음에 금뿔 z 가 0.970 -> 0.937 로 짧아졌다).
    """
    n, lab = cv2.connectedComponents(mask.astype(np.uint8))
    keep = set(np.unique(lab[mask & seed])) - {0}
    return np.isin(lab, list(keep)) if keep else np.zeros_like(mask)


def horns(gold, cap):
    """금뿔을 하나씩 잰다 — 뿌리·끝·반지름을 PCA 주축으로.

    뿔은 뿌리가 캡에 붙어 있다. 캡 중심에서 **먼 쪽 끝**이 뿔끝이다.
    """
    n, lab = cv2.connectedComponents(gold.astype(np.uint8))
    cr, cc = np.nonzero(cap)
    cen = np.array([cc.mean(), cr.mean()])
    res = []
    for i in range(1, n):
        r, c = np.nonzero(lab == i)
        if len(r) < 120:   # 하이라이트가 떨어져 나온 조각(72px, 반지름 0.0016)을 버린다
            continue
        pts = np.stack([c, r], 1).astype(float)
        mu = pts.mean(0)
        _, sv, vt = np.linalg.svd(pts - mu, full_matrices=False)
        ax = vt[0]
        t = (pts - mu) @ ax
        w = np.abs((pts - mu) @ vt[1])
        e0, e1 = mu + ax * t.min(), mu + ax * t.max()
        tip, root = (e0, e1) if np.linalg.norm(e0 - cen) > np.linalg.norm(e1 - cen) else (e1, e0)
        res.append({
            "px": int(len(r)),
            "root_xz": [float(u_of(root[0])), float(z_of(root[1]))],
            "tip_xz": [float(u_of(tip[0])), float(z_of(tip[1]))],
            "length": float(np.hypot(*(tip - root)) * (U1 - U0) / (RES - 1)),
            "radius": float(w.max() * (U1 - U0) / (RES - 1)),
        })
    res.sort(key=lambda h: -h["px"])
    return res


def extent(mask, axis_of):
    r, c = np.nonzero(mask)
    return float(axis_of(c.min())), float(axis_of(c.max()))


def main():
    out = {"box": BOX}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "parts"), exist_ok=True)

    # ---- 정면: 견갑 껍데기 + 금뿔 ----
    rgb, cls, sil = load("front")
    box = boxmask(**BOX)
    ink = sil & (rgb.max(2) < 95)
    shell = ink_region(largest(close(purple(rgb) & sil & box)), ink)
    dark = (cls == CLS_DARK) & sil & box

    # 견갑 본체는 껍데기의 볼록껍질 안쪽 전부 (금뿔·소켓 구멍 포함)
    cnt, _ = cv2.findContours(shell.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnt, key=cv2.contourArea)
    filled = np.zeros((RES, RES), np.uint8)
    cv2.drawContours(filled, [cnt], -1, 1, -1)
    filled = filled.astype(bool)

    ux0, ux1 = extent(filled, u_of)
    zr, zc = np.nonzero(filled)
    zz0, zz1 = float(z_of(zr.max())), float(z_of(zr.min()))
    out["front"] = {
        "u": [ux0, ux1], "z": [zz0, zz1],
        "width": ux1 - ux0, "height": zz1 - zz0,
        "px": int(filled.sum()),
    }

    # 윤곽 폴리곤 (월드 좌표). 모서리를 앵커로 잡고 사이를 편차로 채운다
    poly, nc = outline(filled)
    out["front"]["poly_xz"] = [[float(u_of(x)), float(z_of(y))] for x, y in poly]
    out["front"]["poly_n"] = len(poly)
    out["front"]["corners"] = nc

    # 금뿔: 껍데기 **바로 옆**의 금 화소만. 박스 전체로 잡으면 아래 건틀릿 금이 딸려 온다
    near = cv2.dilate(filled.astype(np.uint8),
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))).astype(bool)
    gold = touching((cls == CLS_GOLD) & sil & box, near)
    gx0, gx1 = extent(gold, u_of)
    gr, _ = np.nonzero(gold)
    out["front"]["gold"] = {"u": [gx0, gx1], "z": [float(z_of(gr.max())), float(z_of(gr.min()))],
                            "px": int(gold.sum())}
    out["horns"] = horns(gold, filled)
    # 부품 대표색. 3판 투영이 색을 못 준 면의 **대체색**으로 쓴다.
    # 클래스 팔레트(armor = 흰색)를 쓰면 라벤더 견갑이 하얗게 구워진다.
    body = filled & ~gold & sil
    out["color"] = {
        "shell": [int(v) for v in np.median(rgb[body], axis=0)],
        "gold": [int(v) for v in np.median(rgb[gold], axis=0)],
    }

    # ---- 측면: 깊이 ----
    srgb, scls, ssil = load("side")
    # 깊이는 **정면에서 잰 z 띠 안에서만** 잰다. 넓게 잡으면 아래 어깨 띠가 딸려 온다
    sbox = boxmask(-0.35, 0.35, zz0, zz1)
    # 측면은 x 가 접혀 있어 박스로 못 가둔다. 견갑은 가슴 갑주와 **좁은 목**으로만 붙어 있으니
    # 열림으로 목을 끊고, 남은 덩어리를 원래 마스크 안에서 되키운다.
    raw_s = close(purple(srgb) & ssil & sbox)
    # touching(raw_s, core) 은 소용없다 — raw_s 가 애초에 한 덩어리라 통째로 돌아온다.
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    core = largest(cv2.morphologyEx(raw_s.astype(np.uint8), cv2.MORPH_OPEN, ker).astype(bool))
    # 열림이 경계를 12px 깎았다. **한 번만** 되키워 원래 마스크 안에서 복원한다
    # (두 번 이상 키우면 끊어 놓은 목을 도로 건너간다)
    sink = ssil & (srgb.max(2) < 95)
    # 측면은 `ink_region`(세선 추적)을 쓰면 안 된다 — 견갑과 가슴 갑주가 먹선 하나를
    # 공유해서 획을 따라가면 이웃으로 넘어가고, 폴리곤이 얇은 조각으로 무너진다
    # (깊이 0.137 -> 0.009). 그걸 hold-out 자로 쓰는 바람에 상관값을 전부 헛짚었다.
    # 측면은 `with_ink`(색 + 먹선 띠) 로 되돌린다.
    sshell = with_ink(cv2.dilate(core.astype(np.uint8), ker).astype(bool) & raw_s, srgb, ssil)
    sy0, sy1 = extent(sshell, u_of)
    scnt, _ = cv2.findContours(sshell.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    scnt = max(scnt, key=cv2.contourArea)
    snear = cv2.dilate(sshell.astype(np.uint8),
                       cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))).astype(bool)
    sgold = touching((scls == CLS_GOLD) & ssil & boxmask(-0.35, 0.35, zz0 - 0.06, zz1 + 0.06), snear)
    spoly, snc = outline(sshell)
    out["side"] = {"y": [sy0, sy1], "depth": sy1 - sy0, "px": int(sshell.sum()),
                   "poly_yz": [[float(u_of(x)), float(z_of(y))] for x, y in spoly],
                   "corners": snc}
    if sgold.any():
        gy0, gy1 = extent(sgold, u_of)
        gr, _ = np.nonzero(sgold)
        out["side"]["gold"] = {"y": [gy0, gy1], "z": [float(z_of(gr.max())), float(z_of(gr.min()))]}
    # 정면 뿔 <-> 측면 뿔 짝짓기.
    # z 근접만 쓰면 틀린다 — 정면에서 가장 짧아 보이는 뿔(len 0.0333)은 작아서가 아니라
    # **뒤로 뻗어 단축돼** 보이는 것이고, z 는 다른 뿔과 겹친다. 방향으로 배정한다.
    sh = horns(sgold, sshell)
    sh.sort(key=lambda x: x["tip_xz"][0] - x["root_xz"][0])   # 앞(-y) -> 뒤(+y)
    fw, up, bk = (sh + [None] * 3)[:3]
    fh = sorted(out["horns"], key=lambda h: -h["px"])
    for h, sm, why in ((fh[0], fw, "소켓 뿔 = 앞으로"),
                       (fh[1], up, "정수리 뿔 = 위로"),
                       (min(fh, key=lambda h: h["length"]), bk, "측면 뒤뿔이 굵다 -> 남은 둘 중 굵은 쪽. 2뷰로는 확정 불가")):
        if sm:
            h["root_y"], h["tip_y"], h["why_y"] = sm["root_xz"][0], sm["tip_xz"][0], why
    ymid = (sy0 + sy1) / 2
    for h in out["horns"]:
        h.setdefault("root_y", ymid)      # 측면에서 안 보이는 뿔은 캡 중앙 y. build 의 노브
        h.setdefault("tip_y", ymid)
        h.setdefault("why_y", "측면에 안 보임 -> 캡 중앙 (추정, 노브)")
    out["side"]["horns"] = sh

    # ---- 증명 그림 ----
    for view, masks in (("front", {"shell": filled, "gold": gold, "dark": dark}),
                        ("side", {"shell": sshell, "gold": sgold, "dark": np.zeros((RES, RES), bool)})):
        base_rgb, _, base_sil = load(view)
        img = cv2.cvtColor(base_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR).copy()
        img[~base_sil] = 255
        img[masks["shell"]] = (img[masks["shell"]] * 0.4 + np.array([0, 0, 255]) * 0.6).astype(np.uint8)
        img[masks["gold"]] = (0, 255, 255)
        img[masks["dark"]] = (255, 0, 0)
        r, c = np.nonzero(masks["shell"])
        pad = 40
        crop = img[max(r.min() - pad, 0):r.max() + pad, max(c.min() - pad, 0):c.max() + pad]
        cv2.imwrite(os.path.join(HERE, "out", f"m_{view}.png"),
                    cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST))

    with open(os.path.join(HERE, "parts", "sh_pauldron.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "box"}, ensure_ascii=False, indent=1)[:1400])


if __name__ == "__main__":
    main()
