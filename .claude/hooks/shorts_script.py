# -*- coding: utf-8 -*-
"""쇼츠 대본 AI 티 관문 (PreToolUse Bash · 10-07 사용자 「강제로 통과된 것만」).
쇼츠 공장 `new_short_ko.py <plan.tsv>` 를 부를 때 그 tsv 에 `#윤문: <무엇으로 · 언제>` 머리줄이 없으면 막는다(종료 2).
머리줄은 대본을 AI 티 점검(humanize-korean 또는 아래 다섯 버릇 직접 점검)에 통과시킨 뒤에 적는다:
  ① 첫째 · 둘째 목록  ② 쉼표 토막(「뼈대는, 하나입니다」)  ③ 「그래서 ~입니다」 교훈 닫기  ④ 겪은 일 없음  ⑤ 전부 「~습니다」
    python shorts_script.py test   자기 검사
"""
import sys, json, re, os

def 막을까(명령):
    if "new_short_ko.py" not in 명령: return ""
    tsvs = re.findall(r'"([^"]+\.tsv)"|\'([^\']+\.tsv)\'|(\S+\.tsv)', 명령)
    빠짐 = []
    for t in (a or b or c for a, b, c in tsvs):
        try: 줄 = open(t, encoding="utf-8").read().splitlines()
        except OSError: 빠짐.append(t + " (못 읽음)"); continue
        if not any(re.match(r"#윤문:\s*\S", l) for l in 줄): 빠짐.append(t)
    if not tsvs: 빠짐.append("(tsv 경로를 못 찾음)")
    return ("쇼츠 대본 관문: %s 에 `#윤문:` 머리줄이 없다. 대본을 AI 티 점검(humanize-korean, 또는 목록 · 쉼표 토막 · 교훈 닫기 · 겪은 일 · 「~습니다」 일색 다섯 버릇)에 통과시킨 뒤 "
            "`#윤문: <방법 · 날짜>` 를 머리에 적고 다시 불러라." % ", ".join(빠짐)) if 빠짐 else ""

if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        import tempfile
        d = tempfile.mkdtemp(); a, b = os.path.join(d, "a.tsv"), os.path.join(d, "b.tsv")
        open(a, "w", encoding="utf-8").write("#제목: x\n그림\t말\n"); open(b, "w", encoding="utf-8").write("#윤문: 직접 다섯 버릇 · 10-07\n그림\t말\n")
        assert 막을까('python tools/new_short_ko.py "%s" slug' % a)
        assert not 막을까('python tools/new_short_ko.py "%s" slug' % b)
        assert not 막을까("ls -la")
        print("ok"); sys.exit(0)
    try: 명령 = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except Exception: sys.exit(0)   # 훅이 고장 나도 다른 일은 막지 않는다
    m = 막을까(명령)
    if m: print(m, file=sys.stderr); sys.exit(2)
