import os
import sys
from helper import BASE_DIR

CFG_TEMPLATE = '''{
  "report_id":"{report_id}",
  "report_name":"{report_id}",
  "owner":"",
  "to":"",
  "cc":"",
  "subject":"{report_id}",
  "file_type": "xlsx",
  "frequency":"每天",
  "db_type":"odps"
}

'''
def generate_report(report_id):
    report_dir = os.path.join(BASE_DIR, 'reports', report_id)
    os.mkdir(report_dir)

    sql_filename = os.path.join(report_dir, '%s.sql' % report_id)
    cfg_filename = os.path.join(report_dir, '%s.cfg' % report_id)

    cfg = CFG_TEMPLATE.replace('{report_id}', report_id)

    with open(sql_filename, 'w') as f, open(cfg_filename, 'w') as g:
        g.write(cfg)

if __name__ == '__main__':
    report_id = sys.argv[1]
    generate_report(report_id)
