#!/bin/sh

cd ~/projects/bi_mail

report_id=$1
log_file=reports/$report_id/log/`date +\%Y\-%m`.log
touch $log_file
echo
date
echo "******start*******" 

./send_report.py $report_id

cd -
echo "******end*******"

