# -*- coding: utf-8 -*-
"""**천이냐 딱딱함이냐** — `재질.py` 를 넷 부류(천 · 피부 · 머리카락 · 딱딱함)로 넓힌다.

    python 재질넷.py 정답                     VRoid 11장 판(재질.py 정답 그대로) + 딱딱한 물건 25장 판 -> out/재질넷/
    py -3.11 재질넷.py 모델 <siglip|qwen> [맥락]
    python 재질넷.py 판정                     -> out/기록/재질넷_<날짜>.json
    python 재질넷.py 그림                     -> out/재질넷_그림.png

함수는 전부 `재질.py` 것이다 — 여기선 부류 목록 · 문장 · 케이스 목록 · 출력 폴더만 바꾼다.

## 정답 — 딱딱함은 **물건 단위**다 (사람이 판마다 찍은 게 아니다)

재질 이름에 「금속」이 적힌 모델이 벤치에 없다. 그래서 **원본 에셋 이름**으로 물건 전체를 딱딱함으로 둔다:
mech 5 · robot 5 · 궤짝 2 · 클로시 1 · 조각상·건물 4 · Google Scanned Objects 8 (도자기 · 플라스틱 · 금속 · 버들 바구니).
사람이 판마다 표시한 정답이 아니다. 로봇에 천 조각이 붙어 있어도 딱딱함으로 센다 — 그 몫이 정답 흠이다.
기사 · 마법사 · 괴물(갑옷 + 천이 섞임)은 뺐다. 천 · 피부 · 머리카락은 `재질.py` 의 VRoid 정답 그대로다.

## ⚠ 뒤섞인 변수 — 돌리기 전에 적는다

딱딱한 물건은 **그림 결이 다르다.** VRoid 는 애니 텍스처, Poly Pizza 는 로우폴리 단색, 스캔은 회색에 촘촘한 면 선이다.
모델이 재질이 아니라 **그림 결**로 가를 수 있다. 이 시험은 그걸 못 막는다 — 그래서 판정을 둘로 가른다.

## 판정 — 돌리기 전에 적는다 (2026-09-13 저녁)

    전체     36장 케이스 평균으로 대조군 둘(다수결 · 색)을 이기고 과반 케이스에서 이긴다
    무리별   VRoid 11장 안에서도, 딱딱한 25장 안에서도 **따로** 색 대조군을 평균 · 과반으로 이긴다
    통과 = 전체와 무리별 둘 다

**무리별에서 다수결을 뺐다 (대조군만 돌려 보고 고침 · 모델 점수는 안 봄).** 처음엔 무리별도 대조군 둘이었다.
그런데 다수결은 딱딱한 물건 면적이 커서 **늘 「딱딱함」**을 답하고, 그러면 무리 안에서 VRoid 0.000 · 딱딱함 1.000 이다 —
딱딱함 무리에서 1.000 은 **아무 모델도 못 넘는다.** 무리 안의 다수결은 0 아니면 1 이라 정보가 없다. 전체 판정엔 그대로 둔다.
대조군만 돌린 값: 전체 다수결 0.694 · 색 0.265 / VRoid 색 0.608 / 딱딱함 색 0.114.

같이 적는 것: **천 -> 딱딱함** 으로 읽은 면적 비율(VRoid) · **딱딱함 -> 천** 비율(딱딱한 물건).
모델은 맥락 판본(판 bbox 3배 창 · 주변 60% 흐리게 · 빨간 테)이 본선, 판 조각만 준 판본은 참고로 siglip 만.
qwen 동의어: metal · plastic · wood · stone · ceramic · porcelain · glass -> 딱딱함 (돌리기 전에 정함).
"""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 재질 as R

