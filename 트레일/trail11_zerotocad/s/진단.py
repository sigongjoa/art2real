# -*- coding: utf-8 -*-
"""실패 원인 진단(trail10 venv): 코드 300 개를 ① 그대로 ② 필렛 · 모따기 줄을 지운 뒤 실행 → 실패 종류 · IoU 변화. 「바탕 모양은 맞는데 마감 버튼에서 깨지나」를 가른다."""
import sys, json, re, collections, numpy as np
sys.path.insert(0, "s"); from score import one, cap
from concurrent.futures import ProcessPoolExecutor
IN = {json.loads(l)["이름"]: json.loads(l) for l in open("runs/역산/입력.jsonl", encoding="utf-8")}
OUT = [json.loads(l) for l in open("runs/역산/출력.jsonl", encoding="utf-8")]
P_ = r"\([^()]*(\([^()]*\)[^()]*)*\)"
def strip(c): return re.sub(r"(\.(edges|faces|vertices)" + P_ + r")*\.(fillet|chamfer)" + P_, "", c)   # 앞의 선택자째 지운다(선택자만 남으면 결과가 모서리라 내보내기 실패 — 10-06 첫 판)
def kind(c):   # 실패한 CadQuery 연산 이름으로 가른다(OCC 오류 글에는 「chamfer」가 안 나와 10-06 첫 판은 모따기 21 개를 「기타」로 셌다)
    try: compile(c, "x", "exec")
    except SyntaxError: return "문법"
    try:
        import cadquery as cq; ns = {"cq": cq, "__name__": "__main__"}; exec(c, ns); return "실행됨"
    except NameError: return "이름 없음"
    except MemoryError: return "메모리 초과"
    except (AttributeError, TypeError): return "없는 API"
    except Exception as e:
        import traceback; tb = traceback.extract_tb(e.__traceback__); i = max((j for j, f in enumerate(tb) if f.filename == "<string>"), default=-1)
        op = tb[i + 1].name if 0 <= i < len(tb) - 1 else ""
        return {"fillet": "필렛·모따기", "chamfer": "필렛·모따기", "shell": "셸", "revolve": "회전", "sweep": "스윕·로프트", "loft": "스윕·로프트"}.get(op) or ("선택자" if any(k in str(e).lower() for k in ("empty list", "co-planar", "selected", "nth element")) else "기타 기하:" + op)
def NewPool(): return ProcessPoolExecutor(1, initializer=cap)
def run(pool, fn, arg, bad):   # 생성 코드는 전부 여기로만(작업자 · 25 초 · 8 GB)
    fu = pool.submit(fn, arg)
    try: return fu.result(timeout=25), pool
    except Exception:
        for p in list(pool._processes.values()): p.kill()
        pool.shutdown(wait=False, cancel_futures=True); return bad, NewPool()
if __name__ == "__main__":   # v2(10-06 밤): 새 채점기(open3d) · 연산 이름 분류 · 부품마다 진단.jsonl 에 바로 적음(10-06 세션 끊김으로 한 번 잃음) · 다시 부르면 이어서
    import os
    J = "runs/역산/진단_v2.jsonl"; done = {json.loads(l)["이름"] for l in open(J, encoding="utf-8")} if os.path.exists(J) else set()
    pool = NewPool()
    for o in OUT[:int(sys.argv[1]) if len(sys.argv) > 1 else None]:   # 앞 N 개만(10 개 먼저 보고 넓힌다)
        if o["이름"] in done: continue
        st = IN[o["이름"]]["stl"]; kinds, a, b = [], [], []
        for c in o["코드"]:
            k, pool = run(pool, kind, c, "시간·메모리 초과"); kinds.append(k); v, pool = run(pool, one, (c, st), -2.0); a.append(round(v, 3)); v, pool = run(pool, one, (strip(c), st), -2.0); b.append(round(v, 3))
        open(J, "a", encoding="utf-8").write(json.dumps({"이름": o["이름"], "종류": kinds, "원래": a, "뺌": b}, ensure_ascii=False) + "\n"); print(o["이름"][:40], max(a), max(b), flush=True)
    R_ = [json.loads(l) for l in open(J, encoding="utf-8")]
    a = np.array([v for r in R_ for v in r["원래"]]); b = np.array([v for r in R_ for v in r["뺌"]]); pa = np.array([max(r["원래"]) for r in R_]); pb = np.array([max(r["뺌"]) for r in R_])
    R = {"부품": len(R_), "실패 종류": dict(collections.Counter(k for r in R_ for k in r["종류"])), "실행률 원래": round(float((a >= 0).mean()), 3), "실행률 필렛·모따기 뺌": round(float((b >= 0).mean()), 3),
         "부품 최고 IoU≥0.8 원래 · 뺌": [int((pa >= 0.8).sum()), int((pb >= 0.8).sum())], "≥0.6": [int((pa >= 0.6).sum()), int((pb >= 0.6).sum())], "부품 중앙": [round(float(np.median(pa)), 3), round(float(np.median(pb)), 3)]}
    json.dump(R, open("runs/역산/진단_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(R)
