#!/ada_program/python
# -*- coding: utf-8 -*-

import odps
import os
import pandas as pd
import time
import datetime
#from IPython.display import display
import random
import sys

workspace = 'phoenix'
odps_obj = odps.ODPS(os.environ['access_id'], os.environ['access_key'], workspace)
odps_obj.get_project()

today = datetime.date.today()
yesterday = today - datetime.timedelta(1)
a_month_ago = today - datetime.timedelta(30)
pt = yesterday.strftime('%Y%m%d')
pt30 = a_month_ago.strftime('%Y%m%d')
print("pt:", pt)

def run_sql(sql_text):
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
