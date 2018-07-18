#!/ada_program/python
# -*- coding: utf-8 -*-

import json
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header

BASE_DIR = os.path.dirname(__file__)
STYLES = open(os.path.join(BASE_DIR, 'styles.css')).read()
MAIL_USER = os.environ['mail_user']
MAIL_PASSWD = os.environ['mail_passwd']
MAIL_MONITOR = os.environ['mail_monitor']
REPORT_TYPE_MAP = {
    'report': '报表',
    'vreport': '报告'
}
def file_to_mail(filenames, subject, owner, to, cc=None, bcc=None, body_prepend='', customized_styles='', fake_cc=None, mail_user=MAIL_USER, mail_passwd=MAIL_PASSWD, supervised=None, caption='', report_type='report'):

    s = smtplib.SMTP('smtp.office365.com', port=587)
    s.ehlo()
    s.starttls()
    s.login(mail_user, mail_passwd)

    me = mail_user
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['to'] = to
    receiver_list = to.split(',')

    msg_cc_list = []
    if cc is not None:
        msg_cc_list += cc.split(',')
        receiver_list += cc.split(',')

    if supervised is None:
        supervised = bool(os.environ.get('supervised', False))

    if supervised and MAIL_MONITOR not in receiver_list:
        msg_cc_list.append(MAIL_MONITOR)
        receiver_list.append(MAIL_MONITOR)

    if fake_cc is not None:
        msg_cc_list.append(MAIL_MONITOR)

    msg['cc'] = ','.join(msg_cc_list)
    msg['bcc'] = bcc
    if bcc is not None:
        receiver_list += bcc.split(',')

    if type(filenames) == str:
        filenames = [filenames]
    if filenames is not None:
        for filename in filenames:
            with open(filename, 'rb') as f:
                file_part = MIMEApplication(f.read(), Name=os.path.basename(filename))
                file_part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
                msg.attach(file_part)

    mail_body = '''
     <style>\n{styles}\n{customized_styles}\n</style>
     <br/><br/>
     {body_prepend}
     {caption}
     <br/><br/>
     --------------------------------
     <br/><br/>
     如对{report_type_name}有任何疑问，请联系{owner}
     <br/><br/>
     [自动发送]
     <br/><br/>
    '''.format(styles=STYLES, customized_styles=customized_styles, body_prepend=body_prepend, owner=owner, caption=caption, report_type_name=REPORT_TYPE_MAP[report_type])

    mail_body_html = MIMEText(mail_body, 'html', 'utf-8')
    msg.attach(mail_body_html)

    print("\nowner:", owner)
    print("receiver_list:", receiver_list)
    print("subject:", msg.get('subject'))
    print("to:", msg.get('to'))
    print("cc:", msg.get('cc'))
    print("bcc:", msg.get('bcc'))
    s.sendmail(me, receiver_list, msg.as_string())
    print("mail sent!\n")
    s.quit()

if __name__ == "__main__":
    file_to_mail(*sys.argv[1:])
