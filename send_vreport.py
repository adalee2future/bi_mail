#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import datetime
import glob
from smtplib import SMTPDataError

from file_to_mail import file_to_mail
import upload_file

def send_vreport(report_id, to=None):
    os.chdir(os.path.join('vreports', report_id))
    base_dir = '.'

    cfg_path = os.path.join(base_dir, '%s.cfg' % report_id)
    pt_path = os.path.join(base_dir, 'current.pt')

    with open(cfg_path) as f, open(pt_path) as g:
        cfg = json.loads(f.read())
        pt = g.read().strip()

    report_name = cfg['report_name']
    owner = cfg.get('owner')

    body_prepend = ''
    report_files = glob.glob('output/*_{}.html'.format(pt))
    data_files = glob.glob('output/*_{}.xlsx'.format(pt))
    filenames = report_files + data_files

    if to is None:
        to = cfg.get('to')
        cc = cfg.get('cc')
        bcc = cfg.get('bcc')
    else:
        cc = None
        bcc = None
        fake_cc = None

    subject = report_name + '_' + pt
    file_to_mail(filenames, subject, owner, to, cc, bcc, report_type='vreport')

if __name__ == '__main__':
    report_id = sys.argv[1]
    if len(sys.argv) > 2:
        to = sys.argv[2]
    else:
        to = None
    send_vreport(report_id, to)
