#!/usr/bin/env bash
source ~/ENV/bin/activate
cd ~/InterpretableAutoRec
python tune_parameters.py -d data/CDsVinyl/ -n CDsVinyl/ncf.csv -y config/ncf.yml