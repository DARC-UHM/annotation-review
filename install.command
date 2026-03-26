#!/usr/bin/env bash

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate darc
cd "$(dirname "$0")"
pip install -r requirements.txt
