# -*- coding: utf-8 -*-

import imaplib
import email
import datetime
import sys
import time
import os
import re
import json
import subprocess
from threading import Thread
import logging

from email.header import decode_header
from file_to_mail import file_to_mail
from helper import EXTERNAL_PROJECTS
from helper import multiple_trials
from helper import IMAP_HOST, IMAP_PORT
from helper import MAIL_USER, MAIL_PASSWD, BASE_DIR, MAIL_MONITOR, MAIL_HOST

DEFAULT_FOLDER = "inbox"
MAIL_SEARCH = 'SUBJECT "bi_mail"'
WAIT_SECONDS = 6
FNULL = open(os.devnull, 'w')
ERROR = '<span style="color:red">ERROR</span>'

os.chdir(BASE_DIR)


@multiple_trials([0] + [60] * 50)
def login_imap():
    M = imaplib.IMAP4_SSL(IMAP_HOST, port=IMAP_PORT)
    M.login(MAIL_USER, MAIL_PASSWD)
    return M

def get_mail_count(folder=DEFAULT_FOLDER):
    M = login_imap()
    M.select(folder)
    resp_code, resp_data = M.search(None, 'ALL')
    return max(int(mail_id) for mail_id in resp_data[0].decode('ascii').split())

def logging_mail_id(mail_id, message, type=logging.INFO):
    logging_prepend = 'mail_id: %s, ' % mail_id
    if type == logging.INFO:
        logger.info(logging_prepend + str(message))
    elif type == logging.ERROR:
        logger.error(logging_prepend + str(message))

def parse_mail_sender_and_subject(mail_id, folder=DEFAULT_FOLDER, M=login_imap()):

    res = {'mail_id': mail_id}

    M.select(folder)
    resp_code, resp_data = M.fetch(str(mail_id), '(RFC822)')

    if(resp_code == 'OK'):
        message_byte = resp_data[0][1]
        message = email.message_from_bytes(message_byte)
        raw_subject = message.get('subject')
        #print(mail_id, raw_subject)
        subject, encoding = decode_header(message.get('subject'))[0]
        if encoding is not None:
            subject = subject.decode(encoding)

        #print(mail_id, "mail header encoding: %s" % encoding)
        res['subject'] = subject

        report_id_search = re.search(r'bi_mail\s+run\s+(\S+)', subject)
        if report_id_search:
            res['report_id'] = report_id_search.groups()[0]

        params_search = re.search(r'bi_mail\s+run\s+\S+\s+(\S+)', subject)
        if params_search:
            res['params'] = params_search.groups()[0]

        sender = str(message.get('from'))
        #print(mail_id, 'sender: %s' % sender)
        #print(mail_id, 'sender decode: %s' % decode_header(sender))
        #print(mail_id, sender)
        res['sender'] = re.findall('[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-zA-Z]{2,}', sender)[0]

    return resp_code, res


# 解决部分邮箱搜索(M.search)无用，需要显式判断邮箱主题，如企业QQ邮箱
def is_mail_cmd(cmd_info):
    if cmd_info.get('subject').find('bi_mail') >= 0 and cmd_info.get('sender').split('@')[1] == MAIL_HOST:
        return True
    else:
        return False

def bi_mail_run(cmd_info):
    def _run():
        mail_id = cmd_info.get('mail_id', -1)
        report_id = cmd_info.get('report_id')
        params = cmd_info.get('params', '')
        sender = cmd_info.get('sender')
        subject = cmd_info.get('subject')

        if report_id is None:
            raise Exception("report_id is None")

        if sender.find(MAIL_HOST) == -1:

            cmd_info[ERROR] = '发件人必须是@%s' % MAIL_HOST
            logging_mail_id(mail_id, cmd_info, type=logging.ERROR)
            mail_params = {
              'filenames': None,
              'subject': '发件人无效',
              'owner': '',
              'to': sender,
              'cc': MAIL_MONITOR,
              'body_prepend': cmd_info
            }
            logging_mail_id(mail_id, 'send mail: %s' % mail_params)
            file_to_mail(**mail_params)
            sender_prefix = None

        else:
            sender_prefix = re.search('(\\S+)@%s' % MAIL_HOST, sender).groups()[0]

        cfg_filename = os.path.join('reports', report_id, '%s.cfg' % report_id)
        try:
            report_owner = json.loads(open(cfg_filename).read()).get('owner').split(',')
        except Exception as e:
            cmd_info[ERROR] = e
            logging_mail_id(mail_id, cmd_info, type=logging.ERROR)

            mail_params = {
              'filenames': None,
              'subject': '配置文件(%s)问题' % cfg_filename,
              'owner': '',
              'to': sender,
              'cc': MAIL_MONITOR,
              'body_prepend': cmd_info
            }
            logging_mail_id(mail_id, 'send mail: %s' % mail_params)

            file_to_mail(**mail_params)
            report_owner = []

        report_owner.append(MAIL_MONITOR.split('@')[0])
        if sender_prefix in report_owner:
            logging_mail_id(mail_id, "./run.sh '%s' '%s'" % (report_id, params))
            exit_code = subprocess.call(["./run.sh", report_id, params])
            logging_mail_id(mail_id, "./run.sh '%s' '%s', result: %s" % (report_id, params, exit_code))
        else:
            cmd_info[ERROR] = '你不是报表<%s>负责人' % report_id
            logging_mail_id(mail_id, cmd_info, type=logging.ERROR)
            mail_params = {
              'filenames': None,
              'subject': '没有权限',
              'owner': '',
              'to': sender,
              'cc': MAIL_MONITOR,
              'body_prepend': cmd_info
            }
            logging_mail_id(mail_id, 'send mail: %s' % mail_params)

            file_to_mail(**mail_params)

    try:
        background_thread = Thread(target=_run)
        background_thread.start()
    except Exception as e:
        logging_mail_id(mail_id, 'bi_mail_run failed\n%s\n%s' % (e, '-' * 40), type=logging.ERROR)

