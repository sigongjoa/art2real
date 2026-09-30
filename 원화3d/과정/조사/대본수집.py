# -*- coding: utf-8 -*-
"""쇼츠 대본 수집 — 다른 사람들의 요즘 쇼츠 자막(대본)을 받아 글로 (2026-09-30 「요새 다른 사람들 대본을 찾아서 다운로드」).
    python 대본수집.py -> out/조사/대본/<id>.txt(시각 + 말) · 목록.tsv(채널 · 제목 · 길이 · 조회 · 글자 · 초당 글자)
영상은 안 받는다(자막 · 정보만). 사적 분석용 — out/ 은 git 밖 · 대본을 옮겨 싣지 않는다.
고르는 법: 채널 쇼츠 탭 + 검색어마다 65 초 이하 · 조회 많은 순 · 곳마다 N 편."""
import os, sys, json, re, subprocess, glob
O = r"G:\art2real\원화3d\out\조사\대본"; os.makedirs(O, exist_ok=True)
Y = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--ignore-errors"]
채널 = ["https://www.youtube.com/@codingapple/shorts"]
검색 = ["코딩 쇼츠 설명", "3D 프린터로 만들어봤다 쇼츠", "블렌더 모델링 쇼츠", "AI로 만들어봤습니다 쇼츠", "피규어 만들기 쇼츠", "직접 만들어봤다 쇼츠 실패", "개발자 쇼츠 썰"]
def 목록(u, n):
    r = subprocess.run(Y + ["--flat-playlist", "--playlist-end", str(n), "-J", u], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    try: d = json.loads(r.stdout)
    except Exception: return []
    return [e for e in d.get("entries", []) if e]
후보 = {}
for u in 채널:
    for e in 목록(u, 60): 후보[e["id"]] = dict(id=e["id"], 제목=e.get("title", ""), 조회=e.get("view_count") or 0, 길이=e.get("duration") or 0, 곳="코딩애플")
for q in 검색:
    for e in 목록("ytsearch40:" + q, 40):
        if (e.get("duration") or 999) <= 65: 후보.setdefault(e["id"], dict(id=e["id"], 제목=e.get("title", ""), 조회=e.get("view_count") or 0, 길이=e.get("duration") or 0, 곳=q, 채널=e.get("channel") or e.get("uploader") or ""))
print("후보", len(후보), flush=True)
고름 = []
for 곳 in ["코딩애플"] + 검색:
    x = sorted([v for v in 후보.values() if v["곳"] == 곳], key=lambda v: -v["조회"]); 고름 += x[:25 if 곳 == "코딩애플" else 8]
def vtt글(p):
    out, 앞 = [], ""
    for blk in re.split(r"\n\n+", open(p, encoding="utf-8", errors="ignore").read()):
        m = re.search(r"(\d\d):(\d\d):(\d\d)\.\d+ -->", blk)
        if not m: continue
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)); 말 = re.sub(r"<[^>]+>", "", " ".join(blk.split("\n")[1:])).strip()
        말 = re.sub(r"\s+", " ", 말)
        if 말 and 말 != 앞 and not 앞.endswith(말): out.append((t, 말[len(앞):].strip() if 말.startswith(앞) and 앞 else 말)); 앞 = 말
    return [(t, s) for t, s in out if s]
줄 = []
for k, v in enumerate(고름):
    f = os.path.join(O, v["id"])
    if not glob.glob(f + "*.vtt"): subprocess.run(Y + ["--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "ko", "--sub-format", "vtt", "--sleep-requests", "1", "-o", f, "https://www.youtube.com/shorts/" + v["id"]], capture_output=True)
    g = glob.glob(f + "*.vtt")
    if not g: print(k, "자막 없음", v["제목"][:30], flush=True); continue
    t = vtt글(g[0]); 글 = " ".join(s for _, s in t)
    if len(글) < 40: continue
    open(f + ".txt", "w", encoding="utf-8").write("# %s | %s | %s초 | 조회 %s\n" % (v.get("채널", v["곳"]), v["제목"], v["길이"], v["조회"]) + "\n".join("%02d %s" % (a, b) for a, b in t))
    줄.append("\t".join(str(x) for x in (v["id"], v.get("채널", v["곳"]), v["제목"][:50], v["길이"], v["조회"], len(글), round(len(글) / max(1, v["길이"]), 1)))); print(k, "ok", v["제목"][:30], len(글), flush=True)
open(os.path.join(O, "목록.tsv"), "w", encoding="utf-8").write("id\t채널\t제목\t초\t조회\t글자\t초당글자\n" + "\n".join(줄)); print("끝 · 대본", len(줄))
