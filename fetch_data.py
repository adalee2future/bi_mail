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
import tkinter
import tkinter.font
import decimal
from file_to_mail import STYLES
from style import default_style
from IPython.display import display

DEFAULT_ODPS_LOGIN_INFO = {
    'access_id': os.environ.get('access_id'),
    'secret_access_key': os.environ.get('access_key'),
    'project': 'phoenix'
}

DEFAULT_MYSQL_LOGIN_INFO = {
    'host': os.environ.get('mysql_host'),
    'user': os.environ.get('mysql_user'),
    'password': os.environ.get('mysql_password'),
    'charset': 'utf8',
    'read_timeout': 60 * 40
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

HTML_TO_STR = True

TABLE_STYLES = [{'selector': '.row_heading, .blank', 'props': [('display', 'none;')]}]

DT_FORMAT = '%Y-%m-%d'
PT_FORMAT = '%Y%m%d'

today = datetime.date.today()
yesterday = today - datetime.timedelta(1)
week_start = yesterday - datetime.timedelta(6)

MIN_COL_WIDTH = 8
MAX_COL_WIDTH = 36

MAX_WAIT_COUNT = 360

def get_dt(date_t):
    return date_t.strftime(DT_FORMAT)

def get_pt(date_t):
    return date_t.strftime(PT_FORMAT)

def add_days(date_t, days):
    if type(date_t) == datetime.datetime:
        date_t = date_t.date()
    return date_t + days * datetime.timedelta(1)

def dt2date(dt):
    return datetime.datetime.strptime(dt, DT_FORMAT).date()

def pt2date(pt):
    return datetime.datetime.strptime(pt, PT_FORMAT).date()

def pt2dt(pt):
    return get_dt(pt2date(pt))

def convert_to_integer(s):
    if sum(pd.notna(s)) == 0:
        return s

    s_type = type(s[pd.notna(s)].iloc[0])
    if np.issubdtype(s_type, np.number) or s_type == decimal.Decimal:
        return pd.to_numeric(s, downcast='integer', errors='ignore')
    else:
        return s

class FetchingData:
    def __init__(self, login_info):
        raise NotImplementedError

    @staticmethod
    def random_filename(file_type):
        random_hash = "%032x" % random.getrandbits(128)
        return '{random_hash}{extension}'.format(random_hash=random_hash, extension=DEFAULT_FILE_EXTENSION.get(file_type))

    def get_text_col_width(text):
        if text is None:
            return MIN_COL_WIDTH
        #tkinter.Frame().destroy()
        #font = tkinter.font.Font(family='SimSun', size=2, weight='bold')
        try:
            text = round(text, 10)
        except:
            pass
        #width = font.measure(text)
        text = str(text)
        width = sum(1 if len(c.encode()) <= 1 else 2 for c in text)
        if width < MIN_COL_WIDTH:
            return MIN_COL_WIDTH
        elif width > MAX_COL_WIDTH:
            return MAX_COL_WIDTH
        else:
            return width

    def get_df_col_width(df, rows=100):
        max_width_body = df.head(rows).applymap(FetchingData.get_text_col_width).max()
        max_width_header = map(FetchingData.get_text_col_width, list(df))
        max_width = [max(x, y) for x, y in zip(max_width_body, max_width_header)]
        df_width_map = {col: width for col, width in enumerate(max_width)}
        return df_width_map

    @classmethod
    def run_sql(self, sql_text, dependency={}):
        raise NotImplementedError

    def get_sql_text_list(sql_text):
        sql_text_raw_list = [sql_text.strip() for sql_text in sql_text.split(';')]
        sql_text_list = []

        for sql_text in sql_text_raw_list:
            if sql_text.lower().find('select') == -1:
                continue
            sql_text_list.append(sql_text)

        return sql_text_list

    def sql_to_data(self, sql_text, dependency={}, df_names=None, part_prefix='', part_suffix=None, coerce_numeric=False):
        sql_text_list = self.__class__.get_sql_text_list(sql_text)
        data_dict = OrderedDict()
        if df_names is None:
            if part_suffix is None:
                df_names = ['%s%s' % (part_prefix, i) for i in range(1, len(sql_text_list) + 1)]
            else:
                print("part_suffix:", part_suffix, "end")
                df_names = ['%s%s' % (part_prefix, part_suffix * i) for i in range(1, len(sql_text_list) + 1)]
        else:
            df_names = [df_name.format(**self._dates) for df_name in df_names]

        for sql_text, df_name in zip(sql_text_list, df_names):
            df = self.run_sql(sql_text, dependency=dependency, coerce_numeric=coerce_numeric)
            data_dict[df_name] = df

        return data_dict

    def sql_to_excel(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION, part_prefix='Sheet', coerce_numeric=False, freeze_panes_list=None, formats_list=None):
        if filename is None:
            filename = self.__class__.random_filename('excel')

        data_dict = self.sql_to_data(sql_text, dependency=dependency, df_names=df_names, part_prefix=part_prefix, coerce_numeric=coerce_numeric)

        if coerce_numeric:
            sql_res_dataframe = sql_res_dataframe.apply(convert_to_integer)
        row_permission = copy.deepcopy(row_permission)
        permit_field = row_permission.get('field')
        permit_detail_list = row_permission.get('detail')

        if freeze_panes_list is None:
            freeze_panes_list = [[1, 0] for _ in data_dict]

        if formats_list is None:
            formats_list = [ {} for _ in data_dict ]

        data_rows_dict_list = []

        for permit_detail in permit_detail_list:
            detail_prefix = permit_detail.get('prefix', '')
            detail_suffix = permit_detail.get('suffix', '')
            detail_permit = permit_detail.get('permit')

            name, extension = os.path.splitext(filename)
            current_filename = ''.join([detail_prefix, name, detail_suffix, extension])
            data_rows_dict = OrderedDict()
            permit_detail['filename'] = current_filename

            with pd.ExcelWriter(current_filename, engine='xlsxwriter', options={'strings_to_urls': False}) as writer:

                for (df_name, df), formats, freeze_panes in zip(data_dict.items(), formats_list, freeze_panes_list):

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)]
                    data_rows_dict[df_name] = {"shape": df.shape}
                    if merge:
                        df.set_index(list(df)[:-1]).to_excel(writer, sheet_name=df_name, freeze_panes=freeze_panes)
                    else:
                        df.to_excel(writer, sheet_name=df_name, index=False, freeze_panes=freeze_panes)

                    # excel format
                    workbook = writer.book
                    worksheet = writer.sheets[df_name]

                    col_formats = formats.get('col_formats', [])
                    print("col_formats:", col_formats)
                    conditional_formats = formats.get('conditional_formats', [])
                    print("conditional_formats:", conditional_formats)
                    col_vs_format = {}
                    col_vs_conditional_format = {}

                    for col_format in col_formats:
                        fmt = workbook.add_format(col_format.get('format'))
                        col_vs_format.update({ list(df).index(col_name): fmt for col_name in col_format.get('col_names') })

                    print("col_vs_format:", col_vs_format)
                    for conditional_format in conditional_formats:
                        options = conditional_format.get('options')
                        fmt = workbook.add_format(conditional_format.get('format'))
                        options["format"] = fmt
                        col_vs_conditional_format.update(
                                { list(df).index(col_name): options for col_name in conditional_format.get('col_names') }
                        )

                    print("col_vs_conditional_format:", col_vs_conditional_format)
                    col_width = self.__class__.get_df_col_width(df)
                    print('col_width:', col_width)
                    for col, width in col_width.items():
                        worksheet.set_column(col, col, width, col_vs_format.get(col))

                    nrows = df.shape[0]
                    for col, options in col_vs_conditional_format.items():
                        worksheet.conditional_format(1, col, nrows, col, options)

            data_rows_dict_list.append(data_rows_dict)
            print("Export to excel %s succeed!" % current_filename)

        return data_rows_dict_list, permit_detail_list


    def sql_to_html(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION, part_suffix=' ', styles=STYLES, customized_styles='', coerce_numeric=True, style_func=None):

        if filename is None:
            filename = self.__class__.random_filename('html')

        data_dict = self.sql_to_data(sql_text, dependency=dependency, df_names=df_names, part_suffix=part_suffix, coerce_numeric=coerce_numeric)

        row_permission = copy.deepcopy(row_permission)
        permit_field = row_permission.get('field')
        permit_detail_list = row_permission.get('detail')

        data_rows_dict_list = []

        for permit_detail in permit_detail_list:

            detail_prefix = permit_detail.get('prefix', '')
            detail_suffix = permit_detail.get('suffix', '')
            detail_permit = permit_detail.get('permit')

            dirname = os.path.dirname(filename)
            name, extension = os.path.splitext(os.path.basename(filename))
            current_filename = os.path.join(dirname, ''.join([detail_prefix, name, detail_suffix, extension]))
            data_rows_dict = OrderedDict()
            permit_detail['filename'] = current_filename

            with open(current_filename, 'w') as f:
                for df_name, df in data_dict.items():

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)].copy()
                    data_rows_dict[df_name] = {"shape": df.shape}
                    f.write('<head><meta charset="UTF-8"></head>\n')
                    f.write('<style>\n{styles}\n{customized_styles}\n</style>'.format(styles=styles, customized_styles=customized_styles))
                    f.write('<br/><h2>%s</h2>\n' % df_name)
                    df.fillna('', inplace=True)
                    if HTML_TO_STR:
                        df = df.applymap(str)

                    if merge:
                        f.write(df.set_index(list(df)).to_html())
                    elif style_func is None:
                        f.write(df.to_html(index=False))
                    else:
                        f.write(df.style.apply(style_func).set_table_styles(TABLE_STYLES).render())


            data_rows_dict_list.append(data_rows_dict)
            print("Export to html %s succeed!" % current_filename)

        return data_rows_dict_list, permit_detail_list


    def sql_to_csv(self, sql_text, filename=None, dependency={}, row_permission=DEFAULT_ROW_PERMISSION):

        if filename is None:
            filename = self.__class__.random_filename('csv')

        res = self.run_sql(sql_text, dependency=dependency)

        res.to_csv(filename, index=False)
        print("Export to csv %s succeed!" % filename)

        data_metas = [OrderedDict(csv={'shape': res.shape})]
        file_metas = [{'filename': filename}]
        return data_metas, file_metas
        # todo csv行权限

