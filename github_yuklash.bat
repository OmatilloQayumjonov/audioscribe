@echo off
chcp 65001 > nul
title AudioScribe AI - GitHub Yuklash
color 0A

cd /d "d:\dars prog\antigravity"

echo ===================================================
echo     AudioScribe AI - GitHub'ga Yuklash
echo ===================================================
echo.

echo [1/5] Foydalanuvchi ma'lumotlari sozlanmoqda...
git config user.name "OmatilloQayumjonov"
git config user.email "omatillo@users.noreply.github.com"

echo [2/5] Git sozlanmoqda...
git init
git branch -M main

echo [3/5] Fayllar tanlanmoqda...
git add .

echo [4/5] Saqlanmoqda (commit)...
git commit -m "AudioScribe AI Release APK Action"

echo [5/5] GitHub manziliga yuklanmoqda (Push)...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/OmatilloQayumjonov/audioscribe.git
git push -u origin main --force

if %errorlevel% neq 0 (
    echo.
    echo ===================================================
    echo [XATO] Yuklashda xatolik bo'ldi.
    echo ===================================================
    pause
    exit /b
)

echo.
echo ===================================================
echo [TABRIKLAYMIZ!] Fayllar muvaffaqiyatli yuklandi!
echo.
echo Endi sahifani yangilang (F5):
echo https://github.com/OmatilloQayumjonov/audioscribe/actions
echo ===================================================
echo.
pause