SRC = R.OUT                                                      # 세 부류 판정의 판 · 조각
OUT = os.path.join(R.HERE, "out", "재질넷")
VROID = list(R.CASES)
HARD = ["cloak_Chest_Closed_AngpV0HxD8", "cloak_Chest_O72u4Drp8k", "cloak_Cloche_Qz9XMYysBQ",
        "mech_Drill_8uBbH7Dvmb", "mech_Mech_4UvIHxnoSR", "mech_Mech_D5wW2jDO42", "mech_Mech_o3Ps8z8ByP",
        "mech_Mech_tLs9mFVCSU", "robot_Animated_Robot_QCm7qe9uNJ", "robot_Robot_Enemy_1gNo5ezvmr",
        "robot_Robot_Enemy_Flying_lF3jeRJwiH", "robot_Robot_Enemy_Legs_Gun_lFZfDh2hzP", "robot_Robot_ejDr8lRglP",
        "statue_Fox_Statue_abxyXID5EA", "statue_Stag_Statue_cKloIsNcT8", "statue_Town_Center_76GTkSh4KM",
        "statue_Town_Center_cuQuFJEIfH", "스캔_Target_Basket_Medium", "스캔_Threshold_Porcelain_Pitcher_White",
        "스캔_Threshold_Porcelain_Teapot_White", "스캔_Toys_R_Us_Treat_Dispenser_Smart_Puzz",
        "스캔_Toysmith_Windem_Up_Flippin_Animals_D", "스캔_TriStar_Products_PPC_Power_Pressure_",
        "스캔_Victor_Reversible_Bookend", "스캔_Vtech_Stack_Sing_Rings_636_Months"]


def setup():
    """`재질.py` 의 전역만 넷 부류로 바꾼다. 부류 번호 0~2 는 그대로 — VRoid 정답을 옮겨 쓴다."""
    R.OUT = OUT
    R.NAMES = ["천", "피부", "머리카락", "딱딱함"]
    R.EN = ["cloth", "skin", "hair", "hard"]
    R.SYN = {w: 3 for w in ("metal", "plastic", "wood", "stone", "ceramic", "porcelain", "glass")}
    R.EN_LONG = ["clothing fabric", "bare skin", "hair", "hard material such as metal, plastic, wood or stone"]
    old = "cloth, skin, or hair."
    new = "cloth, skin, hair, or hard (metal, plastic, wood, stone)."
    assert old in R.ASK and old in R.ASK_CTX, "재질.py 의 질문 문장이 바뀌었다"
    R.ASK, R.ASK_CTX = R.ASK.replace(old, new), R.ASK_CTX.replace(old, new)
    R.CASES = VROID + HARD


