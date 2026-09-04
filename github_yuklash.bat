@echo off
chcp 65001 > nul
title AudioScribe AI - GitHub Yuklash
color 0A

cd /d "d:\dars prog\antigravity"

echo ===================================================
echo     AudioScribe AI - GitHub'ga Yuklash
echo ===================================================
echo.

echo [1/4] Foydalanuvchi ma'lumotlari sozlanmoqda...
git config user.name "OmatilloQayumjonov"
git config user.email "omatillo@users.noreply.github.com"

echo [2/4] O'zgarishlar tanlanmoqda...
git add .

echo [3/4] Saqlanmoqda (commit)...
git commit -m "Fix Dart compile errors in AudioPlayer and ReceiveSharingIntent"

echo [4/4] GitHub manziliga yuklanmoqda (Push)...
git push origin main --force

echo.
echo ===================================================
echo [TABRIKLAYMIZ!] Tuzatishlar GitHub'ga yuborildi!
echo Endi Actions sahifasini yangilang (F5).
echo ===================================================
echo.
pause
