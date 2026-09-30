# -*- coding: utf-8 -*-
"""과정 돌리기 — 단계 파일을 차례로 블렌더에서 실행 · 단계마다 .blend · 프레임 · 기록 한 줄 (2026-09-30 「과정이 보여야 한다」 · OpenCode 가 돌리고 Claude 가 감독).
    python 돌리기.py [처음 끝]   예) python 돌리기.py 1 3
    -> out/오메가몬2/과정/머리/NN.blend · 프레임/NN_<카메라>.png · 기록.md(단계마다: 번호 · 자막 · 한 일 · 값의 출처)
멈춤 규칙(로컬 에이전트용): 프레임 PNG 셋이 안 생기면 그 단계에서 멈추고 종료 코드 1. 형태 판정은 하지 않는다."""
import os, sys, glob, subprocess, ast
H = os.path.dirname(os.path.abspath(__file__)); O = r"G:\art2real\원화3d\out\오메가몬2\과정\머리"; os.makedirs(os.path.join(O, "프레임"), exist_ok=True)
BL = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
단계들 = sorted(glob.glob(os.path.join(H, "단계", "[0-9][0-9]_*.py"))); 처음, 끝 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, len(단계들))
for f in 단계들:
    n = int(os.path.basename(f)[:2])
    if n < 처음 or n > 끝: continue
    이전 = os.path.join(O, "%02d.blend" % (n - 1)); 저장 = os.path.join(O, "%02d.blend" % n); 프레임 = os.path.join(O, "프레임", "%02d" % n)
    cmd = [BL, "-b"] + ([이전] if os.path.exists(이전) else []) + ["--python", os.path.join(H, "_실행.py"), "--", f, 저장, 프레임]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    있음 = [os.path.exists("%s_%s.png" % (프레임, c)) for c in ("02_3-4", "02_옆", "02_정면")]
    if not all(있음) or not os.path.exists(저장):
        print("멈춤: %02d 단계 실패" % n); print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    doc = ast.get_docstring(ast.parse(open(f, encoding="utf-8").read())) or ""; 자막 = doc.split("\n")[0]
    기록 = os.path.join(O, "기록.md"); 줄 = "| %02d | %s | %s |\n" % (n, 자막, " ".join(doc.split("\n")[1:]).strip())
    old = open(기록, encoding="utf-8").read() if os.path.exists(기록) else "| 단계 | 자막 | 한 일 · 값의 출처 |\n|---|---|---|\n"
    old = "".join(l + "\n" for l in old.splitlines() if not l.startswith("| %02d |" % n)); open(기록, "w", encoding="utf-8").write(old + 줄)
    print("완료 %02d %s" % (n, 자막))
print("끝 · 프레임:", os.path.join(O, "프레임"))
