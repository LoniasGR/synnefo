#!/usr/bin/env python

# Copyright 2011 GRNET S.A. All rights reserved.
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

from django.core.management import setup_environ
try:
    from synnefo import settings
except ImportError:
    raise Exception("Cannot import settings, make sure PYTHONPATH contains "
                    "the parent directory of the Synnefo Django project.")
setup_environ(settings)

import inspect
import sys

from collections import defaultdict
from itertools import product
from optparse import OptionParser
from os.path import basename

from synnefo.db import models
from synnefo.invitations.invitations import add_invitation, send_invitation
from synnefo.logic import backend, users
from synnefo.util.dictconfig import dictConfig


def get_user(uid):
    try:
        uid = int(uid)
        return models.SynnefoUser.objects.get(id=uid)
    except ValueError:
        return None
    except models.SynnefoUser.DoesNotExist:
        return None

def print_dict(d, exclude=()):
    if not d:
        return
    margin = max(len(key) for key in d) + 1

    for key, val in sorted(d.items()):
        if key in exclude or key.startswith('_'):
            continue
        print '%s: %s' % (key.rjust(margin), val)

def print_item(item):
    name = getattr(item, 'name', '')
    print '%d %s' % (item.id, name)
    print_dict(item.__dict__, exclude=('id', 'name'))

def print_items(items, detail=False, keys=None):
    keys = keys or ('id', 'name')
    for item in items:
        for key in keys:
            print getattr(item, key),
        print
        
        if detail:
            print_dict(item.__dict__, exclude=keys)
            print


class Command(object):
    group = '<group>'
    name = '<command>'
    syntax = ''
    description = ''
    hidden = False
    
    def __init__(self, exe, argv):
        parser = OptionParser()
        syntax = '%s [options]' % self.syntax if self.syntax else '[options]'
        parser.usage = '%s %s %s' % (exe, self.name, syntax)
        parser.description = self.description
        self.add_options(parser)
        options, self.args = parser.parse_args(argv)
        
        # Add options to self
        for opt in parser.option_list:
            key = opt.dest
            if key:
                val = getattr(options, key)
                setattr(self, key, val)
        
        self.parser = parser
    
    def add_options(self, parser):
        pass
    
    def execute(self):
        try:
            self.main(*self.args)
        except TypeError:
            self.parser.print_help()


# Server commands

class ListServers(Command):
    group = 'server'
    name = 'list'
    syntax = '[server id]'
    description = 'list servers'
    
    def add_options(self, parser):
        parser.add_option('-a', action='store_true', dest='show_deleted',
                        default=False, help='also list deleted servers')
        parser.add_option('-l', action='store_true', dest='detail',
                        default=False, help='show detailed output')
        parser.add_option('-u', dest='uid', metavar='UID',
                            help='show servers of user with id UID')
    
    def main(self, server_id=None):
        if server_id:
            servers = [models.VirtualMachine.objects.get(id=server_id)]
        else:
            servers = models.VirtualMachine.objects.order_by('id')
            if not self.show_deleted:
                servers = servers.exclude(deleted=True)
            if self.uid:
                user = get_user(self.uid)
                if user:
                    servers = servers.filter(owner=user)
                else:
                    print 'Unknown user id'
                    return
        
        print_items(servers, self.detail)


# User commands

class CreateUser(Command):
    group = 'user'
    name = 'create'
    syntax = '<username> <email>'
    description = 'create a user'
    
    def add_options(self, parser):
        parser.add_option('--realname', dest='realname', metavar='NAME',
                            help='set real name of user')
        parser.add_option('--type', dest='type', metavar='TYPE',
                            help='set user type')
    
    def main(self, username, email):
        username = username.decode('utf8')
        realname = self.realname or username
        type = self.type or 'USER'
        types = [x[0] for x in models.SynnefoUser.ACCOUNT_TYPE]
        if type not in types:
            valid = ', '.join(types)
            print 'Invalid type. Must be one of:', valid
            return
        
        user = users._register_user(realname, username, email, type)
        print_item(user)


class InviteUser(Command):
    group = 'user'
    name = 'invite'
    syntax = '<inviter id> <invitee name> <invitee email>'
    description = 'invite a user'
    
    def main(self, inviter_id, name, email):
        name = name.decode('utf8')
        inviter = get_user(inviter_id)
        inv = add_invitation(inviter, name, email)
        send_invitation(inv)


