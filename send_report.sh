#!/bin/sh

report_id=$1
echo
date
echo "******start*******" 

pwd
./send_report.py $report_id

date
echo "******end*******"
