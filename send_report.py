#!/ada_program/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import copy
import re
import datetime
import matplotlib
matplotlib.use('agg')

import fetch_data
from file_to_mail import file_to_mail, BASE_DIR
import upload_file
from smtplib import SMTPDataError
from style import default_style, STYLE_FUNC_MAP

VALID_CONDITIONS = [ 'all', 'any' ]
VALID_ACTIONS = [ 'error', 'exit' ]
ODPS_DEFAULT_NO_DATA_HANDLER = {"condition": "any", "action": "error"}
MYSQL_DEFAULT_NO_DATA_HANDLER = None
DEFAULT_BODY_PREPEND = ''
OSS_DATA_FOLDER = 'data'
VALID_EXTERNAL_PROJECTS = ['store-bi', 'rack-bi']

oss_link_reports = os.environ.get('oss_link_reports', '').split(',')

def get_mail_action(data_meta, no_data_handler):
    if data_meta is None or no_data_handler is None:
        return
    size = len(data_meta)
    rows = [d['shape'][0] for d in data_meta.values()]
    satisfied_size = sum(map(lambda x: x == 0, rows))

    if no_data_handler.get('condition') in VALID_CONDITIONS and no_data_handler.get('action') in VALID_ACTIONS:
        condition= no_data_handler.get('condition')
        action = no_data_handler.get('action')

        if condition == 'any' and satisfied_size > 0:
            return action

        if condition == 'all' and satisfied_size == size:
            return action

