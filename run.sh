#!/bin/sh

export LANG=zh_CN.UTF-8
source ~/.profile
cd ~/projects/bi_mail

project_id=$1
log_file=reports/$project_id/log.txt
echo >> $log_file
date >> $log_file
echo "******start*******" >> $log_file

./send_report.py $project_id >> $log_file

cd -
echo "******end*******" >> log.txt

