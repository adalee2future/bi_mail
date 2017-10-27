#!/Users/Ada/anaconda3/anaconda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
from fetch_data import sql_to_excel, sql_to_csv, pt
from file_to_mail import file_to_mail

project_id = sys.argv[1]
os.chdir(os.path.join('reports', project_id))
base_dir = '.'
sql_path = os.path.join(base_dir, '%s.sql' % project_id)
cfg_path = os.path.join(base_dir, '%s.cfg' % project_id)

with open(sql_path) as f, open(cfg_path) as g:
    sql_text = f.read()
    cfg = json.loads(g.read())

project_name = cfg['project_name']

if cfg.get('customized_file'):
    sys.path.insert(0, os.getcwd())
    import customized_file
    filename = customized_file.main()
else:
    filename = os.path.join(base_dir, 'data', '%s_%s.%s' % (project_name, pt, cfg['file_type'] ))

    if cfg['file_type'] == 'csv':
        sql_to_csv(sql_text, filename)
    if cfg['file_type'] == 'xlsx':
        sql_to_excel(sql_text, filename)

print("filename:", filename)
file_to_mail(filename, '%s_%s' % (cfg['subject'], pt), cfg['to'])

