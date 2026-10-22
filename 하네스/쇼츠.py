# 하네스 쇼츠 단계 — 판 보고서 → 대화 쇼츠 한 편(서재용 채널 꼴) · 대본은 claude -p 가 making-dialogue-shorts 규칙으로 · 대본검사 · 맥락 없는 읽기 · 굽기 · 업로드 대기 · 10-22
# 업로드는 Chrome 확장(Claude 세션)만 할 수 있어 여기선 「업로드 대기」까지 · 사용: python 하네스/쇼츠.py <판>
import os, re, sys, json, glob, shutil, subprocess
뿌리 = "G:/art2real"; 영상 = 뿌리 + "/원화3d/과정/영상05/"; 스킬 = os.path.expanduser("~/.claude/skills/making-dialogue-shorts/SKILL.md")
나표정 = "기본 놀람 말 웃음 으쓱 좌절"; AI표정 = "기본 놀람 말 웃음 으쓱 좌절 설명 코딩 부품 자신만만 충격 머리감싸기 민망 생각 조사 기쁨 사과 엄지"
def 클로드(글, 초=600):
    r = subprocess.run(["claude", "-p", 글], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=초, cwd=뿌리)
    if r.returncode: raise RuntimeError("claude -p 실패: " + r.stderr[-500:])
    return r.stdout.strip()
