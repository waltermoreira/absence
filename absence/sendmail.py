"""
Simple command line utility to send emails through an SMTP server.
"""

import email
import email.utils
import email.mime.text
import smtplib
import socket
import argparse
import sys
from functools import partial
import absence.secrets as secrets

class BaseSendmail(object):
    """
    Example::

      mailer = BaseSendmail(
          'My Real Name <my_email@somewhere.net>',
          'mail.somewhere.net',  # SMTP server for relaying
          'password')            # Authentication, if needed

    Then, do::

      mailer.sendmail(
          ['to@other', 'to@another'],
          'message', 'subject')
    """

    def __init__(self, from_addr, mail_server, password=None):
        self.from_addr = from_addr
        self.password = password
        self.real_name, self.email = email.utils.parseaddr(from_addr)
        self.inbox_name, _ = self.email.split('@')
        self.mail_server = mail_server
        self.authenticate()

    def authenticate(self):
        """
        Create a SMTP connection to a mail relaying server.

        Override this method in subclasses if some other
        authentication method is needed.
        """
        self.smtp = smtplib.SMTP(self.mail_server, 587)
        self.smtp.starttls()
        self.smtp.login(self.inbox_name, self.password)

    def sendmail(self, to, msg, subject=None):
        if self.smtp is None:
            raise smtplib.SMTPException('need to authenticate first')
        mmsg = email.mime.text.MIMEText(msg)
        mmsg['Subject'] = subject or '<no subject>'
        mmsg['From'] = self.from_addr
        mmsg['To'] = ', '.join(to)
        self.smtp.sendmail(self.from_addr, to, mmsg.as_string())
        self.smtp.quit()


def create_mailer():
    c = secrets.read()
    user = c.get('mail', 'user')
    password = c.get('mail', 'password')
    server = c.get('mail', 'server')
    return BaseSendmail(user, server, password)


def parse_args():
    parser = argparse.ArgumentParser(description='Python sendmail')
    parser.add_argument('-t', '--to', nargs=1, metavar='addr',
                        required=True,
                        help='To: addresses (comma separated)')
    parser.add_argument('-m', '--msg', nargs=1, metavar='message',
                        help=('the message (read stdin if not given). '
                              'If empty, no mail is sent.'))
    parser.add_argument('-s', '--subject', nargs=1, metavar='subject',
                        default=[None],
                        help='the subject (default "<no subject>"')
    args = parser.parse_args()
    return args

def process_args(args):
    msg = args.msg[0] if args.msg is not None else sys.stdin.read()
    to = args.to[0].split(',')
    subject = args.subject[0]
    non_empty = msg.strip()
    return non_empty, to, msg, subject

if __name__ == '__main__':
    non_empty, to, msg, subject = process_args(parse_args())
    if non_empty:
        mailer = create_mailer()
        mailer.sendmail(to, msg, subject)
