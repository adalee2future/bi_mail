#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile

cd `dirname $0`
report_id=$1

if [[ ! -d reports/$report_id/log ]]
  then mkdir reports/$report_id/log
fi
if [[ ! -d reports/$report_id/data ]]
  then mkdir reports/$report_id/data
fi

log_file=reports/$report_id/log/`date +%Y-%m-%d_%H:%M:%S`.log
echo $log_file
touch $log_file
./send_report.sh $report_id >> $log_file 2>&1

res_code=$?
echo send_report result: $res_code
if [[ $res_code -eq 0 ]]
  then echo
else
  ./send_log.py $report_id $log_file
fi