def 카드(판, 편):   # 화면 재료 1000×700 · 보고서 위쪽(명제 · 판정) · 시트 · 특징
    from PIL import Image
    s = f"{뿌리}/하네스/판/{판}/"; d = f"{뿌리}/out/영상05/대화/{편}/자료/"; os.makedirs(d, exist_ok=True); 키 = []
    def 맞춤(im, nm):
        im = im.convert("RGB"); im.thumbnail((980, 680)); c = Image.new("RGB", (1000, 700), "#fffdf8"); c.paste(im, ((1000 - im.width) // 2, (700 - im.height) // 2)); c.save(d + nm + ".png"); 키.append(nm)
    if os.path.exists(s + "보고.png"): b = Image.open(s + "보고.png"); 맞춤(b.crop((0, 0, b.width, min(b.height, 900))), "명제")
    if os.path.exists(s + "시트.png"): 맞춤(Image.open(s + "시트.png"), "시트")
    if os.path.exists(s + "특징.png"):
        f = Image.open(s + "특징.png"); 맞춤(f, "특징"); 맞춤(f.crop((0, 0, int(f.width * .5), f.height)), "주의")
    return 키
화면틀 = '''# {편} 위쪽 화면 판 — 재료 out/영상05/대화/{편}/자료/*.png(하네스/쇼츠.py · 판 {판} 보고서)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/{편}/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {카드}
def 판(키, p):
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[키] + (255,), width=8)
    c.alpha_composite(Image.open(A + 키 + ".png").convert("RGBA").resize((1000, 700))); return c
'''
def 대본쓰기(판, 키, 고칠말=""):
    보고 = open(f"{뿌리}/하네스/판/{판}/보고.md", encoding="utf-8").read(); 규칙 = open(스킬, encoding="utf-8").read() if os.path.exists(스킬) else ""
    본보기 = open(영상 + "대화/88_자리/대본.tsv", encoding="utf-8").read()
    글 = f"""너는 한국어 대화 쇼츠 대본 작가다. 아래 규칙과 본보기 꼴 그대로 대본.tsv 내용만 출력해라(설명 · 코드펜스 없이 tsv 만).
[규칙 — making-dialogue-shorts 스킬]
{규칙[:6000]}
[본보기 — 88 편 대본.tsv]
{본보기}
[제약]
- 화면 칸에는 이 키만: {", ".join(키)}
- 나 칸 표정: {나표정} · AI 칸 표정: {AI표정}
- 첫 줄 #윤문: 직접 · 날짜 · 할 말 하나 · 사실 출처(하네스/판/{판}/보고.md)
- 숫자는 보고서에 있는 것만 · 자막은 숫자로 쓰고 읽기는 ｜ 뒤 한글
- 12~16 줄 · 다섯 칸(이상한 장면 → 「나」의 틀린 짐작 → 증거 → 「나」의 결정 → 결과 판정) · 예고 · 약속 금지 · 말 칸 2 줄(약 30 자) 이내
- 「나」의 결정 대사는 반드시 한 줄 이상, 물음표 없이 끝나고 이 말꼴 중 하나를 그대로 넣는다: 「해 봐」 「돌려」 「바꿔」 「넣어」 「빼」 「고쳐」 「하자」 (예: 「같은 설정으로 다시 돌려 봐.」)
{("[앞 판에서 고칠 것]" + chr(10) + 고칠말) if 고칠말 else ""}
[이 판의 보고서]
{보고}"""
    t = 클로드(글); t = re.sub(r"^```\w*\n|\n```$", "", t.strip()); return t
def 검사(편):
    r = subprocess.run(["python", "대본검사.py", 편], cwd=영상, capture_output=True, text=True, encoding="utf-8", errors="replace"); return r.stdout.strip() + r.stderr.strip()[-300:]
def 훅줄빼기(t): return "\n".join(l for l in t.splitlines() if not l.startswith("적용 규칙")).strip()   # 안에서 부른 claude 에도 위키 훅이 「적용 규칙: …」 을 붙임
def 막힘없음(t): return 훅줄빼기(t).strip(" 「」.\n") == "없음"   # 답 전체가 「없음」일 때만(앞 20 자 검사는 「해당 없음」에 속아 막힌 곳 13 줄을 건너뜀 · 10-22)
def 만들기(판, 굽기=True):
    있 = [n for n in os.listdir(영상 + "대화") if n.endswith(f"_판{판}")]   # 같은 판은 그 편 폴더를 다시 씀
    번호 = int(있[0].split("_")[0]) if 있 else max(int(re.match(r"(\d+)", n).group(1)) for n in os.listdir(영상 + "대화") if re.match(r"\d+_", n)) + 1; 편 = f"{번호}_판{판}"
    폴더 = 영상 + f"대화/{편}/"; os.makedirs(폴더, exist_ok=True); 키 = 카드(판, 편)
    색 = {"명제": "금", "시트": "초", "특징": "빨", "주의": "빨"}
    open(폴더 + "화면.py", "w", encoding="utf-8").write(화면틀.format(편=편, 판=판, 카드="{" + ", ".join(f'"{k}": {색.get(k, "금")}' for k in 키) + "}"))
    대본 = 대본쓰기(판, 키); open(폴더 + "대본.tsv", "w", encoding="utf-8").write(대본 + "\n"); 결 = 검사(편)
    if "통과" not in 결: 대본 = 대본쓰기(판, 키, "대본검사 결과:\n" + 결); open(폴더 + "대본.tsv", "w", encoding="utf-8").write(대본 + "\n"); 결 = 검사(편)
    읽기 = 클로드("너는 이 프로젝트를 처음 보는 쇼츠 시청자다. 파일을 찾지 말고 아래 대본만 보고, 줄마다 막히는 곳(모르는 낱말 · 끊긴 곳 · 이상한 서술)을 짧게 적어라. 막힌 곳이 없으면 「없음」.\n\n" + 대본)
    읽기 = 훅줄빼기(읽기)
    if not 막힘없음(읽기):
        대본 = 대본쓰기(판, 키, "맥락 없는 독자가 막힌 곳:\n" + 읽기); open(폴더 + "대본.tsv", "w", encoding="utf-8").write(대본 + "\n"); 결 = 검사(편)
    for _ in range(2):   # 다시 쓴 대본이 검사에 걸리면 검사 결과를 주고 고침(최대 두 번)
        if "통과" in 결: break
        대본 = 대본쓰기(판, 키, "대본검사 결과(이것만 고치고 나머지는 그대로):\n" + 결 + "\n\n지금 대본:\n" + 대본); open(폴더 + "대본.tsv", "w", encoding="utf-8").write(대본 + "\n"); 결 = 검사(편)
    기록 = {"편": 편, "대본검사": 결[-200:], "맥락없는읽기": 읽기[:1500]}
    if "통과" not in 결: 기록["굽기"] = "대본검사 실패로 안 구움"; return 기록
    if 굽기:
        import time; 시작 = time.time()
        r = subprocess.run(["python", "대화쇼츠.py", 편], cwd=영상, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "TTS": "chatterbox"}, timeout=7200)
        기록["굽기"] = (r.stdout.strip().splitlines() or ["?"])[-1]
        mp4 = f"{뿌리}/out/영상05/대화/{편}/{편}.mp4"
        if r.returncode or not os.path.exists(mp4) or os.path.getmtime(mp4) < 시작:   # 실패한 굽기 뒤 남은 옛 영상을 새 것으로 보지 않음
            기록["굽기"] = f"굽기 실패(코드 {r.returncode}): " + (r.stderr.strip().splitlines() or ["?"])[-1][:200]; return 기록
        if True:
            j = json.load(open(f"{뿌리}/하네스/판/{판}/판정.json", encoding="utf-8"))
            open(f"{뿌리}/원화3d/과정/쇼츠/대본/{번호}_업로드.txt", "w", encoding="utf-8").write(f"채널: 서재용 (쇼츠) · 파일 {mp4} · 하네스 판 {판} · 판정 {j['판정']}\n\n제목: (Claude 가 대본에서 한 줄)\n\n설명: 하네스 보고서 https://sigongjoa.github.io/art2real/판/{판}/보고.html\n")
            배포 = f"{뿌리}/원화3d/과정/쇼츠/배포.md"
            if not re.search(rf"\| [^|]*판 {re.escape(판)} \|", open(배포, encoding="utf-8").read()):   # 같은 판 줄은 한 번만(다시 구워도 장부 줄은 그대로 · 올린 주소 보존)
              with open(배포, "a", encoding="utf-8") as f: f.write(f"| {번호} 판 {판} | 대화 쇼츠 `out/영상05/대화/{편}/{편}.mp4` | — | 서재용 업로드 대기 | 하네스 자동 · 판정 {j['판정']} |\n")
            기록["mp4"] = mp4
    return 기록
def 판에넣기(판, 쇼):   # 판 기록에 쇼츠: 웹용 사본(540 폭 · 원본은 out 그대로) · 대본 · 상태 → 하네스/판/<판>/쇼츠.json
    d = f"{뿌리}/하네스/판/{판}/"; 편 = 쇼.get("편") if isinstance(쇼, dict) else None
    if not 편: json.dump({"상태": "없음", **(쇼 if isinstance(쇼, dict) else {})}, open(d + "쇼츠.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); return
    mp4 = 쇼.get("mp4") or f"{뿌리}/out/영상05/대화/{편}/{편}.mp4"; 웹 = d + "쇼츠.mp4"
    if os.path.exists(mp4): subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", 웹], check=False)
    줄 = []
    for l in open(영상 + f"대화/{편}/대본.tsv", encoding="utf-8").read().splitlines()[2:]:
        c = l.split("\t")
        if len(c) >= 6: 줄.append({"누구": c[0], "큰글": c[4], "말": c[5].split("｜")[0]})
    json.dump({"편": 편, "웹용": os.path.exists(웹), "길이": re.sub(r"^\S+\.mp4\s*", "", 쇼.get("굽기", "")), "상태": "업로드 대기", "주소": None, "대본": 줄}, open(d + "쇼츠.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    주소갱신(판)   # 상태 · 주소는 장부에서
def 주소갱신(판):   # 올린 뒤: 장부(배포.md)를 다시 읽어 쇼츠.json 의 상태 · 주소만 고침(웹용 사본 · 대본은 그대로)
    d = f"{뿌리}/하네스/판/{판}/"; j = json.load(open(d + "쇼츠.json", encoding="utf-8")); 배 = open(f"{뿌리}/원화3d/과정/쇼츠/배포.md", encoding="utf-8").read()
    m = re.search(rf"\| [^|]*판 {re.escape(판)} \|[^\n]*\| (서재용[^|]*?)\|", 배)
    if m:
        상 = m.group(1).strip(); 주 = re.search(r"\((https://(?:www\.)?youtube\.com/shorts/[\w-]+)\)", 상)
        j["상태"] = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", 상).replace("**", ""); j["주소"] = 주.group(1) if 주 else None
    json.dump(j, open(d + "쇼츠.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); return j
if __name__ == "__main__": print(json.dumps(만들기(sys.argv[1], "--안굽기" not in sys.argv), ensure_ascii=False, indent=1))
