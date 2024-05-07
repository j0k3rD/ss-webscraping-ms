#!/bin/bash
source .venv/bin/activate

if ! command -v playwright &> /dev/null
then
    playwright install
fi

uvicorn main:app --reload --port 5001