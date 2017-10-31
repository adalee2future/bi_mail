#!/ada_program/python
# -*- coding: utf-8 -*-

from pymysql import connect
import os
import pandas as pd
import time
import datetime
import random
import sys

conn = connect(os.environ['mysql_host'], os.environ['mysql_user'], os.environ['mysql_password'])

today = datetime.date.today()
yesterday = today - datetime.timedelta(1)
pt = yesterday.strftime('%Y%m%d')
print("pt:", pt)

def run_sql(sql_text):
    start = time.time()
    print(sql_text)
    sql_res = pd.read_sql(sql_text, conn)
    return sql_res

def sql_to_excel(sql_text, filename=None):
    res = run_sql(sql_text)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.xlsx' % random_hash
    res.to_excel(filename, index=False)
    print("Export to excel %s succeed!" % filename)

def sql_to_csv(sql_text, filename=None):
    res = run_sql(sql_text)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.csv' % random_hash
    res.to_csv(filename, index=False)
    print("Export to csv %s succeed!" % filename)

def main():
    sql_text, filetype = sys.argv[1:]
    if filetype in ['xlsx', 'excel', 'x']:
        sql_to_excel(sql_text)
    if filetype in ['plain', 'text', 'csv', 'c']:
        sql_to_csv(sql_text)

if __name__ == "__main__":
    main()
