#!/usr/bin/env bash

set -e

echo "**** Making messages..."
python3 manage.py makemessages -l en -l fr