#!/ada_program/python
# -*- coding: utf-8 -*-

import imaplib
import email
import datetime
import sys
import time
import os
import email
from email.header import decode_header
import re
import json
from subprocess import call
from file_to_mail import MAIL_USER, MAIL_PASSWD, BASE_DIR

DEFAULT_FOLDER = "inbox"
VALID_SENDER_SUFFIX = 'owitho.com'
MAIL_SEARCH = 'SUBJECT "bi_mail run"'
WAIT_SECONDS = 60

os.chdir(BASE_DIR)

min_mail_id = open('mail.id').read().strip()

M = imaplib.IMAP4_SSL("mail.office365.com", port=993)
M.login(MAIL_USER, MAIL_PASSWD)

M.select(DEFAULT_FOLDER)
resp_code, resp_data = M.search(None, MAIL_SEARCH)


def parse_mail_sender_and_subject(mail_id, folder=DEFAULT_FOLDER):
    
    M.select(folder)
    
    res = {}
    
    resp_code, resp_data = M.fetch(str(mail_id), '(RFC822)')
    print("reso_code:", resp_code)
    if(resp_code == 'OK'):
        message_byte = resp_data[0][1]
        message = email.message_from_bytes(message_byte)
        raw_subject = message.get('subject')
        print(raw_subject)
        subject, encoding = decode_header(message.get('subject'))[0]
        if encoding is not None:
            subject = subject.decode(encoding)
       
        print("mail header encoding:", encoding)
        res['subject'] = subject
        
        report_id_search = re.search(r'bi_mail run (\S+)', subject)
        if report_id_search:
            res['report_id'] = report_id_search.groups()[0]
            
        sender = message.get('from')
        print('sender:', sender)
        print('sender decode:', decode_header(sender))
        print(sender)
        res['sender'] = re.findall(r'<{0,1}([^<]*@[^>]*)>{0,1}', sender)[0]
        
        return res
  

def bi_mail_run(cmd_info):
    report_id = cmd_info.get('report_id')
    sender = cmd_info.get('sender')
    subject = cmd_info.get('subject')
    
    if report_id is None:
        raise Exception("report_id is None")
        
    if sender.find(VALID_SENDER_SUFFIX) == -1:
        raise Exception("sender has no right to run report, should be @%s" % VALID_SENDER_SUFFIX)
    
    sender_prefix = re.search('(\\S+)@%s' % VALID_SENDER_SUFFIX, sender).groups()[0]
    
    cfg_filename = os.path.join('reports', report_id, '%s.cfg' % report_id)
    report_owner = json.loads(open(cfg_filename).read()).get('owner').split(',')
    if sender_prefix in report_owner:
        print("./run.sh %s" % report_id)
        call(["./run.sh", report_id])
        
def exist_condition_by_time():
    now = datetime.datetime.now()
    if now.hour == 23 and now.minute > 50:
        return True


while True:
    print("server starts at %s" % datetime.datetime.now())
    if exist_condition_by_time():
        break
    time.sleep(WAIT_SECONDS)
    git_cmd = 'git checkout dev; git pull origin dev'
    print(git_cmd)
    os.system(git_cmd)
    print("loop start time:", datetime.datetime.now())
    M.select(DEFAULT_FOLDER)
    resp_code, resp_data = M.search(None, MAIL_SEARCH)
    min_mail_id = int(open('mail.id').read().strip())
    current_mail_id = min_mail_id
    print("min_mail_id:", min_mail_id)
    if resp_code == 'OK':
        print("OK")
        all_mail_ids = [int(mail_id) for mail_id in resp_data[0].decode('ascii').split()]
        mail_ids = list(filter(lambda x: x > min_mail_id, all_mail_ids))
        print("mail_ids:", mail_ids)
        for mail_id in mail_ids:
            print("mail_id:", mail_id)
            print("enter mail_id loops")
            
            cmd_info = parse_mail_sender_and_subject(mail_id)
            print("cmd_info:", cmd_info)
            
            try:
                bi_mail_run(cmd_info)
            except Exception as e:
                print("invalid cmd_info")
                print(e.args)
        
        if len(mail_ids) > 0 and mail_id > min_mail_id:
            with open('mail.id', 'w') as f:
                f.write('{mail_id}\n'.format(mail_id=mail_id)) 