def build():
    import cv2
    import numpy as np
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open(os.path.join(SRC, "판.jsonl"), encoding="utf-8")]
    items = [json.loads(l) for l in open(os.path.join(SRC, "판_맥락.jsonl"), encoding="utf-8")]
    for r in rows:                                               # VRoid — 조각을 그대로 옮긴다
        os.makedirs(os.path.dirname(os.path.join(OUT, r["key"])), exist_ok=True)
        shutil.copyfile(os.path.join(SRC, r["key"]), os.path.join(OUT, r["key"]))
    for it in items:
        os.makedirs(os.path.dirname(os.path.join(OUT, it["key"])), exist_ok=True)
        shutil.copyfile(os.path.join(SRC, it["key"]), os.path.join(OUT, it["key"]))
    print("  VRoid 판 %d 옮김" % len(rows))
    for case in HARD:
        n0 = len(rows)
        for d in (os.path.join(OUT, case), os.path.join(OUT, "맥락", case)):
            os.makedirs(d, exist_ok=True)
        for v in ("front", "side", "back"):
            lab, img = R.view_data(case, v)
            for k in np.unique(lab):
                if k == 0:
                    continue
                m = lab == k
                if m.sum() < R.MIN_PX:
                    continue
                name = "%s_%d.png" % (v, k)
                cv2.imencode(".png", R.masked_tile(img, m))[1].tofile(os.path.join(OUT, case, name))
                cv2.imencode(".png", R.context_tile(img, m))[1].tofile(os.path.join(OUT, "맥락", case, name))
                lab_c = cv2.cvtColor(np.uint8([[img[m].mean(0)]]), cv2.COLOR_BGR2LAB)[0, 0].tolist()
                key = "%s/%s" % (case, name)
                rows.append({"key": key, "case": case, "view": v, "k": int(k), "area": int(m.sum()), "gt": 3,
                             "lab": lab_c})
                items.append({"key": "맥락/" + key, "members": [key]})
        print("  %-40s 판 %d" % (case, len(rows) - n0), flush=True)
    with open(os.path.join(OUT, "판.jsonl"), "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    with open(os.path.join(OUT, "판_맥락.jsonl"), "w", encoding="utf-8") as f:
        f.writelines(json.dumps(it, ensure_ascii=False) + "\n" for it in items)
    import collections
    print("  판 %d · 정답 %s" % (len(rows), dict(collections.Counter(R.NAMES[r["gt"]] for r in rows))))


def judge():
    import numpy as np
    rows = R.load_rows()
    preds = R.all_preds(rows)
    groups = {"전체": VROID + HARD, "VRoid": VROID, "딱딱함": HARD}
    tab = {g: {k: np.array([R.score([r for r in rows if r["case"] == c], v) for c in cs]) for k, v in preds.items()}
           for g, cs in groups.items()}
    area = lambda rr: float(sum(r["area"] for r in rr)) or 1.0
    verdict = {}
    for g, cs in groups.items():
        n = len(cs)
        print("\n  [%s] %d 장 · 판 면적 가중 정답률 (기권 1/4)" % (g, n))
        for k in preds:
            t = tab[g][k]
            line = "    %-12s 평균 %.3f" % (k, t.mean())
            if k not in ("다수결", "색"):
                ctrl = ("다수결", "색") if g == "전체" else ("색",)          # 무리 안 다수결은 0 아니면 1 — docstring
                wins = [(t - tab[g][c]).mean() > 0 and (t > tab[g][c]).sum() > n / 2 for c in ctrl]
                verdict.setdefault(k, {})[g] = all(wins)
                line += " · 다수결 대비 %+.3f (%d/%d) · 색 대비 %+.3f (%d/%d) · %s" % (
                    (t - tab[g]["다수결"]).mean(), (t > tab[g]["다수결"]).sum(), n,
                    (t - tab[g]["색"]).mean(), (t > tab[g]["색"]).sum(), n, "이김" if all(wins) else "짐")
            print(line)
    print("\n  천이냐 딱딱함이냐 — 면적 비율")
    cloth = [r for r in rows if r["gt"] == 0]
    hard = [r for r in rows if r["gt"] == 3]
    for k, v in preds.items():
        c2h = sum(r["area"] for r in cloth if v.get(r["key"], -1) == 3) / area(cloth)
        h2c = sum(r["area"] for r in hard if v.get(r["key"], -1) == 0) / area(hard)
        h_ok = sum(r["area"] for r in hard if v.get(r["key"], -1) == 3) / area(hard)
        print("    %-12s 천 -> 딱딱함 %.3f · 딱딱함 -> 천 %.3f · 딱딱함 맞힘 %.3f" % (k, c2h, h2c, h_ok))
    print("\n  판정 (전체 · VRoid · 딱딱함 셋 다 이겨야 통과)")
    for k, d in verdict.items():
        print("    %-12s %s · %s" % (k, " · ".join("%s %s" % (g, "O" if ok else "X") for g, ok in d.items()),
                                    "**통과**" if all(d.values()) else "**짐**"))
    for k, v in preds.items():
        cm = np.zeros((4, 5), int)
        for r in rows:
            cm[r["gt"], v.get(r["key"], -1)] += 1
        print("    %-12s 혼동 (행 정답 · 열 천/피부/머리/딱딱/기권) %s" % (k, cm.tolist()))
    os.makedirs(R.REC, exist_ok=True)
    p = os.path.join(R.REC, "재질넷_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"),
               "판정": {k: {**d, "통과": all(d.values())} for k, d in verdict.items()},
               "점수": {g: {k: v.tolist() for k, v in t.items()} for g, t in tab.items()}},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, R.HERE))


def figure():
    """규칙으로 고른 6장 — VRoid 는 천 면적이 큰 3장, 딱딱함은 본선 모델 점수 최고 · 중앙 · 최저 3장."""
    rows = R.load_rows()
    preds = R.all_preds(rows)
    main = "siglip_맥락" if "siglip_맥락" in preds else [k for k in preds if k not in ("다수결", "색")][0]
    cloth_area = {c: sum(r["area"] for r in rows if r["case"] == c and r["gt"] == 0) for c in VROID}
    v3 = sorted(VROID, key=lambda c: -cloth_area[c])[:3]
    hs = sorted(HARD, key=lambda c: R.score([r for r in rows if r["case"] == c], preds[main]))
    h3 = [hs[-1], hs[len(hs) // 2], hs[0]]
    picks = [(c, "VRoid · 천 면적 큰 순") for c in v3] + \
            [(c, "딱딱함 · %s %s" % (main, w)) for c, w in zip(h3, ("최고", "중앙", "최저"))]
    models = [k for k in ("siglip_맥락", "qwen_맥락", "siglip") if k in preds]
    R.figure(models, picks=picks)


if __name__ == "__main__":
    setup()
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "모델":
        R.run_model(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif what == "정답":
        build()
    elif what == "판정":
        judge()
    elif what == "그림":
        figure()
    else:
        print(__doc__)
