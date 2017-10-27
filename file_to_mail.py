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

def file_to_mail(filename, subject, to):
    s = smtplib.SMTP('smtp.office365.com')
    s.ehlo()
    s.starttls()
    s.login(os.environ['mail_user'], os.environ['mail_passwd'])

    me = os.environ['mail_user']
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['to'] = to
    print(msg)

    with open(filename, 'rb') as f:
        file_part = MIMEApplication(f.read(), Name=os.path.basename(filename))
        #file_part = MIMEApplication(f.read())
    #filename = os.path.basename(filename).encode('utf-8')
    file_part['Content-Disposition'] = 'attachment; filename="%s"' % Header(os.path.basename(filename), 'UTF-8')
    msg.attach(file_part)

    mail_body = '''
     <br/><br/>
     如需退订，请联系发件人

     <br/><br/>
     如果附件有问题，请用outlook客户端或者<a href="https://outlook.office.com/owa/?path=/group/owitho@owitho.com/mail">outlook网页版</a>打开该邮件
    '''
    mail_body_html = MIMEText(mail_body, 'html', 'utf-8')
    msg.attach(mail_body_html)

    s.sendmail(me, to.split(','), msg.as_string())
