#!/ada_program/python
# -*- coding: utf-8 -*-

import imaplib
import email
import datetime
import sys
import time
import os
import email
import re
import json
import subprocess

from email.header import decode_header
from file_to_mail import MAIL_USER, MAIL_PASSWD, BASE_DIR, MAIL_MONITOR, file_to_mail

DEFAULT_FOLDER = "inbox"
VALID_SENDER_SUFFIX = 'owitho.com'
MAIL_SEARCH = 'SUBJECT "bi_mail"'
WAIT_SECONDS = 6
FNULL = open(os.devnull, 'w')

os.chdir(BASE_DIR)

min_mail_id = open('mail.id').read().strip()

def login_imap():
    M = imaplib.IMAP4_SSL("mail.office365.com", port=993)
    M.login(MAIL_USER, MAIL_PASSWD)
    return M

def get_mail_count(folder=DEFAULT_FOLDER):
    M = login_imap()
    M.select(folder)
    resp_code, resp_data = M.search(None, 'ALL')
    return max(int(mail_id) for mail_id in resp_data[0].decode('ascii').split())

def parse_mail_sender_and_subject(mail_id, folder=DEFAULT_FOLDER, M=login_imap()):
    res = {'mail_id': mail_id}

    M.select(folder)
    resp_code, resp_data = M.fetch(str(mail_id), '(RFC822)')
    print("resp_code:", resp_code)
    if(resp_code == 'OK'):
        message_byte = resp_data[0][1]
        message = email.message_from_bytes(message_byte)
        raw_subject = message.get('subject')
        #print(raw_subject)
        subject, encoding = decode_header(message.get('subject'))[0]
        if encoding is not None:
            subject = subject.decode(encoding)

        #print("mail header encoding:", encoding)
        res['subject'] = subject

        report_id_search = re.search(r'bi_mail\s+run\s+(\S+)', subject)
        if report_id_search:
            res['report_id'] = report_id_search.groups()[0]

        params_search = re.search(r'bi_mail\s+run\s+\S+\s+(\S+)', subject)
        if params_search:
            res['params'] = params_search.groups()[0]

        sender = message.get('from')
        #print('sender:', sender)
        #print('sender decode:', decode_header(sender))
        #print(sender)
        res['sender'] = re.findall(r'<{0,1}([^<]*@[^>]*)>{0,1}', sender)[0]

        return res


def bi_mail_run(cmd_info):
    report_id = cmd_info.get('report_id')
    params = cmd_info.get('params', '')
    sender = cmd_info.get('sender')
    subject = cmd_info.get('subject')

    if report_id is None:
        raise Exception("report_id is None")

    if sender.find(VALID_SENDER_SUFFIX) == -1:
        raise Exception("sender has no right to run report, should be @%s" % VALID_SENDER_SUFFIX)

    sender_prefix = re.search('(\\S+)@%s' % VALID_SENDER_SUFFIX, sender).groups()[0]

    cfg_filename = os.path.join('reports', report_id, '%s.cfg' % report_id)
    report_owner = json.loads(open(cfg_filename).read()).get('owner').split(',')
    report_owner.append(MAIL_MONITOR.split('@')[0])
    if sender_prefix in report_owner:
        print("./run.sh '%s' %s" % (report_id, params))
        print("exit code:", subprocess.call(["./run.sh", report_id, params]))


def current_time():
    return datetime.datetime.now()


def exit_condition_by_time():
    now = current_time()
    if now.hour == 23 and now.minute > 50:
        print("server ends at %s" % current_time())
        return True


def main():
    print("server starts at %s" % current_time())
    M = login_imap()
    while True:
        print("loops starts at %s" % current_time())
        if exit_condition_by_time():
            break

        time.sleep(WAIT_SECONDS)

        subprocess.call(['git', 'checkout', 'dev'], stdout=FNULL, stderr=subprocess.STDOUT)
        subprocess.call(['git', 'pull', 'origin', 'dev'], stdout=FNULL, stderr=subprocess.STDOUT)
        os.chdir('reports')
        subprocess.call(['git', 'checkout', 'dev'], stdout=FNULL, stderr=subprocess.STDOUT)
        subprocess.call(['git', 'pull', 'origin', 'dev'], stdout=FNULL, stderr=subprocess.STDOUT)
        os.chdir(BASE_DIR)

        try:
            M.select(DEFAULT_FOLDER)
            resp_code, resp_data = M.search(None, MAIL_SEARCH)
        except:
            time.sleep(WAIT_SECONDS)
            M = login_imap()

        min_mail_id = int(open('mail.id').read().strip())
        current_mail_id = min_mail_id
        #print("min_mail_id:", min_mail_id)
        if resp_code == 'OK':
            all_mail_ids = [int(mail_id) for mail_id in resp_data[0].decode('ascii').split()]
            mail_ids = list(filter(lambda x: x > min_mail_id, all_mail_ids))
            for mail_id in mail_ids:
                print("mail_id:", mail_id)

                cmd_info = parse_mail_sender_and_subject(mail_id, M=M)
                print("cmd_info:", cmd_info)

                file_to_mail(None, '手动运行报表<%s>监控' % cmd_info.get('report_id'),
		            '', MAIL_MONITOR, cc=cmd_info.get('sender'), body_prepend=cmd_info)

                try:
                    bi_mail_run(cmd_info)
                except Exception as e:
                    print("invalid cmd_info")
                    print(e.args)

                with open('mail.id', 'w') as f:
                    f.write('{mail_id}\n'.format(mail_id=mail_id))

                if exit_condition_by_time():
                    break

if __name__ == "__main__":
    main()

