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

STYLES = open('styles.css').read()

def file_to_mail(filename, subject, owner, to, cc=None, bcc=None, body_prepend=''):
    print("subject", subject)
    print("owner", owner)
    print("to", to)
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
    if cc is not None:
        msg['cc'] = cc
        receiver_list += cc.split(',')
    if bcc is not None:
        msg['bcc'] = bcc
        receiver_list += bcc.split(',')

    if filename is not None:
        with open(filename, 'rb') as f:
            file_part = MIMEApplication(f.read(), Name=os.path.basename(filename))
        file_part['Content-Disposition'] = 'attachment; filename="%s"' % Header(os.path.basename(filename), 'UTF-8')
        msg.attach(file_part)

    mail_body = '''
     <style>{styles}</style>
     <br/><br/>
     {body_prepend}
     <br/><br/>
     --------------------------------
     <br/><br/>
     如对数据有任何疑问，请联系{owner}

     <br/><br/>
     如果附件有问题，请用outlook客户端或者<a href="https://outlook.office.com/owa/?path=/group/owitho@owitho.com/mail">outlook网页版</a>打开该邮件
     <br/><br/>
     [自动发送]
     <br/><br/>
    '''.format(styles=STYLES, body_prepend=body_prepend, owner=owner)

    mail_body_html = MIMEText(mail_body, 'html', 'utf-8')
    msg.attach(mail_body_html)


    print('\n', msg)
    s.sendmail(me, receiver_list, msg.as_string())

if __name__ == "__main__":
    file_to_mail(*sys.argv[1:])
