# Build Article Reader into a standalone Windows executable.
# Output: dist/ArticleReader/ArticleReader.exe
#
# Requirements: pip install pyinstaller (already in requirements.txt)
# Run from the project root: .\build.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Building Article Reader..." -ForegroundColor Cyan

pyinstaller article_reader.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable: dist\ArticleReader\ArticleReader.exe"
Write-Host ""
Write-Host "To distribute: copy the entire dist\ArticleReader\ folder."
Write-Host "The receiving machine needs Ollama installed with llama3.1:8b pulled."
