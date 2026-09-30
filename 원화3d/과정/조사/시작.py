# -*- coding: utf-8 -*-
"""수집 → 요약을 따로 떨어진 프로세스로 시작하고 바로 돌아온다(에이전트 셸 제한 시간에 안 걸리게). 진행은 out/조사/쇼츠/진행.log"""
import subprocess, sys, os
H = os.path.dirname(os.path.abspath(__file__)); O = r"G:\art2real\원화3d\out\조사\쇼츠"; os.makedirs(O, exist_ok=True)
cmd = 'cd /d "%s" && python 수집.py > "%s\진행.log" 2>&1 && python 요약.py >> "%s\진행.log" 2>&1 && echo DONE >> "%s\진행.log"' % (H, O, O, O)
p = subprocess.Popen(cmd, shell=True, creationflags=0x00000008 | 0x00000200, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("시작됨 PID", p.pid, "· 진행:", O + r"\진행.log")
