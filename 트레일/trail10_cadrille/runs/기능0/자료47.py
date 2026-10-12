# 쇼츠 47 · 48 재료 — 시험 #21 Robot Head(BY-NC-SA · 42 편 확인) · 선 그림 · 정답 깊이(선생) · 학생 깊이 · 교차 깊이 · 들어 올림 그림 · 10-12
import os, sys, numpy as np, torch, cv2
H = "G:/art2real/트레일/trail10_cadrille/runs/깊이학습"; sys.path.insert(0, H)
from 학습 import 망
O = "G:/art2real/out/영상05/대화/47_증류/자료/"; os.makedirs(O, exist_ok=True)
X = np.load(os.path.join(H, "시험.npz"))["X"][21].astype(np.float32)
m = 망().cuda(); m.load_state_dict(torch.load(os.path.join(H, "모델T.pt"))); m.eval()
with torch.no_grad(): Z = m(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
def 쓰기(p, im): cv2.imencode(".png", im)[1].tofile(O + p)
def 깊(d, S):   # 가까움 = 밝음 · 실루엣 밖 흰색
    v = np.clip(1 - d, 0, 1); lo, hi = v[S].min(), v[S].max(); v = (v - lo) / max(hi - lo, 1e-6); c = cv2.applyColorMap((v * 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS); c[~S] = 255
    return cv2.resize(c, (512, 512), interpolation=cv2.INTER_NEAREST)
for k in (0, 2, 4):
    S = X[0][k] > .5; L = X[1][k] > .5
    쓰기("선_%d.png" % k, cv2.resize(np.where(L, 30, 255).astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST))
    쓰기("정답_%d.png" % k, 깊(X[3][k], S)); 쓰기("학생_%d.png" % k, 깊(Z[k], S)); 쓰기("교차_%d.png" % k, 깊(X[2][k], S))
print("ok", O)
