#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate

sudo apt-get install libxrandr2 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libgtk-3-0 libatk1.0-0 libcairo-gobject2 libgdk-pixbuf-2.0-0 libasound2

pip3 install -r requirements/dev.txt