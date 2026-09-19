#!/bin/bash
export AI_MODE=mock
export PYTHONPATH=.
PORT=${PORT:-8000}
exec uvicorn backend.app.main:app --port $PORT --reload
