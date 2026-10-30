# 원화 시험(도구 팔)용: CadQuery 글 → 음영 렌더 네 각도(앞 · 옆 · 뒤 · 비스듬) PNG · 정답이 없는 그림이라 눈으로 원화와 비교
# 사용: python 모양보기.py 코드.py 나옴.png
import sys, numpy as np
sys.path[:0] = ["G:/art2real/하네스", "G:/art2real/원화3d/실험_20261013/캐드부품"]
if __name__ == "__main__":
    import 코드글, 설계116 as S, 데이터117 as Q
    from PIL import Image, ImageDraw
    w = 코드글.실행(open(sys.argv[1], encoding="utf-8").read()); m = S.메시(w)[0]
    각 = [("FRONT (from -Y)", 0, 5), ("SIDE (from +X)", 90, 5), ("BACK (from +Y)", 180, 5), ("3/4 view", 35, 25)]
    판 = Image.new("RGB", (4 * 400, 430), "white"); d = ImageDraw.Draw(판)
    for i, (nm, a, e) in enumerate(각):
        판.paste(Image.fromarray(Q.렌더(m, a, e, 400)[0]), (i * 400, 30)); d.text((i * 400 + 5, 8), nm, fill="black")
    판.save(sys.argv[2]); bb = w.val().BoundingBox()
    print(f"ok · 고체 {len(w.val().Solids())} · 상자 x {bb.xlen:.1f} y {bb.ylen:.1f} z {bb.zlen:.1f} → {sys.argv[2]}")
