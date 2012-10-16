# Copyright 2011-2012 GRNET S.A. All rights reserved.
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
#

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from synnefo.db.models import Backend, Network
from django.db.utils import IntegrityError
from synnefo.logic.backend import (get_physical_resources,
                                   update_resources,
                                   create_network_synced,
                                   connect_network_synced)
from synnefo.logic.rapi import GanetiApiError, GanetiRapiClient


class Command(BaseCommand):
    can_import_settings = True

    help = 'Create a new backend.'
    output_transaction = True  # The management command runs inside
                               # an SQL transaction
    option_list = BaseCommand.option_list + (
        make_option('--clustername', dest='clustername'),
        make_option('--port', dest='port', default=5080),
        make_option('--user', dest='username'),
        make_option('--pass', dest='password'),
        make_option('--drained', action='store_true',
            dest='drained', default=False,
            help="Set as drained to exclude from allocations"),
        make_option('--no-check', action='store_false',
            dest='check', default=True,
            help="Do not perform credentials check and resources update"),
        make_option('--no-init', action='store_false',
            dest='init', default=True,
            help="Do not perform initialization of the Backend Model")
        )

    def handle(self, **options):
        clustername = options['clustername']
        port = options['port']
        username = options['username']
        password = options['password']
        drained = options['drained']

        if not (clustername and username and password):
            raise CommandError("Clustername, user and pass must be supplied")

        # Ensure correctness of credentials
        if options['check']:
            self.stdout.write('Checking connectivity and credentials.\n')
            try:
                client = GanetiRapiClient(clustername, port, username, password)
                # This command will raise an exception if there is no
                # write-access
                client.ModifyCluster()
            except GanetiApiError as e:
                self.stdout.write('Check failed:\n%s\n' % e)
                return
            else:
                self.stdout.write('Check passed.\n')

        # Create the new backend in database
        try:
            backend = Backend.objects.create(clustername=clustername,
                                             port=port,
                                             username=username,
                                             password=password,
                                             drained=drained)
        except IntegrityError as e:
            raise CommandError("Cannot create backend: %s\n" % e)

        self.stdout.write('\nSuccessfully created backend with id %d\n' %
                          backend.id)

        if not options['check']:
            return

        self.stdout.write('\rRetrieving backend resources:\n')
        resources = get_physical_resources(backend)
        attr = ['mfree', 'mtotal', 'dfree', 'dtotal', 'pinst_cnt', 'ctotal']
        self.stdout.write('----------------------------\n')
        for a in attr:
            self.stdout.write(a.ljust(12) + ' : ' + str(resources[a]) + '\n')
        update_resources(backend, resources)

        if not options['init']:
            return

        networks = Network.objects.filter(deleted=False, public=False)
        if not networks:
            return

        self.stdout.write('\nCreating the follow networks:\n')
        fields = ('Name', 'Subnet', 'Gateway', 'Mac Prefix', 'Public')
        columns = (20, 16, 16, 16, 10)
        line = ' '.join(f.ljust(c) for f, c in zip(fields, columns))
        sep = '-' * len(line)
        self.stdout.write(sep + '\n')
        self.stdout.write(line + '\n')
        self.stdout.write(sep + '\n')

        for net in networks:
            fields = (net.backend_id, str(net.subnet), str(net.gateway),
                      str(net.mac_prefix), str(net.public))
            line = ' '.join(f.ljust(c) for f, c in zip(fields, columns))
            self.stdout.write(line + '\n')
        self.stdout.write(sep + '\n\n')

        for net in networks:
            net.create_backend_network(backend)
            result = create_network_synced(net, backend)
            if result[0] != "success":
                self.stdout.write('\nError Creating Network %s: %s\n' %\
                                  (net.backend_id, result[1]))
            else:
                self.stdout.write('Successfully created Network: %s\n' %
                                 net.backend_id)
            result = connect_network_synced(network=net, backend=backend)
            if result[0] != "success":
                self.stdout.write('\nError Connecting Network %s: %s\n' %\
                                  (net.backend_id, result[1]))
            else:
                self.stdout.write('Successfully connected Network: %s\n' %
                                 net.backend_id)