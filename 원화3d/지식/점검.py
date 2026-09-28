# -*- coding: utf-8 -*-
"""지식 위키 점검 — 셀 수 있는 것만. python 점검.py  (문제 있으면 종료 코드 1)

깨진 링크 · 목차에 없는 쪽 · 규칙 머리 칸 빠짐 · 검사 칸의 스크립트 없음 · 30 일 넘게 확인 안 됨.
"""
import os, re, sys, datetime
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
칸 = ("상태:", "종류:", "확정도:", "승인:", "확인한 날:")

def 점검(오늘=None):
    오늘 = 오늘 or datetime.date.today(); 문제 = []
    쪽 = [os.path.join(d, f) for d, _, fs in os.walk(R) for f in fs if f.endswith(".md")]
    목차 = open(os.path.join(R, "index.md"), encoding="utf-8").read()
    for p in 쪽:
        t = open(p, encoding="utf-8").read(); 이름 = os.path.relpath(p, R).replace("\\", "/")
        for l in re.findall(r"\]\(([^)#]+)\)", t):
            if not l.startswith("http") and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), l))): 문제.append("깨진 링크 %s → %s" % (이름, l))
        if 이름.startswith(("규칙/", "부위/", "베이스/")) and 이름 not in 목차: 문제.append("목차에 없음 " + 이름)
        if 이름.startswith("규칙/"):
            문제 += ["머리 칸 빠짐 %s: %s" % (이름, k) for k in 칸 if k not in t]
            for s in re.findall(r"`(실험_\d+/[^`]+\.py)`", t):
                if not os.path.exists(os.path.join(원화3d, s)): 문제.append("검사 스크립트 없음 %s: %s" % (이름, s))
            m = re.search(r"확인한 날: (\d{4})-(\d\d)-(\d\d)", t)
            if m and "상태: 쓰는 중" in t and (오늘 - datetime.date(*map(int, m.groups()))).days > 30: 문제.append("30 일 넘게 확인 안 됨 " + 이름)
    return 쪽, 문제

if __name__ == "__main__":
    쪽, 문제 = 점검()
    _, 늙은 = 점검(datetime.date(2099, 1, 1)); assert any("30 일" in x for x in 늙은), "날짜 검사가 질 수 없다"   # 자기 검사
    print("쪽 %d · 문제 %d" % (len(쪽), len(문제))); [print(" -", x) for x in 문제]
    sys.exit(1 if 문제 else 0)