class FetchingDataOdps(FetchingData):
    def __init__(self, login_info=DEFAULT_ODPS_LOGIN_INFO, pt=None):
        self._login_info = login_info
        if pt is not None:
            self._pt = pt
            self._dt = pt2dt(pt)
        else:
            self._pt = get_pt(yesterday)
            self._dt = get_dt(yesterday)
        self._dates = {
                'today': get_dt(add_days(dt2date(self._dt), 1)),
                'yesterday': self._dt
        }
        self._conn = odps.ODPS(**login_info)
        self._conn.to_global()


    def run_sql(self, sql_text, dependency={}, coerce_numeric=False, print_log=True):

        print("dependency:", dependency) if print_log else None
        for project, table_names in dependency.items():
            for table_name in table_names:
                t = self._conn.get_table(table_name, project)
                count = 0
                while True:
                    if t.exist_partition('pt={}'.format(self._pt)):
                        break

                    time.sleep(60)

                    count += 1
                    if count > MAX_WAIT_COUNT:
                        raise Exception('wait for {project}.{table_name} too long ({count} minutes)'.format(project=project, table_name=table_name, count=count))

        sql_text = sql_text.format(pt=self._pt, dt=self._dt, **self._dates)
        start = time.time()
        print(sql_text) if print_log else None
        sql_res = self._conn.execute_sql(sql_text)
        with sql_res.open_reader() as reader:
            sql_res_dataframe = reader.to_pandas()
            if print_log:
                print("fetched size:", sql_res_dataframe.shape)
                print("time take: %ss" % round(time.time() - start))
                display(sql_res_dataframe.head(10))
            if coerce_numeric:
                sql_res_dataframe = sql_res_dataframe.apply(convert_to_integer)
            return sql_res_dataframe


