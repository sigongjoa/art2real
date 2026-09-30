# -*- coding: utf-8 -*-
"""커뮤니티 수집 — 쇼츠 편집 · 유지율 글을 여러 곳에서 모은다 (2026-09-30 「코드 짜서 더 많이 봐 · 다른 데도」).
    python 수집.py -> out/조사/쇼츠/글.jsonl (곳 · 주소 · 제목 · 본문 4000 자) · 수집.log
예의: 요청 사이 1.5~3 초 · 빈 응답 · 403 이면 그 곳은 건너뛴다(우회하지 않는다) · 곳마다 글 최대 60."""
import os, re, json, time, random, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
O = r"G:\art2real\원화3d\out\조사\쇼츠"; os.makedirs(O, exist_ok=True)
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); open(os.path.join(O, "수집.log"), "a", encoding="utf-8").write(s + "\n")
def 받기(u):
    time.sleep(random.uniform(1.5, 3.0))
    try: r = S.get(u, timeout=20)
    except Exception as e: log("  ERR", u[:80], str(e)[:60]); return ""
    if r.status_code != 200 or len(r.content) < 500: log("  빈/막힘", r.status_code, len(r.content), u[:80]); return ""
    return r.text
한 = ["쇼츠 편집", "쇼츠 자막", "쇼츠 효과음", "쇼츠 조회율", "쇼츠 첫 3초", "쇼츠 팁", "숏폼 편집"]; 영 = ["shorts retention editing", "shorts hook first seconds", "shorts captions sound effects", "shorts editing style", "shorts swipe away rate"]
곳 = []   # (이름, 검색 주소들, 글 링크 정규식, 본문 선택자)
곳.append(("레딧", ["https://old.reddit.com/r/%s/search?q=%s&restrict_sr=on&sort=top&t=year" % (sub, quote(q)) for sub in ("NewTubers", "youtubers", "SmallYTChannel", "VideoEditing", "PartneredYoutube") for q in 영[:3]], r'href="(https://old\.reddit\.com/r/\w+/comments/[^"]+)"', "div.sitetable"))
곳.append(("아카", ["https://arca.live/b/%s?target=all&keyword=%s" % (b, quote(q)) for b in ("youtube", "streamer") for q in 한[:4]], r'href="(/b/\w+/\d+)[?"]', "div.article-body"))
곳.append(("펨코", ["https://www.fmkorea.com/search.php?mid=home&search_target=title_content&search_keyword=%s" % quote(q) for q in 한[:4]], r'href="(/\d{8,})"', "div.xe_content"))
곳.append(("루리웹", ["https://bbs.ruliweb.com/search?q=%s" % quote(q) for q in 한[:4]], r'href="(https://bbs\.ruliweb\.com/[^"]+/read/\d+)', "div.view_content"))
for g, kind in (("creator", "mgallery"), ("youtubeeditor", "mgallery"), ("shorts", "mgallery"), ("videoediting", "mini"), ("ytcreation", "mini")):
    곳.append(("디시:" + g, ["https://gall.dcinside.com/%s/board/lists/?id=%s&s_type=search_subject_memo&s_keyword=%s" % (kind, g, quote(q)) for q in ("쇼츠", "편집", "자막", "효과음", "조회율")], r'href="(/%s/board/view/\?id=%s&no=\d+)' % (kind, g), "div.write_div"))
본 = set(json.loads(l)["주소"] for l in open(os.path.join(O, "글.jsonl"), encoding="utf-8")) if os.path.exists(os.path.join(O, "글.jsonl")) else set()
out = open(os.path.join(O, "글.jsonl"), "a", encoding="utf-8")
for 이름, 검색들, 정규, 선택 in 곳:
    링크 = []; 막힘 = 0
    for u in 검색들:
        h = 받기(u)
        if not h:
            막힘 += 1
            if 막힘 >= 2: break
            continue
        for m in re.findall(정규, h):
            m = urljoin(u, m.replace("&amp;", "&"))
            if m not in 링크: 링크.append(m)
    log(이름, "링크", len(링크)); n = 0
    for u in 링크[:60]:
        if u in 본: continue
        h = 받기(u)
        if not h: continue
        d = BeautifulSoup(h, "html.parser"); t = (d.title.get_text() if d.title else "")[:120]; el = d.select_one(선택) or d.body
        txt = re.sub(r"\s+", " ", el.get_text(" ")) if el else ""
        if len(txt) < 200: continue
        out.write(json.dumps(dict(곳=이름, 주소=u, 제목=t, 본문=txt[:4000]), ensure_ascii=False) + "\n"); out.flush(); n += 1
    log(이름, "글", n)
log("끝")
