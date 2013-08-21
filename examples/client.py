# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText


s = smtplib.SMTP('localhost')
s.set_debuglevel(1)
msg = MIMEText("""This is the message's body.""")
sender = 'me@example.com'
recipients = ['you@example.com', 'all@example.com']
msg['Subject'] = "This is the subject."
msg['From'] = sender
msg['To'] = ", ".join(recipients)
s.sendmail(sender, recipients, msg.as_string())
s.quit()
