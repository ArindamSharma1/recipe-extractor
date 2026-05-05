#!/bin/bash

# Recipe Extractor — Start Script
# Starts both backend and frontend

echo "=== Starting Recipe Extractor ==="

# Backend
echo "[1/2] Installing backend dependencies..."
cd backend
pip install -r requirements.txt -q
echo "[1/2] Starting backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo "[2/2] Installing frontend dependencies..."
cd frontend
npm install --silent
echo "[2/2] Starting frontend on port 5173..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== Both servers running ==="
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
