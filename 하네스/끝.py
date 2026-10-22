# 하네스 끝 단계 — 판 하나가 끝나면: Pages 목록 → 쇼츠(대본 · 검사 · 굽기 · 업로드 대기) → 커밋 → 공개 푸시(걸러서) → GitHub 이슈(열고 결과 달고 닫음) · 10-22
# 사용: 하네스.py 가 판 끝에 부름 · 이미 돈 판은 python 하네스/끝.py <판> [커밋 공개 이슈 쇼츠 중 고른 것]
import os, re, sys, json, subprocess
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스")
def 돌(*a, 확인=True, cwd=뿌리):
    r = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if 확인 and r.returncode: raise RuntimeError(f"{a[:3]} 실패: {r.stderr[-600:]}")
    return r.stdout.strip()
def 끝내기(판, 단계=("쇼츠", "커밋", "공개", "이슈")):
    from omegaconf import OmegaConf
    import 목록; d = f"{뿌리}/하네스/판/{판}/"; c = OmegaConf.load(d + "설정.yaml"); j = json.load(open(d + "판정.json", encoding="utf-8")); 명제 = str(c.판.get("명제") or c.판.물음); 시도 = str(c.판.get("시도") or 명제)
    목록.갱신(판); 남 = json.load(open(d + "끝.json", encoding="utf-8")) if os.path.exists(d + "끝.json") else {}   # 일부 단계만 다시 돌려도 앞 기록(이슈 · 공개)은 남김
    남["Pages"] = f"https://sigongjoa.github.io/art2real/판/{판}/보고.html"; 더할 = [f"하네스/판/{판}", "하네스/results.tsv", "docs"]
    if "쇼츠" in 단계:
        import 쇼츠
        try: 쇼 = 쇼츠.만들기(판); 남["쇼츠"] = 쇼; 더할 += [f"원화3d/과정/영상05/대화/{쇼['편']}", "원화3d/과정/쇼츠"]
        except Exception as e: 남["쇼츠"] = {"실패": str(e)[:300]}
        쇼츠.판에넣기(판, 남["쇼츠"])   # 웹용 사본 · 대본 → 판 폴더 · 보고서 「쇼츠」 절
    json.dump(남, open(d + "끝.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import 보고; 보고.만들기(판); 목록.갱신(판)   # 쇼츠가 들어간 보고서로 다시
    json.dump(남, open(d + "끝.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "커밋" in 단계:
        돌("git", "add", "--", *더할); 상 = 돌("git", "diff", "--cached", "--name-only")
        if 상: 돌("git", "commit", "-q", "-m", f"판 {판} — {시도} — {j['판정']}\n\n하네스 자동 · 보고서 하네스/판/{판}/보고.html · 가지 {c.판.가지}\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>")
        남["커밋"] = 돌("git", "rev-parse", "--short", "HEAD")
    if "공개" in 단계:
        import 공개; 주소, 쪽 = 공개.내보내기(); 남["공개"] = 주소
    if "이슈" in 단계:
        짧은 = 시도   # 시도는 관문이 괄호 · 문턱 없이 60 자 안으로 막음
        제목 = f"판 {판} — " + (짧은 if len(짧은) <= 80 else 짧은[:80].rsplit(" ", 1)[0] + "…"); 있 = 돌("gh", "issue", "list", "--repo", "sigongjoa/art2real", "--state", "all", "--search", f"판 {판} in:title", "--json", "number,title", "-q", ".[].title", 확인=False)
        if 제목 not in 있.splitlines():
            줄 = "\n".join(f"| {r['지표']} | {r['식']} {r['값']} | {r['이 판']} | {'✓' if r['통과'] else '✗'} |" for r in j["기준"])
            몸 = f"**시도**: {시도}\n\n**명제**: {명제}\n\n**판정**: {j['판정']} · 가지 {c.판.가지} · {c.판.종류}\n\n| 지표 | 조건 | 이 판 | 결과 |\n|---|---|---|---|\n{줄}\n\n보고서: {남['Pages']}\n\n(하네스 자동 — 판 하나 = 이슈 하나)"
            url = 돌("gh", "issue", "create", "--repo", "sigongjoa/art2real", "--title", 제목, "--body", 몸)
            돌("gh", "issue", "close", url, "--repo", "sigongjoa/art2real", "--comment", f"판정 {j['판정']} — 하네스가 판 끝에 닫음", 확인=False); 남["이슈"] = url
    json.dump(남, open(d + "끝.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); return 남
if __name__ == "__main__": print(json.dumps(끝내기(sys.argv[1], tuple(sys.argv[2:]) or ("쇼츠", "커밋", "공개", "이슈")), ensure_ascii=False, indent=1))
