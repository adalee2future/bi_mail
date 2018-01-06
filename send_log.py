#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import copy

from file_to_mail import file_to_mail, MAIL_USER

MONITOR = 'lili.li@owitho.com'

report_id = sys.argv[1]
log_filename = sys.argv[2]
base_dir = os.path.join('reports', report_id)
cfg_path = os.path.join(base_dir, '%s.cfg' % report_id)

try:
    with open(cfg_path) as g:
        cfg = json.loads(g.read())
except:
    cfg = { 'owner': MAIL_USER.split('@')[0], 'to': MAIL_USER } 

owner = cfg.get('owner')

to = ','.join(['%s@owitho.com' % owner for owner in cfg.get('owner').split(',')])
cc = None
bcc = MONITOR
body_prepend = '''
<font color="red"><{report_id}></font>报错，详情看附件中的报表运行日志
'''.format(report_id=report_id)

file_to_mail(log_filename, '邮件报表<%s>报错!!!' % report_id, owner, to, cc, bcc, body_prepend) 

