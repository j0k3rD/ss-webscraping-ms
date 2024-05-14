#!/bin/bash
source .venv/bin/activate

if ! command playwright -V &> /dev/null
then
    playwright install
fi

uvicorn main:app --reload --host 192.168.18.4 --port 5001