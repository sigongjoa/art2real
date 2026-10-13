# 로드맵 원칙 4 — 판마다 진짜 그림 묶음(메카2 머리 · 발 앞 그림)을 학습한 모델 입구에 넣고 결과를 그대로 · 10-13
# venv python 진짜그림52.py → out/설명/구멍/학습2/진짜_머리.png · 진짜_발.png · 진짜.json(코드)
import os, sys, json, subprocess, shutil, numpy as np, cv2
from PIL import Image
H_ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H_)
import 캐드점수2 as K, 학습2 as T
A = "G:/art2real/out/설명/구멍/"; L = A + "학습2/"; IMG = "G:/art2real/원화3d/out/도안생성/메카2/삼면.png"
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
부위 = {"머리": (20, 160, 200, 350), "발": (815, 975, 60, 250)}   # 그림짓기.py 와 같은 앞 그림 자르기

def 입력(rgb):   # 색 그림 → 학습 그림과 같은 꼴(검은 바탕 흰 선 128²) · 물체가 칸의 약 75 %
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); e = cv2.Canny(g, 60, 150); ys, xs = np.nonzero(e); e = e[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = int(max(e.shape) / .75); c = np.zeros((s, s), np.uint8); oy, ox = (s - e.shape[0]) // 2, (s - e.shape[1]) // 2; c[oy:oy + e.shape[0], ox:ox + e.shape[1]] = e
    c = cv2.dilate(cv2.resize(c, (128, 128), interpolation=cv2.INTER_AREA), np.ones((2, 2), np.uint8)); return (c > 40).astype(np.float32)

if __name__ == "__main__":
    import torch, cadquery as cq
    m = T.망만들기()(); m.load_state_dict(torch.load(L + "망.pt", map_location="cpu")); m.eval()
    im = np.asarray(Image.open(IMG).convert("RGB")); 기록 = {}
    for 이름, (r0, r1, c0, c1) in 부위.items():
        x = 입력(im[r0:r1, c0:c1]); Image.fromarray((x * 255).astype(np.uint8)).save(L + "진짜입력_%s.png" % 이름)
        with torch.no_grad(): bl, b, cl, cv = m(torch.tensor(x[None]))
        p = T.프로그램(bl[0].argmax(), b[0], cl[0].argmax(-1), cv[0]); 기록[이름] = {"코드": K.코드(p), "프로그램": p}
        cq.exporters.export(K.짓기(p), A + "r52_진짜_%s.stl" % 이름, tolerance=0.01, angularTolerance=0.05)
    subprocess.run([BL, "-b", "-P", os.path.join(H_, "렌더_빛.py"), "--"] + ["52_진짜_%s" % n for n in 부위], check=True, stdout=subprocess.DEVNULL)
    for n in 부위: shutil.copy(A + "빛_r52_진짜_%s.png" % n, L + "진짜_%s.png" % n)
    json.dump(기록, open(L + "진짜.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); [print(n, "\n" + v["코드"]) for n, v in 기록.items()]
