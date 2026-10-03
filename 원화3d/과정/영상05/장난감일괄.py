"""장난감 쇼츠 일괄 굽기 — 토큰 없이 PC 혼자. mp4 가 없고 대본.tsv · 장면.py 가 있는 편을 차례로 굽는다(동시 2 개 = GPU 자리 2).
    python 장난감일괄.py        → 결과는 out/영상05/장난감/_일괄.log (편마다 「완성」/「실패」 한 줄)
실패한 편은 사람(또는 에이전트)이 나중에 _블렌더.log 를 보고 고친다. 스틸 확인은 하지 않는다."""
import os, subprocess, datetime
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "장난감"); OUT = "G:/art2real/out/영상05/장난감"
LOG = OUT + "/_일괄.log"

def todo():
    for d in sorted(os.listdir(SRC)):
        s = os.path.join(SRC, d)
        if os.path.exists(f"{OUT}/{d}/{d}.mp4"): continue
        if os.path.exists(os.path.join(s, "대본.tsv")) and os.path.exists(os.path.join(s, "장면.py")): yield d

def bake(d):
    r = subprocess.run(["python", "장난감굽기.py", d], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = r.returncode == 0 and os.path.exists(f"{OUT}/{d}/{d}.mp4")
    last = (r.stdout.strip().splitlines() or [""])[-1] if ok else (r.stdout + r.stderr).strip().replace("\n", " | ")[-300:]
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%H:%M} {'완성' if ok else '실패'} {d} — {last}\n")

if __name__ == "__main__":
    jobs = list(todo())
    with open(LOG, "a", encoding="utf-8") as f: f.write(f"--- {datetime.datetime.now():%m-%d %H:%M} 시작 {len(jobs)} 편\n")
    with ThreadPoolExecutor(2) as ex: list(ex.map(bake, jobs))
    with open(LOG, "a", encoding="utf-8") as f: f.write(f"--- {datetime.datetime.now():%H:%M} 끝\n")
