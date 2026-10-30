# 판정기준117 데이터 — 설계116 생성기로 부품 100 · 부품마다 T1(다른 종류 5) · T2(변형 5) 후보 · 렌더(3/4) · 턴테이블 mp4 · 글 설명 · 코드 문자열 · 10-20
# 사용(cadrille venv · ART_MEM_GB=10): 데이터117.py [수=100] → out/설명/캐드부품/임베딩117/ (색인.json · 그림 · 영상)
import sys, os, json, copy, subprocess, numpy as np, cv2
import 설계116 as S
D = S.O + "임베딩117/"; os.makedirs(D + "렌더", exist_ok=True); os.makedirs(D + "영상", exist_ok=True)
def 부피(m, n=64):   # 10-30 새 자: 도면과 같은 정규화(상자 가운데 · 가장 긴 변 1) 뒤 n³ 점유 → packbits · 옛 실루엣 IoU 는 원기둥 하나만 그려도 0.41(바닥) · 부피는 0.15
    import open3d as o3d
    v = (m.vertices - m.bounds.mean(0)) / float(m.extents.max()); sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(v.astype(np.float32)), o3d.core.Tensor(np.asarray(m.faces, np.uint32)))
    g = (np.arange(n) + .5) / n * 1.1 - .55; X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    return np.packbits(sc.compute_occupancy(o3d.core.Tensor(np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32))).numpy() > 0)
def 부피겹(a, b):   # packbits 둘 → 부피 IoU · 하나라도 None 이면 0
    if a is None or b is None: return 0.
    a, b = np.unpackbits(a).astype(bool), np.unpackbits(b).astype(bool); return float((a & b).sum() / max((a | b).sum(), 1))
def 렌더(m, 방위=35., 고도=25., n=256):   # open3d 광선 · 법선 음영(램버트) · 흰 바탕
    import open3d as o3d
    v = (m.vertices - m.bounds.mean(0)) / float(m.extents.max()); sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(v.astype(np.float32)), o3d.core.Tensor(np.asarray(m.faces, np.uint32)))
    a, e = np.radians(방위), np.radians(고도); f = -np.array([np.cos(e) * np.sin(a), -np.cos(e) * np.cos(a), np.sin(e)]); up = np.array([0, 0, 1.]); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    g = (np.arange(n) + .5) / n * 1.3 - .65; X, Y = np.meshgrid(g, -g); o = -2.5 * f + X[..., None] * r + Y[..., None] * u
    ray = np.concatenate([o, np.broadcast_to(f, o.shape)], -1).reshape(-1, 6).astype(np.float32); h = sc.cast_rays(o3d.core.Tensor(ray))
    t = h["t_hit"].numpy().reshape(n, n); nr = h["primitive_normals"].numpy().reshape(n, n, 3); 빛 = np.array([.4, -.5, .75]); 빛 /= np.linalg.norm(빛)
    sh = np.clip(np.abs((nr * 빛).sum(-1)), 0, 1) * .75 + .2; img = np.where(np.isfinite(t), sh, 1.0)
    return (np.stack([img] * 3, -1) * 255).astype(np.uint8), np.isfinite(t)
def 글(s):   # 사양 → 글 설명(mm)
    b = s["바탕"]; k = b["종류"]; 치 = ", ".join(f"{a} {x:.0f} mm" for a, x in b.items() if isinstance(x, float))
    특 = "; ".join(f"{f['종류']} 구멍" if f["종류"] in ("관통", "막힌") else f["종류"] for f in s["특징"]) or "특징 없음"
    return f"CAD 부품: {k}. 치수 {치}. 특징: {특}." + (f" x 축으로 {s['기울임']:.0f}° 기울임." if s["기울임"] else "")
def 코드(s): return json.dumps(s, ensure_ascii=False, sort_keys=True)
def 하나(이름, s, 영상=False):
    w = S.짓기(s)
    if not w.val().isValid(): raise ValueError("깨짐")
    m, *_ = S.메시(w); img, sil = 렌더(m); cv2.imencode(".png", img)[1].tofile(D + "렌더/" + 이름 + ".png"); np.save(D + "렌더/" + 이름 + "_실루엣.npy", np.packbits(sil))
    if 영상:
        fr = D + "영상/_" + 이름; os.makedirs(fr, exist_ok=True)
        for k in range(12): cv2.imencode(".png", 렌더(m, 35 + k * 30)[0])[1].tofile(f"{fr}/{k:02d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "6", "-i", f"{fr}/%02d.png", "-pix_fmt", "yuv420p", D + "영상/" + 이름 + ".mp4"], check=True)
        for k in range(12): os.remove(f"{fr}/{k:02d}.png")
        os.rmdir(fr)
    return {"이름": 이름, "글": 글(s), "코드": 코드(s), "종류": s["바탕"]["종류"]}
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100; rng = np.random.default_rng(117); 색 = []
    풀 = []   # T1 다른 종류 후보용 부품 풀
    while len(풀) < 60:
        s = S.무작위(rng)
        try: 풀.append(하나(f"풀{len(풀):03d}", s))
        except Exception: pass
    t = 0
    while len(색) < n:
        s = S.무작위(rng)
        try: 정 = 하나(f"p{t:03d}", s, 영상=True)
        except Exception: t += 1; continue
        다른 = [x for x in 풀 if x["종류"] != 정["종류"]]; T1 = [다른[i] for i in rng.choice(len(다른), 5, replace=False)]
        T2 = []
        for j, (종, v) in enumerate(S.변형들(s, rng, 8)):
            if len(T2) == 5: break
            try: T2.append({**하나(f"p{t:03d}_v{j}", v), "변형": 종})
            except Exception: pass
        if len(T2) == 5: 색.append({"정답": 정, "T1": T1, "T2": T2}); print(len(색), 정["종류"], flush=True)
        t += 1
    json.dump(색, open(D + "색인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("끝", len(색))
