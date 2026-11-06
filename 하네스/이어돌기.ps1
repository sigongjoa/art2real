# 판 여러 개를 차례로 · 앞 판(PID)이 끝나길 기다렸다가 · 세션과 떨어진 프로세스로(세션이 끝나도 계속) · 11-06
# PowerShell 5.1 은 BOM 없는 UTF-8 의 한글을 깨뜨림 → 이 파일은 BOM UTF-8 · 변수 이름은 영문
# 사용: Start-Process powershell -ArgumentList '-File','하네스\이어돌기.ps1','-WaitPid','17444','-Runs','169a부품3천,169b부품만2천' -WindowStyle Hidden
param([int]$WaitPid = 0, [string]$Runs = "")
Set-Location G:\art2real
$log = "out\하네스\이어돌기.log"
if ($WaitPid) { while (Get-Process -Id $WaitPid -ErrorAction SilentlyContinue) { Start-Sleep 30 } }
foreach ($r in $Runs.Split(",")) {
    $o = Get-CimInstance Win32_OperatingSystem
    ("{0} 시작 {1} · 예약 여유 {2:N1} GB" -f $r, (Get-Date -Format HH:mm), ($o.FreeVirtualMemory / 1MB)) | Out-File -Append -Encoding utf8 $log
    $env:CUDA_VISIBLE_DEVICES = "0"; $env:ART_MEM_GB = "26"
    & "G:\art2real\트레일\trail10_cadrille\venv\Scripts\python.exe" -u 하네스\하네스.py --config-name "판_$r" *> "out\하네스\판$r.log"
    ("{0} 끝 {1} · 코드 {2}" -f $r, (Get-Date -Format HH:mm), $LASTEXITCODE) | Out-File -Append -Encoding utf8 $log
}
