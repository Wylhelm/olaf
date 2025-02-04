#!/bin/bash
export PYTHONPATH=/opt/anaconda3/envs/olaf/lib/python3.10/site-packages:$PYTHONPATH
crewai "$@"
