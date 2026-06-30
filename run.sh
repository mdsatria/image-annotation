#!/bin/bash
uv run uvicorn main:app --reload &
SERVER_PID=$!
sleep 1
open http://localhost:8000
wait $SERVER_PID
