# -*- coding: utf-8 -*-
"""**키트 규칙** — 사람이 나눈 실제 키트에서 분할 규칙을 숫자로 뽑아 우리 후보와 같은 자로 잰다 (2026-09-25).

    python 키트규칙.py          -> 표 출력 · out/분할후보/키트규칙.json · 키트규칙.png · G1/lab.npy + 채점

같은 자 = **격자**. 키트 부품 메시를 몸 키 152 칸(우리 몸 z 19..170 과 같은 칸 수)으로 복셀화해 lab 을 만들고,
우리 lab.npy 와 **같은 함수 재기()** 로 잰다. 축은 우리 것 [x 좌우 · y 깊이(작은 y 가 앞) · z 높이].
  부품    높이 구간(발 0 ~ 머리 꼭대기 1) · 좌우(가운데/왼/오) · 부피 몫 · 블록(이름 우선, 없으면 높이·위치 규칙)
  이음면  맞닿은 짝의 경계 면(6 이웃) 중심점에 평면 → RMS/키 · 법선 분류(수평 · 앞뒤 · 좌우 · 기운 것, |cos|>0.8)
          · 겉에서 보이는 둘레(경계 면 중 바깥 공기에 닿은 것의 수 / 키 칸)
조립 좌표가 살아 있는 키트는 **529278 (건담 · 11 부품)** · **529483 (Ex-S · _Sup 뺀 15 부품)** 둘뿐이었다.
813280 · 680191 · 588149 는 부품이 원점 둘레 · 출력 판 배치라(bounds 확인) 좌표 비교에서 뺀다 — 파일 이름으로 블록 수만 센다."""
import json, os, re, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage
sys.path[:0] = [r"G:\art2real\원화3d\실험_20260925"]
import 채점 as C

KIT = r"G:\art2real\원화3d\out\키트정답"
키칸 = 152                                    # 우리 몸 키(칸)
COS = 0.8

# ── 키트 읽기 ─────────────────────────────────────────────
# 축 바꾸기: 메시 좌표 → [x 좌우, y 깊이(앞 = 작은 y), z 위]
키트들 = {
    "529278": dict(이름="건담 (Anycubic)", 뺄=("Gundam",), 축=lambda v: np.c_[v[:, 0], -v[:, 2], v[:, 1]]),   # y 가 위 · +z 가 앞
    "529483": dict(이름="Ex-S (BobertmaX)", 뺄=("_Sup",), 축=lambda v: np.c_[v[:, 0], v[:, 1], v[:, 2]]),      # z 가 위 · -y 가 앞
}
블록낱말 = [("머리", ("head",)), ("무기", ("knife", "rifle")), ("백팩", ("backpack", "booster", "fuelpod", "wing")),
          ("팔", ("arm", "hand")), ("허리", ("waist",)), ("몸통", ("body", "torso")),
          ("허벅지", ("thigh",)), ("다리아래", ("calf",)), ("다리", ("leg",))]


def 이름블록(f):
    s = f.lower()
    for b, ks in 블록낱말:
        if any(k in s for k in ks): return b
    return None


def 키트읽기(kit):
    k = 키트들[kit]; d = os.path.join(KIT, kit); 부 = []
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".stl") or any(x in f for x in k["뺄"]): continue
        m = trimesh.load(os.path.join(d, f), force="mesh")
        m = trimesh.Trimesh(k["축"](np.asarray(m.vertices)), m.faces, process=False)
        부.append((re.sub(r"^p\d+_", "", f[:-4]), m))
    return 부


씨앗 = int(os.environ.get("KIT_SEED", "0"))


