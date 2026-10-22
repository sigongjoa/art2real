# 공개 저장소 내보내기 — 로컬 이력을 걸러서 github.com/<계정>/art2real(공개) 로 · 근거 claudedocs/감사_공개전_20261022.md · 10-22
# 규칙: md 는 기본 뺌(허용: README.md · docs/ · 하네스/판/) · 남의 그림(trail4 · trail7 in · 파생 npy) · 피규어제작과정 뺌 · 개인 정보는 out/공개/_규칙/바꿀말.txt(git 밖)로 내용 · 커밋 메시지에서 바꿈
# 같은 이력을 같은 규칙으로 거르면 같은 결과 → 판마다 다시 걸러 밀어도 앞부분이 같다 · 사용: python 하네스/공개.py [--만들기]
import os, sys, shutil, subprocess, re
뿌리 = "G:/art2real"; 밖 = 뿌리 + "/out/공개/"; 저장 = 밖 + "repo"; 규칙 = 밖 + "_규칙/"; 이름 = "art2real"
FR = 뿌리 + "/트레일/trail10_cadrille/venv/Scripts/git-filter-repo.exe"
뺄 = """트레일/trail4_gen3d/in/
트레일/trail7_part3d/in/
트레일/trail4_gen3d/snap_front.npy
트레일/trail4_gen3d/snap_side.npy
트레일/trail4_gen3d/snap_back.npy
트레일/trail4_gen3d/rgb_front.npy
트레일/trail4_gen3d/rgb_side.npy
트레일/trail4_gen3d/rgb_back.npy
트레일/trail4_gen3d/named_labels.npy
트레일/trail4_gen3d/uv_dump.json
claudedocs/피규어제작과정/
claudedocs/CAD제작과정/
regex:^(?!README\\.md$|docs/|하네스/판/).*\\.md$
"""
def 돌(*a, cwd=None, 확인=True):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if 확인 and r.returncode: raise RuntimeError(f"{a[:3]} 실패:\n{r.stderr[-1500:]}")
    return r.stdout.strip()
def 거르기():
    if os.path.exists(저장): shutil.rmtree(저장, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
    가지 = "정답세우기"   # 공개 main 은 이 가지의 거울 · 지금 HEAD 가 무엇이든(떨어진 HEAD · 다른 가지) 이 가지만 내보냄
    if 돌("git", "-C", 뿌리, "rev-parse", "--verify", "-q", f"refs/heads/{가지}", 확인=False) == "": raise RuntimeError(f"가지 {가지} 가 없음 — 공개 안 함")
    돌("git", "clone", "--no-local", "--single-branch", "--branch", 가지, 뿌리, 저장)
    open(규칙 + "뺄경로.txt", "w", encoding="utf-8").write(뺄)
    돌(FR, "--force", "--invert-paths", "--paths-from-file", 규칙 + "뺄경로.txt", "--replace-text", 규칙 + "바꿀말.txt", "--replace-message", 규칙 + "바꿀말.txt", "--mailmap", 규칙 + "mailmap", cwd=저장)   # 작성자 메일 → GitHub noreply
    돌("git", "branch", "-M", "main", cwd=저장)
def 감사():   # 걸러진 이력에 남으면 안 되는 것이 0 인지 — 하나라도 있으면 밀지 않는다
    문 = []; 바꿀 = [l.split("==>")[0] for l in open(규칙 + "바꿀말.txt", encoding="utf-8").read().splitlines() if l.strip()]
    for s in 바꿀:
        if 돌("git", "log", "--all", "--oneline", "-S", s, cwd=저장): 문.append(f"내용에 남음: {s[:4]}…")
        if 돌("git", "log", "--all", "--oneline", f"--grep={re.escape(s)}", cwd=저장): 문.append(f"메시지에 남음: {s[:4]}…")
    if "gmail.com" in 돌("git", "log", "--all", "--format=%ae%n%ce", cwd=저장): 문.append("작성자 메일이 개인 주소로 남음")
    파일 = 돌("git", "-c", "core.quotepath=off", "log", "--all", "--name-only", "--format=", cwd=저장).splitlines()
    for p in set(파일):
        if p.endswith(".md") and not (p == "README.md" or p.startswith(("docs/", "하네스/판/"))): 문.append(f"md 남음: {p}")
        if p.startswith(("트레일/trail4_gen3d/in/", "트레일/trail7_part3d/in/", "claudedocs/피규어제작과정/")): 문.append(f"뺄 경로 남음: {p}")
    if 문: raise RuntimeError("공개 감사 실패 — 밀지 않음:\n  " + "\n  ".join(sorted(set(문))[:20]))
    return len(set(파일))
def 밀기(만들기=False):
    계정 = 돌("gh", "api", "user", "-q", ".login"); 주소 = f"https://github.com/{계정}/{이름}"
    if 만들기 and subprocess.run(["gh", "repo", "view", f"{계정}/{이름}"], capture_output=True).returncode:
        돌("gh", "repo", "create", f"{계정}/{이름}", "--public", "--description", "임의의 이미지 → CAD 코드 · 연구 저장소(판마다 하네스 보고서)")
    돌("git", "remote", "add", "origin", 주소 + ".git", cwd=저장, 확인=False)
    돌("git", "push", "--force", "origin", "main", cwd=저장)   # 공개 쪽은 로컬에서 거른 거울 — 덮어써도 원본은 로컬
    return 주소
def Pages(계정):
    r = subprocess.run(["gh", "api", f"repos/{계정}/{이름}/pages"], capture_output=True)
    if r.returncode: 돌("gh", "api", "-X", "POST", f"repos/{계정}/{이름}/pages", "-f", "source[branch]=main", "-f", "source[path]=/docs", 확인=False)
    return f"https://{계정}.github.io/{이름}/"
def 내보내기(만들기=False):
    거르기(); n = 감사(); 주소 = 밀기(만들기); 계정 = 주소.split("/")[3]
    쪽 = Pages(계정) if os.path.exists(저장 + "/docs") else None
    print(f"공개: {주소} · 이력 파일 {n} · Pages {쪽 or '(docs 없음)'}"); return 주소, 쪽
if __name__ == "__main__": 내보내기("--만들기" in sys.argv)
