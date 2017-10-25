#!/Users/Ada/anaconda3/anaconda/bin/python
# -*- coding: utf-8 -*-

import json
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart



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
    file_part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filename)
    msg.attach(file_part)
    
    mail_body = MIMEText('\n\n\n如需退订，请联系发件人')
    msg.attach(mail_body)
    
    s.sendmail(me, to.split(','), msg.as_string())