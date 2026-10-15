# 여섯방향.깎기 를 빠르게(10-15 · 결과는 같게) — 원본은 방향 6 × 층 17 × 다각형마다 s.cut(겹치는 기둥) + 매번 clean
# 바꾼 것: ① 층마다 기둥 대신 층 사이 판(slab)만 — 층 가림이 포개져 있어(깊 ≥ dz) 합집합이 같다 · 맨 아래 판이 바닥까지 뚫으니 「안 맞음」 층(17)은 빈 일
#          ② 섬은 구멍 난 면을 바로 밀어 낸다(빼기 불리언 없음 · 면이 무효면 원래 _도구)
#          ③ 방법 "층": 한 층의 판들(서로 안 겹침)을 불리언 한 번에 · 정리(clean)는 방향 끝에 한 번 · "방향": 한 방향의 판을 BRepAlgoAPI_Cut 한 번에(도구 여러 개) · "전부": 여섯 방향을 한 번에 · "판": 판을 하나씩(원래 순서)
#          ④ 퍼지 · 병렬 · 겹 손잡이 · 다각 = 마스크 → [(바깥, [섬…])] (기본 J.다각섬4 · 10-15 감사 뒤 기본)
import numpy as np
import 짓기 as J, 여섯방향 as S6
def _판(q, 구, w0, w1):   # 지역 w ∈ [w0, w1] 판 · 구멍 난 면을 바로 민다(무효면 원래 길: 기둥 − 섬 기둥)
    import cadquery as cq
    V = lambda p: cq.Wire.makePolygon([cq.Vector(x, y, w0) for x, y in p], close=True)
    if 구:
        f = cq.Face.makeFromWires(V(q), [V(r) for r in 구])
        if f.isValid(): return cq.Solid.extrudeLinear(f, cq.Vector(0, 0, w1 - w0))
        return J._도구(q, 구, w1 - w0, w0).val()
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(V(q)), cq.Vector(0, 0, w1 - w0))
def _뺌(s, 도구, 퍼지, 병렬, 정리=True):   # 도구 여러 개를 불리언 한 번에 → 정리(clean) 한 번
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.TopTools import TopTools_ListOfShape
    a = TopTools_ListOfShape(); a.Append(s.wrapped); t = TopTools_ListOfShape()
    for x in 도구: t.Append(x.wrapped)
    op = BRepAlgoAPI_Cut(); op.SetArguments(a); op.SetTools(t); op.SetRunParallel(병렬)
    if 퍼지: op.SetFuzzyValue(퍼지)
    op.Build()
    if not op.IsDone(): raise RuntimeError("불리언 실패")
    r = cq.Shape.cast(op.Shape()); return r.clean() if 정리 else r
def _여럿뺌(s, 도구, 퍼지, 병렬, 정리=True):   # 한 번에 안 되면 하나씩(깨진 도구만 버리고 센다)
    if not 도구: return s
    try: return _뺌(s, 도구, 퍼지, 병렬, 정리)
    except Exception:
        for t in 도구:
            try: s = _뺌(s, [t], 퍼지, 병렬, 정리)
            except Exception: J.버린["여섯 깎기"] += 1
        return s
def 깎기(몸, 지도, 마감=None, 방법="방향", 퍼지=0.0, 병렬=False, 다각=None, 겹=.5):   # 겹 = 판을 위로 몇 층 더 덮나(층 사이 근사 다각형이 안 포개지는 틈 · 맞닿은 면 피함) → (cq.Workplane, 버린 수) · 여섯방향.깎기 와 같은 꼴
    import time, cadquery as cq
    다각 = 다각 or J.다각섬4; J.버린.clear(); s = 몸.val(); 모두 = []; 층수 = S6.층수
    for k, (축, 도) in S6.방향.items():
        r = S6.R(축, 도); h = S6.반높이(몸, r); 깊 = S6.층(지도[k], h); 단 = 2 * h / 층수; 이번 = []; 첫 = 0
        for i in range(1, 층수 + 1):
            m = 깊 >= i * 단 - 1e-6
            if not m.any(): break
            w0 = -h - .1 if i == 층수 else h - i * 단; w1 = min(h + .05, h - (i - 1 - 겹) * 단) if i > 1 else h + .05
            for q, 구 in 다각(m):
                if 마감 and time.time() > 마감: raise TimeoutError("여섯 깎기 %s 층 %d" % (k, i))
                try:
                    t = _판(q, 구, w0, w1); t = t.rotate(cq.Vector(0, 0, 0), cq.Vector(*((1, 0, 0) if 축 == "X" else (0, 1, 0))), 도) if 도 else t
                    if 방법 == "판":
                        try: s = _뺌(s, [t], 퍼지, 병렬)
                        except Exception: J.버린["여섯 깎기"] += 1
                    else: 이번.append(t)
                except Exception: J.버린["여섯 깎기"] += 1
            if 방법 == "층": s = _여럿뺌(s, 이번[첫:], 퍼지, 병렬, False); 첫 = len(이번)
        if 방법 == "층" and 이번: s = s.clean()
        if 방법 == "방향": s = _여럿뺌(s, 이번, 퍼지, 병렬)
        모두 += 이번
    if 방법 == "전부": s = _여럿뺌(s, 모두, 퍼지, 병렬)
    return cq.Workplane(s), sum(J.버린.values())
