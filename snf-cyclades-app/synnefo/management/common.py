# Copyright 2012 GRNET S.A. All rights reserved.
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


import ipaddr
from datetime import datetime

from django.utils.timesince import timesince, timeuntil

from django.core.management import CommandError
from synnefo.db.models import Backend, VirtualMachine, Network, Flavor
from synnefo.api.util import get_image as backend_get_image
from synnefo.api.faults import ItemNotFound
from django.core.exceptions import FieldError


from synnefo.api.util import validate_network_size
from synnefo.settings import MAX_CIDR_BLOCK


def format_bool(b):
    return 'YES' if b else 'NO'


def format_date(d):
    if not d:
        return ''

    if d < datetime.now():
        return timesince(d) + ' ago'
    else:
        return 'in ' + timeuntil(d)


def format_vm_state(vm):
    if vm.operstate == "BUILD":
        return "BUILD(" + str(vm.buildpercentage) + "%)"
    else:
        return vm.operstate


def validate_network_info(options):
    subnet = options['subnet']
    gateway = options['gateway']
    subnet6 = options['subnet6']
    gateway6 = options['gateway6']

    try:
        net = ipaddr.IPv4Network(subnet)
        prefix = net.prefixlen
        if not validate_network_size(prefix):
            raise CommandError("Unsupport network mask %d."
                               " Must be in range (%s,29] "
                               % (prefix, MAX_CIDR_BLOCK))
    except ValueError:
        raise CommandError('Malformed subnet')
    try:
        gateway and ipaddr.IPv4Address(gateway) or None
    except ValueError:
        raise CommandError('Malformed gateway')

    try:
        subnet6 and ipaddr.IPv6Network(subnet6) or None
    except ValueError:
        raise CommandError('Malformed subnet6')

    try:
        gateway6 and ipaddr.IPv6Address(gateway6) or None
    except ValueError:
        raise CommandError('Malformed gateway6')

    return subnet, gateway, subnet6, gateway6


def get_backend(backend_id):
    try:
        backend_id = int(backend_id)
        return Backend.objects.get(id=backend_id)
    except ValueError:
        raise CommandError("Invalid Backend ID: %s" % backend_id)
    except Backend.DoesNotExist:
        raise CommandError("Backend with ID %s not found in DB. "
                           " Use snf-manage backend-list to find"
                           " out available backend IDs." % backend_id)


def get_image(image_id, user_id):
    if image_id:
        try:
            return backend_get_image(image_id, user_id)
        except ItemNotFound:
            raise CommandError("Image with ID %s not found."
                               " Use snf-manage image-list to find"
                               " out available image IDs." % image_id)
    else:
        raise CommandError("image-id is mandatory")


def get_vm(server_id):
    try:
        server_id = int(server_id)
        return VirtualMachine.objects.get(id=server_id)
    except ValueError:
        raise CommandError("Invalid server ID: %s", server_id)
    except VirtualMachine.DoesNotExist:
        raise CommandError("Server with ID %s not found in DB."
                           " Use snf-manage server-list to find out"
                           " available server IDs." % server_id)


def get_network(network_id):
    try:
        network_id = int(network_id)
        return Network.objects.get(id=network_id)
    except ValueError:
        raise CommandError("Invalid network ID: %s", network_id)
    except Network.DoesNotExist:
        raise CommandError("Network with ID %s not found in DB."
                           " Use snf-manage network-list to find out"
                           " available network IDs." % network_id)


def get_flavor(flavor_id):
    try:
        flavor_id = int(flavor_id)
        return Flavor.objects.get(id=flavor_id)
    except ValueError:
        raise CommandError("Invalid flavor ID: %s", flavor_id)
    except Flavor.DoesNotExist:
        raise CommandError("Flavor with ID %s not found in DB."
                           " Use snf-manage flavor-list to find out"
                           " available flavor IDs." % flavor_id)


def filter_results(objects, filter_by):
    filter_list = filter_by.split(",")
    filter_dict = {}
    exclude_dict = {}

    def map_field_type(query):
        def fix_bool(val):
            if val.lower() in ("yes", "true", "t"):
                return True
            if val.lower() in ("no", "false", "f"):
                return False
            return val

        if "!=" in query:
            key, val = query.split("!=")
            exclude_dict[key] = fix_bool(val)
            return
        OP_MAP = {
            ">=": "__gte",
            "=>": "__gte",
            ">":  "__gt",
            "<=": "__lte",
            "=<": "__lte",
            "<":  "__lt",
            "=":  ""
        }
        for op, new_op in OP_MAP.items():
            if op in query:
                key, val = query.split(op)
                filter_dict[key + new_op] = fix_bool(val)
                return

    map(lambda x: map_field_type(x), filter_list)

    try:
        objects = objects.filter(**filter_dict)
        return objects.exclude(**exclude_dict)
    except FieldError as e:
        raise CommandError(e)