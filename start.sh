#!/usr/bin/env bash

echo "Loading application..."
gunicorn server:app

