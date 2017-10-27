#!/bin/sh

cd ~/projects/bi_mail

project_id=$1
log_file=reports/$project_id/log/`date +\%Y\-%m`.log
touch $log_file
echo
date
echo "******start*******" 

./send_report.py $project_id

cd -
echo "******end*******"