# ── 면짓기(10-15 · 불리언 0 번) — 층 지도가 정해지면 모양은 칸 셈으로 정해진다(여섯방향.칸깎기 를 128³ 로) · 칸 덩어리의 경계 면을 사각면으로 → 꿰맴 → 고체 → 같은 평면 합침
def _경계(q):   # q [x, y, z] bool → [(축 a, 면 자리 p, 칸 판 D(2 차원 · 나머지 두 축 순서), 바깥 법선 ±1)] · 칸 i 의 + 쪽 면은 자리 i + 1 · − 쪽은 i
    P = np.pad(q, 1); out = []
    for a in range(3):
        A = np.moveaxis(P, a, 0)
        for 위, 옆 in ((A[1:-1] & ~A[2:], 1), (A[1:-1] & ~A[:-2], 0)):
            for i in np.nonzero(위.any((1, 2)))[0]: out.append((a, i + 옆, 위[i][1:-1, 1:-1], 1 if 옆 else -1))
    return out
def _사각(m):   # 2 차원 판 → 직사각형 [(b0, b1, c0, c1)] · 행마다 줄(run) → 위 행과 같은 줄이면 이어 붙임
    out = []; 열린 = {}
    for b in range(m.shape[0] + 1):
        r = m[b] if b < m.shape[0] else np.zeros(m.shape[1], bool); d = np.diff(np.r_[0, r.astype(np.int8), 0]); 줄 = set(zip(np.nonzero(d == 1)[0].tolist(), np.nonzero(d == -1)[0].tolist()))
        for c in [c for c in 열린 if c not in 줄]: out.append((열린.pop(c), b) + c)
        for c in 줄: 열린.setdefault(c, b)
    return out
def _고침표():   # 2×2×2 칸 무늬 256 개 → [무늬, 칸 0 ~ 7] = 그 빈 칸 하나를 채우면 가운데 꼭짓점이 다양체가 되나 · 나쁜 무늬 표
    # 나쁨 = 찬 칸끼리 또는 빈 칸끼리 면으로 안 이어짐(모서리만 닿는 것도 여기 걸린다) · 고쳐지는 칸이 없으면 빈 칸 전부를 후보로
    from scipy.ndimage import label
    나쁨 = lambda b: bool((b.any() and label(b.reshape(2, 2, 2))[1] > 1) or ((~b).any() and label(~b.reshape(2, 2, 2))[1] > 1))
    t = np.zeros((256, 8), bool); 나 = np.zeros(256, bool)
    for k in range(256):
        b = np.array([(k >> i) & 1 for i in range(8)], bool); 나[k] = 나쁨(b)
        if not 나[k]: continue
        빈 = [i for i in range(8) if not b[i]]; 좋 = [i for i in 빈 if not 나쁨(np.where(np.arange(8) == i, True, b))]
        t[k, 좋 or 빈] = True
    return 나, t
