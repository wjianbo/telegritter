""" Copyright 2017-2021 Facundo Batista

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License version 3, as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranties of
MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>.

For further info, check  https://github.com/facundobatista/telegritter """

import logging
import imaplib
import email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class GmailToKindleForwarder:
    """An interface to Gmail."""

    def __init__(self, auth_info):
        self.email_address = auth_info['email_address']
        self.kindle_address = auth_info['kindle_address']
        self.imap = imaplib.IMAP4_SSL('imap.gmail.com')
        self.imap.login(self.email_address, auth_info['password'])
        self.imap.select('book')
        self.smtp = smtplib.SMTP_SSL('smtp.gmail.com')
        self.smtp.login(
            auth_info['email_address'], auth_info['password'])

    async def forward_unread_books_to_kindle(self):
        """Get messages from Gmail."""
        _typ, data = self.imap.search(None, '(UNSEEN)')
        for msg_id in data[0].split():
            _typ, message_parts = self.imap.fetch(msg_id, '(RFC822)')
            email_body = message_parts[0][1]
            raw_email_string = email_body.decode('utf-8')
            mail = email.message_from_string(raw_email_string)
            logger.debug('emailbody complete ...')
            msg = MIMEMultipart()
            msg['Subject'] = mail['Subject']
            msg['From'] = self.email_address
            msg['To'] = self.kindle_address
            msg.attach(
                MIMEText(f'Forwarded from {mail["From"]}.', 'plain', 'utf-8'))
            for part in mail.walk():
                if part.get_content_maintype() == 'multipart':
                    # logger.debug(part.as_string())
                    continue
                if part.get('Content-Disposition') is None:
                    # logger.debug(part.as_string())
                    continue
                file_name = part.get_filename()
                logger.debug('file names processed ...')
                if bool(file_name):
                    attach_file = MIMEText(part.get_payload(), 'plain')
                    attach_file.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=file_name
                    )
                    msg.attach(attach_file)
            self.smtp.send_message(msg)

    async def poller(self, _other):
        """Check telegram to see if something's new, send it to twitter."""
        logger.debug("Running gmail poller")
        await self.forward_unread_books_to_kindle()
