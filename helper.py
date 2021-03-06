# -*- coding: utf-8 -*-
import pandas as pd
import os
from functools import wraps
import time
import datetime
import commentjson
from datetime_truncate import truncate

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, 'main.cfg')
STYLES = open(os.path.join(BASE_DIR, 'styles.css')).read()
REPORT_TYPE_MAP = {
    'report': '报表',
    'vreport': '报告'
}

def add_days(d, num):
    if isinstance(d, datetime.date):
        d = datetime.datetime.combine(d, datetime.datetime.min.time())

    delta = datetime.timedelta(num)
    return d + delta

def diff_days(d1, d2):
    return (d1 - d2) / datetime.timedelta(1)

def datetime_truncate(d, truncate_to='day'):
    if isinstance(d, datetime.date):
        d = datetime.datetime.combine(d, datetime.datetime.min.time())
    try:
        start_d = truncate(d, truncate_to)
    except:
        num, day = split(truncate_to, '_')
        if day == 'day':
            start_d = add_days(d, num)

    return  start_d

def file_size(filename):
    '''
    文件大小（MB）
    '''
    b = os.path.getsize(filename)
    mb = b / 1000 / 1000
    return mb

def multiple_trials(wait_seconds=[0, 60, 120]):
    def _multiple_trials(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for idx, wait_second in enumerate(wait_seconds):
                msg = ''
                msg += ('wait %s seconds\n' % wait_second)
                msg += ('multiple_trials %s: %s, %s, %s\n' % (idx + 1, func.__name__, args, kwargs))

                time.sleep(wait_second)
                try:
                    if idx > 0:
                        print(msg)
                    return func(*args, **kwargs)
                except Exception as e:
                    if idx == 0:
                        print(msg)
                    print('ERROR: %s\n' % e)
        return wrapper
    return _multiple_trials

def coalesce(a, b=''):
    if pd.isna(a):
        return b
    else:
        return a

def excel_datetime_to_num(t):
    base_date = datetime.date(1899, 12, 31)
    base_time = datetime.datetime.combine(base_date, datetime.datetime.min.time())

    # 来自excel世纪大bug，以为1900年是闰年
    bug_date = datetime.date(1900, 2, 28)
    bug_time = datetime.datetime.combine(bug_date, datetime.datetime.max.time())

    try:
        t.hour
        t_time = t
    except:
        t_time = datetime.datetime.combine(t, datetime.datetime.min.time())

    num = (t_time-base_time)/datetime.timedelta(1)
    if t_time > bug_time:
        num += 1
    return num

with open(CONFIG_FILE) as f:
    cfg = commentjson.loads(f.read())
    SMTP_HOST = cfg['smtp_host']
    SMTP_PORT = cfg['smtp_port']
    SMTP_PROTOCOL = cfg.get('smtp_protocol', 'tls')
    IMAP_HOST = cfg['imap_host']
    IMAP_PORT = cfg['imap_port']
    MAIL_MONITOR = cfg['mail_monitor']
    MAIL_USER = cfg['mail_sender']['user']
    MAIL_PASSWD = cfg['mail_sender']['password']
    MAIL_HOST= cfg.get('mail_host')
    DB_LOGIN = cfg['db'] 
    ODPS_LOGIN = DB_LOGIN.get('odps')

    DATE_RANGE_FMTS = cfg.get('date_range_fmts')

    
    oss_setting = cfg.get('oss_setting', {}) 
    OSS_ENABLE = oss_setting.get('oss_enable', False)
    if OSS_ENABLE:
        OSS_ENDPOINT = oss_setting.get('oss_endpoint')
        OSS_BUCKET = oss_setting.get('oss_bucket')
        OSS_FOLDER = oss_setting.get('oss_folder')
        OSS_LINK_REPORTS = oss_setting.get('oss_link_reports', [])

    EXTERNAL_PROJECTS = cfg.get('external_projects', [])