def 다양체로(q, 폭=None):   # 칸 덩어리를 꿰맬 수 있게 — 나쁜 꼭짓점마다 칸 하나씩 채움(가장 작은 칸 · 폭 = 축마다 칸 폭) · 채우기만 하니 끝난다 → (q, 채운 칸 수)
    n0 = int(q.sum()); 나, 표 = _고침표(); P = np.pad(q, 1); 자 = [(i, j, l) for i in range(2) for j in range(2) for l in range(2)]
    폭 = 폭 or [np.ones(n) for n in q.shape]; 폭 = [np.r_[1e9, w, 1e9] for w in 폭]   # 덧댄 칸은 안 채운다
    while True:
        S = [P[i:P.shape[0] - 1 + i, j:P.shape[1] - 1 + j, l:P.shape[2] - 1 + l] for i, j, l in 자]
        k = sum(S[t].astype(np.int32) << t for t in range(8)); 곳 = np.nonzero(나[k])
        if not len(곳[0]): return P[1:-1, 1:-1, 1:-1].copy(), int(P.sum()) - n0
        후 = 표[k[곳]]; 부 = np.stack([폭[0][곳[0] + i] * 폭[1][곳[1] + j] * 폭[2][곳[2] + l] for i, j, l in 자], 1); 고 = np.argmin(np.where(후, 부, np.inf), 1)
        for t, (i, j, l) in enumerate(자):
            m = 고 == t; P[곳[0][m] + i, 곳[1][m] + j, 곳[2][m] + l] = True
def 면짓기(몸, 지도, n=128, 합침=True, 고침=True):   # → (cq.Workplane, 면 수 정보) · 합침=False 면 칸 하나 = 사각면 하나(이음이 딱 맞음)
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopoDS import TopoDS

    return 칸고체(S6.칸깎기(J.점유_캐드(몸, n), 몸, 지도, n), 합침, 고침)
def 칸고체(q, 합침=True, 고침=True, 자=None):   # 칸 [x, y, z] → (cq.Workplane, 정보) · 자 = 축마다 칸 경계 좌표(길이 n + 1 · 없으면 −.55 ~ .55 고른 n³ + 1e-5 밀기)
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopoDS import TopoDS
    n = q.shape[0]; q, 채움 = 다양체로(q, [np.diff(z) for z in 자] if 자 else None) if 고침 else (q, 0); e = 1.1 / n   # 1e-5 밀기: 128 칸 면이 48³ 채점 칸 가운데(3 칸에 하나)와 딱 겹쳐 선이 면을 스친다
    자 = 자 or [-.55 + np.arange(n + 1) * e + 1e-5] * 3
    판 = []
    for a, p, m, sg in _경계(q):
        판 += [(a, p, sg) + r for r in _사각(m)] if 합침 else [(a, p, sg, b, b + 1, cc, cc + 1) for b, cc in zip(*np.nonzero(m))]
    sew = BRepBuilderAPI_Sewing(1e-6, True, True, True, not 고침)   # 안 고치면 비다양체 모서리를 그대로 꿰맨다
    for a, p, sg, b0, b1, c0, c1 in 판:   # 감는 방향으로 바깥 법선을 맞춘다(b → c 감기의 법선 = e_b × e_c = 축 1 만 −)
        나 = [x for x in range(3) if x != a]; pts = []; 감 = ((b0, c0), (b1, c0), (b1, c1), (b0, c1))
        for b, cc in (감 if sg == (-1 if a == 1 else 1) else 감[::-1]):
            v = [0.0] * 3; v[a] = 자[a][p]; v[나[0]] = 자[나[0]][b]; v[나[1]] = 자[나[1]][cc]; pts.append(cq.Vector(*v))
        sew.Add(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)).wrapped)
    sew.Perform(); sh = sew.SewedShape(); 고 = []
    ex = TopExp_Explorer(sh, TopAbs_SHELL)
    while ex.More():   # 바깥에서만 깎으니 속 빈 곳(공동)은 없다 — 껍질 하나 = 고체 하나
        fs = ShapeFix_Shell(TopoDS.Shell_s(ex.Current())); fs.Perform()   # 꿰맨 면 방향이 어긋난 곳(467: BadOrientationOfSubshape)
        ms = BRepBuilderAPI_MakeSolid(fs.Shell()); f = ShapeFix_Solid(ms.Solid()); f.Perform(); 고.append(cq.Shape.cast(f.Solid())); ex.Next()
    s = 고[0] if len(고) == 1 else cq.Compound.makeCompound(고)
    u = ShapeUpgrade_UnifySameDomain(s.wrapped, True, True, False); u.Build(); s = cq.Shape.cast(u.Shape())
    return cq.Workplane(s), {"사각": len(판), "껍질": len(고), "칸": int(q.sum()), "채움": 채움}
