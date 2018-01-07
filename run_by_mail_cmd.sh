#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile

cd `dirname $0`

log_file=log/`date +%Y-%m-%d`.log
echo $log_file
touch $log_file
./run_by_mail_cmd.py >> $log_file 2>&1

