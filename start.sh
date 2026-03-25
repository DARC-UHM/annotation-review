#!/usr/bin/env bash

gunicorn run:app --workers 1 --threads 3
