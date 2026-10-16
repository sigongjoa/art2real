# 68 편(숨은선) 카드 재료 — 실제 부품 9806(나사 이음) · 5926(컵): 3/4 음영 렌더 + 위 · 앞 · 옆 선 그림(검정 보이는 · 빨강 숨은) 두 규칙(꺾임 포함 · 끊김만) → 투명 PNG · 10-16
# 사용(venv): 재료68.py → out/영상05/대화/68_숨은선/자료/<부품>_{렌더,꺾임_위,꺾임_앞,꺾임_옆,끊김_위,…}.png
import sys, json, numpy as np, cv2
sys.path.insert(0, "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/1b9641c4-09e3-416a-8c59-c894cf94f212/scratchpad/숨은선_실물")
import 층애니 as L, 숨은선 as H
from 데이터_앞옆 import 선그림
from PIL import Image
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/영상05/대화/68_숨은선/자료/"
if __name__ == "__main__":
    목 = json.load(open(O + "목록.json", encoding="utf-8"))
    for i in (9806, 5926):
        sc, 광, 입 = L.장면(목[i]); r = np.array(입.convert("L")); a = np.where(r < 250, 255, 0).astype(np.uint8); Image.fromarray(np.dstack([np.repeat(r[..., None], 3, -1), a])).save(A + "%d_렌더.png" % i)
        for j, rr in enumerate(광):
            Ls = H.벗기기(sc, rr); 보 = 선그림(*Ls[0]) > 0; 번 = cv2.dilate(보.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            for 규칙, 이름 in ((선그림, "꺾임"), (H.끊김선, "끊김")):
                숨 = np.zeros_like(보)
                for t, S in Ls[1:]: 숨 |= 규칙(t, S) > 0
                숨 &= ~번; c = np.zeros((128, 128, 4), np.uint8); c[숨] = (220, 50, 50, 255); c[보] = (40, 40, 50, 255)
                Image.fromarray(c).resize((512, 512), Image.NEAREST).save(A + "%d_%s_%s.png" % (i, 이름, ("위", "앞", "옆")[j]))
    print("ok")
