# Copyright 2011-2012 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

import logging
import socket

from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

import astakos.im.messages as astakos_messages

from astakos.im.settings import LOGGING_LEVEL

logger = logging.getLogger(__name__)

def _send_admin_notification(template_name,
                             dictionary=None,
                             subject='alpha2 testing notification',):
    """
    Send notification email to settings.ADMINS.

    Raises SendNotificationError
    """
    if not settings.ADMINS:
        return
    dictionary = dictionary or {}
    message = render_to_string(template_name, dictionary)
    sender = settings.SERVER_EMAIL
    try:
        send_mail(subject,
                  message, sender, [i[1] for i in settings.ADMINS])
    except (SMTPException, socket.error) as e:
        logger.exception(e)
        raise SendNotificationError()
    else:
        msg = 'Sent admin notification for user %s' % dictionary.get('email',
                                                                     None)
        logger.log(LOGGING_LEVEL, msg)

class EmailNotification(Notification):
    def send(self):
        send_mail(
            subject,
            message,
            sender,
            recipients
        )

class Notification(object):
    def __init__(self, sender, recipients, subject, message):
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.message = message

    def send(self):
        pass

class SendMailError(Exception):
    pass

class SendNotificationError(SendMailError):
    def __init__(self):
        self.message = _(astakos_messages.NOTIFICATION_SEND_ERR)
        super(SendNotificationError, self).__init__()
