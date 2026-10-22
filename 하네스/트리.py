# 연구 트리 — claudedocs/문제트리.md(원본 · 사람이 고침) → 자료 {목표, 줄기[{이름, 잎[{번호, 이름, 상태, 증거, 다음, 판[]}]}]} + 판마다 붙은 판정 · Pages 메인 · 판 보고서가 같이 씀 · 10-22
import re, glob, json, os
뿌리 = "G:/art2real"; 상태표 = {"🟢": "해결", "🔴": "열림", "🟡": "보류", "⚫": "기각", "⚪": "안 봄"}
def 읽기():
    t = open(f"{뿌리}/claudedocs/문제트리.md", encoding="utf-8").read()
    목표 = re.search(r"## ① 목표\s*\n\s*\*\*(.+?)\*\*", t).group(1).strip(); 줄기 = []
    for m in re.finditer(r"### (\w) (.+?)\n(.*?)(?=\n### |\n## |\Z)", t, re.S):
        잎 = []
        for 줄 in m.group(3).splitlines():
            칸 = [c.strip() for c in 줄.strip().strip("|").split("|")]
            if len(칸) < 4 or not re.match(r"\w\d", 칸[0]) : continue
            번호, 이름 = 칸[0].split(" ", 1); 이름 = re.sub(r"\*\*|\(사용자 줄기\)", "", 이름).strip()
            잎.append({"번호": 번호, "이름": 이름, "상태": 상태표.get(칸[1], 칸[1]), "증거": re.sub(r"\*\*", "", 칸[2]), "다음": 칸[3], "판": [], "줄기": "사용자 줄기" in 칸[0]})
        줄기.append({"글자": m.group(1), "이름": m.group(2).split("—")[0].strip(), "잎": 잎})
    판들 = []
    for p in glob.glob(f"{뿌리}/하네스/판/*/판정.json"):
        from omegaconf import OmegaConf
        판 = os.path.basename(os.path.dirname(p)); j = json.load(open(p, encoding="utf-8")); c = OmegaConf.load(os.path.dirname(p) + "/설정.yaml")
        판들.append({"판": 판, "가지": str(c.판.가지), "판정": j["판정"], "명제": str(c.판.get("시도") or c.판.get("명제") or c.판.물음), "날짜": j.get("날짜", "")})
    for 판 in 판들:
        for 줄 in 줄기:
            for 잎 in 줄["잎"]:
                if 잎["번호"] == 판["가지"]: 잎["판"].append(판)
    return {"목표": 목표, "줄기": 줄기}
if __name__ == "__main__": print(json.dumps(읽기(), ensure_ascii=False, indent=1)[:2500])
