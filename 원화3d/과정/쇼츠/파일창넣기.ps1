# YouTube Studio 업로드에 로컬 mp4 넣기 — 확장 file_upload 10 MB 한계 · 확장 클릭은 파일 창을 디버거가 가로챔 → 윈도우 진짜 마우스로 누른다.
#   powershell -File 파일창넣기.ps1 "<mp4 전체 경로>" <창제목> <x> <y>
# 창제목 · x · y 는 페이지 JS 가 document.title 을 바꾸고 「파일 선택」(#select-files-button) 화면 좌표를 재서 넘긴다. x 를 0 으로 주면 클릭 없이 열린 창만 채운다.
# 경로는 클립보드(다른 프로그램이 잡고 있으면 실패) 대신 파일 이름 칸에 WM_SETTEXT 로 직접 쓴다.
param([string]$Path, [string]$Title, [int]$X, [int]$Y)
Add-Type @'
using System; using System.Text; using System.Runtime.InteropServices;
public class M {
[DllImport("user32")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32")] public static extern void mouse_event(int f, int x, int y, int d, int e);
[DllImport("user32", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string c, string t);
[DllImport("user32", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowEx(IntPtr p, IntPtr a, string c, string t);
[DllImport("user32", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, string l);
[DllImport("user32")] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, IntPtr l);
public static bool Fill(string path) {
  IntPtr d = FindWindow("#32770", "열기"); if (d == IntPtr.Zero) return false;
  IntPtr e = FindWindowEx(FindWindowEx(FindWindowEx(d, IntPtr.Zero, "ComboBoxEx32", null), IntPtr.Zero, "ComboBox", null), IntPtr.Zero, "Edit", null);
  if (e == IntPtr.Zero) return false;
  SendMessage(e, 0x000C, IntPtr.Zero, path);                         // WM_SETTEXT
  IntPtr ok = FindWindowEx(d, IntPtr.Zero, "Button", null);           // 첫 버튼 = 열기
  SendMessage(d, 0x0111, (IntPtr)1, IntPtr.Zero);                     // WM_COMMAND IDOK
  return true; } }
'@
if ($X -gt 0) {
    $sh = New-Object -ComObject WScript.Shell
    if (-not $sh.AppActivate($Title)) { "창 없음: $Title"; exit 1 }
    Start-Sleep -Milliseconds 700
    [M]::SetCursorPos($X, $Y) | Out-Null; Start-Sleep -Milliseconds 200
    [M]::mouse_event(2, 0, 0, 0, 0); [M]::mouse_event(4, 0, 0, 0, 0)     # 왼쪽 누름 · 뗌
}
for ($i = 0; $i -lt 40; $i++) {            # 20 초 안에 열기 창
    Start-Sleep -Milliseconds 500
    if ([M]::Fill($Path)) { 'ok'; exit 0 }
}
'열기 창 없음'; exit 1
