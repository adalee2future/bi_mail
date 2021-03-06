#!/bin/sh

export LANG=zh_CN.UTF-8
cd `dirname $0`

export PATH=`pwd`:$PATH
export supervised=true

log_file=log/`date +%Y-%m-%d`.log
echo $log_file
touch $log_file

mail_monitor=`python -c "from helper import MAIL_MONITOR; print(MAIL_MONITOR)"`

kill $(ps aux | grep run_by_mail_cmd.py | grep python | grep `pwd` | awk '{print $2}')
python `pwd`/run_by_mail_cmd.py >> $log_file 2>&1

res_code=$?

if [[ $res_code -eq 0 ]]
  then echo
else
  python file_to_mail.py $log_file '手动运行报表脚本(run_by_mail_cmd.py) 错误!!!' '' $mail_monitor
fi
