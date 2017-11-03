#!/bin/sh

report_id=$1
echo
date
echo "******start*******" 

./send_report.py $report_id

echo "******end*******"
