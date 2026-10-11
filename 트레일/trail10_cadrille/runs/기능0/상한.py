# -*- coding: utf-8 -*-
"""메모리 상한 걸고 돌리기 — Windows 작업 개체(Job Object)가 프로세스 메모리를 OS 에서 막는다 · 넘으면 그 프로세스만 할당 실패로 죽는다 · 10-11 PC 다운 두 번 뒤
python 상한.py <GB> <명령…>   → 종료 코드 그대로"""
import sys, ctypes, subprocess
from ctypes import wintypes as w
k = ctypes.WinDLL("kernel32", use_last_error=True)
class 기본(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", w.DWORD), ("c", ctypes.c_size_t), ("d", ctypes.c_size_t),
                ("e", w.DWORD), ("f", ctypes.c_size_t), ("g", w.DWORD), ("h", w.DWORD)]
class 확장(ctypes.Structure):
    _fields_ = [("Basic", 기본), ("Io", ctypes.c_uint64 * 6), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]
k.CreateJobObjectW.restype = w.HANDLE; k.OpenProcess.restype = w.HANDLE
def 돌림(gb, cmd):
    j = k.CreateJobObjectW(None, None); x = 확장(); x.Basic.LimitFlags = 0x100 | 0x200 | 0x2000   # 프로세스 · 작업 메모리 · 핸들 닫으면 같이 죽음
    x.ProcessMemoryLimit = x.JobMemoryLimit = int(gb * 2**30)
    assert k.SetInformationJobObject(j, 9, ctypes.byref(x), ctypes.sizeof(x)), ctypes.get_last_error()
    p = subprocess.Popen(cmd); h = k.OpenProcess(0x1F0FFF, False, p.pid)
    assert k.AssignProcessToJobObject(j, h), ctypes.get_last_error()   # ponytail: 띄운 뒤 몇 ms 는 상한 밖 — 시작 직후엔 메모리를 거의 안 쓴다
    return p.wait()
if __name__ == "__main__":
    if sys.argv[1] == "시험":   # 1 GB 상한에서 3 GB 잡기 → 죽어야 한다
        r = 돌림(1, [sys.executable, "-c", "import time; time.sleep(.5); b = bytearray(3 * 2**30); print('안 막힘')"]); assert r != 0, r; print("ok 막힘", r)
    else: sys.exit(돌림(float(sys.argv[1]), sys.argv[2:]))
