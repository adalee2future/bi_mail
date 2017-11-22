#!/ada_program/python
# -*- coding: utf-8 -*-

import odps
import os
import pandas as pd
import time
import datetime
import random
import sys

today = datetime.date.today()
yesterday = today - datetime.timedelta(1)
a_month_ago = today - datetime.timedelta(30)
pt = yesterday.strftime('%Y%m%d')
pt30 = a_month_ago.strftime('%Y%m%d')
print("pt:", pt)

def login(workspace):
    global odps_obj
    odps_obj = odps.ODPS(os.environ['access_id'], os.environ['access_key'], workspace)
    return odps_obj

def run_sql(sql_text, dependency={}):

    print("dependency:", dependency)
    for project, table_names in dependency.items():
        for table_name in table_names:
            t = odps_obj.get_table(table_name, project)
            while True:
                if t.exist_partition('pt={}'.format(pt)):
                    break
                time.sleep(60)

    sql_text = sql_text.format(pt=pt)
    start = time.time()
    print(sql_text)
    sql_res = odps_obj.execute_sql(sql_text)
    with sql_res.open_reader() as reader:
        sql_res_dataframe = reader.to_pandas()
        print("fetched size:", sql_res_dataframe.shape)
        print("time take: %ss" % round(time.time() - start))
        #display(sql_res_dataframe.head(10))
        return sql_res_dataframe

def sql_to_excel_single(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text, dependency=dependency)
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
            df = run_sql(sql_text, dependency=dependency)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("Export to excel %s succeed!" % filename)

def sql_to_csv(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text, dependency=dependency)
    if filename is None:
        random_hash = "%032x" % random.getrandbits(128)
        filename = '%s.csv' % random_hash
    res.to_csv(filename, index=False)
    print("Export to csv %s succeed!" % filename)

def sql_to_html(sql_text, filename=None, dependency={}):
    res = run_sql(sql_text, dependency=dependency)
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

workspace = 'phoenix'
odps_obj = login(workspace)

if __name__ == "__main__":
    main()
