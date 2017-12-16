# -*- coding: utf-8 -*-

import odps
import pymysql
import os
import pandas as pd
import numpy as np
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
week_start = yesterday - datetime.timedelta(6)

DATES = {
    'today': today.strftime('%Y-%m-%d'),
    'yesterday': yesterday.strftime('%Y-%m-%d'),
    'week_range': '{week_start}-{week_end}'.format(week_start=week_start.strftime('%m%d'), week_end=yesterday.strftime('%m%d')),
    'month': yesterday.strftime('%Y-%m')
}


class FetchingData:
    def __init__(self, login_info):
        raise NotImplementedError

    def run_sql(self, sql_text, dependency={}):
        raise NotImplementedError

    def sql_to_excel(self, sql_text, filename=None, dependency={}, df_names=None, merge=False):
        if filename is None:
            random_hash = "%032x" % random.getrandbits(128)
            filename = '%s.xlsx' % random_hash

        sql_text_raw_list = [sql_text.strip() for sql_text in sql_text.split(';')]
        sql_text_list = []

        for sql_text in sql_text_raw_list:
            if sql_text.lower().find('select') == -1:
                continue
            sql_text_list.append(sql_text)

        if df_names is None:
            df_names = ['Sheet%s' % i for i in range(1, len(sql_text_list) + 1)]
        else:
            df_names = [df_name.format(**DATES) for df_name in df_names]

        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            for df_name, sql_text in zip(df_names, sql_text_list):
                df = self.run_sql(sql_text, dependency=dependency)
                if merge:
                    df.set_index(list(df)[:-1]).to_excel(writer, sheet_name=df_name)
                else:
                    df.to_excel(writer, sheet_name=df_name, index=False)
        print("Export to excel %s succeed!" % filename)

    def sql_to_csv(self, sql_text, filename=None, dependency={}):
        res = self.run_sql(sql_text, dependency=dependency)
        if filename is None:
            random_hash = "%032x" % random.getrandbits(128)
            filename = '%s.csv' % random_hash
        res.to_csv(filename, index=False)
        print("Export to csv %s succeed!" % filename)

    def sql_to_html(self, sql_text, filename=None, dependency={}, df_names=None, merge=False):
        #res = self.run_sql(sql_text, dependency=dependency)

        sql_text_raw_list = [sql_text.strip() for sql_text in sql_text.split(';')]
        sql_text_list = []

        for sql_text in sql_text_raw_list:
            if sql_text.lower().find('select') == -1:
                continue
            sql_text_list.append(sql_text)

        if df_names is None:
            df_names = ['' for _ in sql_text_list]

        if filename is None:
            random_hash = "%032x" % random.getrandbits(128)
            filename = '%s.html' % random_hash

        with open(filename, 'w') as f:
            for sql_text, df_name in zip(sql_text_list, df_names):
                f.write('<br/><h2>%s</h2>\n' % df_name)
                df = self.run_sql(sql_text)
                df.fillna('', inplace=True)
                if merge:
                    f.write(df.set_index(list(df)).to_html())
                else:
                    f.write(df.to_html(index=False))
        print("Export to html %s succeed!" % filename)

class FetchingDataOdps(FetchingData):
    def __init__(self, login_info=DEFAULT_ODPS_LOGIN_INFO):
        self._login_info = login_info
        self._pt = yesterday.strftime('%Y%m%d')
        self._conn = odps.ODPS(**login_info)

    def run_sql(self, sql_text, dependency={}):

        print("dependency:", dependency)
        for project, table_names in dependency.items():
            for table_name in table_names:
                t = self._conn.get_table(table_name, project)
                while True:
                    if t.exist_partition('pt={}'.format(self._pt)):
                        break
                    time.sleep(60)
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
        start = time.time()
        print(sql_text)
        sql_res_dataframe = pd.read_sql(sql_text, self._conn)
        print("fetched size:", sql_res_dataframe.shape)
        print("time take: %ss" % round(time.time() - start))
        #display(sql_res_dataframe.head(10))
        return sql_res_dataframe

