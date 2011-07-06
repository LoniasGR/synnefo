# vim: set fileencoding=utf-8 :
# Copyright 2011 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   1. Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of GRNET S.A.

from synnefo.aai import middleware
from synnefo.db.models import SynnefoUser
from django.conf import settings
from django.http import HttpResponse
import time

class HelpdeskMiddleware(object):

    auth_tmp_token = "X-Auth-Tmp-Token"
    install_path  = "/helpdesk"

    def __init__(self):
       middleware.add_url_exception(self.install_path)

    def process_request(self, request):

        if not request.path.startswith('/helpdesk'):
            if not 'X-Auth-Tmp-Token' in request.COOKIES:
                return 

        # Check the request's IP address
        allowed = settings.HELPDESK_ALLOWED_IPS
        if not check_ip(request.META['REMOTE_ADDR'], allowed):
            try:
                proxy_ip = request.META['HTTP_X_FORWARDED_FOR']
            except Exception:
                return HttpResponse(status=403,
                                    content="IP Address not allowed")
            if not check_ip(proxy_ip, allowed):
                return HttpResponse(status=403,
                                    content="IP Address not allowed")

        # Helpdesk application request, search for a valid helpdesk user
        try:
            hd_user_token = request.COOKIES['X-Auth-Token']
            if hd_user_token:
                try:
                    hd_user = SynnefoUser.objects.get(auth_token=hd_user_token)
                except Exception:
                    return HttpResponse(status=401,
                                        content="Not a valid helpdesk user")

                if not hd_user.type == 'HELPDESK':
                    return HttpResponse(status=401,
                                    content="Not a valid helpdesk user")
            else:
                return HttpResponse(status=401,
                                    content="Not a valid helpdesk user")
        except KeyError:
            return

        # Helpdesk application request, search for a valid tmp token
        if not 'X-Auth-Tmp-Token' in request.COOKIES:
            return

        tmp_token = request.COOKIES['X-Auth-Tmp-Token']

        try:
            tmp_user = SynnefoUser.objects.get(tmp_auth_token=tmp_token)
        except Exception:
            return HttpResponse(status=401, content="Not a valid helpdesk user")

        if (time.time() -
            time.mktime(tmp_user.tmp_auth_token_expires.timetuple())) > 0:
            # The impersonated user's token has expired, re-login
            return

        # Impersonate the request user: Perform requests from the helpdesk
        # account on behalf of the impersonated user
        request.user = tmp_user
        request.readonly = True

def check_ip(ip, allowed):
    for addr in allowed:
        # Check exact match
        if ip == addr:
            return True;
        # Check range match
        if addr.endswith('.0'):
            iprange = ip[0:ip.rfind(".")]
            if addr.startswith(iprange):
                return True
        else:
            continue

        return False