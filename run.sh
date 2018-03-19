#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile

cd `dirname $0`
report_id=$1
params=$2

if [[ ! -d reports/$report_id/log ]]
  then mkdir reports/$report_id/log
fi
if [[ ! -d reports/$report_id/data ]]
  then mkdir reports/$report_id/data
fi

report_log_file=reports/$report_id/log/`date +%Y-%m-%d_%H:%M:%S`.log
daily_report_log_file=reports/$report_id/log/`date +%Y-%m-%d`.log
daily_log_file=log/report_`date +%Y-%m-%d`.log

touch $report_log_file
touch $daily_report_log_file
touch $daily_log_file

echo './send_report.sh' $report_id $params >> $daily_log_file
./send_report.sh $report_id $params >> $report_log_file 2>&1
res_code=$?

cat $report_log_file >> $daily_report_log_file
echo send_report result: $res_code
echo send_report result: $res_code >> $daily_log_file
echo >> $daily_log_file

if [[ $res_code -eq 0 ]]
  then echo
else
  ./send_log.py report $report_id $report_log_file
fi
