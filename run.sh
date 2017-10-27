#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile
cd ~/projects/bi_mail

project_id=$1
log_file=reports/$project_id/log/`date +\%Y\-%m`.log
touch $log_file
./send_report.sh $project_id >> $log_file 2>&1
