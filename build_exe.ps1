# EmployeeVault Build Script
# Automatically enables network guard before building .exe, then restores settings

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EmployeeVault Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Backup current settings.json
Write-Host "[1/5] Backing up settings.json..." -ForegroundColor Yellow
Copy-Item "settings.json" "settings.json.backup" -Force
Write-Host "✓ Settings backed up" -ForegroundColor Green
Write-Host ""

# Step 2: Enable network guard for production build
Write-Host "[2/5] Enabling network guard for production..." -ForegroundColor Yellow
$settings = Get-Content "settings.json" -Raw | ConvertFrom-Json
$settings.enable_network_guard = $true
$settings | ConvertTo-Json -Depth 10 | Set-Content "settings.json"
Write-Host "✓ Network guard enabled" -ForegroundColor Green
Write-Host ""

# Step 3: Run PyInstaller
Write-Host "[3/5] Building EmployeeVault.exe with PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

pyinstaller --name EmployeeVault --onedir --noconfirm `
  --icon ".\apruva.ico" `
  --add-data ".\app;app" `
  --add-data ".\assets;assets" `
  --add-data ".\employee_export;employee_export" `
  --add-data ".\employee_files;employee_files" `
  --add-data ".\employee_letters;employee_letters" `
  --add-data ".\employee_photos;employee_photos" `
  --add-data ".\employee_vault;employee_vault" `
  --add-data ".\docs;docs" `
  --add-data ".\pptx_reference;pptx_reference" `
  --add-data ".\temp_pptx_extract;temp_pptx_extract" `
  --add-data ".\templates;templates" `
  --add-data ".\logs;logs" `
  --add-data ".\company_logo.png;." `
  --add-data ".\cuddly_header.png;." `
  --add-data ".\cuddly_footer.png;." `
  --add-data ".\cuddly_logo.png;." `
  --add-data ".\id_card_background.png;." `
  --add-data ".\apruva_logo.png;." `
  --add-data ".\settings.json;." `
  --add-data ".\audit_log.json;." `
  --add-data ".\employee_vault.db;." `
  --add-data ".\theme_preference.txt;." `
  ".\main.py"

$buildSuccess = $LASTEXITCODE -eq 0

Write-Host ""
if ($buildSuccess) {
    Write-Host "✓ Build completed successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed with error code: $LASTEXITCODE" -ForegroundColor Red
}
Write-Host ""

# Step 4: Restore original settings.json for development
Write-Host "[4/5] Restoring settings.json for development..." -ForegroundColor Yellow
Copy-Item "settings.json.backup" "settings.json" -Force
Remove-Item "settings.json.backup" -Force
Write-Host "✓ Settings restored (network guard disabled for local dev)" -ForegroundColor Green
Write-Host ""

# Step 4.5: Copy network launcher to dist folder
Write-Host "[4.5/5] Copying network launcher scripts..." -ForegroundColor Yellow
if (Test-Path "dist\EmployeeVault\") {
    Copy-Item "LaunchFromNetwork.bat" "dist\EmployeeVault\" -Force
    Copy-Item "LaunchFromNetwork.ps1" "dist\EmployeeVault\" -Force
    Copy-Item "LaunchFromNetwork_Debug.bat" "dist\EmployeeVault\" -Force
    Write-Host "✓ Network launcher scripts copied to dist\EmployeeVault\" -ForegroundColor Green
}
Write-Host ""

# Step 5: Summary
Write-Host "[5/5] Build Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

if ($buildSuccess) {
    Write-Host "Status: SUCCESS" -ForegroundColor Green
    Write-Host "Output: dist\EmployeeVault\" -ForegroundColor White
    Write-Host "Executable: dist\EmployeeVault\EmployeeVault.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Network Guard: ENABLED in .exe" -ForegroundColor Green
    Write-Host "Network Guard: DISABLED in source (development mode)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test the .exe: .\dist\EmployeeVault\EmployeeVault.exe" -ForegroundColor White
    Write-Host "2. Deploy to: \\extra\EmployeeVault\" -ForegroundColor White
    Write-Host "3. IMPORTANT: Run LaunchFromNetwork.bat from network path!" -ForegroundColor Yellow
    Write-Host "   (Do NOT run EmployeeVault.exe directly from UNC paths)" -ForegroundColor Yellow
} else {
    Write-Host "Status: FAILED" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    Write-Host "Settings have been restored to development mode" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
