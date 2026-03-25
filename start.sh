#!/usr/bin/env bash

gunicorn 'application:create_app()' --workers 1 --threads 3
