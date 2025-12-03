@echo off
REM ====================================================
REM Web Print Service - Başlangıç Scripti
REM Windows Görev Zamanlayıcısı için kullanılabilir
REM ====================================================

REM Çalışma dizinini script konumuna ayarla
cd /d "%~dp0"

REM Sanal ortam varsa aktive et
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Environment değişkenlerini ayarla
set FLASK_ENV=production
set FLASK_DEBUG=False
set AUTO_OPEN_BROWSER=False

REM Uygulamayı başlat (arka planda)
echo.
echo ================================================
echo   Web Print Service - Ag Yazdirma Servisi
echo ================================================
echo.
echo Uygulama baslatiliyor...
echo Tarayicinizda http://localhost:5000 adresini acin
echo.
echo Kapatmak icin bu pencereyi kapatin veya Ctrl+C
echo ================================================
echo.

pythonw app.py

REM Eğer pythonw yoksa normal python kullan
if errorlevel 1 (
    python app.py
)