def send_report(report_id, params=''):
    if params is None:
        params = ''
    project_dir = os.path.join(BASE_DIR, 'reports', report_id)

    cfg_path = os.path.join(project_dir, '%s.cfg' % report_id)
    cpt_path = os.path.join(project_dir, '%s.caption.html' % report_id)

    if os.path.exists(cpt_path):
        caption = open(cpt_path).read()
    else:
        caption = ''

    with open(cfg_path) as f:
        cfg = json.loads(f.read())

    external_sql_location = cfg.get('external_sql_location')
    if external_sql_location in VALID_EXTERNAL_PROJECTS:
        os.chdir('..')
        os.chdir(os.path.join('xbl_bi', external_sql_location, '周期取数'))
    else:
        os.chdir(project_dir)
    sql_path = '%s.sql' % report_id
    with open(sql_path) as f:
        sql_text = f.read()

    report_name = cfg['report_name']
    db_type = cfg.get('db_type', 'odps')
    dependency = cfg.get('dependency', {})
    file_type = cfg.get('file_type', 'xlsx')
    owner = cfg.get('owner')
    merge = cfg.get('merge', False)
    df_names = cfg.get('df_names')
    style_func = STYLE_FUNC_MAP.get(cfg.get('style_func'), None)

    param_json = dict(re.findall(r'([^;]+)=([^;]+)', params))
    to = param_json.get('to')
    pt = param_json.get('pt')

    if to is None:
        to = cfg.get('to')
        cc = cfg.get('cc')
        bcc = cfg.get('bcc')
        fake_cc = cfg.get('fake_cc')
    else:
        cc = None
        bcc = None
        fake_cc = None

    customized_styles = cfg.get('customized_styles', '')


    default_row_permission = copy.deepcopy(fetch_data.DEFAULT_ROW_PERMISSION)
    default_row_permission['detail'][0]['to'] = to
    default_row_permission['detail'][0]['cc'] = cc
    default_row_permission['detail'][0]['fake_cc'] = fake_cc
    default_row_permission['detail'][0]['bcc'] = bcc

    row_permission = cfg.get('row_permission', default_row_permission)

    if db_type == 'odps':
        fetching_data = fetch_data.FetchingDataOdps(pt=pt)
        no_data_handler = cfg.get('no_data_handler', ODPS_DEFAULT_NO_DATA_HANDLER)
    elif db_type == 'mysql':
        fetching_data = fetch_data.FetchingDataMysql()
        no_data_handler = cfg.get('no_data_handler', MYSQL_DEFAULT_NO_DATA_HANDLER)

    if cfg.get('customized_file'):
        sys.path.insert(0, os.getcwd())
        import customized_file
        cust_res = customized_file.main()
        filename = cust_res.get('filename')
        body_prepend = cust_res.get('body_prepend', DEFAULT_BODY_PREPEND)
        data_meta = cust_res.get('data_meta')

        subject = '%s_%s' % (cfg.get('subject'), fetching_data._pt)
        print()

        if len(body_prepend) > 0:

            current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            oss_filename = '{}_{}_{}.html'.format(report_id, fetching_data._pt, current_datetime)
            upload_file.upload_text_to_oss(oss_filename, body_prepend, folder=OSS_DATA_FOLDER)

        if filename is not None:
            oss_filename = upload_file.upload_file_to_oss(filename, folder=OSS_DATA_FOLDER)

        mail_action = get_mail_action(data_meta, no_data_handler)
        print('\ndata_meta:', data_meta)
        print('no_data_handler:', no_data_handler)
        print('mail_action:', mail_action)
        if mail_action == 'error':
            raise Exception('NoData Error!')
        elif mail_action == 'exit':
            return

        try:
            file_to_mail(filename, subject, owner, to, cc=cc, bcc=bcc, body_prepend=body_prepend, customized_styles=customized_styles, fake_cc=fake_cc, caption=caption)
        except SMTPDataError as e:
            if report_id in oss_link_reports:
                share_url = upload_file.get_file_url(oss_filename)
                valid_hours = round(upload_file.EXPIRE_SECONDS / 3600)
                body_prepend = '附件太大，请<a href=%s>点击链接</a>下载(有效期%s小时)<br/>' % (share_url, valid_hours)
                print("body_prepend:", body_prepend)
                file_to_mail(None, subject, owner, to, cc=cc, bcc=bcc, body_prepend=body_prepend, customized_styles=customized_styles, fake_cc=fake_cc, caption=caption)
            else:
                raise e

    else:
        filename = os.path.join(project_dir, 'data', '%s_%s.%s' % (report_name, fetching_data._pt, file_type))
        print('filename:', filename)

        if file_type == 'csv':
            file_metas = fetching_data.sql_to_csv(sql_text, filename=filename, dependency=dependency, row_permission=row_permission)
        elif file_type == 'xlsx':
            data_metas, file_metas = fetching_data.sql_to_excel(sql_text, filename=filename, dependency=dependency, df_names=df_names, merge=merge, row_permission=row_permission)
        elif file_type == 'html':
            data_metas, file_metas = fetching_data.sql_to_html(sql_text, filename=filename, dependency=dependency, df_names=df_names, merge=merge, row_permission=row_permission, customized_styles=customized_styles, style_func=style_func)

        for data_meta, file_meta in zip(data_metas, file_metas):

            mail_action = get_mail_action(data_meta, no_data_handler)
            print('\ndata_meta:', data_meta)
            print('no_data_handler:', no_data_handler)
            print('mail_action:', mail_action)

            if mail_action == 'error':
                raise Exception('NoData Error!')
            elif mail_action == 'exit':
                return

            mail_meta = {}
            filename = file_meta.get('filename')
            mail_meta['filenames'] = filename
            oss_filename = upload_file.upload_file_to_oss(filename, folder=OSS_DATA_FOLDER)
            if file_type == 'html':
                mail_meta['body_prepend'] = open(file_meta['filename']).read()
                mail_meta['filenames'] = None

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
            mail_meta['caption'] = caption

            try:
                file_to_mail(**mail_meta)
            except SMTPDataError as e:
                if report_id in oss_link_reports:
                    share_url = upload_file.get_file_url(oss_filename)
                    valid_hours = round(upload_file.EXPIRE_SECONDS / 3600)
                    body_prepend = '附件太大，请<a href=%s>点击链接</a>下载(有效期%s小时)<br/>' % (share_url, valid_hours)
                    mail_meta['body_prepend'] = body_prepend
                    print("body_prepend:", body_prepend)
                    mail_meta['filenames'] = None
                    file_to_mail(**mail_meta)
                else:
                    raise e

if __name__ == '__main__':
    report_id = sys.argv[1]
    if len(sys.argv) > 2:
        params = sys.argv[2]
    else:
        params = None
    send_report(report_id, params)