def 복셀화(부, 머리=None):
    """부품마다 표면을 촘촘히 뿌려 칸에 찍고 속을 채운다(binary_fill_holes). 겹친 칸은 먼저 온 부품.
    키 = 발바닥 ~ 머리 부품 꼭대기 → 152 칸."""
    lo = np.min([m.bounds[0] for _, m in 부], 0); hi = np.max([m.bounds[1] for _, m in 부], 0)
    머 = [m for n, m in 부 if 이름블록(n) == "머리"][0]
    피치 = (머.bounds[1][2] - lo[2]) / 키칸
    o = lo - 3 * 피치; shp = np.ceil((hi - o) / 피치).astype(int) + 4
    lab = np.zeros(shp, np.int16)
    for i, (n, m) in enumerate(부, 1):
        k = int(m.area / (피치 * 0.35) ** 2) + 1000
        P = np.asarray(m.sample(min(k, 4_000_000), seed=씨앗 * 100 + i))
        ijk = np.floor((P - o) / 피치).astype(int)
        s = np.zeros(shp, bool); s[tuple(ijk.T)] = True
        s = ndimage.binary_fill_holes(ndimage.binary_closing(s, iterations=1))   # 안 닫힌 메시(건담)의 틈을 1 칸 닫고 채운다
        lab[s & (lab == 0)] = i
    return lab, 피치, o


# ── 같은 자 ───────────────────────────────────────────────
def 분류(n):
    a = np.abs(n)
    return "수평" if a[2] > COS else "앞뒤" if a[1] > COS else "좌우" if a[0] > COS else "기운"


def 재기(lab, 축x, 이름=None, 블록=None, 발=None, 머리=None):
    """lab (x, y, z) · 축x = 좌우 거울 면 x 색인 · 이름/블록 = 부품 번호 → 문자열 (없으면 규칙).
    돌려주는 것: 부품 표 · 이음면 표 · 요약."""
    O = lab > 0; n = int(lab.max())
    zs = np.nonzero(O.any((0, 1)))[0]
    z0 = zs[0] if 발 is None else 발
    zt = 머리 if 머리 is not None else zs[-1]
    H = float(zt - z0)
    바깥 = ndimage.label(~O)[0]; 바깥 = 바깥 == 바깥[0, 0, 0]
    공기닿음 = ndimage.binary_dilation(바깥) & O                    # 겉 칸
    부품 = []
    전 = O.sum()
    for k in range(1, n + 1):
        P = np.argwhere(lab == k)
        if not len(P): continue
        c = P.mean(0); h = (c[2] - z0) / H; d = (c[0] - 축x) / H
        쪽 = "가운데" if abs(d) < 0.04 else ("오" if d < 0 else "왼")     # 앞에서 볼 때 몸의 오른쪽 = 작은 x
        부품.append(dict(k=k, 이름=(이름 or {}).get(k, ""), 블록=(블록 or {}).get(k) or 규칙블록(h, abs(d)),
                       높이=[round((P[:, 2].min() - z0) / H, 3), round((P[:, 2].max() - z0) / H, 3)],
                       중심높이=round(h, 3), 좌우=쪽, 몫=round(len(P) / 전, 4)))
    # 이음면
    면 = {}
    for a in range(3):
        a0 = np.take(lab, range(lab.shape[a] - 1), axis=a); a1 = np.take(lab, range(1, lab.shape[a]), axis=a)
        dd = (a0 != a1) & (a0 > 0) & (a1 > 0)
        g0 = np.take(공기닿음, range(lab.shape[a] - 1), axis=a); g1 = np.take(공기닿음, range(1, lab.shape[a]), axis=a)
        idx = np.argwhere(dd).astype(float); 보 = (g0 | g1)[dd]; idx[:, a] += 0.5
        for P, p, q, v in zip(idx, a0[dd], a1[dd], 보):
            e = 면.setdefault((int(min(p, q)), int(max(p, q))), [[], 0]); e[0].append(P); e[1] += int(v)
    이음 = []; 블 = {b["k"]: b["블록"] for b in 부품}
    for (p, q), (P, 보) in sorted(면.items()):
        P = np.array(P)
        if len(P) < 8: continue                                     # 모서리 스침
        c = P.mean(0); _, s, vt = np.linalg.svd(P - c, full_matrices=False); nn = vt[2]
        이음.append(dict(짝=[p, q], 블록=[블[p], 블[q]], 종류=분류(nn), 법선=np.round(nn, 3).tolist(),
                       rms키=round(float(s[2] / np.sqrt(len(P)) / H), 4), 넓이=len(P),
                       높이=round((c[2] - z0) / H, 3), 보임둘레키=round(보 / H, 3)))
    # 거울 짝: 부품을 축으로 뒤집어 IoU 최대 이웃
    j = np.clip(np.round(2 * 축x - np.arange(lab.shape[0])).astype(int), 0, lab.shape[0] - 1)
    거 = lab[j]; 짝몫 = 0; 대칭자기 = 0
    for b in 부품:
        M = lab == b["k"]; 후 = 거[M]; 후 = 후[후 > 0]
        if not len(후): continue
        q = np.bincount(후).argmax(); Mq = lab == q; Mm = 거 == b["k"]
        iou = (Mm & Mq).sum() / (Mm | Mq).sum()
        b["거울"] = int(q) if iou > 0.5 else None; b["거울IoU"] = round(float(iou), 2)
        짝몫 += iou > 0.5; 대칭자기 += (iou > 0.5) and q == b["k"]
    return dict(부품=부품, 이음=이음, 키칸=H, 요약=요약(부품, 이음, 짝몫, 대칭자기))


