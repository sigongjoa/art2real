# 1d 진짜 그림 — 메카2 머리 · 발 앞 그림 → 윤곽 바탕 + U-Net 깎을 자리 지도 → 다각형 깎기 → 렌더 · 10-13
import os, sys, json, subprocess, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 캐드점수2 as K, 학습3 as T, 학습4 as U, 진짜그림52 as R
A = "G:/art2real/out/설명/구멍/"; L = A + "학습4/"
if __name__ == "__main__":
    import torch, cadquery as cq
    m = U.U만들기()(); m.load_state_dict(torch.load(L + "망.pt", map_location="cpu")); m.eval(); im = np.asarray(Image.open(R.IMG).convert("RGB")); 기록 = {}
    for 이름, (r0, r1, c0, c1) in R.부위.items():
        x = R.입력(im[r0:r1, c0:c1])
        with torch.no_grad(): 지도 = m(torch.tensor(x[None])).argmax(1)[0].numpy().astype(np.uint8)
        Image.fromarray((지도 * 120).astype(np.uint8)).save(L + "진짜지도_%s.png" % 이름); 바 = T.바탕맞춤(x)
        cq.exporters.export(U.다각깎기(바, 지도), A + "r54_진짜_%s.stl" % 이름, tolerance=0.01, angularTolerance=0.05)
        기록[이름] = {"구멍화소": int((지도 == 1).sum()), "홈화소": int((지도 == 2).sum())}; print(이름, 기록[이름])
    subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "렌더_빛.py", "--", "54_진짜_머리", "54_진짜_발"], check=True, stdout=subprocess.DEVNULL)
    json.dump(기록, open(L + "진짜.json", "w", encoding="utf-8"), ensure_ascii=False)
