#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import copy

from helper import MAIL_USER, MAIL_MONITOR, REPORT_TYPE_MAP
from file_to_mail import file_to_mail


def main(report_type, report_id, log_filename):
    report_type_name = REPORT_TYPE_MAP[report_type]
    base_dir = os.path.join('{}s'.format(report_type), report_id)
    cfg_path = os.path.join(base_dir, '%s.cfg' % report_id)
    print("base_dir:", base_dir)
    print("cfg_path:", cfg_path)

    try:
        with open(cfg_path) as g:
            cfg = json.loads(g.read())
    except:
        cfg = { 'owner': MAIL_USER.split('@')[0], 'to': MAIL_USER }

    owner = cfg.get('owner')

    to = ','.join(['%s@owitho.com' % owner for owner in cfg.get('owner').split(',')])
    cc = MAIL_MONITOR
    bcc = None
    body_prepend = '''
    <font color="red"><{report_id}></font>报错，详情看附件中的{report_type_name}运行日志
    '''.format(report_id=report_id, report_type_name=report_type_name)

    file_to_mail(log_filename, '邮件%s<%s>报错!!!' % (report_type_name, report_id), owner, to, cc, bcc, body_prepend, report_type=report_type)

if __name__ == '__main__':
    report_type = sys.argv[1]
    report_id = sys.argv[2]
    log_filename = sys.argv[3]
    main(report_type, report_id, log_filename)

