
# coding: utf-8

# In[9]:


import odps
import pymysql
import os
import pandas as pd
import time
import datetime
import random
import sys

DEFAULT_ODPS_LOGIN_INFO = {
    'access_id': os.environ.get('access_id'),
    'secret_access_key': os.environ.get('access_key'),
    'project': 'phoenix'}

DEFAULT_MYSQL_LOGIN_INFO = {
    'host': os.environ.get('mysql_host'),
    'user': os.environ.get('mysql_user'),
    'password': os.environ.get('mysql_password'),
    'charset': 'utf8'
}

today = datetime.date.today()
yesterday = today - datetime.timedelta(1)


class FetchingData:
    def __init__(self, login_info):
        raise NotImplementedError

    def run_sql(self, sql_text, dependency={}):
        raise NotImplementedError

    def sql_to_excel(self, sql_text, filename=None, dependency={}):
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
                df = self.run_sql(sql_text, dependency=dependency)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print("Export to excel %s succeed!" % filename)

    def sql_to_csv(self, sql_text, filename=None, dependency={}):
        res = self.run_sql(sql_text, dependency=dependency)
        if filename is None:
            random_hash = "%032x" % random.getrandbits(128)
            filename = '%s.csv' % random_hash
        res.to_csv(filename, index=False)
        print("Export to csv %s succeed!" % filename)

    def sql_to_html(self, sql_text, filename=None, dependency={}):
        res = self.run_sql(sql_text, dependency=dependency)
        if filename is None:
            random_hash = "%032x" % random.getrandbits(128)
            filename = '%s.html' % random_hash
        res.to_html(filename, index=False)
        print("Export to html %s succeed!" % filename)

class FetchingDataOdps(FetchingData):
    def __init__(self, login_info=DEFAULT_ODPS_LOGIN_INFO):
        self._login_info = login_info
        self._pt = yesterday.strftime('%Y%m%d')
        self._conn = odps.ODPS(**login_info)

    def run_sql(self, sql_text, dependency={}):
        sql_text = sql_text.format(pt=self._pt)
        start = time.time()
        print(sql_text)
        sql_res = self._conn.execute_sql(sql_text)
        with sql_res.open_reader() as reader:
            sql_res_dataframe = reader.to_pandas()
            print("fetched size:", sql_res_dataframe.shape)
            print("time take: %ss" % round(time.time() - start))
            #display(sql_res_dataframe.head(10))
            return sql_res_dataframe

class FetchingDataMysql(FetchingData):
    def __init__(self, login_info=DEFAULT_MYSQL_LOGIN_INFO):
        self._login_info = login_info
        self._pt = today.strftime('%Y%m%d')
        self._conn = pymysql.connect(**DEFAULT_MYSQL_LOGIN_INFO)

    def run_sql(self, sql_text, dependency={}):
        sql_text = sql_text.format(pt=self._pt)
        start = time.time()
        print(sql_text)
        sql_res_dataframe = pd.read_sql(sql_text, self._conn)
        print("fetched size:", sql_res_dataframe.shape)
        print("time take: %ss" % round(time.time() - start))
        #display(sql_res_dataframe.head(10))
        return sql_res_dataframe