def 규칙블록(h, d):
    """이름 없는 부품: 중심 높이 h(0 발 ~ 1 머리) · 가운데서 떨어진 거리 d (키 대비). 사람 비례 기본값."""
    if d > 0.13 and h > 0.42:
        return "팔"
    for 문, b in ((0.87, "머리"), (0.62, "몸통"), (0.52, "허리"), (0.33, "허벅지"), (0.0, "다리아래")):
        if h >= 문: return b


def 요약(부품, 이음, 짝몫, 대칭자기):
    n = len(부품); 넓 = sum(e["넓이"] for e in 이음) or 1
    종 = {t: round(sum(e["넓이"] for e in 이음 if e["종류"] == t) / 넓, 2) for t in ("수평", "앞뒤", "좌우", "기운")}
    보 = sum(e["보임둘레키"] for e in 이음)
    블수 = {}
    for b in 부품: 블수[b["블록"]] = 블수.get(b["블록"], 0) + 1
    r = np.array([e["rms키"] for e in 이음]); w = np.array([e["넓이"] for e in 이음])
    같은블록앞뒤 = sorted({e["블록"][0] for e in 이음 if e["종류"] == "앞뒤" and e["블록"][0] == e["블록"][1]})
    컷 = sorted({(round(e["높이"], 2), "|".join(sorted(e["블록"])), e["종류"]) for e in 이음
                if not {"팔", "무기", "백팩"} & set(e["블록"]) and e["종류"] != "앞뒤" and e["넓이"] >= 40})
    return {"부품": n, "블록별": 블수, "이음 짝": len(이음), "이음 종류(넓이 몫)": 종,
            "평면 RMS/키 (넓이가중 중앙 · 90%)": [round(float(np.median(np.repeat(r, np.maximum(1, w // 10)))), 4), round(float(np.quantile(r, .9)), 4)] if len(r) else None,
            "거울 짝 몫": round(짝몫 / n, 2), "자기 대칭 부품": int(대칭자기),
            "최소 몫": min(b["몫"] for b in 부품), "최대 몫": max(b["몫"] for b in 부품),
            "앞뒤 반쪽 블록": 같은블록앞뒤, "몸 컷 (높이·블록·종류)": 컷, "보이는 이음 둘레 합 (키 배)": round(보, 2)}


# ── 우리 후보 ─────────────────────────────────────────────
def 우리(이름표):
    lab = np.load(os.path.join(C.D, 이름표, "lab.npy")).astype(np.int16); lab = np.where(C.O, lab, 0)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(C.O.shape).astype(np.int16)
    zs = np.nonzero(C.O.any((0, 1)))[0]
    가 = np.nonzero(C.O[int(C.축i) - 10:int(C.축i) + 11].any((0, 1)))[0]    # 머리 꼭대기 = 가운데 기둥 꼭대기
    return 재기(lab, C.축i, 발=zs[0], 머리=가[-1]), lab


# ── 그림 ──────────────────────────────────────────────────
종색 = {"수평": (0.9, 0.1, 0.1), "앞뒤": (0.1, 0.3, 0.95), "좌우": (0.1, 0.75, 0.2), "기운": (0.95, 0.8, 0.0)}


def 판(lab, 결과, 보기):
    """앞(y 작은 쪽에서) · 옆(x 작은 쪽에서) 보기 · 부품 색 연하게 + 겉 이음 칸을 종류 색으로."""
    ax = 1 if 보기 == "앞" else 0
    O = lab > 0; has = O.any(ax); 깊 = np.argmax(O, ax)
    img = np.take_along_axis(lab, np.expand_dims(깊, ax), ax).squeeze(ax); img = np.where(has, img, 0)
    rng = np.random.default_rng(3); 색 = rng.uniform(.55, .95, (lab.max() + 1, 3)); 색[0] = 1
    rgb = 색[img]
    종 = {tuple(e["짝"]): e["종류"] for e in 결과["이음"]}
    # 이웃 칸(투영 판 2D)의 라벨이 다르면 이음 — 그 짝의 종류 색 (1 칸 굵혀 칠한다)
    이름들 = list(종색) + ["?"]; 판종 = np.full(img.shape, -1)
    for ax2 in (0, 1):
        b = np.roll(img, -1, axis=ax2); d = (img != b) & (img > 0) & (b > 0)
        for (i, jj) in np.argwhere(d):
            k = (int(min(img[i, jj], b[i, jj])), int(max(img[i, jj], b[i, jj])))
            판종[i, jj] = 이름들.index(종.get(k, "?"))
    for t, 이 in enumerate(이름들):
        M = ndimage.binary_dilation(판종 == t) & has
        rgb[M] = 종색.get(이, (0.25, 0.25, 0.25))
    rgb = np.transpose(rgb, (1, 0, 2))[::-1]
    if 보기 == "옆": rgb = rgb[:, ::-1]                              # 옆: 왼쪽이 앞
    return rgb


def 그림(쌍, 경로):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    fig, axs = plt.subplots(1, 2 * len(쌍), figsize=(3.4 * 2 * len(쌍), 5.6))
    i = 0
    for 제목, lab, 결과 in 쌍:
        zs = np.nonzero((lab > 0).any((0, 1)))[0]
        for 보기 in ("앞", "옆"):
            im = 판(lab, 결과, 보기); a = axs[i]; i += 1
            x0 = (200 - im.shape[1]) / 2
            a.imshow(im, extent=(x0, x0 + im.shape[1], 0, im.shape[0])); a.set_xlim(25, 175); a.set_ylim(0, 215); a.set_title("%s · %s" % (제목, 보기)); a.axis("off")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c, label=t) for t, c in 종색.items()], loc="lower center", ncol=4, fontsize=12)
    fig.suptitle("같은 배율(키 152 칸) — 겉 이음 색: 수평 빨강 · 앞뒤 파랑 · 좌우 초록 · 기운 노랑", fontsize=14)
    fig.savefig(경로, dpi=90, bbox_inches="tight"); plt.close(fig)


# ── 이름으로만 세는 키트 (좌표 없음) ─────────────────────────
def 이름세기():
    """813280 Dummy 13 Gundam · 680191 Sisters 13 — 파일 이름의 2x · 1sthalf/2ndhalf · frame/armor 로 블록 짜임을 센다."""
    out = {}
    for kit in ("813280", "680191"):
        fs = [re.sub(r"^p\d+_", "", f).lower() for f in sorted(os.listdir(os.path.join(KIT, kit))) if not f.endswith(".json")]
        out[kit] = {"파일": len(fs), "반쪽(1st/2nd half)": [f for f in fs if "half" in f],
                    "프레임": sum("frame" in f for f in fs), "장갑": sum("armor" in f for f in fs), "2x(좌우 짝)": sum(f.startswith("2x") or "x2" in f for f in fs)}
    return out


def 표(이름, s):
    print("  %-18s 부품 %2d · 이음 짝 %2d · 종류 %s · RMS/키 %s · 거울 짝 %.2f · 최소 %.3f 최대 %.3f · 보이는 둘레 %.1f키" % (
        이름, s["부품"], s["이음 짝"], s["이음 종류(넓이 몫)"], s["평면 RMS/키 (넓이가중 중앙 · 90%)"], s["거울 짝 몫"],
        s["최소 몫"], s["최대 몫"], s["보이는 이음 둘레 합 (키 배)"]))
    print("      블록별 %s" % s["블록별"]); print("      앞뒤 반쪽 블록 %s\n      몸 컷 %s" % (s["앞뒤 반쪽 블록"], s["몸 컷 (높이·블록·종류)"]))


def main():
    t0 = time.time(); 결과 = {}; 그림쌍 = []
    for kit in 키트들:
        부 = 키트읽기(kit)
        lab, 피치, o = 복셀화(부)
        블 = {i: 이름블록(n) for i, (n, _) in enumerate(부, 1)}
        # 거울 면 = 몸통 부품 x 중심 (건담은 0 · Ex-S 는 자세라 몸통 기준)
        몸 = [i for i, b in 블.items() if b == "몸통"][0]
        축x = float(np.argwhere(lab == 몸)[:, 0].mean())
        zs = np.nonzero((lab > 0).any((0, 1)))[0]
        머 = [i for i, b in 블.items() if b == "머리"][0]
        r = 재기(lab, 축x, 이름={i: n for i, (n, _) in enumerate(부, 1)}, 블록=블, 발=zs[0],
               머리=np.nonzero((lab == 머).any((0, 1)))[0][-1])
        r["피치mm"] = round(피치, 3); 결과[kit] = r
        print("%s %s 격자 %s 피치 %.3fmm (%.0fs)" % (kit, 키트들[kit]["이름"], lab.shape, 피치, time.time() - t0), flush=True)
        for b in r["부품"]: print("    %-28s %-5s 높이 %s 몫 %.3f %s 거울 %s" % (b["이름"], b["블록"], b["높이"], b["몫"], b["좌우"], b.get("거울")))
        for e in r["이음"]: print("    이음 %-22s %-3s rms/키 %.4f 넓이 %4d 높이 %.2f 보임 %.2f" % ("|".join(e["블록"]), e["종류"], e["rms키"], e["넓이"], e["높이"], e["보임둘레키"]))
        그림쌍.append((키트들[kit]["이름"], lab, r))
    for 이름표 in ("A4", "E8") + (("G1",) if os.path.exists(os.path.join(C.D, "G1", "lab.npy")) else ()):
        r, lab = 우리(이름표); 결과[이름표] = r
        if 이름표 in ("E8", "G1"): 그림쌍.append(("우리 " + 이름표, lab, r))
    결과["이름으로"] = 이름세기()
    print("\n== 규칙표 ==")
    for k, r in 결과.items():
        if k != "이름으로": 표(k, r["요약"])
    print("  이름으로:", json.dumps(결과["이름으로"], ensure_ascii=False))
    그림([그림쌍[0], 그림쌍[1]] + 그림쌍[2:], os.path.join(C.D, "키트규칙.png"))
    json.dump({k: (v if k == "이름으로" else {"요약": v["요약"], "부품": v["부품"], "이음": v["이음"]}) for k, v in 결과.items()},
              open(os.path.join(C.D, "키트규칙.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    print("걸린 시간 %.0fs" % (time.time() - t0))


def 짓기G1():
    """A4 뼈대(스냅 + 기울 스냅 컷)에 키트 규칙을 컷 값과 가를 목록만 바꿔 넣는다.
    ① 가슴 + 복부 한 몸통 (가슴 컷 = 복부 컷 → 가슴 블록이 다 먹는다) — 키트 몸통 1 조각 · 몸통|허리 0.66
    ② 무릎 조각 없음 (무릎아래 = 무릎위) · ③ 발목 컷 없음 (발목 = 0) — 키트 종아리 = 무릎 ~ 발 한 조각
    ④ 앞뒤 반쪽은 팔다리 껍질만 (허벅지 · 정강이 · 팔끝 · 대포) — Dummy13 장갑의 1st/2nd half 자리. 머리 · 몸통 · 허리 · 발은 통짜"""
    import 분할_A as A
    c = A.기울스냅(A.스냅(dict(A.컷)))
    c.update(가슴=c["복부"], 무릎아래=c["무릎위"], 발목=0)
    A.짓기("G1", c, ["L허벅지", "L정강이", "L팔끝", "R대포"])
    return C.채점("G1")


if __name__ == "__main__":
    if sys.argv[1:] == ["G1"]: 짓기G1()
    main()
