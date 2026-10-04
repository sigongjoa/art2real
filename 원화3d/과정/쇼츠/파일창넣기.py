"""YouTube Studio 업로드에 로컬 mp4 넣기 — 확장 file_upload 10 MB 한계 · 확장 클릭은 파일 창을 디버거가 가로챔 → 윈도우 쪽에서 넣는다.
    python 파일창넣기.py <mp4 전체 경로>              이미 떠 있는 「열기」 창에 경로를 넣고 연다
    python 파일창넣기.py <mp4> <창제목> <x> <y>       그 창을 앞으로 · 진짜 마우스로 「파일 선택」(x, y) 클릭 · 열기 창 채움
창제목 · x · y 는 페이지 JS 가 document.title 을 바꾸고 #select-files-button 화면 좌표를 재서 넘긴다. 표준 라이브러리만."""
import sys, time, ctypes
from ctypes import wintypes
u = ctypes.WinDLL("user32", use_last_error=True)
u.FindWindowW.restype = u.FindWindowExW.restype = wintypes.HWND
u.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
u.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPCWSTR]

def fill(path):
    d = u.FindWindowW("#32770", "열기")
    if not d: return False
    e = d
    for c in ("ComboBoxEx32", "ComboBox", "Edit"):     # 파일 이름 칸
        e = u.FindWindowExW(e, None, c, None)
        if not e: return False
    u.SendMessageW(e, 0x000C, 0, path)                  # WM_SETTEXT
    u.SendMessageW(d, 0x0111, 1, None)                  # WM_COMMAND IDOK = 열기
    return True

path = sys.argv[1]
if path == "restore":                                   # python 파일창넣기.py restore <창제목> — 최소화된 창을 되살린다(그 뒤 좌표를 다시 잰다)
    w = u.FindWindowW("Chrome_WidgetWin_1", sys.argv[2] + " - Chrome")
    if not w: sys.exit("창 없음: " + sys.argv[2])
    u.ShowWindow(w, 9); u.SetForegroundWindow(w); print("restored"); sys.exit()
if len(sys.argv) > 4:
    title, x, y = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    w = u.FindWindowW("Chrome_WidgetWin_1", title + " - Chrome")
    if not w: sys.exit("창 없음: " + title)
    u.SetForegroundWindow(w); time.sleep(0.7)
    # 그 좌표 맨 앞 창이 이 크롬인지 먼저 본다 — 10-04 앞으로 못 가져온 채 눌러 위에 있던 블렌더를 클릭했다
    u.WindowFromPoint.restype = wintypes.HWND; u.WindowFromPoint.argtypes = [wintypes.POINT]; u.GetAncestor.restype = wintypes.HWND
    if u.GetAncestor(u.WindowFromPoint(wintypes.POINT(x, y)), 2) != w: sys.exit("맨 앞이 크롬이 아니다 — 클릭 안 함")
    u.SetCursorPos(x, y); time.sleep(0.2)
    u.mouse_event(2, 0, 0, 0, 0); u.mouse_event(4, 0, 0, 0, 0)   # 왼쪽 누름 · 뗌
for _ in range(40):                                     # 20 초 안에 열기 창
    time.sleep(0.5)
    if fill(path): print("ok", path); sys.exit()
sys.exit("열기 창 없음")
