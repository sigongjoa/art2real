"""크롬 창들 중 확장 탭(제목 표지)을 앞으로 — 창마다 앞으로 올리고 맨 앞이 그 창인지 확인한 뒤에만 Ctrl+Tab(최대 15) · 10-06 메모 정리 · 10-13
python 탭찾기.py SAU_SJY → 찾은 창 핸들 · 못 찾으면 「없음」"""
import ctypes, sys, time
from ctypes import wintypes as w
u = ctypes.windll.user32; 표지 = sys.argv[1]
# 사용자가 쓰는 중이면 창을 안 뺏는다 — 10-18 리그 오브 레전드 위로 세 번 Alt · 앞으로 가져옴(10-08 에도 같은 일) · 마지막 입력 뒤 60 초 안이면 그만
class _LII(ctypes.Structure): _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
def 쉰초():
    l = _LII(ctypes.sizeof(_LII)); ctypes.windll.user32.GetLastInputInfo(ctypes.byref(l)); return (ctypes.windll.kernel32.GetTickCount() - l.dwTime) / 1000
def 가드(초=60):   # 사용자가 「올려 · 게임 껐어」처럼 직접 말했으면 FORCE=1
    if __import__("os").environ.get("FORCE"): return
    if 쉰초() < 초:
        b = ctypes.create_unicode_buffer(200); ctypes.windll.user32.GetWindowTextW(ctypes.windll.user32.GetForegroundWindow(), b, 200)
        sys.exit("사용 중 — 창 안 뺏음 (마지막 입력 %.0f 초 전 · 맨 앞 %s)" % (쉰초(), b.value))

def 제목(h):
    n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1); return b.value
def 클래스(h): b = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, b, 64); return b.value
창 = []
@ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
def 셈(h, _):
    if 클래스(h) == "Chrome_WidgetWin_1" and 제목(h).endswith("Chrome"): 창.append(h)
    return True
u.EnumWindows(셈, 0)
def 키(*vk):
    for v in vk: u.keybd_event(v, 0, 0, 0)
    for v in reversed(vk): u.keybd_event(v, 0, 2, 0)
for h in 창:
    if 표지 in 제목(h): print("찾음", h, 제목(h)); sys.exit(0)
    가드(); u.ShowWindow(h, 9); u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0); u.BringWindowToTop(h); u.SetForegroundWindow(h); time.sleep(.6)
    for _ in range(15):
        if u.GetForegroundWindow() != h: print("맨 앞이 이 창이 아님 — 건너뜀", 제목(h)); break   # 다른 프로그램에 키가 들어가지 않게
        if 표지 in 제목(h): print("찾음", h, 제목(h)); sys.exit(0)
        키(0x11, 0x09); time.sleep(.4)   # Ctrl+Tab
    if 표지 in 제목(h): print("찾음", h, 제목(h)); sys.exit(0)
print("없음")
