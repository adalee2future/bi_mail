#!/bin/sh
set -e

report_id=$1
to=$2
echo
date
echo "******start*******" 

pwd
./send_report.py $report_id $to

date
echo "******end*******"