def current_time():
    return datetime.datetime.now()


def exit_condition_by_time():
    now = current_time()
    if now.hour == 23 and now.minute > 50:
        logger.info("server ends")
        return True

@multiple_trials([0] + [30] * 4)
def fetch_code(directory=BASE_DIR):
    origin_cwd = os.getcwd()
    os.chdir(directory)
    subprocess.call(['git', 'checkout', 'master'], stdout=FNULL, stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull', 'origin', 'master'], stdout=FNULL, stderr=subprocess.STDOUT)
    os.chdir('reports')
    subprocess.call(['git', 'checkout', 'master'], stdout=FNULL, stderr=subprocess.STDOUT)
    subprocess.call(['git', 'pull', 'origin', 'master'], stdout=FNULL, stderr=subprocess.STDOUT)
    os.chdir(origin_cwd)


def main():

    logger.info("server starts")

    M = login_imap()
    while True:
        if exit_condition_by_time():
            break

        logger.info('sleeping')
        time.sleep(WAIT_SECONDS)

        logger.info("fetch code")
        fetch_code()

        os.chdir('..')
        for external_project in EXTERNAL_PROJECTS:
            os.chdir(external_project)
            subprocess.call(['git', 'pull', 'origin', 'master'], stdout=FNULL, stderr=subprocess.STDOUT)
            os.chdir('..')

        os.chdir(BASE_DIR)

        try:
            M.select(DEFAULT_FOLDER)
            resp_code, resp_data = M.search(None, MAIL_SEARCH)
        except:
            time.sleep(WAIT_SECONDS)
            M = login_imap()

        min_mail_id = int(open('mail.id').read().strip())
        current_mail_id = min_mail_id
        #logger.info("min_mail_id: %s" % min_mail_id)
        if resp_code == 'OK':
            all_mail_ids = [int(mail_id) for mail_id in resp_data[0].decode('ascii').split()]
            mail_ids = list(filter(lambda x: x > min_mail_id, all_mail_ids))
            for mail_id in mail_ids:

                mail_respb_code, cmd_info = parse_mail_sender_and_subject(mail_id, M=M)
                logging_mail_id(mail_id, "got mail: %s" % mail_respb_code)
                logging_mail_id(mail_id, 'mail parsed: %s' % cmd_info)
                if is_mail_cmd(cmd_info):
                    mail_params = {
                      'filenames': None,
                      'subject': '手动运行报表<%s>监控' % cmd_info.get('report_id'),
                      'owner': '',
                      'to': MAIL_MONITOR,
                      'cc': cmd_info.get('sender'),
                      'body_prepend': cmd_info
                    }
                    logging_mail_id(mail_id, 'send mail: %s' % mail_params)

                    file_to_mail(**mail_params)
                    logging_mail_id(mail_id, "bi_mail_run: %s" % cmd_info)
                    bi_mail_run(cmd_info)

                with open('mail.id', 'w') as f:
                    f.write('{mail_id}\n'.format(mail_id=mail_id))


                if exit_condition_by_time():
                    break


if __name__ == "__main__":
    log_filename = os.path.join(BASE_DIR, 'log', '%s.log' % current_time().strftime('%Y-%m-%d_%H%M%S'))
    print('log filename:', log_filename)
    logging.basicConfig(
        filename=log_filename,
        format='\n%(levelname)s|%(asctime)s\n%(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger(__name__)
    main()

