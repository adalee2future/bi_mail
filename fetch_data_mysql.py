#!/ada_program/python
# -*- coding: utf-8 -*-

from pymysql import connect
import os
import pandas as pd
import time
import datetime
import random
import sys

conn = connect(os.environ['mysql_host'], os.environ['mysql_user'], os.environ['mysql_password'], charset="utf8")

today = datetime.date.today()
pt = today.strftime('%Y%m%d')
print("pt:", pt)

def run_sql(sql_text, dependency={}):
    start = time.time()
    print(sql_text)
    sql_res = pd.read_sql(sql_text, conn)
    return sql_res

def sql_to_excel_single(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.xlsx' % random_hash
    res.to_excel(filename, index=False)
    print("Export to excel %s succeed!" % filename)

def sql_to_excel(sql_text, filename=None, dependency={}):

    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.xlsx' % random_hash

    sql_text_raw_list = [sql_text.strip() for sql_text in sql_text.split(';')]
    sql_text_list = []

    for sql_text in sql_text_raw_list:
        if sql_text.lower().find('select') == -1:
            continue
        sql_text_list.append(sql_text)

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for idx, sql_text in enumerate(sql_text_list):
            sheet_name = "Sheet%s" % idx
            df = run_sql(sql_text)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("Export to excel %s succeed!" % filename)

def sql_to_csv(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.csv' % random_hash
    res.to_csv(filename, index=False)
    print("Export to csv %s succeed!" % filename)

def sql_to_html(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.html' % random_hash
    res.to_html(filename, index=False)
    print("Export to html %s succeed!" % filename)

def main():
    sql_text, filetype = sys.argv[1:]
    if filetype in ['xlsx', 'excel', 'x']:
        sql_to_excel(sql_text)
    elif filetype in ['plain', 'text', 'csv', 'c']:
        sql_to_csv(sql_text)
    elif filetype in ['html', 'h']:
        sql_to_html(sql_text)

if __name__ == "__main__":
    main()
