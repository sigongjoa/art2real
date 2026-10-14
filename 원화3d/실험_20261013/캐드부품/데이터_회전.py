# 판정기준39 — 앞 · 옆 그림을 90° 세워(회전) 위 그림 칸에 맞춘 높이 두 장 · 정답 안 봄 · 10-14
# 위 칸 (r, c): 좌우 = c → 앞 그림 c 열 · 앞뒤 y = −u[r] = u[127 − r] → 옆 그림 127 − r 열 · 높이 = 앞 · 옆 그림 행(위가 큼)
# 두 그림을 세워 겹친 틀에서 그 칸 기둥의 윗면 · 아랫면 → 부품 높이로 나눈 비율(윗면 깊이 = 데이터.py 의 D 와 같은 뜻)
import sys, numpy as np
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
O = "G:/art2real/out/설명/캐드부품/"
def 회전높이(F, S):   # → (2, 128, 128) float: [윗면 깊이, 아랫면 깊이] · 기둥이 비면 1, 1 · 그림이 비면 0, 0(정보 없음)
    try: Ff, Sf = W.바깥(F)[0], W.바깥(S)[0]
    except ValueError: return np.zeros((2, 128, 128), np.float16)
    occ = Ff[:, None, :] & Sf[:, ::-1][:, :, None]   # [높이행 k, 위 행 r, 위 열 c]
    k = np.nonzero(Ff.any(1) | Sf.any(1))[0]; k0, k1 = k.min(), k.max(); h = max(k1 - k0 + 1, 1)
    있 = occ.any(0); 위 = np.where(있, occ.argmax(0), k1 + 1); 아 = np.where(있, 127 - occ[::-1].argmax(0), k1 + 1)
    return np.stack([np.clip((위 - k0) / h, 0, 1), np.clip((아 - k0 + 1) / h, 0, 1)]).astype(np.float16)
if __name__ == "__main__":
    e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]
    R = np.stack([회전높이(F[i], S[i]) for i in range(len(F))]); np.savez_compressed(O + "데이터_회전.npz", R=R); print("ok", R.shape)
