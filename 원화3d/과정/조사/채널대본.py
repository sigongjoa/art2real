# -*- coding: utf-8 -*-
"""채널별 쇼츠 대본 비교 — 정보 전달 유튜버들의 쇼츠 자막을 받아 채널마다 뼈대 통계 (2026-09-30 「이것과 유사한 정보 전달 유튜버들을 알아봐」).
    python 채널대본.py -> out/조사/대본/<채널>/<id>.txt · 채널비교.tsv · 채널비교_첫끝.txt(채널마다 첫 · 끝 조각 — 분석용 · 싣지 않는다)
영상은 안 받는다. 채널마다 쇼츠 탭에서 조회 많은 순 12 편."""
import os, sys, json, re, subprocess, glob, statistics as st
O = r"G:\art2real\원화3d\out\조사\대본"; Y = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--ignore-errors"]
채널 = {"조코딩": "@jocoding", "1분과학": "@1minscience", "안될과학": "@Unrealscience", "과학드림": "@ScienceDream", "긱블": "channel/UCp94pzrtA5wPyZazbDq0CXA", "Fireship": "@Fireship", "ZackDFilms": "@zackdfilms",
        "사나고": "?사나고 Sanago", "사물궁이": "?사물궁이 잡학지식", "너진똑": "?너진똑", "1분만": "?1분만", "노마드코더": "?노마드 코더 Nomad Coders", "잇섭": "?ITSub잇섭", "MichaelReeves": "@MichaelReeves", "StuffMadeHere": "@StuffMadeHere"}
def J(args):
    r = subprocess.run(Y + args, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    try: return json.loads(r.stdout) or {}
    except Exception: return {}
def vtt글(p):
    out, 앞 = [], ""
    for blk in re.split(r"\n\n+", open(p, encoding="utf-8", errors="ignore").read()):
        m = re.search(r"(\d\d):(\d\d):(\d\d)\.\d+ -->", blk)
        if not m: continue
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)); 말 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", " ".join(blk.split("\n")[1:]))).strip()
        if 말 and 말 != 앞 and not 앞.endswith(말): out.append((t, 말)); 앞 = 말
    return out
표 = []; 첫끝 = []
for 이름, h in 채널.items():
    if h.startswith("?"):
        d = J(["--flat-playlist", "--playlist-end", "3", "-J", "ytsearch3:" + h[1:]]); u = next((e.get("channel_url") for e in d.get("entries", []) if e and e.get("channel_url")), None)
    else: u = "https://www.youtube.com/" + h
    if not u: print(이름, "채널 못 찾음", flush=True); continue
    es = [e for e in J(["--flat-playlist", "--playlist-end", "80", "-J", u.rstrip("/") + "/shorts"]).get("entries", []) if e]; es.sort(key=lambda e: -(e.get("view_count") or 0)); D = os.path.join(O, 이름); os.makedirs(D, exist_ok=True); S = []
    언어 = "en" if 이름 in ("Fireship", "ZackDFilms", "MichaelReeves", "StuffMadeHere") else "ko"
    for e in es[:12]:
        f = os.path.join(D, e["id"])
        if not glob.glob(f + "*.vtt"): subprocess.run(Y + ["--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", 언어, "--sub-format", "vtt", "--sleep-requests", "1", "-o", f, "https://www.youtube.com/shorts/" + e["id"]], capture_output=True)
        g = glob.glob(f + "*.vtt")
        if not g: continue
        t = vtt글(g[0])
        if len(t) < 3: continue
        글 = " ".join(s for _, s in t); open(f + ".txt", "w", encoding="utf-8").write("# %s | %s | 조회 %s\n" % (이름, e.get("title", ""), e.get("view_count")) + "\n".join("%02d %s" % x for x in t))
        S.append(dict(초=t[-1][0] + 2, 자=len(글), 조회=e.get("view_count") or 0, 첫=글[:60], 끝=글[-60:]))
    if not S: print(이름, "쇼츠", len(es), "· 자막 0", flush=True); continue
    인사 = sum(1 for s in S if re.search(r"안녕|여러분|오늘은|hey|hello|welcome|what's up", s["첫"], re.I)); 물음 = sum(1 for s in S if re.search(r"\?|까요|나요|아세요|do you|did you|what if|why", s["첫"], re.I)); 구독 = sum(1 for s in S if re.search(r"구독|좋아요|subscribe|follow|like", s["끝"], re.I))
    표.append("\t".join(str(x) for x in (이름, len(es), len(S), int(st.median(s["초"] for s in S)), int(st.median(s["자"] for s in S)), round(st.median(s["자"] / s["초"] for s in S), 1), int(st.median(s["조회"] for s in S)), 인사, 물음, 구독)))
    첫끝.append("## %s\n" % 이름 + "\n".join("첫: %s | 끝: %s" % (s["첫"], s["끝"]) for s in S[:4])); print(표[-1], flush=True)
open(os.path.join(O, "채널비교.tsv"), "w", encoding="utf-8").write("채널\t쇼츠수(탭)\t대본\t초(중앙)\t글자(중앙)\t초당글자\t조회(중앙)\t인사로시작\t물음으로시작\t구독으로끝\n" + "\n".join(표)); open(os.path.join(O, "채널비교_첫끝.txt"), "w", encoding="utf-8").write("\n\n".join(첫끝)); print("끝")
