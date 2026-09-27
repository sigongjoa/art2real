# -*- coding: utf-8 -*-
"""EG 정강이 반쪽 셋째 판 — 옆 · 안쪽 사진으로 깊이 · 속을 읽어 껍질로 (2026-09-27).

    python 정강이3.py -> out/키트/EG_RX78/2단계/부품_44_v3.stl · 부품_45_v3.stl · 정강이3.json
                         out/키트/EG_RX78/정강이/정강이3_대조.png

둘째 판(정강이2.py) = 위 사진 한 장 · 두께 · 돔 높이 가정 · 속 참(바닥판만 비움).
셋째 판 = 같은 하위 도형(바닥판 · 종아리 돔 · 무릎 원판 · 발목 탭 · 브래킷) + 읽은 값:
  · 껍질: 바닥판 · 돔 · 원판 모두 안쪽을 벽 t 로 판다(gp_019 안쪽 사진의 V 자 = 돔 속 빔 · 무릎 원판 = 안에서 컵)
  · 속: 원통 보스 다섯 + 무릎 칸막이 리브(gp_019) · 브래킷 구멍
  · 암수: 44 = 핀(hw_044 · gp_019 위 부품의 발목 탭 밑 핀) · 45 = 구멍(gp_019 안쪽) — 어느 번호가 암인지는 가정
  · 발목 탭: 겉쪽에 붙고 가운데(맞붙는 면 쪽)는 빈 틈(hw_045) · 44 탭의 축 핀이 틈을 건너 45 탭 구멍으로
좌표 · 척도는 정강이2 와 같다(정규 L = 60 · x = 두께(겉 +) · y = u · z = v → 2단계 에서 136 px × 0.17 mm 로 줄임).
값의 근거 · 확실도는 읽은값 사전과 정강이3.json."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from matplotlib.path import Path
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 정강이 as S1, 정강이2 as S2, 방패 as B
import 그룹_다리발 as G

L = S1.L; D = S1.D
k = 136 * G.MM / L                    # 정규 단위 → mm (2단계 와 같음)
틈 = 0.12 / k                         # 핀 · 구멍 지름 틈 0.12 mm(한쪽) → 정규 단위

# 읽은 값(L 배). 확실도: 읽음 = 사진에서 바로 · 어림 = 원근 · 흐림 보정한 추정 · 가정 = 사진에 없음
읽은값 = {
    "반두께":    (0.145, "어림", "hw_046 앞모습 조립 두께/길이 ≈ 0.31 → 반 0.155 · gp_019 안쪽 앞벽 띠 0.10/cos47° ≈ 0.12~0.15"),
    "벽":        (0.020, "어림", "gp_019 안쪽 테두리 윗면 띠 0.013~0.02 L(흐림)"),
    "돔높이":    (0.065, "어림", "hw_046 종아리 조립 두께 0.41 L − 아래 정강이 0.31 L → 한쪽 0.05 · gp_019 위 부품 돔이 먼 테두리 위로 ≈0.057/cos45° → 0.065 로 올림(첫 대조에서 돔이 낮아 보였다) · 단차 0.008 포함"),
    "원판높이":  (0.040, "어림", "hw_047 · gb_086 무릎 원판 옆 띠 ≈ 지름의 0.35 · 지름 0.116 L"),
    "원판홈깊이": (0.010, "가정", "사진에서 홈 바닥이 안 보임"),
    "탭안":      (0.30, "어림", "hw_045 발목: 두 탭 사이 틈 ≈ 조립 두께의 0.3 → 탭 안쪽 면 = 0.30 × 반두께"),
    "탭겉단차":  (0.020, "어림", "gb_034 발목 탭 윗면이 몸통 겉면보다 한 단 낮음"),
    "속시작v":   (0.16, "읽음", "gp_019 안쪽: 발목 쪽 끝벽 x≈220/1200 → v 0.17"),
    "발목핀지름": (0.061, "어림", "gp_019 안쪽 발목 탭 구멍 ≈ 70/1149 px"),
    "발목겉구멍": (0.044, "읽음", "정강이.py 발목구멍 r 0.022 · gp_019 위 부품 탭 구멍 45/1055 px"),
    "발목깃":    (0.10, "어림", "gp_019 안쪽 확대: 45 발목 탭 구멍 둘레 도톰한 깃 바깥지름"),
    "발목깃높이": (0.015, "어림", "gp_019 안쪽 확대: 깃 옆 띠"),
    "핀길이":    (0.040, "가정", "핀 끝이 안 보임(hw_044 발목 핀만 보임 · 길이 ≈ 탭 두께)"),
    "리브":      ((-0.25, 0.695, 0.25, 0.74), "읽음", "gp_019 안쪽 무릎 칸막이 벽 (830,40)→(870,330)/1200 px"),
    "브래킷구멍": (0.025, "어림", "gp_019 위 부품 브래킷 · 안쪽 (850,325) 작은 구멍"),
}
# 보스: (u, v, 바깥지름, 구멍지름) — gp_019 안쪽 확대(3 배)에서 발목 구멍 (105,300) · 무릎 원 (1085,225) 두 점으로 v, 앞뒤 테두리 사이 몫으로 u
보스 = [(-0.093, 0.255, 0.095, 0.050), (0.103, 0.229, 0.052, 0.022), (-0.104, 0.655, 0.083, 0.048),
        (0.055, 0.633, 0.060, 0.022), (-0.060, 0.851, 0.060, 0.022)]
V = {n: v[0] for n, v in 읽은값.items()}
a0, t = V["반두께"] * L, V["벽"] * L
돔단차 = 0.008; 돔높이 = V["돔높이"] - 돔단차; 탭v = 0.14; 가장r = 0.02

def 판cs(cs, x0, x1): return cs.extrude(x1 - x0).transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
def cs(poly): return M.CrossSection([B.반시계(np.asarray(poly, float) * L).tolist()])
def 상자(u0, v0, u1, v1, x0, x1): return S2.판x(np.array([(u0, v0), (u1, v0), (u1, v1), (u0, v1)]), x0, x1)
def 원기둥(u, v, d, x0, x1): return S2.판x(S1.원((u, v), d / 2, 40), x0, x1)

def 돔장():
    g = np.load(os.path.join(D, "정강이_정답.npz")); mask = S1.매끈마스크(g["겉"]); H, W = mask.shape
    yy, xx = np.mgrid[0:H, 0:W]; uu = (xx + 0.5 - W / 2) / H; vv = 1 - (yy + 0.5) / H
    안쪽 = Path(S1.잘게(S1.물방울)).contains_points(np.c_[uu.ravel(), vv.ravel()]).reshape(H, W)
    dd = ndimage.gaussian_filter(ndimage.distance_transform_edt(안쪽) / H, 3.0)
    return mask, dd, float(dd.max())

def 부풀기(m, 바닥x, dd, dmax, shape):
    """정강이2 의 돔 곡면을 바닥x 위 정점에만 — 겉 돔과 속 돔이 같은 장을 쓰니 벽이 고르다."""
    def f(Vv):
        top = Vv[:, 0] > 바닥x + 0.5 * 돔단차 * L
        d = S1.표본(dd, shape, Vv[:, 1] / L, Vv[:, 2] / L); kk = np.sqrt(np.clip(1 - (1 - np.clip(d / dmax, 0, 1)) ** 2, 0, 1))
        return np.c_[Vv[:, 0] + top * 돔높이 * L * kk, Vv[:, 1], Vv[:, 2]]
    return m.refine_to_length(0.5).warp_batch(f)

def 짓기(수):
    """수 = True → 핀 쪽(44) · False → 구멍 쪽(45). 정규 좌표로 돌려준다(2단계 변환 전)."""
    mask, dd, dmax = 돔장(); H, W = mask.shape; P = S1.다각형(mask)
    바깥 = cs(P); 탭안, 탭겉 = V["탭안"] * a0, a0 - V["탭겉단차"] * L; 원판top = a0 + V["원판높이"] * L
    # ── 겉 부피 O ──
    바닥 = 판cs(바깥, 0, a0) - 상자(-1, -0.1, 1, 탭v, 탭겉, a0 + 9) - 상자(-1, -0.1, 1, 탭v, -9, 탭안)
    돔윤곽 = S1.잘게(S1.물방울)
    돔 = 부풀기(S2.판x(돔윤곽, a0 - 0.2, a0 + 돔단차 * L), a0, dd, dmax, (H, W))
    c = S1.무릎원; 원판 = 원기둥(c[0], c[1], 2 * c[2], a0 - 0.2, 원판top)
    u0, u1, v0, v1 = S2.브래킷; 브 = 상자(u0, v0, u1, v1, 0.3 * a0, 0.9 * a0)
    O = 바닥 + 돔 + 원판 + 브
    # ── 속 I (벽 t 로 판다) ──
    안돔 = 부풀기(판cs(cs(돔윤곽).offset(-t, M.JoinType.Round), a0 - t - 1.0, a0 - t + 돔단차 * L), a0 - t, dd, dmax, (H, W))
    I = 판cs(바깥.offset(-t, M.JoinType.Round), -1, a0 - t) + 안돔 + 원기둥(c[0], c[1], 2 * c[2] - 2 * V["벽"], -1, 원판top - t)
    I = I - 상자(-1, -0.1, 1, V["속시작v"], -9, a0 + 9)
    m = O - I
    # ── 보스 · 리브 (겉 부피 안으로만) ──
    rb = V["리브"]; 리브 = S2.판x(np.array([(rb[0], rb[1]), (rb[2], rb[3]), (rb[2], rb[3] + V["벽"]), (rb[0], rb[1] + V["벽"])]), 0, a0 + 9)
    속 = 리브
    for u, v, od, _ in 보스: 속 = 속 + 원기둥(u, v, od, 0, a0 + 9)
    속 = 속 + (원기둥(c[0], c[1], 2 * c[2], 0, a0 + 9) - 원기둥(c[0], c[1], 2 * c[2] - 2 * V["벽"], -1, a0 + 10))   # 무릎 컵 둘레벽(gp_019: 몸통 속과 따로 둥근 컵)
    m = m + (속 ^ O)
    ax, av = S1.발목구멍[:2]; 핀 = V["핀길이"] * L
    if 수:
        for u, v, od, idd in 보스: m = m + 원기둥(u, v, idd - 2 * 틈 / L, -핀, 0.01)
        m = m + 원기둥(ax, av, V["발목핀지름"] - 2 * 틈 / L, -(탭겉 - 0.005 * L), 탭안 + 0.01)   # 발목 축 핀: 틈을 건너 짝 탭 관통
        m = m - 원기둥(ax, av, V["발목겉구멍"], 탭겉 - 0.02 * L, a0 + 9)                     # 겉에서 본 오목(성형 수축 자리)
    else:
        for u, v, od, idd in 보스: m = m - 원기둥(u, v, idd, -1, a0 - t)
        m = m + 원기둥(ax, av, V["발목깃"], 탭안 - V["발목깃높이"] * L, 탭안 + 0.01)             # 탭 안쪽 면의 깃(gp_019 확대)
        m = m - 원기둥(ax, av, V["발목핀지름"], -9, a0 + 9)
    m = m - 원기둥(u0 + 0.5 * (u1 - u0) - 0.005, 0.5 * (v0 + v1), V["브래킷구멍"], -9, a0 + 9)
    홈 = 상자(c[0] - 0.045, c[1] - 0.007, c[0] + 0.045, c[1] + 0.007, 원판top - V["원판홈깊이"] * L, a0 + 9)
    m = m - 홈
    # 가장자리 둥글림(정강이2 와 같음): 겉면 쪽 윤곽 가까이만
    # 거리는 마스크가 아니라 실제 윤곽 다각형 P 에서 잰다 — 마스크 계단과 P 가 어긋나 옆벽 윗모서리가 톱니가 됐다(둘째 판 그림에도 있음)
    yy, xx = np.mgrid[0:H, 0:W]; 안P = Path(P).contains_points(np.c_[(xx.ravel() + 0.5 - W / 2) / H, 1 - (yy.ravel() + 0.5) / H]).reshape(H, W)
    거리 = ndimage.gaussian_filter(ndimage.distance_transform_edt(안P) / H, 1.0)
    def 둥글(Vv):
        d = S1.표본(거리, (H, W), Vv[:, 1] / L, Vv[:, 2] / L); 위 = np.clip((Vv[:, 0] - 0.5 * a0) / (0.5 * a0), 0, 1)
        return np.c_[Vv[:, 0] - 위 * 가장r * L * (1 - np.sqrt(np.clip(1 - (1 - np.clip(d / 가장r, 0, 1)) ** 2, 0, 1))), Vv[:, 1], Vv[:, 2]]
    return m.refine_to_length(0.6).warp_batch(둥글)

def 부품좌표(m, n):
    """그룹_다리발.정강이 와 같은 변환: (u, v, 두께) mm · 45 = 거울."""
    s = -1.0 if n == 45 else 1.0
    return m.transform(np.array([[0, s, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float) * k)

# 조립: 45 를 Y 축으로 180° 돌리면 44 의 (u, v, −두께) 자리에 온다
조립R = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0]], float)

# ---------- 그림 ----------
def 렌더(tm, R, W=360, Hh=360, 색=(0.86, 0.9, 0.88)):
    """정강이_그림.py 와 같은 음영 + 선(깊이 튐 · 법선 꺾임)."""
    Vv = tm.vertices @ R.T; N = tm.face_normals @ R.T
    cx_, cy_ = (Vv[:, 0].min() + Vv[:, 0].max()) / 2, (Vv[:, 1].min() + Vv[:, 1].max()) / 2
    s = max((Vv[:, 0].max() - Vv[:, 0].min()) / (W - 20), (Vv[:, 1].max() - Vv[:, 1].min()) / (Hh - 20)); Wb = max(W, Hh) + 2
    zb, tid = G.DD.래스터(Vv - [cx_, cy_, 0], tm.faces, W / 2, Hh / 2, s, Wb); zb, tid = zb[:Hh, :W], tid[:Hh, :W]
    img = np.ones((Hh, W, 3)) * 0.9; A = tid >= 0; Lt = np.array([-0.5, 0.45, 0.74]); Lt /= np.linalg.norm(Lt)
    img[A] = np.array(색) * (np.clip(N[tid[A]] @ Lt, 0, 1) * 0.75 + 0.25)[:, None]
    nb = np.zeros((Hh, W, 3)); nb[A] = N[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((Hh, W), bool)
    for ax in (0, 1):
        선 |= A & np.roll(A, 1, ax) & ((np.abs(z - np.roll(z, 1, ax)) > 3 * s) | ((nb * np.roll(nb, 1, ax)).sum(-1) < np.cos(np.radians(25))))
    img[선] *= 0.55
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def 보기(*회전):
    """회전 = [(축, 도)] 차례로(화면 축 기준). 모델 기본 = 겉(+Z)에서, 무릎 위."""
    R = np.eye(3)
    for a, d in 회전: R = Rot.from_euler(a, d, degrees=True).as_matrix() @ R
    return R

def 조립(t44, t45): return trimesh.util.concatenate([t44, t45.copy().apply_transform(np.vstack([조립R, [0, 0, 0, 1]]))])

if __name__ == "__main__":
    OUT = G.OUT; 결과 = {}; 모 = {}
    for n in (44, 45):
        m = 부품좌표(짓기(n == 44), n); fn = os.path.join(OUT, "부품_%02d_v3.stl" % n)
        닫힘 = G.내보내기(m, fn); 모[n] = m
        tm = trimesh.load(fn)
        결과[n] = dict(쪽="핀(수)" if n == 44 else "구멍(암)", 닫힘=닫힘, 부피mm3=round(m.volume(), 1), 크기mm=np.round(tm.extents, 2).tolist(), 조각=len(m.decompose()))
        print(n, 결과[n])
    # 맞물림 검사: 조립했을 때 44 와 45 가 겹치면 핀이 구멍에 안 들어간 것
    겹침 = (모[44] ^ 모[45].transform(조립R)).volume()
    핀부피 = (모[44] ^ 상자(-1, -1, 1, 2, -9, 0).transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float) * k)).volume()
    결과["조립"] = dict(겹침mm3=round(겹침, 4), 맞붙는면_너머_핀부피mm3=round(핀부피, 3), 틈mm=0.12)
    assert all(결과[n]["닫힘"] and 결과[n]["조각"] == 1 for n in (44, 45)), "안 닫힘 · 떨어진 조각"
    assert 겹침 < 1e-3, "핀이 짝과 부딪친다 %.4f" % 겹침
    assert 핀부피 > 0.05, "핀이 맞붙는 면을 안 넘는다"
    # 척도 대조: gb_034 격자(국소 1 칸 = 10 mm ≈ 세로 57 px · 가로 68 px)로 정강이 길이 282 px → 약 46~49 mm vs 0.17 체계 23.8 mm
    결과["척도"] = dict(체계_mm_px=G.MM, 체계_길이mm=round(136 * G.MM, 1), 격자_길이mm="46~49 (gb_034 · 원근 · 부품 높이 확대 포함)", 배="≈ 2.0",
                      비고="gb_005 전신 옆: 정강이 ≈ 전고의 0.33 → 전고 125 mm 면 약 41 mm. 0.17 mm/px 체계가 실물의 약 절반으로 보인다 — 척도는 체계대로 두었다")
    g = 짓기(True).to_mesh(); 모옆 = ndimage.binary_fill_holes(S1.옆실루엣(trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)))
    결과["참고_옆실루엣IoU_heldout"] = round(S1.맞춤(S1.정답("정강이_짝"), 모옆)[0], 4)          # 판정은 눈 — 윤곽은 둘째 판과 같다
    결과["읽은값"] ={n: dict(값=v[0], 확실도=v[1], 근거=v[2]) for n, v in 읽은값.items()}
    결과["보스"] = [dict(u=b[0], v=b[1], 바깥지름=b[2], 구멍지름=b[3], 확실도="어림(gp_019 안쪽 · 45 만 봄 · 44 핀 자리는 같은 자리 가정)") for b in 보스]
    결과["단위"] = "값은 L(정강이 길이) 배 · 1 L = %.2f mm(체계)" % (L * k)
    json.dump(결과, open(os.path.join(OUT, "정강이3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- 대조 그림 ----
    A_ = r"G:\art2real\원화3d\out\키트\EG_RX78\추가"
    t3 = {n: trimesh.load(os.path.join(OUT, "부품_%02d_v3.stl" % n)) for n in (44, 45)}
    t2 = {n: trimesh.load(os.path.join(OUT, "부품_%02d.stl" % n)) for n in (44, 45)}
    줄 = [("inner (45) - gp_019", ("gp_019.jpg", (60, 200, 460, 360)), lambda t: t[45], 보기(("y", 180), ("z", -90), ("x", -45))),
         ("outer (44) - gp_019", ("gp_019.jpg", (90, 80, 470, 230)), lambda t: t[44], 보기(("z", -90), ("x", -45))),
         ("assembled oblique - hw_046", ("hw_046.jpg", (310, 150, 1060, 530)), lambda t: 조립(t[44], t[45]), 보기(("x", -90), ("y", -90), ("x", 30), ("z", 20))),
         ("assembled side - gb_035", ("gb_035.jpg", (480, 0, 800, 534)), lambda t: 조립(t[44], t[45]), 보기(("z", -12)))]
    W = 360; 캔 = Image.new("RGB", (W * 3, (W + 20) * len(줄)), "white"); dr = ImageDraw.Draw(캔)
    for i, (이름, (f, box), 고름, R) in enumerate(줄):
        ph = Image.open(os.path.join(A_, f)).convert("RGB").crop(box); ph.thumbnail((W, W), Image.LANCZOS)
        y = i * (W + 20); 캔.paste(ph, ((W - ph.size[0]) // 2, y + 20 + (W - ph.size[1]) // 2))
        캔.paste(렌더(고름(t3), R), (W, y + 20)); 캔.paste(렌더(고름(t2), R, 색=(0.8, 0.82, 0.9)), (2 * W, y + 20))
        dr.text((4, y + 4), "%s   |  photo  |  v3 (this)  |  v2" % 이름, fill=(0, 0, 0))
    fn = os.path.join(D, "정강이", "정강이3_대조.png"); 캔.save(fn); print(fn)
    print(json.dumps({k_: v for k_, v in 결과.items() if k_ in (44, 45, "조립")}, ensure_ascii=False, indent=1))
