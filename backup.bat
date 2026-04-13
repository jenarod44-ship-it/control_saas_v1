@echo off
set fecha=%date:~-4,4%-%date:~-10,2%-%date:~-7,2%

mkdir backup 2>nul

copy db.sqlite3 backup\db_%fecha%.sqlite3

echo Backup completado: %fecha%
pause
