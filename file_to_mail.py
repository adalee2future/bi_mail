# -*- coding: utf-8 -*-

import json
import sys
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header
import premailer

from helper import multiple_trials
from helper import BASE_DIR, REPORT_TYPE_MAP
from helper import SMTP_HOST, SMTP_PORT, SMTP_PROTOCOL
from helper import MAIL_MONITOR, MAIL_USER, MAIL_PASSWD, STYLES


@multiple_trials()
def file_to_mail(filenames, subject, owner, to, cc=None, bcc=None, body_prepend='', customized_styles='', fake_cc=None, mail_user=MAIL_USER, mail_passwd=MAIL_PASSWD, supervised=None, caption='', report_type='report', sender_display=None, fake_to=None, smtp_protocol=SMTP_PROTOCOL):

    if smtp_protocol.lower() == 'ssl': 
        s = smtplib.SMTP_SSL(SMTP_HOST, port=SMTP_PORT)
        s.ehlo()
    else:
        s = smtplib.SMTP(SMTP_HOST, port=SMTP_PORT)
        s.ehlo()
        if(smtp_protocol == 'tls'):
            s.starttls()

    s.login(mail_user, mail_passwd)
    me = mail_user
    msg = MIMEMultipart()
    msg['Subject'] = subject
    if sender_display is None:
        msg['From'] = me
    else:
        msg['From'] = "%s<%s>" % (sender_display, me)
    print(msg['From'])
    receiver_list = to.split(',')

    msg_to_list = to.split(',')
    msg_cc_list = []

    if cc is not None:
        msg_cc_list += cc.split(',')
        receiver_list += cc.split(',')

    if supervised is None:
        os_supervised = os.environ.get('supervised', 'false')
        if os_supervised.lower().startswith('t'):
            supervised = True
        else:
            supervised = False

    print("supervised:", supervised)
    if supervised and MAIL_MONITOR not in receiver_list:
        msg_cc_list.append(MAIL_MONITOR)
        receiver_list.append(MAIL_MONITOR)

    if fake_cc is not None:
        msg_cc_list += fake_cc.split(',')

    if fake_to is not None:
        msg_to_list += fake_to.split(',')

    msg['to'] = ','.join(msg_to_list)
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
     [BI自建报表系统]
     <br/><br/>
    '''.format(styles=STYLES, customized_styles=customized_styles, body_prepend=body_prepend, owner=owner, caption=caption, report_type_name=REPORT_TYPE_MAP[report_type])

    mail_body = premailer.transform(mail_body)
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