class ListUsers(Command):
    group = 'user'
    name = 'list'
    syntax = '[user id]'
    description = 'list users'
    
    def add_options(self, parser):
        parser.add_option('-a', action='store_true', dest='show_deleted',
                        default=False, help='also list deleted users')
        parser.add_option('-l', action='store_true', dest='detail',
                        default=False, help='show detailed output')
    
    def main(self, user_id=None):
        if user_id:
            users = [models.SynnefoUser.objects.get(id=user_id)]
        else:
            users = models.SynnefoUser.objects.order_by('id')
            if not self.show_deleted:
                users = users.exclude(state='DELETED')
        print_items(users, self.detail, keys=('id', 'name', 'uniq'))


class ModifyUser(Command):
    group = 'user'
    name = 'modify'
    syntax = '<user id>'
    description = 'modify a user'
    
    def add_options(self, parser):
        types = ', '.join(x[0] for x in models.SynnefoUser.ACCOUNT_TYPE)
        states = ', '.join(x[0] for x in models.SynnefoUser.ACCOUNT_STATE)
        
        parser.add_option('--credit', dest='credit', metavar='VALUE',
                            help='set user credits')
        parser.add_option('--invitations', dest='invitations',
                            metavar='VALUE', help='set max invitations')
        parser.add_option('--realname', dest='realname', metavar='NAME',
                            help='set real name of user')
        parser.add_option('--type', dest='type', metavar='TYPE',
                            help='set user type (%s)' % types)
        parser.add_option('--state', dest='state', metavar='STATE',
                            help='set user state (%s)' % states)
        parser.add_option('--uniq', dest='uniq', metavar='ID',
                            help='set external unique ID')
        parser.add_option('--username', dest='username', metavar='NAME',
                            help='set username')
    
    def main(self, user_id):
        user = get_user(user_id)
        
        if self.credit:
            user.credit = self.credit
        if self.invitations:
            user.max_invitations = self.invitations
        if self.realname:
            user.realname = self.realname
        if self.type:
            allowed = [x[0] for x in models.SynnefoUser.ACCOUNT_TYPE]
            if self.type not in allowed:
                valid = ', '.join(allowed)
                print 'Invalid type. Must be one of:', valid
                return
            user.type = self.type
        if self.state:
            allowed = [x[0] for x in models.SynnefoUser.ACCOUNT_STATE]
            if self.state not in allowed:
                valid = ', '.join(allowed)
                print 'Invalid state. Must be one of:', valid
                return
            user.state = self.state
        if self.uniq:
            user.uniq = self.uniq
        if self.username:
            user.name = self.username
        
        user.save()
        print_item(user)


# Image commands

class ListImages(Command):
    group = 'image'
    name = 'list'
    syntax = '[image id]'
    description = 'list images'
    
    def add_options(self, parser):
        parser.add_option('-a', action='store_true', dest='show_deleted',
                        default=False, help='also list deleted images')
        parser.add_option('-l', action='store_true', dest='detail',
                        default=False, help='show detailed output')
    
    def main(self, image_id=None):
        if image_id:
            images = [models.Image.objects.get(id=image_id)]
        else:
            images = models.Image.objects.order_by('id')
            if not self.show_deleted:
                images = images.exclude(state='DELETED')
        print_items(images, self.detail)


class RegisterImage(Command):
    group = 'image'
    name = 'register'
    syntax = '<name> <backend id> <format>'
    description = 'register an image'
    
    def add_options(self, parser):
        parser.add_option('--meta', dest='meta', action='append',
                            metavar='KEY=VAL',
                            help='add metadata (can be used multiple times)')
        parser.add_option('--public', action='store_true', dest='public',
                            default=False, help='make image public')
        parser.add_option('-u', dest='uid', metavar='UID',
                            help='assign image to user with id UID')
    
    def main(self, name, backend_id, format):
        formats = [x[0] for x in models.Image.FORMATS]
        if format not in formats:
            valid = ', '.join(formats)
            print 'Invalid format. Must be one of:', valid
            return
        
        user = None
        if self.uid:
            user = get_user(self.uid)
            if not user:
                print 'Unknown user id'
                return
        
        image = models.Image.objects.create(
            name=name,
            state='ACTIVE',
            owner=user,
            backend_id=backend_id,
            format=format,
            public=self.public)
        
        if self.meta:
            for m in self.meta:
                key, sep, val = m.partition('=')
                if key and val:
                    image.metadata.create(meta_key=key, meta_value=val)
                else:
                    print 'WARNING: Ignoring meta', m
        
        print_item(image)


