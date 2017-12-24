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
import copy
from collections import OrderedDict

DEFAULT_ODPS_LOGIN_INFO = {
    'access_id': os.environ.get('access_id'),
    'secret_access_key': os.environ.get('access_key'),
    'project': 'phoenix'
}

DEFAULT_MYSQL_LOGIN_INFO = {
    'host': os.environ.get('mysql_host'),
    'user': os.environ.get('mysql_user'),
    'password': os.environ.get('mysql_password'),
    'charset': 'utf8'
}

DEFAULT_ROW_PERMISSION = {
    'field': None,
    'detail':
      [
        {
          'prefix': '',
          'suffix': '',
          'permit': None
        }
      ]
}

DEFAULT_FILE_EXTENSION = {
    'excel': '.xlsx',
    'csv': '.csv',
    'html': '.html'
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

    @staticmethod
    def random_filename(file_type):
        random_hash = "%032x" % random.getrandbits(128)
        return '{random_hash}{extension}'.format(random_hash=random_hash, extension=DEFAULT_FILE_EXTENSION.get(file_type))
    
    @classmethod
    def run_sql(self, sql_text, dependency={}):
        raise NotImplementedError
     
    def sql_to_data(self, sql_text, dependency, df_names=None, part_prefix='part'):
        data_dict = OrderedDict()
        sql_text_raw_list = [sql_text.strip() for sql_text in sql_text.split(';')]
        sql_text_list = []

        for sql_text in sql_text_raw_list:
            if sql_text.lower().find('select') == -1:
                continue
            sql_text_list.append(sql_text)
        
        if df_names is None:
                df_names = ['%s%s' % (part_prefix, i) for i in range(1, len(sql_text_list) + 1)]
        else:
            df_names = [df_name.format(**DATES) for df_name in df_names]
        
        for sql_text, df_name in zip(sql_text_list, df_names):
            df = self.run_sql(sql_text, dependency=dependency)
            data_dict[df_name] = df

        return data_dict

    def sql_to_excel(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION, part_prefix='sheet'):
        if filename is None:
            filename = self.__class__.random_filename('excel')

        data_dict = self.sql_to_data(sql_text, dependency=dependency, df_names=df_names, part_prefix=part_prefix)
        
        row_permission = copy.deepcopy(row_permission)
        permit_field = row_permission.get('field')
        permit_detail_list = row_permission.get('detail')

        for permit_detail in permit_detail_list:
            detail_prefix = permit_detail.get('prefix', '')
            detail_suffix = permit_detail.get('suffix', '')
            detail_permit = permit_detail.get('permit')

            name, extension = os.path.splitext(filename)
            current_filename = ''.join([detail_prefix, name, detail_suffix, extension])
            permit_detail['filename'] = current_filename

            with pd.ExcelWriter(current_filename, engine='xlsxwriter', options={'strings_to_urls': False}) as writer:
                for df_name, df in data_dict.items():

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)]

                    if merge:
                        df.set_index(list(df)[:-1]).to_excel(writer, sheet_name=df_name)
                    else:
                        df.to_excel(writer, sheet_name=df_name, index=False)
            print("Export to excel %s succeed!" % current_filename)

        return permit_detail_list


    def sql_to_html(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION):
        
        if filename is None:
            filename = self.__class__.random_filename('html')

        data_dict = self.sql_to_data(sql_text, dependency=dependency, df_names=df_names)

        row_permission = copy.deepcopy(row_permission)
        permit_field = row_permission.get('field')
        permit_detail_list = row_permission.get('detail')

        for permit_detail in permit_detail_list:

            detail_prefix = permit_detail.get('prefix', '')
            detail_suffix = permit_detail.get('suffix', '')
            detail_permit = permit_detail.get('permit')

            dirname = os.path.dirname(filename)
            name, extension = os.path.splitext(os.path.basename(filename))
            current_filename = os.path.join(dirname, ''.join([detail_prefix, name, detail_suffix, extension]))
            permit_detail['filename'] = current_filename

            with open(current_filename, 'w') as f:
                for df_name, df in data_dict.items():

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)].copy()

                    f.write('<br/><h2>%s</h2>\n' % df_name)
                    df.fillna('', inplace=True)
                    if merge:
                        f.write(df.set_index(list(df)).to_html())
                    else:
                        f.write(df.to_html(index=False))
            print("Export to html %s succeed!" % current_filename)

        return permit_detail_list


    def sql_to_csv(self, sql_text, filename=None, dependency={}, row_permission=DEFAULT_ROW_PERMISSION):

        if filename is None:
            filename = self.__class__.random_filename('csv')

        res = self.run_sql(sql_text, dependency=dependency)
        
        res.to_csv(filename, index=False)
        print("Export to csv %s succeed!" % filename)

        # todo csv行权限

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


try:
    odps_obj = FetchingDataOdps()
except:
    pass

try:
    mysql_obj = FetchingDataMysql()
except:
    pass
