#!/bin/sh
set -e

report_id=$1
params=$2
echo
date
echo "******start*******" 

pwd
./send_report.py $report_id $params

date
echo "******end*******"