def 지킴짓기(몸, 지도, 고침=True, 띠=.01):   # 면짓기 의 정확판 — 틀은 칸으로 바꾸지 않는다: 「안 깎이는 곳」 K 를 고르지 않은 격자로 칸 셈 → 면 → 고체 · 몸 ∩ K 불리언 한 번
    # 격자 = 화소 경계 ± 띠/2 화소 + 방향마다 층 면(h − i 단) · 칸 가운데마다 여섯방향.칸깎기 와 같은 셈(np.round 화소 · L_w > h − 깊)
    # 띠: 48³ 채점 칸 가운데의 1/3 이 화소 경계에 딱 놓인다(t = 8j + 3.5) — 경계 위 점은 칸깎기 처럼 반올림 쪽 화소를 따르도록 경계에 폭 1 % 화소의 띠 칸을 둔다(모양은 화소 그대로)
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    e = -.55 + np.arange(S6.N + 1) * S6.칸; 자 = [list(np.r_[e - 띠 * S6.칸 / 2, e + 띠 * S6.칸 / 2]) for _ in range(3)]
    for k, (축, 도) in S6.방향.items():
        r = S6.R(축, 도); h = S6.반높이(몸, r); a = int(np.argmax(np.abs(r[:, 2]))); sg = np.sign(r[a, 2])
        자[a] += [sg * (h - i * 2 * h / S6.층수) for i in range(S6.층수 + 1)]
    자 = [np.unique(np.clip(np.round(np.array(z), 12), -.6, .6)) for z in 자]; 자 = [z[np.r_[True, np.diff(z) > 1e-5]] for z in 자]   # 1e-5 보다 얇은 칸(층 면이 띠 경계에 거의 붙음)은 없앤다 — 꿰맴이 어긋남(467 · 126)
    가 = [(z[1:] + z[:-1]) / 2 for z in 자]
    q = np.ones([len(x) for x in 가], bool); Y, Z = np.meshgrid(가[1], 가[2], indexing="ij"); 끝 = S6.N - 1
    for k, (축, 도) in S6.방향.items():   # 메모리 아끼려 x 판마다
        r = S6.R(축, 도); h = S6.반높이(몸, r); 깊 = S6.층(지도[k], h)
        for i, x in enumerate(가[0]):
            L = np.stack([np.full_like(Y, x), Y, Z], -1) @ r
            u = np.clip(np.round((L[..., 0] + .55) / S6.칸 - .5).astype(int), 0, 끝); v = np.clip(np.round((-L[..., 1] + .55) / S6.칸 - .5).astype(int), 0, 끝)
            q[i] &= ~(L[..., 2] > h - 깊[v, u])
    K, 정 = 칸고체(q, True, 고침, 자)
    op = BRepAlgoAPI_Common(몸.val().wrapped, K.val().wrapped); op.Build()
    if not op.IsDone(): raise RuntimeError("몸 ∩ K 실패")
    from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp; from OCP.TopTools import TopTools_ListOfShape
    부피 = lambda x: (lambda g: (BRepGProp.VolumeProperties_s(x, g), g.Mass())[1])(GProp_GProps()); 다시 = 0
    if 부피(op.Shape()) < 1e-9 < 부피(K.val().wrapped):   # 10-15 천장51c 5 번: 맞닿은 면 때문에 「성공」인데 빈 결과 → 퍼지 1e-6 로 한 번 더(1e-4 는 다시 비었다) · 센다
        op = BRepAlgoAPI_Common(); a_, b_ = TopTools_ListOfShape(), TopTools_ListOfShape(); a_.Append(몸.val().wrapped); b_.Append(K.val().wrapped)
        op.SetArguments(a_); op.SetTools(b_); op.SetFuzzyValue(1e-6); op.Build(); 다시 = 1
        if not op.IsDone() or 부피(op.Shape()) < 1e-9: raise RuntimeError("몸 ∩ K 빈 결과(퍼지로도)")
    return cq.Workplane(cq.Shape.cast(op.Shape()).clean()), dict(정, 격자=[len(x) for x in 가], 퍼지다시=다시)
