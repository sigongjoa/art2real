# -*- coding: utf-8 -*-
"""로컬 눈 시험 — qwen2.5vl 이 캡처와 모델 렌더를 보고 형태 차이를 짚나 (2026-09-30 · 로컬 모델 테스트).
    python 로컬눈시험.py [모델]  -> 표준출력 · out/오메가몬2/블렌더/로컬눈시험.json
정답(Claude 가 먼저 적어 둔 것 · 사용자 동의 「형태가 이상하다」): ① 투구가 넓고 깊은 통(해골 · 항아리) ② 주둥이가 앞으로 안 나옴 ③ 볼 날개가 작음 ④ 눈 띠가 없음(구멍 두 개)."""
import os, sys, json, base64, io, time, urllib.request
import numpy as np, cv2
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(R, "out", "오메가몬2", "블렌더"); D = os.path.join(R, "out", "오메가몬2", "자료")
모델 = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5vl:7b"
기록 = json.load(open(os.path.join(D, "자료.json"), encoding="utf-8"))
def 잘라(t):
    im = cv2.imdecode(np.fromfile(기록[t]["파일"], np.uint8), cv2.IMREAD_COLOR); r = cv2.imdecode(np.fromfile(os.path.join(B, "렌더_%s.png" % t), np.uint8), cv2.IMREAD_UNCHANGED)
    x0, y0, x1, y1 = 기록[t]["상자"]; a = r[:, :, 3:4] / 255.0; rr = (np.full_like(im, 70) * (1 - a) + r[:, :, :3] * a).astype(np.uint8)
    return Image.fromarray(np.concatenate([im[y0:y1, x0:x1], rr[y0:y1, x0:x1]], 1)[:, :, ::-1])
def b64(p): p.thumbnail((1024, 1024)); b = io.BytesIO(); p.save(b, "JPEG", quality=88); return base64.b64encode(b.getvalue()).decode()
질문 = {
    "정면": ("02_정면", "Left: an anime frame of a robot knight head (Omnimon). Right: a grey 3D model render from the same camera. List the 3 biggest SHAPE differences of the 3D model compared with the anime head (proportions, what sticks out, what is missing). Be concrete, one line each."),
    "옆": ("02_옆", "Left: an anime frame of a robot knight head seen from the side. Right: a grey 3D model render from the same camera. List the 3 biggest SHAPE differences of the 3D model compared with the anime head. Be concrete, one line each."),
}
결과 = {}
for k, (t, q) in 질문.items():
    body = dict(model=모델, prompt=q, images=[b64(잘라(t))], stream=False, options=dict(temperature=0.2))
    req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}); s = time.time()
    d = json.load(urllib.request.urlopen(req, timeout=900)); 결과[k] = dict(답=d.get("response", d.get("error")), 초=round(time.time() - s, 1))
    print("=== %s (%.0fs)\n%s" % (k, 결과[k]["초"], 결과[k]["답"]))
json.dump(dict(모델=모델, 결과=결과, 정답="투구 통 · 주둥이 안 나옴 · 볼 날개 작음 · 눈 띠 없음"), open(os.path.join(B, "로컬눈시험.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
