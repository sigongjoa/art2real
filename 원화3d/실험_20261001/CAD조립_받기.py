"""공개 CAD 조립 데이터셋 둘을 받는다 (10-07) · 로그인 없음.

Fusion 360 Gallery Assembly a1.0.0 (S3 7z 11 개 · 18.8 GB · 비상업 연구 라이선스)
AutoMate (Zenodo 7776208 · assemblies.zip + step.zip · CC0) — md5 대조.
저장: 원화3d/out/레퍼런스/CAD조립/{fusion_assembly,automate}/ · out/ 은 git 밖.
한 연결이 ~200 KB/s(태평양 건너) 라 Range 16 조각으로 나눠 받는다. 조각 파일 크기로 이어받기.
G: 여유가 40 GB 아래로 떨어질 것 같으면 시작 전에 멈춘다.
"""
import hashlib, json, shutil, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "CAD조립"
S3 = "https://fusion-360-gallery-dataset.s3-us-west-2.amazonaws.com/assembly/a1.0.0/"
ZEN = "https://zenodo.org/api/records/7776208/files/"
N = 16
FLOOR = 40 << 30


def size(url):
    for i in range(20):  # DNS 가 가끔 끊긴다
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
                return int(r.headers["content-length"])
        except Exception as e:
            print("  HEAD 다시", e, flush=True); time.sleep(30)
    raise RuntimeError(f"HEAD 실패 {url}")


def chunk(url, part, a, b):
    # 조각 하나 · 끊기면 이어서 다시
    for i in range(30):
        have = part.stat().st_size if part.exists() else 0
        if a + have > b:
            return
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={a + have}-{b}"})
            with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        except Exception as e:
            print("  다시", part.name, e, flush=True); time.sleep(10 * (i + 1))
    raise RuntimeError(f"조각 실패 {part}")


def get(url, out, md5=None):
    if out.exists():
        print("있음", out.name, out.stat().st_size, flush=True); return
    n = size(url)
    free = shutil.disk_usage(out.parent).free
    assert free - n > FLOOR, f"여유 부족: {free >> 30} GB - {n >> 30} GB"
    step = -(-n // N)
    parts = [out.with_name(f"{out.name}.p{i:02d}") for i in range(N)]
    t = time.time()
    with ThreadPoolExecutor(N) as ex:
        list(ex.map(lambda i: chunk(url, parts[i], i * step, min(n, (i + 1) * step) - 1), range(N)))
    tmp = out.with_name(out.name + ".tmp")
    with open(tmp, "wb") as f:
        for p in parts:
            with open(p, "rb") as g:
                shutil.copyfileobj(g, f, 8 << 20)
    assert tmp.stat().st_size == n, f"크기 다름 {tmp.stat().st_size} != {n}"
    if md5:
        h = hashlib.md5()
        with open(tmp, "rb") as f:
            while b := f.read(8 << 20):
                h.update(b)
        assert h.hexdigest() == md5, f"md5 다름 {out.name}"
    tmp.rename(out)
    for p in parts:
        p.unlink()
    print(f"받음 {out.name} {n / 2**30:.2f} GB {(time.time() - t) / 60:.0f} 분 md5={'맞음' if md5 else '-'}", flush=True)


def zenodo(names):
    d = json.load(urllib.request.urlopen("https://zenodo.org/api/records/7776208", timeout=60))
    md5 = {f["key"]: f["checksum"].split(":")[1] for f in d["files"]}
    for k in names:
        get(ZEN + k + "/content", ROOT / "automate" / k, md5[k])


def fusion():
    for i in range(11):
        get(S3 + f"a1.0.0_{i:02d}.7z", ROOT / "fusion_assembly" / f"a1.0.0_{i:02d}.7z")


if __name__ == "__main__":
    # 사용: python CAD조립_받기.py automate | fusion
    for d in ("automate", "fusion_assembly"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    zenodo(["assemblies.zip", "step.zip"]) if sys.argv[1] == "automate" else fusion()
    print("끝", flush=True)
