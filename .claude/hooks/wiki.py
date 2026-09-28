# -*- coding: utf-8 -*-
"""지식 위키를 「읽게 · 적게」 만드는 장치. 원화3d/지식/index.md 「쓰는 법」 참조.

    wiki.py prompt     (UserPromptSubmit)  말에 부위 낱말이 있으면 그 부위 시작 카드를 문맥에 넣는다
    wiki.py agent      (PreToolUse Agent)  부위 일을 맡기는데 지시문에 위키 경로가 없으면 막는다(종료 2)
    wiki.py precommit  (git pre-commit)    부위 스크립트를 커밋하는데 log.md 가 같이 없으면 막는다 · 점검.py 도 돈다
    wiki.py test       자기 검사
부위 낱말은 부위 쪽의 `낱말:` 줄에서 읽는다. 훅이 고장 나도 작업을 막지 않게 prompt 는 항상 종료 0.
"""
import os, re, sys, json, glob, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
지식 = os.path.join(ROOT, "원화3d", "지식")

def 부위들():
    r = {}
    for p in glob.glob(os.path.join(지식, "부위", "*.md")):
        t = open(p, encoding="utf-8").read(); m = re.search(r"^낱말:(.*)$", t, re.M)
        if m: r[p] = (m.group(1).split(), t)
    return r
def 맞는(글):
    return [(p, t) for p, (w, t) in 부위들().items() if any(k in 글 for k in w)]
def 카드(t):
    m = re.search(r"## 시작 카드\n(.*?)(?=\n## )", t, re.S); return m.group(1).strip() if m else ""
def 상대(p): return os.path.relpath(p, ROOT).replace("\\", "/")

def prompt(글):
    out = []
    for p, t in 맞는(글):
        out.append("[지식 위키] 이 일은 부위 「%s」에 걸린다. 아래 시작 카드를 적용하고, 답 첫 줄에 「적용 규칙: …」을 밝혀라. 서브에이전트 지시문에는 `%s` 경로를 넣어라. 끝나면 log.md · 바퀴 표를 같은 커밋에.\n\n%s"
                   % (os.path.basename(p)[:-3], 상대(p), 카드(t)))
    return "\n\n".join(out)
def agent(지시문):
    빠짐 = [상대(p) for p, _ in 맞는(지시문) if "원화3d/지식" not in 지시문.replace("\\", "/")]
    return "지식 위키: 부위 일을 맡기는데 지시문에 위키 경로가 없다. 다음을 읽으라고 넣어라: " + ", ".join(빠짐) if 빠짐 else ""
def precommit(파일들):
    낱말 = [k for w, _ in 부위들().values() for k in w]
    걸림 = [f for f in 파일들 if re.search(r"원화3d/실험_\d+/.*\.py$", f) and any(k in os.path.basename(f) for k in 낱말)]
    if 걸림 and "원화3d/지식/log.md" not in 파일들:
        return "지식 위키: 부위 스크립트(%s)를 커밋하는데 원화3d/지식/log.md 가 같이 없다. 일지 한 줄과 바퀴 표를 적고 같이 올려라." % ", ".join(걸림)
    return ""

if __name__ == "__main__":
    for s in (sys.stdin, sys.stdout, sys.stderr): s.reconfigure(encoding="utf-8")
    일 = sys.argv[1] if len(sys.argv) > 1 else "test"
    if 일 == "prompt":
        try: print(prompt(json.load(sys.stdin).get("prompt", "")))
        except Exception as e: print("[지식 위키 훅 오류] %r" % e, file=sys.stderr)
        sys.exit(0)
    if 일 == "agent":
        try: 말 = agent(json.load(sys.stdin).get("tool_input", {}).get("prompt", ""))
        except Exception as e: print("[지식 위키 훅 오류] %r" % e, file=sys.stderr); sys.exit(0)
        if 말: print(말, file=sys.stderr); sys.exit(2)
        sys.exit(0)
    if 일 == "precommit":
        파일들 = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-only"], capture_output=True, cwd=ROOT).stdout.decode("utf-8").split("\n")
        말 = precommit([f.strip() for f in 파일들 if f.strip()])
        if 말: print(말, file=sys.stderr); sys.exit(1)
        if any(f.startswith("원화3d/지식/") for f in 파일들): sys.exit(subprocess.run([sys.executable, os.path.join(지식, "점검.py")]).returncode)
        sys.exit(0)
    # 자기 검사 — 걸려야 할 때 걸리고 안 걸려야 할 때 안 걸리나
    assert "시작 카드" not in prompt("README 오타 고쳐 줘") and prompt("README 오타 고쳐 줘") == ""
    assert "하지 말 것" in prompt("오메가몬 얼굴 턱 다시 고쳐 봐"), "부위 낱말에 카드가 안 나옴"
    assert agent("오메가몬 턱을 사선으로 고쳐라") and not agent("오메가몬 턱을 고쳐라. 먼저 원화3d/지식/부위/머리.md 를 읽어라") and not agent("README 정리")
    assert precommit(["원화3d/실험_20260928/얼굴7.py"]) and not precommit(["원화3d/실험_20260928/얼굴7.py", "원화3d/지식/log.md"]) and not precommit(["원화3d/실험_20260928/나사쿠폰.py"])
    print("훅 자기 검사 통과")
