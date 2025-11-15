# AudioBook TTS - Installation Script for Windows
# Run this in PowerShell with .venv activated

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AudioBook TTS - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Upgrade pip
Write-Host "[1/4] Upgrading pip..." -ForegroundColor Yellow
python.exe -m pip install --upgrade pip

# Step 2: Install PyTorch with CUDA support for RTX 3050
Write-Host ""
Write-Host "[2/4] Installing PyTorch with CUDA 11.8..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes - downloading ~2GB)" -ForegroundColor Gray
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Step 3: Install other dependencies
Write-Host ""
Write-Host "[3/4] Installing other dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Step 4: Verify installation
Write-Host ""
Write-Host "[4/4] Verifying installation..." -ForegroundColor Yellow
Write-Host ""

python -c "import torch; print(f'PyTorch Version: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}' if torch.cuda.is_available() else 'CPU Only')"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Place your PDF file in this directory (or specify path)" -ForegroundColor White
Write-Host "2. Run: python TTS.py" -ForegroundColor White
Write-Host ""
