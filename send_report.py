#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
from file_to_mail import file_to_mail

report_id = sys.argv[1]
os.chdir(os.path.join('reports', report_id))
base_dir = '.'
sql_path = os.path.join(base_dir, '%s.sql' % report_id)
cfg_path = os.path.join(base_dir, '%s.cfg' % report_id)

with open(sql_path) as f, open(cfg_path) as g:
    sql_text = f.read()
    cfg = json.loads(g.read())

report_name = cfg['report_name']
db_type = cfg.get('db_type', 'odps') # default odps
owner = cfg.get('owner')


if db_type == "odps":
    from fetch_data_odps import sql_to_excel, sql_to_csv, pt

if db_type == "mysql":
    from fetch_data_mysql import sql_to_excel, sql_to_csv, pt

if cfg.get('customized_file'):
    sys.path.insert(0, os.getcwd())
    import customized_file
    filename = customized_file.main()
else:
    filename = os.path.join(base_dir, 'data', '%s_%s.%s' % (report_name, pt, cfg['file_type'] ))

    if cfg['file_type'] == 'csv':
        sql_to_csv(sql_text, filename)
    if cfg['file_type'] == 'xlsx':
        sql_to_excel(sql_text, filename)

print("filename:", filename)
subject = '%s_%s' % (cfg['subject'], pt)
to = cfg.get('to')
file_to_mail(filename, subject, owner, to)

