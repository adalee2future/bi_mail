#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import copy

import fetch_data
from file_to_mail import file_to_mail

VALID_CONDITIONS = [ 'all', 'any' ]
VALID_ACTIONS = [ 'error', 'exit' ]

def get_mail_action(data_meta, no_data_handler):
    size = len(data_meta)
    rows = [d['shape'][0] for d in data_meta.values()]
    satisfied_size = sum(map(lambda x: x == 0, rows))

    if no_data_handler is not None and no_data_handler.get('condition') in VALID_CONDITIONS and no_data_handler.get('action') in VALID_ACTIONS:
        condition= no_data_handler.get('condition')
        action = no_data_handler.get('action')

        if condition == 'any' and satisfied_size > 0:
            return action

        if condition == 'all' and satisfied_size == size:
            return action

def main():
    report_id = sys.argv[1]
    os.chdir(os.path.join('reports', report_id))
    base_dir = '.'
    sql_path = os.path.join(base_dir, '%s.sql' % report_id)
    cfg_path = os.path.join(base_dir, '%s.cfg' % report_id)

    with open(sql_path) as f, open(cfg_path) as g:
        sql_text = f.read()
        cfg = json.loads(g.read())

    report_name = cfg['report_name']
    db_type = cfg.get('db_type', 'odps')
    dependency = cfg.get('dependency', {})
    file_type = cfg.get('file_type', 'xlsx')
    owner = cfg.get('owner')
    merge = cfg.get('merge', False)
    df_names = cfg.get('df_names')

    to = cfg.get('to')
    cc = cfg.get('cc')
    bcc = cfg.get('bcc')
    fake_cc = cfg.get('fake_cc')
    customized_styles = cfg.get('customized_styles', '')

    no_data_handler = cfg.get('no_data_handler')


    default_row_permission = copy.deepcopy(fetch_data.DEFAULT_ROW_PERMISSION)
    default_row_permission['detail'][0]['to'] = to
    default_row_permission['detail'][0]['cc'] = cc
    default_row_permission['detail'][0]['fake_cc'] = fake_cc
    default_row_permission['detail'][0]['bcc'] = bcc


    row_permission = cfg.get('row_permission', default_row_permission)

    body_prepend = ''

    if db_type == 'odps':
        fetching_data = fetch_data.odps_obj
    elif db_type == 'mysql':
        fetching_data = fetch_data.mysql_obj

    if cfg.get('customized_file'):
        sys.path.insert(0, os.getcwd())
        import customized_file
        cust_res = customized_file.main()
        filename = cust_res.get('filename')
        body_prepend = cust_res.get('body_prepend', '')
        subject = '%s_%s' % (cfg.get('subject'), fetching_data._pt)
        file_to_mail(filename, subject, owner, to, cc=cc, bcc=bcc, body_prepend=body_prepend, customized_styles=customized_styles, fake_cc=fake_cc)

    else:
        filename = os.path.join(base_dir, 'data', '%s_%s.%s' % (report_name, fetching_data._pt, file_type))
        print('filename:', filename)

        if file_type == 'csv':
            file_metas = fetching_data.sql_to_csv(sql_text, filename=filename, dependency=dependency, row_permission=row_permission)
        elif file_type == 'xlsx':
            data_metas, file_metas = fetching_data.sql_to_excel(sql_text, filename=filename, dependency=dependency, df_names=df_names, merge=merge, row_permission=row_permission)
        elif file_type == 'html':
            data_metas, file_metas = fetching_data.sql_to_html(sql_text, filename=filename, dependency=dependency, df_names=df_names, merge=merge, row_permission=row_permission)

        for data_meta, file_meta in zip(data_metas, file_metas):

            if no_data_handler is not None:
                mail_action = get_mail_action(data_meta, no_data_handler)
                print('data_meta:', data_meta)
                print('no_data_handler:', no_data_handler)
                print('mail_action:', mail_action)

                if mail_action == 'error':
                    raise Exception('NoData Error!')
                elif mail_action == 'exit':
                    return

            mail_meta = {}
            mail_meta['filename'] = file_meta.get('filename')
            if file_type == 'html':
                mail_meta['body_prepend'] = open(file_meta['filename']).read()
                mail_meta['filename'] = None

            mail_meta['subject'] = '{prefix}{subject}_{pt}{suffix}'.format(prefix=file_meta.get('prefix', ''),
                                                                           subject=cfg.get('subject'),
                                                                           pt=fetching_data._pt,
                                                                           suffix=file_meta.get('suffix', ''))
            mail_meta['customized_styles'] = customized_styles
            mail_meta['owner'] = owner

            mail_meta['to'] = file_meta.get('to')
            mail_meta['cc'] = file_meta.get('cc')
            mail_meta['fake_cc'] = file_meta.get('fake_cc')
            mail_meta['bcc'] = file_meta.get('bcc')

            file_to_mail(**mail_meta)

if __name__ == '__main__':
    main()
