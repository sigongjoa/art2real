# -*- coding: utf-8 -*-
"""**GPT 가 부품 깊이를 얼마나 맞히나** — 도면 스키마의 「깊이」 칸 출처를 정한다 (2026-09-22).

    python 깊이추정.py            얼린 10 케이스 전부 -> out/기록/깊이추정_<때>.json · out/깊이추정/<케이스>_번호.png
    python 깊이추정.py <케이스>    한 케이스만
    python 깊이추정.py 웹 <답.json> <모델>   채팅 웹에서 받은 답을 같은 자로 채점 (API 크레딧이 없을 때)

사용자(09-22): 「디자인은 gpt 가 하고 gpt 가 뱉은 추정치에 검산 및 보정한다」 · 「그림은 수치가 없다」

도면에서 **정면 그림으로 못 재는 칸은 깊이 하나**다. 그 칸을 GPT 추정으로 채울지, 비율 사전으로 채울지를
설계 단계에서 싸게 잰다. 정답 = 벤치 `truth.glb` 의 연결 덩어리(부품)마다 앞뒤 두께.

    입력    정면 판(`시트` 셀 렌더 = 원화 흉내) 위에 부품 번호 + 표(번호 · 정면 폭 mm · 높이 mm) · 전체 키 150 mm
            폭 · 높이는 앱에서 그림으로 잴 값이라 **정답을 준다** (깊이만 묻는다)
    GPT     gpt-5.5 · 부품마다 depth_mm
    대조    비율 사전 = 깊이/폭 의 중앙값, **다른 케이스들에서만** 뽑는다 (leave-one-case-out)
    자      e = |ln(예측/정답)|  (두 배 틀림 = 0.69 · 25% 틀림 = 0.22)

문턱을 **돌리기 전에** 적는다. 집계 = 모든 부품을 모은 중앙값 · 케이스 승 = 케이스 안 중앙값 비교:

    Q1  GPT 의 e 중앙값 < 비율 사전의 e 중앙값  **그리고**  케이스 10 중 6 이상에서 GPT 가 이긴다
    Q2  GPT 의 e 중앙값 <= 0.22 (25% 안 — 노란 칸 제안값으로 쓸 만하다)

    Q1 짐         -> 깊이 칸 기본값 = 비율 사전. GPT 숫자는 도면에 안 쓴다
    Q1 이김 Q2 짐 -> GPT 제안을 쓰되 **항상 노란 칸** (사람 확인 필수)
    둘 다 이김    -> GPT 제안을 기본값으로 (그래도 출처 태그는 guessed)
"""
import base64
import json
import os
import sys
import time
import urllib.request

os.environ.setdefault("OMP_NUM_THREADS", "2")
import cv2
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
import win as W
import 시트 as S

HERE = r"G:\art2real\원화3d"
OUT = os.path.join(HERE, "out")
D = os.path.join(OUT, "깊이추정")
키mm = 150.0
모델 = "gpt-5.5"
최소몫, 최소화소, 최대부품 = 0.01, 400, 12
# 얼린 집합 — 부품 4 개 이상인 메카 · 로봇 · 기사 · 괴물 (피규어 키트의 본 영역). 돌린 뒤 바꾸지 않는다.
케이스들 = ["mech_Mech_4UvIHxnoSR", "mech_Mech_D5wW2jDO42", "mech_Mech_o3Ps8z8ByP", "mech_Mech_tLs9mFVCSU",
         "mech_Drill_8uBbH7Dvmb", "robot_Robot_ejDr8lRglP", "robot_Robot_Enemy_Flying_lF3jeRJwiH",
         "knight_Characters_Matt_66kQ4dBBC7", "knight_Character_Animated_DgOCW9ZCRJ", "monster_Mimic_B8HrWzkuNp"]


def 부품표(case):
    """truth.glb -> 정면에 보이는 부품마다 {폭 · 높이 · 깊이 mm, 번호 자리}. 좌표 = 창 규약(z 위 · 앞이 −y)."""
    t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh", process=False)
    V, F = np.asarray(t.vertices, np.float64), np.asarray(t.faces, np.int64)
    fc = trimesh.graph.connected_component_labels(trimesh.Trimesh(V, F).face_adjacency, node_count=len(F))
    넓이 = trimesh.Trimesh(V, F, process=False).area_faces
    mm = 키mm / (V[:, 2].max() - V[:, 2].min())
    _, ident = S.draw(V, F, np.full((len(F), 3), 200, np.uint8), np.zeros(len(F), np.int32), "front", line=False)
    보임 = np.where(ident >= 0, fc[np.clip(ident, 0, None)], -1)
    줄 = []
    for c in np.unique(fc):
        if 넓이[fc == c].sum() < 최소몫 * 넓이.sum():
            continue
        m = 보임 == c
        if m.sum() < 최소화소:
            continue
        p = V[np.unique(F[fc == c])]
        dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
        y, x = np.unravel_index(dt.argmax(), dt.shape)
        e = (p.max(0) - p.min(0)) * mm
        줄.append({"덩어리": int(c), "폭": round(float(e[0]), 1), "높이": round(float(e[2]), 1),
                  "깊이": round(float(e[1]), 1), "화소": int(m.sum()), "자리": [int(x), int(y)]})
    줄 = sorted(줄, key=lambda r: -r["화소"])[:최대부품]
    for i, r in enumerate(줄, 1):
        r["번호"] = i
    return 줄


