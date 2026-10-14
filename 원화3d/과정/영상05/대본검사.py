"""대화 쇼츠 대본 검사 (10-14) — 굽기 전에: python 대본검사.py <편>  → 문제 없으면 0, 있으면 1
다섯 칸(shorts-five-beat-structure): ① 첫 줄은 장면 — 질문 · 「지난번」 시작 금지 ② 「나」 결정 대사 ≥ 1 ③ 끝 두 줄에 예고 금지
그 밖: #윤문 줄 · 표정 파일 있음(10-13 「민망」 없어서 굽기 멈춤) · 자막에 한글 숫자 읽기 금지(숫자로) · 화면 키는 화면.py 에 있음 · 큰글 길이 · 대사창 2 줄"""
import sys, os, re, csv, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); NAME = sys.argv[1]; SRC = os.path.join(HERE, "대화", NAME); CH = "G:/art2real/out/영상05/캐릭터시안/누끼/"
raw = open(os.path.join(SRC, "대본.tsv"), encoding="utf-8").read().splitlines(); 문제 = []
if not any(l.startswith("#윤문:") for l in raw): 문제.append("#윤문: 줄 없음")
from PIL import Image, ImageDraw, ImageFont
_d, _f = ImageDraw.Draw(Image.new("L", (1, 1))), ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 60)
def 줄수(t, wmax=900):   # 대화쇼츠.py 줄나눔과 같은 규칙(글꼴 60 · 폭 900) · 대사창(1560~1880)에는 2 줄까지
    n, cur = 1, ""
    for x in t.split(" "):
        if cur and _d.textlength(cur + " " + x, font=_f) > wmax: n += 1; cur = x
        else: cur = (cur + " " + x).strip()
    return n
rows = [r for r in csv.reader([l for l in raw if l and not l.startswith("#")], delimiter="\t")][1:]
자막 = lambda r: r[5].split("｜")[0].strip()
첫 = 자막(rows[0])
if 첫.endswith("?") or re.match(r"(지난번|저번|전에|아까)", 첫): 문제.append("① 첫 줄이 질문이거나 회상: " + 첫[:30])
결정 = [자막(r) for r in rows if r[0] == "나" and re.search(r"(해 ?봐|해\.|깎아|바꿔|빼|넣어|하자|돌려|정하자|으로 해|로 가)", 자막(r)) and not 자막(r).endswith("?")]
if not 결정: 문제.append("② 「나」의 결정 대사 없음(질문만 함)")
for r in rows[-2:]:
    if re.search(r"(다음 ?편|다음에|나중에|보여 ?드릴게|알려 ?줘|해 볼게요|기대)", 자막(r)): 문제.append("③ 끝에 예고 · 약속: " + 자막(r)[:30])
질 = sum(자막(r).endswith("?") for r in rows if r[0] == "나"); 나 = sum(r[0] == "나" for r in rows)
if 나 and 질 / 나 > .5: 문제.append("「나」 대사 %d 중 물음표 %d — 사회자가 되고 있음" % (나, 질))
for i, r in enumerate(rows, 2):
    for who, e in (("2_후드개발자", r[1]), ("6_안드로이드", r[2])):
        if not os.path.exists(CH + "표정_%s_%s.png" % (who, e)): 문제.append("%d 줄 표정 파일 없음: %s_%s" % (i, who, e))
    if re.search(r"영점|퍼센트|[일이삼사오육칠팔구십백천만]+ ?개[^가-힣]", 자막(r)): 문제.append("%d 줄 자막에 숫자를 한글로 씀(읽기는 ｜ 뒤에): %s" % (i, 자막(r)[:30]))
    if 줄수(자막(r)) > 2: 문제.append("%d 줄 대사창 %d 줄 — 2 줄 넘으면 잘림(58 편) · 줄을 나눠라: %s" % (i, 줄수(자막(r)), 자막(r)[:20]))
    if len(r[4].split(":", 1)[-1]) > 13: 문제.append("%d 줄 큰글 %d 자 — 13 자 넘으면 잘림(55 편 14 자 잘림)" % (i, len(r[4].split(":", 1)[-1])))
spec = importlib.util.spec_from_file_location("화면", os.path.join(SRC, "화면.py")); 화면 = importlib.util.module_from_spec(spec); spec.loader.exec_module(화면)
for k in sorted({r[3] for r in rows}):
    try: 화면.판(k, .5)
    except KeyError: 문제.append("화면 키 없음: " + k)
print("\n".join(문제) if 문제 else "통과 — 다섯 칸 · 표정 · 숫자 · 화면 키"); sys.exit(1 if 문제 else 0)
