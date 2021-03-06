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
from pprint import pprint
import decimal
import style
from IPython.display import display
from helper import DB_LOGIN, STYLES
from helper import add_days, diff_days, datetime_truncate
from helper import coalesce, excel_datetime_to_num
pd.set_option('max_colwidth', 1000)

odps.options.sql.settings =  { "odps.sql.submit.mode" : "script" }
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

EXCEL_DATE_FORMAT = 'yyyy-mm-dd'
EXCEL_DATETIME_FORMAT = 'yyyy-mm-dd hh:mm:ss'

HTML_TO_STR = True

TABLE_STYLES = [{'selector': '.row_heading, .blank', 'props': [('display', 'none;')]}]

DT_FORMAT = '%Y-%m-%d'
PT_FORMAT = '%Y%m%d'

ODPS_VALUE_MAP = {
  '${bdp.system.bizdate}': '{pt}'
}

TODAY = datetime.date.today()

MIN_COL_WIDTH = 8
MAX_COL_WIDTH = 36

MAX_WAIT_COUNT = 360

LINK_TEMPLATE_HTML = '<a href="{}">{}</a>'
LINK_TEMPLATE_EXCEL = '=HYPERLINK("{}", "{}")'

DEFAULT_COL_FORMAT_JSON = {'font_name': '微软雅黑'}
DEFAULT_HEADER_FORMAT_JSON = {'font_name': '微软雅黑', 'font_color': 'white', 'bg_color': '#4286f4'}

def get_dt(date_t):
    return date_t.strftime(DT_FORMAT)

def get_pt(date_t):
    return date_t.strftime(PT_FORMAT)

def dt2date(dt):
    return datetime.datetime.strptime(dt, DT_FORMAT).date()

def pt2date(pt):
    return datetime.datetime.strptime(pt, PT_FORMAT).date()

def pt2dt(pt):
    return get_dt(pt2date(pt))

def get_max_digits_count(s, e=1e-8):
    def get_digits_count(x):
        for i in range(11):
            if pd.isna(x):
                return np.nan
            if abs(x - round(x, i)) < e:
                return i

    res = s.apply(get_digits_count).max()
    if pd.isna(res):
        return res
    else:
        return int(res)

def numeric_fields(df):
    numeric_cols = []
    if df.shape[0] == 0:
        return numeric_cols
    for col in df.columns.values:
        s = df[col]
        if s.notna().sum() == 0:
            break
        s_type = type(s[pd.notna(s)].iloc[0])
        if np.issubdtype(s_type, np.number) or s_type == decimal.Decimal:
            numeric_cols.append(col)
    return numeric_cols

def get_datetime_fields(df):
    time_cols = []
    if df.shape[0] == 0:
        return time_cols
    for col in df.columns.values:
        s = df[col]
        if s.notna().sum() == 0:
            break
        sample = s[pd.notna(s)].iloc[0]
        try:
            sample.date(), sample.time()
            time_cols.append(col)
        except:
            pass
    return time_cols

def get_date_fields(df):
    date_cols = []
    if df.shape[0] == 0:
        return date_cols
    for col in df.columns.values:
        s = df[col]
        if s.notna().sum() == 0:
            break
        s_type = type(s[pd.notna(s)].iloc[0])
        if s_type in [datetime.date]:
            date_cols.append(col)
    return date_cols

def convert_to_integer(s):
    if sum(pd.notna(s)) == 0:
        return s

    s_type = type(s[pd.notna(s)].iloc[0])
    if np.issubdtype(s_type, np.number) or s_type == decimal.Decimal:
        return pd.to_numeric(s, downcast='integer', errors='ignore')
    else:
        return s

def decimal_columns(df):
    decimal_columns = []
    for col in df.columns.values:
        s = df[col]
        if sum(pd.notna(s)) > 0 and type(s[pd.notna(s)].iloc[0]) == decimal.Decimal:
            decimal_columns.append(col)
    return decimal_columns

def decimal2float(x):
    if pd.isna(x):
        return np.nan
    else:
        return float(x)

