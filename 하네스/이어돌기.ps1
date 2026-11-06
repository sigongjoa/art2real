# 판 여러 개를 차례로 · 앞 판(PID)이 끝나길 기다렸다가 · 세션과 떨어진 프로세스로(세션이 끝나도 계속) · 11-06
# 사용: Start-Process powershell -ArgumentList '-File','하네스\이어돌기.ps1','-기다릴','17444','-판들','169a부품3천,169b부품만2천' -WindowStyle Hidden
param([int]$기다릴 = 0, [string]$판들 = "")
Set-Location G:\art2real
if ($기다릴) { while (Get-Process -Id $기다릴 -ErrorAction SilentlyContinue) { Start-Sleep 30 } }
foreach ($판 in $판들.Split(",")) {
    $o = Get-CimInstance Win32_OperatingSystem
    "{0} 시작 · 예약 여유 {1:N1} GB" -f $판, ($o.FreeVirtualMemory / 1MB) | Out-File -Append -Encoding utf8 out\하네스\이어돌기.log
    $env:CUDA_VISIBLE_DEVICES = "0"; $env:ART_MEM_GB = "26"
    & "G:\art2real\트레일\trail10_cadrille\venv\Scripts\python.exe" -u 하네스\하네스.py --config-name "판_$판" *> "out\하네스\판$판.log"
    "{0} 끝 · 코드 {1}" -f $판, $LASTEXITCODE | Out-File -Append -Encoding utf8 out\하네스\이어돌기.log
}
