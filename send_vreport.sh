#!/bin/sh
set -e

report_id=$1
to=$2
echo
date
echo "******start*******" 

pwd
jupyter nbconvert --execute --ExecutePreprocessor.timeout=-1 vreports/$report_id/$report_id.ipynb
pt=`cat vreports/$report_id/current.pt`
mv vreports/$report_id/$report_id.html vreports/$report_id/output/${report_id}_${pt}.html

./send_vreport.py $report_id $to

date
echo "******end*******"
