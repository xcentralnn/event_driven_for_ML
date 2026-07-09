$docsPath = "c:\Users\long.nguyen4\Downloads\central-stuffs\uit-sdh\he-tinh-toan\event_driven_for_ML\docs"
Write-Host "Bắt đầu theo dõi thư mục $docsPath để tự động compile LaTeX..."

cd $docsPath
$lastTime = (Get-ChildItem -Recurse -Filter *.tex | Measure-Object -Property LastWriteTime -Maximum).Maximum

while ($true) {
    Start-Sleep -Seconds 2
    $currentFiles = Get-ChildItem -Recurse -Filter *.tex
    if ($currentFiles.Count -gt 0) {
        $newTime = ($currentFiles | Measure-Object -Property LastWriteTime -Maximum).Maximum
        if ($newTime -gt $lastTime) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Phát hiện file thay đổi. Đang biên dịch..."
            # Biên dịch bằng xelatex
            xelatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Biên dịch hoàn tất!"
            $lastTime = $newTime
        }
    }
}
