# -*- coding: utf-8 -*-
"""**정답 있는 케이스를 모은다.** Poly Pizza 에서 CC0 모델만 골라 받는다.

    python 모으기.py [키워드 ...] [--n 6]
        -> out/모델/<이름>.glb  +  out/모델/목록.json

첫 대조는 VRoid 11종이었다 — 전부 같은 생성기 · 전부 애니 인체 · 전부 T포즈다.
거기서 나온 결론(치마가 부피비를 망친다)이 **「속이 빈 형태」 때문인지 「복잡한 실루엣」
때문인지 못 가른다.** 메카는 실루엣이 복잡한데 속이 안 비었으니 그 둘을 가르는 대조군이다.

## 규약

- **CC0 만 받는다.** 모델 페이지의 `Licence` 가 CC0 이 아니면 건너뛴다. 조건 붙은 걸
  섞으면 나중에 이 저장소 전체가 그 조건에 걸린다
- 페이지에 `window.__SERVER_APP_STATE__` 로 메타가 통째로 박혀 있다. 거기서
  `ResourceID`(glb uuid) · `Licence` · `Tris` · `Creator` 를 읽는다
- glb 는 `https://static.poly.pizza/<ResourceID>.glb` 로 인증 없이 받아진다

받은 것은 `시트.py` 가 그대로 먹고 `대조.py` 가 자동으로 채점한다.
"""
import argparse
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "모델")
UA = {"User-Agent": "Mozilla/5.0 (art2real reference collector)"}
TRIS = (300, 400000)                             # 너무 작으면 형태가 없고 너무 크면 느리다


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    return b if binary else b.decode("utf-8", "replace")


def meta(pid):
    """모델 페이지에 박힌 상태 JSON 에서 메타를 읽는다."""
    html = get("https://poly.pizza/m/%s" % pid)
    m = re.search(r"window\.__SERVER_APP_STATE__\s*=\s*(\{.*?\})\s*(?:let |</script>)", html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))["initialData"]["model"]
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="*",
                    default=["mech", "robot", "knight", "cloak", "dress", "monster"])
    ap.add_argument("--n", type=int, default=6, help="키워드당 최대 개수")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    listing = os.path.join(OUT, "목록.json")
    have = json.load(open(listing, encoding="utf-8")) if os.path.exists(listing) else []
    seen = {r["id"] for r in have}

    for kw in a.keywords:
        try:
            ids = list(dict.fromkeys(re.findall(r"/m/([A-Za-z0-9_-]{6,})",
                                                get("https://poly.pizza/search/%s" % kw))))
        except Exception as e:
            print("  %-10s 검색 실패 %s" % (kw, e)); continue
        got = 0
        for pid in ids:
            if got >= a.n:
                break
            if pid in seen:
                got += 1; continue
            d = meta(pid)
            if not d:
                continue
            lic = str(d.get("Licence", ""))
            tris = int(d.get("Tris") or 0)
            if "CC0" not in lic.upper():
                continue                          # **CC0 만.** 조건 붙은 건 안 받는다
            if not (TRIS[0] <= tris <= TRIS[1]):
                continue
            # 제목이 겹치는 게 흔하다 (Mech 4개). **id 를 붙여야 덮어쓰지 않는다**
            name = re.sub(r"[^0-9A-Za-z가-힣]+", "_",
                          "%s_%s" % (kw, d.get("Title", pid))).strip("_")[:40] + "_" + pid
            path = os.path.join(OUT, name + ".glb")
            try:
                blob = get("https://static.poly.pizza/%s.glb" % d["ResourceID"], binary=True)
            except Exception as e:
                print("  %-10s %s 내려받기 실패 %s" % (kw, name, e)); continue
            open(path, "wb").write(blob)
            have.append({"id": pid, "kw": kw, "name": name, "title": d.get("Title"),
                         "creator": (d.get("Creator") or {}).get("Username"),
                         "licence": lic, "tris": tris, "bytes": len(blob),
                         "category": d.get("Category")})
            seen.add(pid); got += 1
            print("  %-8s %-40s %6d 삼각 · %7d B · %s" % (kw, name, tris, len(blob), lic))
        print("  -- %s: %d 개" % (kw, got))

    json.dump(have, open(listing, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n  모두 %d 개 -> %s" % (len(have), OUT))
    assert all("CC0" in r["licence"].upper() for r in have), "CC0 아닌 게 섞였다"


if __name__ == "__main__":
    main()
