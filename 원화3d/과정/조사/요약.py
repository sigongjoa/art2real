# -*- coding: utf-8 -*-
"""로컬 모델로 글마다 편집 기법을 뽑고(qwen3:14b) 모아서 한 장으로(qwen3-coder:30b) — Claude 는 마지막 한 장만 읽는다.
    python 요약.py -> out/조사/쇼츠/뽑음.jsonl · 집계.md"""
import os, json, urllib.request, collections
O = r"G:\art2real\원화3d\out\조사\쇼츠"
def 묻기(model, prompt, fmt=None, n=400):
    body = dict(model=model, prompt=prompt, stream=False, think=False, options=dict(temperature=0.1, num_predict=n, num_ctx=8192))
    if fmt: body["format"] = fmt
    r = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=900)).get("response", "")
글 = [json.loads(l) for l in open(os.path.join(O, "글.jsonl"), encoding="utf-8")]; 한 = set(json.loads(l)["주소"] for l in open(os.path.join(O, "뽑음.jsonl"), encoding="utf-8")) if os.path.exists(os.path.join(O, "뽑음.jsonl")) else set()
out = open(os.path.join(O, "뽑음.jsonl"), "a", encoding="utf-8")
for i, g in enumerate(글):
    if g["주소"] in 한: continue
    p = ("다음은 커뮤니티 글이다. 유튜브 쇼츠(세로 짧은 영상)의 **편집 · 구성 · 자막 · 효과음 · 첫 몇 초 · 길이 · 유지율**에 대한 구체적 조언이 있으면 뽑아라. 없으면 관련=false.\n"
         "JSON 으로만: {\"관련\": true/false, \"기법\": [\"짧은 한국어 구 (숫자 포함)\", ...최대 6], \"수치\": [\"글에 나온 숫자와 뜻\", ...최대 4], \"한줄\": \"글의 요지 한 문장\"}\n\n제목: %s\n본문: %s" % (g["제목"], g["본문"][:3000]))
    try: r = json.loads(묻기("qwen3:14b", p, "json"))
    except Exception as e: r = dict(관련=False, 오류=str(e)[:80])
    r.update(곳=g["곳"], 주소=g["주소"], 제목=g["제목"]); out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush(); print(i + 1, len(글), r.get("관련"), (r.get("한줄") or "")[:50], flush=True)
뽑 = [json.loads(l) for l in open(os.path.join(O, "뽑음.jsonl"), encoding="utf-8")]; 관 = [r for r in 뽑 if r.get("관련") and r.get("기법")]
줄 = ["[%d|%s] %s" % (k, r["곳"], " ; ".join(r["기법"])[:300]) for k, r in enumerate(관)]
p = ("아래는 여러 커뮤니티 글에서 뽑은 유튜브 쇼츠 편집 조언이다(줄마다 [번호|곳]). 같은 뜻끼리 묶어 **많이 나온 순서**로 표를 만들어라. "
     "열: 기법 · 몇 글이 말했나 · 구체 수치/방법 · 근거 글 번호(최대 5). 15 줄 이하. 그다음 「서로 부딪치는 조언」 3 줄, 「한 번만 나왔지만 구체적인 것」 5 줄. 지어내지 마라 — 아래에 없는 것은 쓰지 않는다.\n\n" + "\n".join(줄)[:24000])
md = 묻기("qwen3-coder:30b", p, n=1800); 곳수 = collections.Counter(r["곳"] for r in 뽑)
open(os.path.join(O, "집계.md"), "w", encoding="utf-8").write("# 커뮤니티 쇼츠 편집 조언 집계 (로컬 모델 요약 · 검증 전)\n\n모은 글 %d · 관련 %d · 곳별 %s\n\n%s\n\n## 근거 글\n%s\n" % (len(뽑), len(관), dict(곳수), md, "\n".join("%d. [%s] %s — %s" % (k, r["곳"], r["제목"][:60], r["주소"]) for k, r in enumerate(관))))
print("집계.md · 관련", len(관), "/", len(뽑))
