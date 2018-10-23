#!/bin/sh

export LANG=zh_CN.UTF-8
export supervised=true
source ~/.profile

cd `dirname $0`

log_file=log/`date +%Y-%m-%d`.log
echo $log_file
touch $log_file
./run_by_mail_cmd.py >> $log_file 2>&1

res_code=$?

if [[ $res_code -eq 0 ]]
  then echo
else
  python file_to_mail.py $log_file '手动运行报表脚本(run_by_mail_cmd.py) 错误!!!' '' $mail_monitor
fi
