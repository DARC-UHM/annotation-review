#!/usr/bin/env bash

gunicorn run:app --threads 3
