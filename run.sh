#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile
cd ~/projects/bi_mail

report_id=$1

if [[ ! -d reports/$report_id/log ]]
  then mkdir reports/$report_id/log
fi
if [[ ! -d reports/$report_id/data ]]
  then mkdir reports/$report_id/data
fi
log_file=reports/$report_id/log/`date +\%Y\-%m-%d`.log
touch $log_file
./send_report.sh $report_id >> $log_file 2>&1
