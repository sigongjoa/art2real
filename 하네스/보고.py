# 하네스 보고서 — 판마다 같은 틀의 보고.md (하네스/판/<판>/) · 판정.json · 설정.yaml · 학습.json · 특징.json 에서 만든다 · 10-22
# 사용: python 하네스/보고.py <판이름>   (하네스.py 가 판 끝에 자동으로 부름) · 「해석」 · 「다음 가지」 칸만 사람(또는 Claude)이 채운다 — 다시 만들어도 그 칸은 보존
import os, sys, json, re
뿌리 = "G:/art2real"
틀 = """# 판 {이름} — {물음}

| 가지 | 종류 | 바탕 | 바꾼 손잡이 | 에폭 | git | 날짜 |
|---|---|---|---|---|---|---|
| {가지} | {종류} | 127 (하네스/conf/바탕.yaml) | {바뀐} | {에폭} | `{git}` | {날짜} |

## 1. 판정: **{판정}**

| 지표 | 식 | 문턱 | 이 판 | 대조({대조판}) | 통과 |
|---|---|---|---|---|---|
{기준표}

## 2. 숫자 — 이 판 대 대조

| 지표 | 이 판 | 대조 |
|---|---|---|
{지표표}

## 모델 구조
{구조}

## 3. 학습 곡선

| 에폭 | 학습 loss | 시험 loss | 덩어리 수 맞음 |
|---|---|---|---|
{곡선표}

![시트](시트.png)

## 4. 점검

### 4.1 연기 판
첫 loss {첫loss} → 배치 하나 40 걸음 {한배치} · VRAM {vram} GB

### 4.2 층보기 (시험 64 · 4 층)
칸끼리 닮음 {칸닮음} (1 = 6 칸 같음) · 빈 조각 주의 몫 {빈조각} (빈 조각 비율 0.54) · 주의 엔트로피 {엔트로피} · 출력 자리 퍼짐 {퍼짐} (정답 0.148)

### 4.3 탐침 — 합성 그림 (블록 4 · 128)
구조 6 종 {탐구조} · 곡률 R² {탐곡률} · (블록 3: {탐구조3} · {탐곡률3})

### 4.4 특징 — 실제 도면 (조각 라벨 · 하네스/특징.py)
{특징}

## 쇼츠
{쇼츠}

## 5. 해석
{해석}

## 6. 다음 가지 (사람이 고름 · claudedocs/문제트리.md)
{다음}

## 7. 재현
`python 하네스/하네스.py --config-name 판_{이름}` · 설정 [설정.yaml](설정.yaml) · 판정 [판정.json](판정.json) · 산출 `{산출}`
"""
사람칸 = "<!-- 사람 칸: 아래를 채운다 · 보고서를 다시 만들어도 남는다 -->\n(비어 있음)"
def f(v, n=3): return "—" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))
def 만들기(판, 모션=None, 파일="보고.html"):   # 모션 = None | 도장 | 그리기 (시안 고르는 동안)
    d = f"{뿌리}/하네스/판/{판}/"; j = json.load(open(d + "판정.json", encoding="utf-8")); 지 = j["지표"]
    from omegaconf import OmegaConf
    c = OmegaConf.load(d + "설정.yaml"); 대 = dict(c.대조.get("값", {})) if c.대조 else {}
    곡 = json.load(open(d + "학습.json", encoding="utf-8")) if os.path.exists(d + "학습.json") else []
    특 = json.load(open(d + "특징.json", encoding="utf-8")) if os.path.exists(d + "특징.json") else None
    구 = json.load(open(d + "구조.json", encoding="utf-8")) if os.path.exists(d + "구조.json") else None
    쇼 = json.load(open(d + "쇼츠.json", encoding="utf-8")) if os.path.exists(d + "쇼츠.json") else None
    쇼글 = "(이 판은 쇼츠를 안 만듦)"
    if 쇼 and 쇼.get("편"):
        쇼글 = f"편 {쇼['편']} · {쇼['길이']} · {쇼['상태']}" + ("\n\n[쇼츠 영상](쇼츠.mp4)" if 쇼.get("웹용") else "")
        쇼글 += "\n\n| 누구 | 말 |\n|---|---|\n" + "\n".join(f"| {r['누구']} | {r['말']} |" for r in 쇼["대본"])
    import 구조 as 구조모; 구조글 = 구조모.md(구) if 구 else "(이 판은 구조를 안 잼)"
    옛 = open(d + "보고.md", encoding="utf-8").read() if os.path.exists(d + "보고.md") else ""
    def 보존(제목):
        m = re.search(rf"## {제목}[^\n]*\n(.*?)(?=\n## |\Z)", 옛, re.S); return m.group(1).strip() if m and "(비어 있음)" not in m.group(1) else 사람칸
    if 특:
        이름 = list(특["조각 비율"]); 특글 = "| | " + " | ".join(이름) + " |\n|---|" + "---|" * len(이름) + "\n"
        특글 += "| 조각 비율 | " + " | ".join(f(특["조각 비율"][k], 2) for k in 이름) + " |\n"
        for 층 in (1, 4): 특글 += f"| 주의 쏠림 {층} 층 (배) | " + " | ".join(f(특[f'쏠림{층}'][k], 2) for k in 이름) + " |\n"
        for 키, 말 in (("탐침_학습CNN", "학습 CNN 재현율"), ("탐침_무작위CNN", "무작위 CNN 재현율"), ("탐침_화소", "화소 그대로 재현율")): 특글 += f"| {말} (균형 {f(특[키][0], 2)}) | " + " | ".join(f(특[키][1][k], 2) for k in 이름) + " |\n"
        특글 += "\n![특징](특징.png)"
    else: 특글 = "(이 판은 특징 점검을 안 함)"
    연 = j.get("연기", {})
    글 = 틀.format(이름=판, 물음=c.판.물음, 가지=c.판.가지, 종류=c.판.종류, 바뀐=", ".join(f"{k}: {a} → {b}" for k, (a, b) in j["바뀐 손잡이"].items()) or "없음(재현)", 에폭=c.학습.에폭, git=j["git"],
                  날짜=j.get("날짜", "—"), 판정=j["판정"], 대조판=c.대조.get("판", "—") if c.대조 else "—",
                  기준표="\n".join(f"| {r['지표']} | {r['식']} | {r['값']} | {f(r['이 판'])} | {f(대.get(r['지표']))} | {'✓' if r['통과'] else '✗'} |" for r in j["기준"]),
                  지표표="\n".join(f"| {k} | {f(v)} | {f(대.get(k))} |" for k, v in 지.items()),
                  곡선표="\n".join(f"| {r['에폭']} | {r['학습']:.3f} | {r['시험']:.3f} | {r.get('몸수맞음', r.get('몸 수 맞음', 0)):.3f} |" for r in 곡),
                  첫loss=f(연.get("첫loss")), 한배치=f(연.get("한배치40걸음")), vram=f(연.get("VRAM_GB"), 2), 칸닮음=f(지.get("칸닮음4")), 빈조각=f(지.get("빈조각주의4")), 엔트로피=f(지.get("주의엔트로피4")), 퍼짐=f(지.get("자리퍼짐")),
                  탐구조=f(지.get("탐침_구조")), 탐곡률=f(지.get("탐침_곡률")), 탐구조3=f(지.get("탐침3_구조")), 탐곡률3=f(지.get("탐침3_곡률")), 특징=특글, 구조=구조글, 쇼츠=쇼글, 해석=보존("5. 해석"), 다음=보존("6. 다음 가지"), 산출=j.get("산출 폴더", "—"))
    open(d + "보고.md", "w", encoding="utf-8").write(글)
    import 보고html; 보고html.만들기(판, d, c, j, 지, 대, 곡, 특, 보존("5. 해석"), 보존("6. 다음 가지"), 모션, 파일, 구, 쇼); return d + "보고.md"
if __name__ == "__main__": print(만들기(sys.argv[1], *(sys.argv[2:4])))
