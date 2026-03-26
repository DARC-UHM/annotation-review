#!/usr/bin/env bash

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate darc
cd "$(dirname "$0")"
git pull
gunicorn 'application:create_app()' --workers 1 --threads 3 &
GUNICORN_PID=$!
trap "kill $GUNICORN_PID 2>/dev/null" EXIT
sleep 2 && open http://localhost:8000 &
wait $GUNICORN_PID
