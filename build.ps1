# Complete RMS Build Script
# This script builds the app and prepares it for Inno Setup

Write-Host "=== RMS Build Script ===" -ForegroundColor Cyan

# Step 1: Clean old builds
Write-Host "`n[1/4] Cleaning old builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "dist\main", "build", "main.spec" -ErrorAction SilentlyContinue

# Step 2: Build with PyInstaller
Write-Host "[2/4] Building with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller --windowed `
  --add-data "serviceAccountKey.json;." `
  --add-data "Logo.ico;." `
  --add-data "version.txt;." `
  --distpath "dist" `
  --name "main" `
  main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] PyInstaller build successful" -ForegroundColor Green
} else {
    Write-Host "[FAILED] PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Step 3: Copy essential files to dist\main
Write-Host "[3/4] Copying essential files..." -ForegroundColor Yellow
Copy-Item "serviceAccountKey.json" "dist\main\" -Force
Copy-Item "Logo.ico" "dist\main\" -Force
Copy-Item "version.txt" "dist\main\" -Force

# Verify files
$files = @("dist\main\main.exe", "dist\main\serviceAccountKey.json", "dist\main\Logo.ico", "dist\main\version.txt")
$all_present = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  [OK] $(Split-Path $file -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "  [FAILED] $(Split-Path $file -Leaf) - MISSING!" -ForegroundColor Red
        $all_present = $false
    }
}

if ($all_present) {
    Write-Host "`n[4/4] Build complete!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Open Inno Setup Compiler"
    Write-Host "2. File -> Open -> setup.iss"
    Write-Host "3. Click Compile"
    Write-Host "4. Installer will be in: output\installer.exe"
} else {
    Write-Host "`n[FAILED] Build incomplete - some files are missing" -ForegroundColor Red
    exit 1
}
