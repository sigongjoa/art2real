# 실제 그림(GPT · Gemini 3면도 한 장 · 정답 없음) → 판0(학습69 32 단계)로 3D · 10-18
# 사용(venv · ART_MEM_GB=8): 실제76.py <그림.png> [...] → out/설명/캐드부품/실제입력/<이름>/ (입력.png · 칸.npy · 돌림.mp4)
# 그림 → 세 면: 잉크 세로줄 투영의 빈 틈으로 왼쪽부터 위 · 앞 · 옆 · 면마다 가장 큰 덩어리(7 화소 부풀려 셈) 상자 안 잉크만(글자 뺌)
# 크기: x = 위 폭 · 앞 폭 평균 · y = 위 높이 · 옆 폭 평균 · z = 앞 · 옆 높이 평균 → 면마다 그 크기로 늘려 서로 맞춤(생성 그림은 축척이 어긋난다)
# 방향: 제도 위 그림은 앞이 아래 · 데이터 위 그림은 앞(+y)이 위 → 위 그림만 상하 뒤집음 · x 거울은 세 장이 같이라 무시
# ponytail: 데이터는 가장 얇은 축이 z(위) · 피규어 부품은 아닐 수 있다 — 그대로 넣음
import sys, os, subprocess, numpy as np, cv2
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; N = 128
def 읽기(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_GRAYSCALE) < 200   # 생성 그림 선은 옅은 회색(안티앨리어싱)
def 세면(잉):
    열 = 잉.any(0); 구 = []; s = None
    for i, c in enumerate(np.append(열, False)):
        if c and s is None: s = i
        if not c and s is not None: 구.append((s, i)); s = None
    while len(구) > 3:   # 가장 좁은 틈부터 붙임
        j = int(np.argmin([구[k + 1][0] - 구[k][1] for k in range(len(구) - 1)])); 구[j:j + 2] = [(구[j][0], 구[j + 1][1])]
    assert len(구) == 3, "면이 셋으로 안 갈림: %d" % len(구)
    out = []
    for a, b in 구:
        m = 잉[:, a:b].astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(m, np.ones((7, 7), np.uint8)), connectivity=8)   # 끊긴 선을 붙여서 덩어리를 셈
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); x, y, w, h = st[k, :4]
        c = m[y:y + h, x:x + w] > 0; r, q = np.nonzero(c.any(1))[0], np.nonzero(c.any(0))[0]; out.append(c[r[0]:r[-1] + 1, q[0]:q[-1] + 1])   # 부풀린 테두리를 빼고 잉크에 딱 맞춤
    return out
def 놓기(m, 가, 세):   # 잉크 상자를 (세 × 가) 화소로 늘려 128² 가운데
    r = cv2.resize(m.astype(np.float32), (max(int(round(가)), 2), max(int(round(세)), 2)), interpolation=cv2.INTER_AREA) > .1
    c = np.zeros((N, N), np.uint8); y0, x0 = (N - r.shape[0]) // 2, (N - r.shape[1]) // 2; c[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r; return c
def 그림셋(p):
    위, 앞, 옆 = 세면(읽기(p)); 위 = 위[::-1]
    x = (위.shape[1] + 앞.shape[1]) / 2; y = (위.shape[0] + 옆.shape[1]) / 2; z = (앞.shape[0] + 옆.shape[0]) / 2; 화 = N / 1.1 / max(x, y, z) * .999
    return 놓기(위, x * 화, y * 화), 놓기(앞, x * 화, z * 화), 놓기(옆, y * 화, z * 화), float(z / max(x, y, z))
if __name__ == "__main__":
    import torch, torch.nn as nn, 학습 as T, 짓기 as J, 여섯방향 as S6, 입력51 as I, 천장쪼개기52 as C
    class 모(nn.Module):   # 학습69 와 같은 망
        def __init__(s): super().__init__(); s.u = T.U만들기(10)(); s.u.o = nn.Conv2d(32, 33, 1)
        def forward(s, x):
            u = s.u; a = u.e1(x); b_ = u.e2(u.p(a)); c = u.e3(u.p(b_)); d = u.e4(u.p(c))
            c2 = u.d3(torch.cat([u.u3(d), c], 1)); b2 = u.d2(torch.cat([u.u2(c2), b_], 1)); a2 = u.d1(torch.cat([u.u1(b2), a], 1)); return u.o(a2)
    m = 모().cuda(); m.load_state_dict(torch.load(O + "학습69_판0/망.pt")); m.eval(); 눈 = torch.eye(6, device="cuda")
    for p in sys.argv[1:]:
        이름 = os.path.splitext(os.path.basename(p))[0]; D = O + "실제입력/%s/" % 이름; os.makedirs(D, exist_ok=True)
        X, F, S, H = 그림셋(p); 몸, 길 = J.몸통37((X, F, S), H); 반 = [S6.반높이(몸, S6.R(*S6.방향[k])) for k in S6.방향]
        a = torch.tensor(I.하나((X, F, S, np.array(반, np.float32))), device="cuda").float()   # (6, 3, 128, 128)
        껍 = torch.where(a[:, 2] == 17, 32., a[:, 2] * 2); x = torch.cat([a[:, :1], a[:, 1:2], 껍[:, None] / 32, 껍[:, None] / 32, 눈[:, :, None, None].expand(-1, -1, N, N)], 1)
        with torch.no_grad(): 층 = torch.maximum(m(x).argmax(1), 껍.long()).cpu().numpy()
        틀 = J.점유_캐드(몸); w = {d: np.where(층[j] == 32, np.nan, h - 층[j] * (2 * h / 32)) for j, (d, h) in enumerate(zip(S6.방향, 반))}; v = C.깎(틀, w, 48, False, 반)
        np.save(D + "칸.npy", v); np.save(D + "틀.npy", 틀); cv2.imencode(".png", 255 - 255 * np.concatenate([X, F, S], 1))[1].tofile(D + "입력.png")
        print(이름, "몸통", 길, "틀 칸", int(틀.sum()), "깎은 칸", int(v.sum()), flush=True)
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes
        plt.rcParams["font.family"] = "Malgun Gothic"; 빛 = matplotlib.colors.LightSource(315, 40)
        def 칸면(b, v, 색):   # 그림63.칸면 과 같음(그림63 은 가져오면 그림 전체를 굽는다)
            vs, fs, _, _ = marching_cubes(np.pad(v, 1).astype(np.float32), .5); b.add_collection3d(Poly3DCollection(((vs - .5) / 48 * 1.1 - .55)[fs], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
        원 = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)[..., ::-1]; 장 = 36
        for t in range(장):
            f = plt.figure(figsize=(12, 8)); q = f.add_subplot(2, 1, 1); q.imshow(원); q.set_axis_off(); q.set_title("입력 그림 (정답 없음)", fontsize=14)
            for j, (제, 색, 칸) in enumerate([("세 장 윤곽 교차 (틀)", "#cfcfcf", 틀), ("판0 · 32 단계 깎기", "#e8c06a", v)]):
                b = f.add_subplot(2, 2, 3 + j, projection="3d"); b.set_axis_off(); b.set_box_aspect((1, 1, 1)); b.set_xlim(-.55, .55); b.set_ylim(-.55, .55); b.set_zlim(-.55, .55); b.view_init(28, -50 + 360 * t / 장); 칸면(b, 칸, 색); b.set_title(제, fontsize=13)
            plt.tight_layout(); f.savefig(D + "%02d.png" % t, dpi=60); plt.close(f)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", D + "%02d.png", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-crf", "20", D + "돌림.mp4"], check=True)