class ModifyImage(Command):
    group = 'image'
    name = 'modify'
    syntax = '<image id>'
    description = 'modify an image'
    
    def add_options(self, parser):
        states = ', '.join(x[0] for x in models.Image.IMAGE_STATES)
        formats = ', '.join(x[0] for x in models.Image.FORMATS)

        parser.add_option('-b', dest='backend_id', metavar='BACKEND_ID',
                            help='set image backend id')
        parser.add_option('-f', dest='format', metavar='FORMAT',
                            help='set image format (%s)' % formats)
        parser.add_option('-n', dest='name', metavar='NAME',
                            help='set image name')
        parser.add_option('--public', action='store_true', dest='public',
                            default=False, help='make image public')
        parser.add_option('--nopublic', action='store_true', dest='private',
                            default=False, help='make image private')
        parser.add_option('-s', dest='state', metavar='STATE', default=False,
                            help='set image state (%s)' % states)
        parser.add_option('-u', dest='uid', metavar='UID',
                            help='assign image to user with id UID')
    
    def main(self, image_id):
        try:
            image = models.Image.objects.get(id=image_id)
        except:
            print 'Image not found'
            return
        
        if self.backend_id:
            image.backend_id = self.backend_id
        if self.format:
            allowed = [x[0] for x in models.Image.FORMATS]
            if self.format not in allowed:
                valid = ', '.join(allowed)
                print 'Invalid format. Must be one of:', valid
                return
            image.format = self.format
        if self.name:
            image.name = self.name
        if self.public:
            image.public = True
        if self.private:
            image.public = False
        if self.state:
            allowed = [x[0] for x in models.Image.IMAGE_STATES]
            if self.state not in allowed:
                valid = ', '.join(allowed)
                print 'Invalid state. Must be one of:', valid
                return
            image.state = self.state
        if self.uid:
            image.owner = get_user(self.uid)
        
        image.save()
        print_item(image)


class ModifyImageMeta(Command):
    group = 'image'
    name = 'meta'
    syntax = '<image id> [key[=val]]'
    description = 'get and manipulate image metadata'
    
    def main(self, image_id, arg=''):
        try:
            image = models.Image.objects.get(id=image_id)
        except:
            print 'Image not found'
            return
        
        key, sep, val = arg.partition('=')
        if not sep:
            val = None
        
        if not key:
            metadata = {}
            for meta in image.metadata.order_by('meta_key'):
                metadata[meta.meta_key] = meta.meta_value
            print_dict(metadata)
            return
        
        try:
            meta = image.metadata.get(meta_key=key)
        except models.ImageMetadata.DoesNotExist:
            meta = None
        
        if val is None:
            if meta:
                print_dict({key: meta.meta_value})
            return
        
        if val:
            if not meta:
                meta = image.metadata.create(meta_key=key)
            meta.meta_value = val
            meta.save()
        else:
            # Delete if val is empty
            if meta:
                meta.delete()


# Flavor commands

class CreateFlavor(Command):
    group = 'flavor'
    name = 'create'
    syntax = '<cpu>[,<cpu>,...] <ram>[,<ram>,...] <disk>[,<disk>,...]'
    description = 'create one or more flavors'
    
    def add_options(self, parser):
        disk_templates = ', '.join(t for t in settings.GANETI_DISK_TEMPLATES)
        parser.add_option('--disk-template',
            dest='disk_template',
            metavar='TEMPLATE',
            default=settings.DEFAULT_GANETI_DISK_TEMPLATE,
            help='available disk templates: %s' % disk_templates)
    
    def main(self, cpu, ram, disk):
        cpus = cpu.split(',')
        rams = ram.split(',')
        disks = disk.split(',')
        
        flavors = []
        for cpu, ram, disk in product(cpus, rams, disks):
            try:
                flavors.append((int(cpu), int(ram), int(disk)))
            except ValueError:
                print 'Invalid values'
                return
        
        created = []
        
        for cpu, ram, disk in flavors:
            flavor = models.Flavor.objects.create(
                cpu=cpu,
                ram=ram,
                disk=disk,
                disk_template=self.disk_template)
            created.append(flavor)
        
        print_items(created, detail=True)


