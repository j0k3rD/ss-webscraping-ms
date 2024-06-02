#!/bin/bash
source .venv/bin/activate

if ! command playwright -V &> /dev/null
then
    playwright install
fi

uvicorn main:app --reload --host localhost --port 5001