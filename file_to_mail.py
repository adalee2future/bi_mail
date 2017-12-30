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

def file_to_mail(filename, subject, owner, to, cc=None, bcc=None, body_prepend='', customized_styles='', fake_cc=None):

    s = smtplib.SMTP('smtp.office365.com', port=587)
    s.ehlo()
    s.starttls()
    s.login(os.environ['mail_user'], os.environ['mail_passwd'])

    me = os.environ['mail_user']
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['to'] = to
    receiver_list = to.split(',')
    msg_cc = None

    if cc is not None:
        msg_cc = cc
        receiver_list += cc.split(',')

    if fake_cc is not None:
        if cc is None:
            msg_cc = fake_cc
        else:
            msg_cc = ','.join([cc, fake_cc])
 
    msg['cc'] = msg_cc

    if bcc is not None:
        msg['bcc'] = bcc
        receiver_list += bcc.split(',')

    if filename is not None:
        with open(filename, 'rb') as f:
            file_part = MIMEApplication(f.read(), Name=os.path.basename(filename))
        file_part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
        msg.attach(file_part)

    mail_body = '''
     <style>\n{styles}\n{customized_styles}\n</style>
     <br/><br/>
     {body_prepend}
     <br/><br/>
     --------------------------------
     <br/><br/>
     如对数据有任何疑问，请联系{owner}
     <br/><br/>
     [自动发送]
     <br/><br/>
    '''.format(styles=STYLES, customized_styles=customized_styles, body_prepend=body_prepend, owner=owner)

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
