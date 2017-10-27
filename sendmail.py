#!/ada_program/python
# -*- coding: utf-8 -*-

import sys
import os
import smtplib
from email.mime.text import MIMEText

s = smtplib.SMTP('smtp.office365.com')
s.ehlo()
s.starttls()
s.login(os.environ['mail_user'], os.environ['mail_passwd'])
me = os.environ['mail_user']
you = me

msg = MIMEText('hello')
msg['Subject'] = '自动发送(python)'
msg['From'] = me
msg['to'] = you

s.sendmail(me, you.split(','), msg.as_string())