class FetchingDataMysql(FetchingData):
    def __init__(self, login_info=DEFAULT_MYSQL_LOGIN_INFO, pt=None):
        self._login_info = login_info
        if pt is not None:
            self._pt = pt
            self._dt = pt2dt(pt)
        else:
            self._pt = get_pt(today)
            self._dt = get_dt(today)
        self._dates = {
            'today': self._dt,
            'yesterday': add_days(dt2date(self._dt), -1)
        }
        self._conn = pymysql.connect(**DEFAULT_MYSQL_LOGIN_INFO)

    def run_sql(self, sql_text, dependency={}, coerce_numeric=False, print_log=True):
        start = time.time()
        sql_text = sql_text.format(pt=self._pt, dt=self._dt, **self._dates)
        print(sql_text) if print_log else None
        sql_res_dataframe = pd.read_sql(sql_text, self._conn)
        if print_log:
            print("fetched size:", sql_res_dataframe.shape)
            print("time take: %ss" % round(time.time() - start))
            display(sql_res_dataframe.head(10))
        if coerce_numeric:
            sql_res_dataframe = sql_res_dataframe.apply(convert_to_integer)
        return sql_res_dataframe


try:
    odps_obj = FetchingDataOdps()
except:
    pass

try:
    mysql_obj = FetchingDataMysql()
except:
    pass
