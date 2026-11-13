@echo off
title Insurance Rater Engine - Running
echo ========================================================
echo Starting Motor Policy Commission Rater Backend on port 8000
echo ========================================================
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
pause
