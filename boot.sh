#!/bin/bash

if ! command -v playwright &> /dev/null; then
    echo "Installing Playwright..."
    playwright install --with-deps
fi

uvicorn src.main:app --reload --host 0.0.0.0 --port 5001
