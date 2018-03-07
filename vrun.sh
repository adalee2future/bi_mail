#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile

cd `dirname $0`
report_id=$1
to=$2

if [[ ! -d vreports/$report_id/log ]]
  then mkdir vreports/$report_id/log
fi
if [[ ! -d vreports/$report_id/ouput ]]
  then mkdir vreports/$report_id/output
fi

report_log_file=vreports/$report_id/log/`date +%Y-%m-%d_%H:%M:%S`.log
daily_report_log_file=vreports/$report_id/log/`date +%Y-%m-%d`.log
daily_log_file=log/vreport_`date +%Y-%m-%d`.log

touch $report_log_file
touch $daily_report_log_file
touch $daily_log_file

echo './send_vreport.sh' $report_id $to >> $daily_log_file
./send_vreport.sh $report_id $to >> $report_log_file 2>&1
res_code=$?

cat $report_log_file >> $daily_report_log_file
echo send_report result: $res_code
echo send_report result: $res_code >> $daily_log_file
echo >> $daily_log_file

if [[ $res_code -eq 0 ]]
  then echo
else
  ./send_log.py vreport $report_id $report_log_file
fi