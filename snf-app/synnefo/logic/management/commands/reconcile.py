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
#
"""Reconciliation management command

Management command to reconcile the contents of the Synnefo DB with
the state of the Ganeti backend. See docstring on top of
logic/reconciliation.py for a description of reconciliation rules.

"""
import sys

from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.db.models import Q
from django.core.management.base import BaseCommand

from synnefo.db.models import VirtualMachine
from synnefo.logic import reconciliation, backend
from synnefo.util.rapi import GanetiRapiClient


class Command(BaseCommand):
    can_import_settings = True

    help = 'Reconcile contents of Synnefo DB with state of Ganeti backend'
    output_transaction = True  # The management command runs inside
                               # an SQL transaction
    option_list = BaseCommand.option_list + (
        make_option('--detect-stale', action='store_true', dest='detect_stale',
                    default=False, help='Detect stale VM entries in DB'),
        make_option('--detect-orphans', action='store_true',
                    dest='detect_orphans',
                    default=False, help='Detect orphan instances in Ganeti'),
        make_option('--detect-unsynced', action='store_true',
                    dest='detect_unsynced',
                    default=False, help='Detect unsynced operstate between ' +
                                        'DB and Ganeti'),
        make_option('--detect-all', action='store_true',
                    dest='detect_all',
                    default=False, help='Enable all --detect-* arguments'),
        make_option('--fix-stale', action='store_true', dest='fix_stale',
                    default=False, help='Fix (remove) stale DB entries in DB'),
        make_option('--fix-orphans', action='store_true', dest='fix_orphans',
                    default=False, help='Fix (remove) orphan Ganeti VMs'),
        make_option('--fix-unsynced', action='store_true', dest='fix_unsynced',
                    default=False, help='Fix server operstate in DB, set ' +
                                        'from Ganeti'),
        make_option('--fix-all', action='store_true', dest='fix_all',
                    default=False, help='Enable all --fix-* arguments'))

    def _process_args(self, options):
        keys_detect = [k for k in options.keys() if k.startswith('detect_')]
        keys_fix = [k for k in options.keys() if k.startswith('fix_')]

        if options['detect_all']:
            for kd in keys_detect:
                options[kd] = True
        if options['fix_all']:
            for kf in keys_fix:
                options[kf] = True

        if not reduce(lambda x, y: x or y,
                      map(lambda x: options[x], keys_detect)):
            raise Exception("At least one of --detect-* must be specified")

        for kf in keys_fix:
            kd = kf.replace('fix_', 'detect_', 1)
            if (options[kf] and not options[kd]):
                raise Exception("Cannot use --%s without corresponding "
                                "--%s argument" % (kf, kd))

    def handle(self, **options):
        verbosity = int(options['verbosity'])
        self._process_args(options)

        D = reconciliation.get_servers_from_db()
        G = reconciliation.get_instances_from_ganeti()

        #
        # Detect problems
        #
        if options['detect_stale']:
            stale = reconciliation.stale_servers_in_db(D, G)
            if len(stale) > 0:
                print >> sys.stderr, "Found the following stale server IDs: "
                print "    " + "\n    ".join(
                    [str(x) for x in stale])
            elif verbosity == 2:
                print >> sys.stderr, "Found no stale server IDs in DB."

        if options['detect_orphans']:
            orphans = reconciliation.orphan_instances_in_ganeti(D, G)
            if len(orphans) > 0:
                print >> sys.stderr, "Found orphan Ganeti instances with IDs: "
                print "    " + "\n    ".join(
                    [str(x) for x in orphans])
            elif verbosity == 2:
                print >> sys.stderr, "Found no orphan Ganeti instances."

        if options['detect_unsynced']:
            unsynced = reconciliation.unsynced_operstate(D, G)
            if len(unsynced) > 0:
                print >> sys.stderr, "The operstate of the following server" \
                                     " IDs is out-of-sync:"
                print "    " + "\n    ".join(
                    ["%d is %s in DB, %s in Ganeti" %
                     (x[0], x[1], ('UP' if x[2] else 'DOWN'))
                     for x in unsynced])
            elif verbosity == 2:
                print >> sys.stderr, "The operstate of all servers is in sync."

        #
        # Then fix them
        #
        if options['fix_stale'] and len(stale) > 0:
            print >> sys.stderr, \
                "Simulating successful Ganeti removal for %d " \
                "servers in the DB:" % len(stale)
            for vm in VirtualMachine.objects.filter(pk__in=stale):
                backend.process_op_status(vm=vm, jobid=-0,
                    opcode='OP_INSTANCE_REMOVE', status='success',
                    logmsg='Reconciliation: simulated Ganeti event')
            print >> sys.stderr, "    ...done"

        if options['fix_orphans'] and len(orphans) > 0:
            print >> sys.stderr, \
                "Issuing OP_INSTANCE_REMOVE for %d Ganeti instances:" % \
                len(orphans)
            for id in orphans:
                rapi = GanetiRapiClient(*settings.GANETI_CLUSTER_INFO)
                rapi.DeleteInstance('%s%s' %
                                    (settings.BACKEND_PREFIX_ID, str(id)))
            print >> sys.stderr, "    ...done"

        if options['fix_unsynced'] and len(unsynced) > 0:
            print >> sys.stderr, "Setting the state of %d out-of-sync VMs:" % \
                len(unsynced)
            for id, db_state, ganeti_up in unsynced:
                vm = VirtualMachine.objects.get(pk=id)
                opcode = "OP_INSTANCE_REBOOT" if ganeti_up \
                         else "OP_INSTANCE_SHUTDOWN"
                backend.process_op_status(vm=vm, jobid=-0,
                    opcode=opcode, status='success',
                    logmsg='Reconciliation: simulated Ganeti event')
            print >> sys.stderr, "    ...done"