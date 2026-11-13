@echo off
title Cloudflare Live Public Tunnel
echo ========================================================
echo Starting Cloudflare Tunnel for http://127.0.0.1:8000
echo ========================================================
:loop
cloudflared.exe tunnel --url http://127.0.0.1:8000 --protocol http2 --http2-origin
echo Tunnel disconnected. Reconnecting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
