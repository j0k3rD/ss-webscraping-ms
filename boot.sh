#!/bin/bash
source bin/activate

if ! command -v playwright &> /dev/null
then
    playwright install
fi

python3 run.py