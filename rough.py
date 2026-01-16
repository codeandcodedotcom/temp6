@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ===============================
REM CONFIG
REM ===============================

set TOKEN=PASTE_THE_FULL_BEARER_TOKEN_HERE_WITHOUT_QUOTES
set URL=https://civ-apis-dev.rolls-royce.com/apd-lit/v1/pdf/project_charter_fece8fc9-2b60-40be-be36-fd96b85e1d2d.pdf
set OUT=charter.pdf

REM ===============================
REM DOWNLOAD
REM ===============================

curl -L ^
 -H "Authorization: Bearer %TOKEN%" ^
 -o "%OUT%" ^
 "%URL%"

REM ===============================
REM VERIFY
REM ===============================

echo.
if exist "%OUT%" (
    echo Download completed
    dir "%OUT%"
) else (
    echo Download failed
)

pause
