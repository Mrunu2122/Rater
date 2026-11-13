@echo off
title Cloudflare Live Public Tunnel
echo ========================================================
echo Starting Cloudflare Tunnel for http://localhost:8000
echo ========================================================
cloudflared.exe tunnel --url http://localhost:8000
pause
