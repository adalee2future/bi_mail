import pandas as pd
import os
from functools import wraps
import time
import datetime
import commentjson

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, 'main.cfg')
STYLES = open(os.path.join(BASE_DIR, 'styles.css')).read()
REPORT_TYPE_MAP = {
    'report': '报表',
    'vreport': '报告'
}

with open(CONFIG_FILE) as f:
    cfg = commentjson.loads(f.read())
    MAIL_MONITOR = cfg['mail_monitor']
    MAIL_USER = cfg['mail_sender']['user']
    MAIL_PASSWD = cfg['mail_sender']['password']
    ODPS_LOGIN = cfg['db']['odps']
    MYSQL_LOGIN = cfg['db']['mysql']
    OSS_LINK_REPORTS = cfg.get('oss_link_reports', [])


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