def 번호판(case, 줄):
    im = cv2.imdecode(np.fromfile(os.path.join(OUT, "시트", case, "front.png"), np.uint8), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:
        a = im[:, :, 3:] / 255.0
        im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    im = cv2.resize(im, (W.RES, W.RES)) if im.shape[0] != W.RES else im.copy()
    for r in 줄:
        x, y = (int(np.clip(v, 14, W.RES - 15)) for v in r["자리"])   # 창에 잘린 부품은 번호를 안쪽으로
        cv2.circle(im, (x, y), 11, (255, 255, 255), -1)
        cv2.circle(im, (x, y), 11, (40, 40, 220), 2)
        s = str(r["번호"])
        cv2.putText(im, s, (x - 5 * len(s), y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 220), 1, cv2.LINE_AA)
    os.makedirs(D, exist_ok=True)
    p = os.path.join(D, case + "_번호.png")
    cv2.imencode(".png", im)[1].tofile(p)
    return p


def 열쇠():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    import glob
    for p in glob.glob(r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\*\scratchpad\oai.key"):
        return open(p).read().strip()
    raise SystemExit("OPENAI_API_KEY 없음")


def 묻기(png, 줄):
    표 = "\n".join("%d: width %.1f mm, height %.1f mm" % (r["번호"], r["폭"], r["높이"]) for r in 줄)
    글 = ("This is an orthographic FRONT view of a figure (character/mecha) that will be 3D printed at a total "
          "height of %.0f mm. Numbered circles mark separate parts. For each part I give its measured front-view "
          "width and height. Estimate each part's DEPTH: its front-to-back thickness in mm (the dimension "
          "along the viewing direction, not visible in this image).\n\n%s\n\n"
          "Answer with JSON only: {\"parts\": [{\"id\": 1, \"depth_mm\": 12.3}, ...]}" % (키mm, 표))
    b64 = base64.b64encode(open(png, "rb").read()).decode()
    body = {"model": 모델, "input": [{"role": "user", "content": [
        {"type": "input_text", "text": 글},
        {"type": "input_image", "image_url": "data:image/png;base64," + b64}]}],
        "text": {"format": {"type": "json_object"}}}
    rq = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode(),
                                headers={"Authorization": "Bearer " + 열쇠(), "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(rq, timeout=600))
    txt = "".join(c.get("text", "") for o in r["output"] if o.get("type") == "message" for c in o["content"])
    return {int(p["id"]): float(p["depth_mm"]) for p in json.loads(txt)["parts"]}


def e(p, t):
    return abs(np.log(max(p, 0.1) / max(t, 0.1)))


def main(only=None):
    cases = [only] if only else 케이스들
    표들, 답들 = {}, {}
    for c in cases:
        t0 = time.time()
        줄 = 부품표(c)
        png = 번호판(c, 줄)
        답들[c] = 묻기(png, 줄)
        표들[c] = 줄
        print("  %-40s 부품 %2d  %.0f초" % (c, len(줄), time.time() - t0), flush=True)
    채점(cases, 표들, 답들, 모델)


def 웹(답json, 모델명):
    """API 대신 채팅 웹에서 받은 답(`{케이스: {번호: 깊이}}`)을 같은 자로 채점한다."""
    표들 = json.load(open(os.path.join(D, "정답표.json"), encoding="utf-8"))
    답들 = {c: {int(k): v for k, v in d.items()} for c, d in json.load(open(답json)).items()}
    채점(케이스들, 표들, 답들, 모델명)


def 채점(cases, 표들, 답들, 모델명):
    기록 = {"모델": 모델명, "케이스": {}}
    모든g, 모든p, 승 = [], [], 0
    for c in cases:
        남 = [r["깊이"] / max(r["폭"], 0.1) for k in 표들 if k != c for r in 표들[k]]
        비 = float(np.median(남)) if 남 else 1.0
        eg = [e(답들[c].get(r["번호"], r["폭"]), r["깊이"]) for r in 표들[c]]
        ep = [e(비 * r["폭"], r["깊이"]) for r in 표들[c]]
        모든g += eg; 모든p += ep
        이김 = bool(np.median(eg) < np.median(ep)); 승 += 이김
        기록["케이스"][c] = {"비율": 비, "e_gpt": float(np.median(eg)), "e_사전": float(np.median(ep)), "gpt승": 이김,
                        "부품": [dict(r, gpt=답들[c].get(r["번호"])) for r in 표들[c]]}
        print("  %-40s GPT %.3f  사전 %.3f  %s" % (c, np.median(eg), np.median(ep), "GPT" if 이김 else "사전"))
    mg, mp = float(np.median(모든g)), float(np.median(모든p))
    Q1 = mg < mp and 승 >= 0.6 * len(cases)
    Q2 = mg <= 0.22
    기록["요약"] = {"부품수": len(모든g), "e_gpt": mg, "e_사전": mp, "GPT승": 승, "케이스": len(cases), "Q1": Q1, "Q2": Q2}
    print("\n부품 %d · e 중앙값 GPT %.3f · 사전 %.3f · GPT 승 %d/%d · Q1 %s · Q2 %s"
          % (len(모든g), mg, mp, 승, len(cases), Q1, Q2))
    p = os.path.join(OUT, "기록", "깊이추정_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(기록, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "웹":                  # python 깊이추정.py 웹 <답.json> <모델 이름>
        웹(a[1], a[2])
    else:
        main(a[0] if a else None)
