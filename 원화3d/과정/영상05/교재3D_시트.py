# -*- coding: utf-8 -*-
"""교재 원그림 | 우리 3D 재현 | 설명 — 한 줄씩 쌓는 시트. python 교재3D_시트.py <차수>"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
G = r"G:\art2real\out\영상05\교재그림"; D = r"G:\art2real\out\영상05\3D"; BG = (20, 20, 28)
B = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 34); R = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 26); S = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 20)
def ld(p, bg=BG):
    im = Image.open(p).convert("RGBA"); b = Image.new("RGBA", im.size, bg + (255,)); return Image.alpha_composite(b, im).convert("RGB")
def fit(im, w, h):
    im = im.copy(); im.thumbnail((w, h)); return im
def row(title, src_img, src_cap, ours, lines, H=520):
    W = 2000; r = Image.new("RGB", (W, H + 230), BG); d = ImageDraw.Draw(r)
    d.text((24, 14), title, fill=(255, 200, 120), font=B)
    a = fit(ld(os.path.join(G, src_img), (255, 255, 255)), 560, H - 80); d.rectangle([20, 70, 600, 70 + H - 60], fill=(255, 255, 255)); r.paste(a, (20 + (580 - a.width) // 2, 70 + (H - 60 - a.height) // 2))
    d.text((24, H + 18), "교재: " + src_cap, fill=(150, 150, 160), font=S)
    ims = [ld(os.path.join(D, p)) for p in ours]; ws = (W - 660) // len(ims)
    for k, im in enumerate(ims):
        im = fit(im, ws - 10, H - 60); r.paste(im, (640 + k * ws + (ws - im.width) // 2, 70 + (H - 60 - im.height) // 2))
    d.text((640, H + 18), "우리 3D", fill=(150, 150, 160), font=S)
    for k, l in enumerate(lines): d.text((24, H + 60 + k * 38), l, fill=(235, 235, 240), font=R)
    return r
def sheet(rows, out):
    h = sum(r.height for r in rows); s = Image.new("RGB", (2000, h), BG); y = 0
    for r in rows: s.paste(r, (0, y)); y += r.height
    s.save(out, quality=88); print(out, s.size)
if __name__ == "__main__" and sys.argv[1:] == ["1"]:
    sheet([
        row("① 지온 만들기 — 원통 하나에서 네 가지만 바꾼다", "crop_지온01c.png", "Biederman 1987 p8",
            ["g1_지온만들기.png"],
            ["왼쪽부터: 원통(기준) · 단면 모서리를 곧게 → 각기둥 · 굵기를 줄여 → 뿔 · 축을 굽혀 → 휜 관 · 가운데만 키워 → 통.",
             "Biederman: 이 몇 가지 성질(단면 · 대칭 · 굵기 변화 · 축)은 어느 각도에서 봐도 잘 안 바뀐다 → 덩어리 이름표가 된다.",
             "피규어로: 뿔 = 굵기 줄어든 곧은 쐐기 · 볼날개 = 휜 판 · 투구 = 커졌다 작아지는 돔."]),
        row("② 선 하나 없는 벌레가 「관」으로 보인다", "crop_아모달04b.png", "Tse 1999 Fig 11 p14",
            ["g2_벌레_그림.png", "g2_벌레_3D.png"],
            ["왼쪽: 교재처럼 검은 면 + 앞을 지나는 세로선 둘. 음영 · 무늬가 하나도 없다.",
             "오른쪽: 같은 것을 돌려 보면 우리가 「보았다」고 느낀 둥근 관. 눈은 윤곽선이 아니라 덩어리(부피)를 채운다(Tse).",
             "피규어로: 원화의 납작한 색 면도 사람은 이미 둥근 팔 · 둥근 투구로 읽는다 — 그 둥글기는 그림에 없고 눈이 넣은 것."]),
        row("③ 같은 선화, 다른 입체", "crop_아모달10.png", "Malik 1987 Fig 31 p27",
            ["g3_선화_그시점_0.png", "g3_선화_그시점_1.png", "g3_선화_그시점_2.png", "g3_선화_돌림_0.png", "g3_선화_돌림_1.png", "g3_선화_돌림_2.png"],
            ["왼쪽 셋(이 시점): 셋 다 똑같은 정육면체 선화. 오른쪽 셋(75° 돌림): 상자 · 뒤틀린 철사 · 찌그러진 틀 — 전혀 다른 입체.",
             "꼭짓점을 「시선 방향으로만」 앞뒤로 밀었기 때문 — 그 카메라에서는 선이 한 픽셀도 안 바뀐다.",
             "Malik: 「많은 모양이 같은 선화로 투영된다」 · 사람이 상자로 보는 건 「반듯한 모양」을 고르는 눈의 습관(prior)."]),
    ], os.path.join(D, "교재3D_1차.jpg"))
if __name__ == "__main__" and sys.argv[1:] == ["2"]:
    sheet([
        row("④ 같은 윤곽, 다른 부품 — 얼굴 옆선을 돌려 깎은 꽃병", "crop_지온03.png", "Hoffman & Richards 1984 Fig 12 p18",
            ["g4_술잔_정면.png", "g4_술잔_3D.png"],
            ["얼굴 옆선(이마 · 코 · 입술 · 턱)을 반지름으로 삼아 선반처럼 돌려 깎았다. 정면에서는 흰 꽃병도, 검은 마주 보는 얼굴 둘도 된다.",
             "Hoffman: 부품 경계(오목한 점)는 「어느 쪽이 앞(전경)이냐」에 따라 뒤집힌다 — 꽃병이면 받침 · 줄기 · 그릇, 얼굴이면 이마 · 코 · 입술.",
             "피규어로: 원화 윤곽의 오목점에서 부품을 자르려면, 먼저 덮음 순서(무엇이 앞 판인가)를 정해야 한다."]),
        row("⑤ 오목부 선을 지우면 못 읽고, 가리면 읽는다", "crop_지온01b.png", "Biederman 1987 Fig 25–26 p28–29",
            ["g5_손전등_선.png", "g5_손전등_지움.png", "g5_손전등_가림.png"],
            ["왼쪽: 손전등 3D 를 선으로 렌더. 가운데: 덩어리 이음매(몸통-머리 · 버튼 · 끝마개) 여섯 곳의 선을 지움. 오른쪽: 같은 자리 · 같은 크기를 회색 판으로 덮음.",
             "지우면 이음매에서 선이 그냥 끊겨 덩어리가 안 나뉜다. 덮으면 선이 판 가장자리에서 T 자로 멈춰 「뒤로 이어진다」고 읽힌다.",
             "정직하게: 우리 판은 지운 양이 적어 지운 쪽도 아직 손전등으로 읽힌다 — 교재(Fig 25)는 훨씬 많이 지웠다."]),
        row("⑥ 선 몇 개가 입체를 바꾼다 — 윤곽만 vs 「거의 윤곽」 선", "crop_아모달12.png", "DeCarlo 외 2003 Fig 1 p1",
            ["g6_수잔_윤곽만.png", "g6_수잔_암시.png"],
            ["블렌더 원숭이 머리(수잔)를 Freestyle 로 선 렌더. 왼쪽: 바깥 윤곽선만. 오른쪽: 시점을 조금만 바꾸면 윤곽이 될 자리(suggestive contour)를 더함.",
             "눈두덩 · 귀 안쪽 · 콧구멍이 생기면서 납작한 판이 둥근 머리로 읽힌다. 같은 3D 인데 선 종류만 바꿨다.",
             "피규어로: 원화의 선이 「실루엣」인지 「거의 윤곽」인지 가려야 깊이를 잘못 읽지 않는다(우리 추론)."]),
    ], os.path.join(D, "교재3D_2차.jpg"))