def merge_fields_hyperlink(df, hyperlinks, template):
    df = df.copy()

    if hyperlinks is None:
        return df

    for hyperlink in hyperlinks:
        nrows = df.shape[0]
        columns = list(df)
        text_field = hyperlink.get('text_field')
        url_field = hyperlink.get('url_field')
        merged_field = hyperlink.get('merged_field', text_field)
        if text_field in columns and url_field in columns:
            if nrows == 0:
                merged_value = None
            else:
                merged_value = df.apply(lambda x: template.format(x[url_field], x[text_field]), axis=1)
            loc = columns.index(text_field)
            df.drop([text_field, url_field], axis=1, inplace=True)
            df.insert(loc, column=merged_field, value=merged_value)
    return df

def trunc_datetime(s):
    '''
    对于日期时间格式，如果时间都为0，则转化成日期
    '''
    if pd.notna(s).any() and type(s[pd.notna(s)].iloc[0]) == pd._libs.tslibs.timestamps.Timestamp:
        s1 = s[s.notna()]
        if (s1.dt.time == datetime.time(0, 0, 0)).all():
            s = s.dt.date

    return s

class FetchingData:
    def __init__(self, account="default", day_shift=None, pt=None, date_range='day', db_type=None):
        
        self._db_type = db_type
        login_info = copy.deepcopy(DB_LOGIN.get(db_type).get(account))
        self._day_shift = 0
        if 'day_shift' in login_info.keys():
            self._day_shift = login_info.pop('day_shift')

        self._login_info = login_info
        if pt is not None:
            self._pt = pt
            self._dt = pt2dt(self._pt)
            self._day_shift = diff_days(TODAY, pt2date(self._pt))
        else:
            if day_shift is not None:
                self._day_shift = day_shift
            self._pt = get_pt(add_days(TODAY, self._day_shift))
            self._dt = pt2dt(self._pt)
        self._end_date = datetime.datetime.strptime(self._pt, PT_FORMAT)
        self._start_date = datetime_truncate(self._end_date, date_range)
        self._dates = {
                'pt': self._pt,
                'dt': self._dt,
                'start_date': self._start_date,
                'end_date': self._end_date
        }
        pprint(self._dates)

    @staticmethod
    def random_filename(file_type):
        random_hash = "%032x" % random.getrandbits(128)
        return '{random_hash}{extension}'.format(random_hash=random_hash, extension=DEFAULT_FILE_EXTENSION.get(file_type))

    @staticmethod
    def get_text_col_width(text, adjust=0):
        if text is None:
            return MIN_COL_WIDTH
        try:
            text = round(text, 10)
        except:
            pass
        #width = font.measure(text)
        text = str(text)
        width = sum(1 if len(c.encode()) <= 1 else 2 for c in text)
        width += adjust
        if width < MIN_COL_WIDTH:
            return MIN_COL_WIDTH
        elif width > MAX_COL_WIDTH:
            return MAX_COL_WIDTH
        else:
            return width

    @staticmethod
    def get_df_col_width(df, rows=100):
        max_width_body = df.head(rows).applymap(FetchingData.get_text_col_width).max()
        max_width_header = map(FetchingData.get_text_col_width, list(df), [3 for _ in df])
        max_width = [max(x, y) for x, y in zip(max_width_body, max_width_header)]
        df_width_map = {col: width for col, width in enumerate(max_width)}

        return df_width_map

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
            df[decimal_columns(df)] = df[decimal_columns(df)].applymap(decimal2float)
            df = df.apply(trunc_datetime)
            data_dict[df_name] = df

        return data_dict

    def sql_to_excel(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION, part_prefix='Sheet', coerce_numeric=False, freeze_panes_list=None, formats_list=None, hyperlinks=None):
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

            dirname = os.path.dirname(filename)
            name, extension = os.path.splitext(os.path.basename(filename))
            current_filename = os.path.join(dirname, ''.join([detail_prefix, name, detail_suffix, extension]))
            data_rows_dict = OrderedDict()
            permit_detail['filename'] = current_filename

            with pd.ExcelWriter(current_filename, engine='xlsxwriter', options={'strings_to_urls': False}) as writer:

                for (df_name, df), formats, freeze_panes in zip(data_dict.items(), formats_list, freeze_panes_list):

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)]

                    df = merge_fields_hyperlink(df, hyperlinks, LINK_TEMPLATE_EXCEL)
                    nrows, ncols = df.shape
                    data_rows_dict[df_name] = {"shape": df.shape}

                    num_fields = numeric_fields(df)
                    datetime_fields = get_datetime_fields(df)
                    date_fields = get_date_fields(df)

                    df[date_fields + datetime_fields] = df[date_fields + datetime_fields].applymap(excel_datetime_to_num)

                    if merge:
                        df.set_index(list(df)[:-1]).to_excel(writer, sheet_name=df_name, freeze_panes=freeze_panes)
                    else:
                        df.to_excel(writer, sheet_name=df_name, index=False, freeze_panes=freeze_panes)

                    columns = list(df)
                    # excel format
                    workbook = writer.book
                    worksheet = writer.sheets[df_name]

                    worksheet.autofilter(0, 0, 0, ncols - 1)

                    # first row format
                    header_format = workbook.add_format(DEFAULT_HEADER_FORMAT_JSON)
                    for col_num, value in enumerate(columns):
                        worksheet.write(0, col_num, value, header_format)

                    # col format
                    col_formats = formats.get('col_formats', [])
                    print("col_formats:", col_formats)
                    conditional_formats = formats.get('conditional_formats', [])
                    print("conditional_formats:", conditional_formats)

                    col_vs_format = {}
                    for idx, col in enumerate(columns):
                        fmt_json = copy.deepcopy(DEFAULT_COL_FORMAT_JSON)
                        if col in num_fields:
                            digits_count = get_max_digits_count(df[col])
                            if(digits_count > 0):
                                num_format = '#,##0.%s' % ('0' * digits_count)
                            else:
                                num_format = '#,##0'

                            fmt_json.update({'num_format': num_format})

                        if col in date_fields:
                            fmt_json.update({'num_format': EXCEL_DATE_FORMAT})

                        if col in datetime_fields:
                            fmt_json.update({'num_format': EXCEL_DATETIME_FORMAT})


                        col_vs_format[idx] = workbook.add_format(fmt_json)

                    for col_format in col_formats:
                        fmt_json = copy.deepcopy(DEFAULT_COL_FORMAT_JSON)
                        fmt_json.update(col_format.get('format'))
                        fmt = workbook.add_format(fmt_json)

                        col_vs_format.update({ list(df).index(col_name): fmt for col_name in col_format.get('col_names') })

                    print("col_vs_format:", col_vs_format)
                    for conditional_format in conditional_formats:
                        options = conditional_format.get('options')
                        fmt = workbook.add_format(conditional_format.get('format'))
                        options["format"] = fmt
                        col_vs_conditional_format = { list(df).index(col_name): options for col_name in conditional_format.get('col_names') }

                        print("col_vs_conditional_format:", col_vs_conditional_format)
                        for col, options in col_vs_conditional_format.items():
                            worksheet.conditional_format(1, col, nrows, col, options)

                    col_width = self.__class__.get_df_col_width(df)
                    print('col_width:', col_width)
                    for col, width in col_width.items():
                        worksheet.set_column(col, col, width, col_vs_format.get(col))

            data_rows_dict_list.append(data_rows_dict)
            print("Export to excel %s succeed!" % current_filename)

        return data_rows_dict_list, permit_detail_list


    def sql_to_html(self, sql_text, filename=None, dependency={}, df_names=None, merge=False, row_permission=DEFAULT_ROW_PERMISSION, part_suffix=' ', styles=STYLES, customized_styles='', coerce_numeric=True, formats_list=None, hyperlinks=None):

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
                if formats_list is None:
                    formats_list = [{}] * len(data_dict)
                for (df_name, df), formats in zip(data_dict.items(), formats_list):

                    if detail_permit is not None:
                        df = df[df[permit_field].isin(detail_permit)].copy()

                    df = merge_fields_hyperlink(df, hyperlinks, LINK_TEMPLATE_HTML)
                    data_rows_dict[df_name] = {"shape": df.shape}
                    f.write('<head><meta charset="UTF-8"></head>\n')
                    f.write('<style>\n{styles}\n{customized_styles}\n</style>'.format(styles=styles, customized_styles=customized_styles))
                    f.write('<br/><h2>%s</h2>\n' % df_name)
                    #df.fillna('', inplace=True)


                    if merge:
                        df = df.copy().fillna('')
                        if HTML_TO_STR:
                            df = df.applymap(str)
                        f.write(df.set_index(list(df)).to_html(escape=False))
                    #elif formats == {}:

                        #if HTML_TO_STR:
                        #    df = df.applymap(str)
                        #f.write(df.to_html(index=False, escape=False))
                    else:
                        print(df.columns.values)
                        fields_vs_format = {}
                        num_fields = numeric_fields(df)
                        num_fields_format = {}
                        for col in num_fields:
                            digits_count = get_max_digits_count(df[col])
                            num_fields_format[col] = lambda x: '' if pd.isna(x) else ('{:,.%sf}' % digits_count).format(x)
                        fields_vs_format.update(num_fields_format)
                        other_fields = set(df.columns.values) - set(num_fields)
                        fields_vs_format.update({f: lambda x: '' if pd.isna(x) else str(x) for f in other_fields})
                        df_style = df.style.format(fields_vs_format)
                        df_style.set_properties(**{'text-align': 'right'}, subset=num_fields)
                        col_formats = formats.get('col_formats')
                        conditional_formats = formats.get('conditional_formats')
                        if col_formats is not None:
                            for col_format in col_formats:
                                df_style = df_style.format({col: col_format.get('format') for col in col_format.get('col_names')})
                        if conditional_formats is not None:
                            for conditional_format in conditional_formats:
                                col_names = conditional_format.get('col_names')
                                options = conditional_format.get('options')
                                print(options)
                                func_type, func_name = options.pop('func_type', 'apply'), options.pop('func_name')
                                if func_type == 'apply':
                                    df_style = df_style.apply(eval('style.%s' % func_name), subset=col_names, **options)
                                elif func_type == 'applymap':
                                    df_style = df_style.applymap(eval('style.%s' % func_name), subset=col_names, **options)

                        #f.write(df_style.set_table_styles(TABLE_STYLES).render())
                        f.write(df_style.hide_index().render())


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
    def __init__(self, account="default", day_shift=None, pt=None, date_range='day', db_type='odps'):
        super(FetchingDataOdps, self).__init__(account, day_shift, pt, date_range, db_type)

        self._conn = odps.ODPS(**self._login_info)
        self._conn.to_global()


    def partition_name(self, t):
        try:
            return t.schema.partitions[0].name
        except:
            return None

    def is_table_ready(self, t, pt):
        p_name = self.partition_name(t)
        print("table and partition:", t.name, p_name)
        if p_name is not None:
            return t.exist_partition('{}={}'.format(p_name, pt))
        else:
            return t.last_modified_time.strftime('%Y%m%d') > pt

    def run_sql(self, sql_text, dependency={}, coerce_numeric=False, print_log=True):

        print("dependency:", dependency) if print_log else None
        for project, table_names in dependency.items():
            for table_name in table_names:
                t = self._conn.get_table(table_name, project)
                count = 0
                while True:
                    if self.is_table_ready(t, self._pt):
                        break

                    time.sleep(60)

                    count += 1
                    if count > MAX_WAIT_COUNT:
                        raise Exception('wait for {project}.{table_name} too long ({count} minutes)'.format(project=project, table_name=table_name, count=count))

        for odps_val, py_val in ODPS_VALUE_MAP.items():
            sql_text = sql_text.replace(odps_val, py_val)
        sql_text = sql_text.format(**self._dates)
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
    def __init__(self, account="default", day_shift=None, pt=None, date_range='day', db_type='mysql'):
        super(FetchingDataMysql, self).__init__(account, day_shift, pt, date_range, db_type)
        self._conn = pymysql.connect(**self._login_info)

    def run_sql(self, sql_text, dependency={}, coerce_numeric=False, print_log=True):
        start = time.time()
        sql_text = sql_text.format(**self._dates)
        print(sql_text) if print_log else None
        sql_res_dataframe = pd.read_sql(sql_text, self._conn)
        if print_log:
            print("fetched size:", sql_res_dataframe.shape)
            print("time take: %ss" % round(time.time() - start))
            display(sql_res_dataframe.head(10))
        if coerce_numeric:
            sql_res_dataframe = sql_res_dataframe.apply(convert_to_integer)
        return sql_res_dataframe