class DeleteFlavor(Command):
    group = 'flavor'
    name = 'delete'
    syntax = '<flavor id> [<flavor id>] [...]'
    description = 'delete one or more flavors'
    
    def main(self, *args):
        if not args:
            raise TypeError
        for flavor_id in args:
            flavor = models.Flavor.objects.get(id=int(flavor_id))
            flavor.deleted = True
            flavor.save()


class ListFlavors(Command):
    group = 'flavor'
    name = 'list'
    syntax = '[flavor id]'
    description = 'list images'
    
    def add_options(self, parser):
        parser.add_option('-a', action='store_true', dest='show_deleted',
                default=False, help='also list deleted flavors')
        parser.add_option('-l', action='store_true', dest='detail',
                        default=False, help='show detailed output')
    
    def main(self, flavor_id=None):
        if flavor_id:
            flavors = [models.Flavor.objects.get(id=flavor_id)]
        else:
            flavors = models.Flavor.objects.order_by('id')
            if not self.show_deleted:
                flavors = flavors.exclude(deleted=True)
        print_items(flavors, self.detail)


class ShowStats(Command):
    group = 'stats'
    name = None
    description = 'show statistics'

    def main(self):
        stats = {}
        stats['Users'] = models.SynnefoUser.objects.count()
        stats['Images'] = models.Image.objects.exclude(state='DELETED').count()
        stats['Flavors'] = models.Flavor.objects.count()
        stats['VMs'] = models.VirtualMachine.objects.filter(deleted=False).count()
        stats['Networks'] = models.Network.objects.exclude(state='DELETED').count()
        stats['Invitations'] = models.Invitations.objects.count()
        
        stats['Ganeti Instances'] = len(backend.get_ganeti_instances())
        stats['Ganeti Nodes'] = len(backend.get_ganeti_nodes())
        stats['Ganeti Jobs'] = len(backend.get_ganeti_jobs())
        
        print_dict(stats)


class ListInvitations(Command):
    group = 'invitation'
    name = 'list'
    syntax = '[invitation id]'
    description = 'list invitations'
    
    def main(self, invitation_id=None):
        if invitation_id:
            invitations = [models.Invitations.objects.get(id=invitation_id)]
        else:
            invitations = models.Invitations.objects.order_by('id')
        print_items(invitations, detail=True, keys=('id',))


class ResendInviation(Command):
    group = 'invitation'
    name = 'resend'
    syntax = '<invitation id>'
    description = 'resend an invitation'

    def main(self, invitation_id):
        invitation = models.Invitations.objects.get(id=invitation_id)
        send_invitation(invitation)


def print_usage(exe, groups, group=None, shortcut=False):
    nop = Command(exe, [])
    nop.parser.print_help()
    if group:
        groups = {group: groups[group]}

    print
    print 'Commands:'
    
    for group, commands in sorted(groups.items()):
        for command, cls in sorted(commands.items()):
            if cls.hidden:
                continue
            name = '  %s %s' % (group, command or '')
            print '%s %s' % (name.ljust(22), cls.description)
        print


def main():
    groups = defaultdict(dict)
    module = sys.modules[__name__]
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if not issubclass(cls, Command) or cls == Command:
            continue
        groups[cls.group][cls.name] = cls
    
    argv = list(sys.argv)
    exe = basename(argv.pop(0))
    prefix, sep, suffix = exe.partition('-')
    if sep and prefix == 'snf' and suffix in groups:
        # Allow shortcut aliases like snf-image, snf-server, etc
        group = suffix
    else:
        group = argv.pop(0) if argv else None
        if group in groups:
            exe = '%s %s' % (exe, group)
        else:
            exe = '%s <group>' % exe
            group = None
    
    command = argv.pop(0) if argv else None
    
    if group not in groups or command not in groups[group]:
        print_usage(exe, groups, group)
        sys.exit(1)
    
    cls = groups[group][command]
    cmd = cls(exe, argv)
    cmd.execute()


if __name__ == '__main__':
    dictConfig(settings.SNFADMIN_LOGGING)
    main()