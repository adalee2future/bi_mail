#!/Users/Ada/anaconda3/anaconda/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
from fetch_data import sql_to_excel, sql_to_csv, pt
from file_to_mail import file_to_mail


project_id = sys.argv[1]
print("project_id:", project_id)
base_dir = os.path.join('/Users/Ada/projects/bi_mail/reports', project_id)
print("base_dir:", base_dir)
sql_path = os.path.join(base_dir, '%s.sql' % project_id)
cfg_path = os.path.join(base_dir, '%s.cfg' % project_id)
print("sql_path:", sql_path)
print("cfg_path:", cfg_path)

with open(sql_path) as f, open(cfg_path) as g:
    sql_text = f.read()
    cfg = json.loads(g.read())

project_name = cfg['project_name']
filename = os.path.join(base_dir, 'data', '%s_%s.%s' % (project_name, pt, cfg['file_type'] ))
print("filename:", filename)

if cfg['file_type'] == 'csv':
    sql_to_csv(sql_text, filename)
if cfg['file_type'] == 'xlsx':
    sql_to_excel(sql_text, filename)

file_to_mail(filename, '%s_%s' % (cfg['subject'], pt), cfg['to'])

