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
import json
import time 

from django.views.decorators.csrf import csrf_protect
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest
from synnefo.db.models import SynnefoUser, Invitations
from synnefo.api.common import method_not_allowed
from synnefo.logic import users

@csrf_protect
def index(request):

    if request.method == 'GET':
        data = render_to_string('helpdesk.html',
                                {'users': get_users(request)},
                                context_instance=RequestContext(request))
        return HttpResponse(data)
    else:
        method_not_allowed(request)

def get_users(request):
    #XXX: The following filter should change when the invitations app is removed
    invitations = Invitations.objects.filter(accepted = False)
    ids = map(lambda x: x.target.id, invitations)
    users = SynnefoUser.objects.exclude(id__in = ids)\
                               .exclude(type__exact = "HELPDESK")\
                               .order_by('realname')
    result = []

    for user in users:
        resultentry = {}

        resultentry['id'] = user.id
        resultentry['name'] = user.realname

        result.append(resultentry)

    return result

def get_tmp_token(request):

    try:
        user_id = request.GET['user_id']
    except KeyError:
        return HttpResponseBadRequest()

    user = SynnefoUser.objects.get(id = user_id)

    if user is None:
        return HttpResponseBadRequest()

    if  user.tmp_auth_token_expires is None or \
        time.time() - time.mktime(user.tmp_auth_token_expires.timetuple()) > 0:
        users.create_tmp_token(user)

    token = dict()
    token['token'] = user.tmp_auth_token
    token['expires'] = int(time.mktime(user.tmp_auth_token_expires.timetuple()))

    response = HttpResponse(json.dumps(token))

    expire_fmt = user.tmp_auth_token_expires.strftime('%a, %d-%b-%Y %H:%M:%S %Z')
    response.set_cookie('X-Auth-Tmp-Token', value=user.tmp_auth_token,
                            expires = expire_fmt,
                            path='/')
    return response