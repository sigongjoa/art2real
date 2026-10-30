# 큰 모델 시험(도구 팔)용: CadQuery 글 파일 → 입력과 같은 꼴의 세 방향 도면 PNG (위 · 앞 · 옆 · 보이는 선 검정 · 숨은선 회색 점선)
# 사용: python 세뷰보기.py 코드.py 나옴.png  — 글은 result(cq.Workplane)를 만들면 됨 · place(w, 축, 자리) 도 쓸 수 있음
import os, sys, numpy as np
os.environ["ART_CL"] = "0"; sys.path[:0] = ["G:/art2real/하네스", "G:/art2real/원화3d/실험_20261013/캐드부품"]
if __name__ == "__main__":
    import 코드글, 설계116 as S, 모델123 as T
    from PIL import Image, ImageDraw
    w = 코드글.실행(open(sys.argv[1], encoding="utf-8").read()); m = S.메시(w)[0]; ims = T.도면(m=m)
    판 = Image.new("RGB", (3 * 512 + 40, 560), "white"); d = ImageDraw.Draw(판)
    for v, (im, nm) in enumerate(zip(ims, ["TOP (view from +Z; right=+X, up=+Y)", "FRONT (view from +Y; right=+X, up=+Z)", "SIDE (view from +X; right=+Y, up=+Z)"])):
        판.paste(Image.fromarray(im).resize((512, 512), Image.NEAREST), (v * 532, 40)); d.text((v * 532 + 5, 10), nm, fill="black")
    판.save(sys.argv[2]); bb = w.val().BoundingBox()
    print(f"ok · 고체 {len(w.val().Solids())} · 부피 {w.val().Volume():.1f} · 상자 x {bb.xlen:.1f} y {bb.ylen:.1f} z {bb.zlen:.1f} → {sys.argv[2]}")
