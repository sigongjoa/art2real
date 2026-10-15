# -*- coding: utf-8 -*-
# 파이썬이 켜질 때마다 메모리 상한을 건다(Windows 작업 개체) — 10-15 PC 다운 세 번째(OCC 81 GB) 뒤 사용자 「인터프리터 자체에 설정을 바꿔서 꺼지게」
# 원본은 저장소 트레일/trail10_cadrille/runs/기능0/sitecustomize.py · 설치는 같은 폴더 상한설치.py (프로젝트 venv · chatterbox venv · Python311 · Python313 에 복사)
# 최상위 프로세스 하나 + 그 자식(Pool 일꾼 등) 합쳐 ART_MEM_GB(기본 12) · 넘으면 할당 실패(MemoryError)로 그 파이썬만 죽는다 · ART_MEM_GB=0 이면 끔
import os, sys
def _건다():
    if os.name != "nt" or os.environ.get("ART_MEM_CAPPED"): return
    gb = float(os.environ.get("ART_MEM_GB", "12"))
    if gb <= 0: return
    import ctypes
    from ctypes import wintypes as w
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    class 기본(ctypes.Structure):
        _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", w.DWORD), ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", w.DWORD), ("f", ctypes.c_size_t), ("g", w.DWORD), ("h", w.DWORD)]
    class 확장(ctypes.Structure):
        _fields_ = [("Basic", 기본), ("Io", ctypes.c_uint64 * 6), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]
    k.CreateJobObjectW.restype = w.HANDLE; k.GetCurrentProcess.restype = w.HANDLE
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]; k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    j = k.CreateJobObjectW(None, None); x = 확장(); x.Basic.LimitFlags = 0x100 | 0x200; x.ProcessMemoryLimit = x.JobMemoryLimit = int(gb * 2**30)
    if not (j and k.SetInformationJobObject(j, 9, ctypes.byref(x), ctypes.sizeof(x)) and k.AssignProcessToJobObject(j, k.GetCurrentProcess())):
        sys.stderr.write("[메모리 상한] 못 걸었다 · 오류 %d\n" % ctypes.get_last_error()); return
    os.environ["ART_MEM_CAPPED"] = "%g" % gb   # 자식은 이 개체 안에 태어나 합쳐서 gb — 다시 걸지 않는다
try: _건다()
except Exception as e: sys.stderr.write("[메모리 상한] 못 걸었다 · %r\n" % (e,))
