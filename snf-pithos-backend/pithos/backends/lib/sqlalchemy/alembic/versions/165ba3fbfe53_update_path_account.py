"""update account in paths

Revision ID: 165ba3fbfe53
Revises: 3dd56e750a3
Create Date: 2012-12-04 19:08:23.933634

"""

# revision identifiers, used by Alembic.
revision = '165ba3fbfe53'
down_revision = '3dd56e750a3'

from alembic import op
from sqlalchemy.sql import table, column, literal, and_

from synnefo.lib.astakos import get_user_uuid, get_displayname as get_user_displayname
from pithos.api.settings import (
    SERVICE_TOKEN, USER_CATALOG_URL, AUTHENTICATION_USERS)

USER_CATALOG_URL = USER_CATALOG_URL.replace('user_catalogs', 'service/api/user_catalogs')

import sqlalchemy as sa

catalog = {}
def get_uuid(account):
    global catalog
    uuid = catalog.get(account, -1)
    if uuid != -1:
        return uuid
    try:
        catalog[account] = get_user_uuid(
            SERVICE_TOKEN, account, USER_CATALOG_URL, AUTHENTICATION_USERS)
        print account, catalog[account]
    except:
        raise
    else:
        return catalog[account]

inverse_catalog = {}
def get_displayname(account):
    global inverse_catalog
    displayname = inverse_catalog.get(account, -1)
    if displayname != -1:
        return displayname
    try:
        inverse_catalog[account] = get_user_displayname(
            SERVICE_TOKEN, account, USER_CATALOG_URL, AUTHENTICATION_USERS)
        print account, inverse_catalog[account]
    except:
        raise
    else:
        return inverse_catalog[account]

n = table(
    'nodes',
    column('node', sa.Integer),
    column('path', sa.String(2048))
)

v = table(
    'versions',
    column('node', sa.Integer),
    column('muser', sa.String(2048))
)

p = table(
    'public',
    column('public_id', sa.Integer),
    column('path', sa.String(2048))
)

x = table(
    'xfeatures',
    column('feature_id', sa.Integer),
    column('path', sa.String(2048))
)

xvals =  table(
    'xfeaturevals',
    column('feature_id', sa.Integer),
    column('key', sa.Integer),
    column('value', sa.String(256))
)

g =  table(
    'groups',
    column('owner', sa.String(256)),
    column('name', sa.String(256)),
    column('member', sa.String(256))
)

def upgrade():
    connection = op.get_bind()

    s = sa.select([n.c.node, n.c.path])
    nodes = connection.execute(s).fetchall()
    for node, path in nodes:
        account, sep, rest = path.partition('/')
        uuid = get_uuid(account)
        if not uuid:
            continue
        path = sep.join([uuid, rest])
        u = n.update().where(n.c.node == node).values({'path':path})
        connection.execute(u)

    s = sa.select([v.c.node, v.c.muser])
    versions = connection.execute(s).fetchall()
    for node, muser in versions:
        uuid = get_uuid(muser)
        if not uuid:
            continue
        u = v.update().where(v.c.node == node).values({'muser':uuid})
        connection.execute(u)

    s = sa.select([p.c.public_id, p.c.path])
    public = connection.execute(s).fetchall()
    for id, path in public:
        account, sep, rest = path.partition('/')
        uuid = get_uuid(account)
        if not uuid:
            continue
        path = sep.join([uuid, rest])
        u = p.update().where(p.c.public_id == id).values({'path':path})
        connection.execute(u)

    s = sa.select([x.c.feature_id, x.c.path])
    xfeatures = connection.execute(s).fetchall()
    for id, path in xfeatures:
        account, sep, rest = path.partition('/')
        uuid = get_uuid(account)
        if not uuid:
            continue
        path = sep.join([uuid, rest])
        u = x.update().where(x.c.feature_id == id).values({'path':path})
        connection.execute(u)

    s = sa.select([xvals.c.feature_id, xvals.c.key, xvals.c.value])
    s = s.where(xvals.c.value != '*')
    xfeaturevals = connection.execute(s).fetchall()
    for feature_id, key, value in xfeaturevals:
        account, sep, group = value.partition(':')
        uuid = get_uuid(account)
        if not uuid:
            continue
        new_value = sep.join([uuid, group])
        u = xvals.update()
        u = u.where(and_(
                xvals.c.feature_id == feature_id,
                xvals.c.key == key,
                xvals.c.value == value))
        u = u.values({'value':new_value})
        connection.execute(u)

    s = sa.select([g.c.owner, g.c.name, g.c.member])
    groups = connection.execute(s).fetchall()
    for owner, name, member in groups:
        owner_uuid = get_uuid(owner)
        member_uuid = get_uuid(member)
        if owner_uuid or member_uuid:
            u = g.update()
            u = u.where(and_(
                g.c.owner == owner,
                g.c.name == name,
                g.c.member == member))
            values = {}
            if owner_uuid:
                values['owner'] = owner_uuid
            if member_uuid:
                values['member'] = member_uuid
            u = u.values(values)
            connection.execute(u)

def downgrade():
    connection = op.get_bind()

    s = sa.select([n.c.node, n.c.path])
    nodes = connection.execute(s).fetchall()
    for node, path in nodes:
        account, sep, rest = path.partition('/')
        displayname = get_displayname(account)
        if not displayname:
            continue
        path = sep.join([displayname, rest])
        u = n.update().where(n.c.node == node).values({'path':path})
        connection.execute(u)

    s = sa.select([v.c.node, v.c.muser])
    versions = connection.execute(s).fetchall()
    for node, muser in versions:
        displayname = get_displayname(muser)
        if not displayname:
            continue
        u = v.update().where(v.c.node == node).values({'muser':displayname})
        connection.execute(u)

    s = sa.select([p.c.public_id, p.c.path])
    public = connection.execute(s).fetchall()
    for id, path in public:
        account, sep, rest = path.partition('/')
        displayname = get_displayname(account)
        if not displayname:
            continue
        path = sep.join([displayname, rest])
        u = p.update().where(p.c.public_id == id).values({'path':path})
        connection.execute(u)

    s = sa.select([x.c.feature_id, x.c.path])
    xfeatures = connection.execute(s).fetchall()
    for id, path in xfeatures:
        account, sep, rest = path.partition('/')
        displayname = get_displayname(account)
        if not displayname:
            continue
        path = sep.join([displayname, rest])
        u = x.update().where(x.c.feature_id == id).values({'path':path})
        connection.execute(u)

    s = sa.select([xvals.c.feature_id, xvals.c.key, xvals.c.value])
    s = s.where(xvals.c.value != '*')
    xfeaturevals = connection.execute(s).fetchall()
    for feature_id, key, value in xfeaturevals:
        account, sep, group = value.partition(':')
        displayname = get_displayname(account)
        if not displayname:
            continue
        new_value = sep.join([displayname, group])
        u = xvals.update()
        u = u.where(and_(
                xvals.c.feature_id == feature_id,
                xvals.c.key == key,
                xvals.c.value ==value))
        u = u.values({'value':new_value})
        connection.execute(u)

    s = sa.select([g.c.owner, g.c.name, g.c.member])
    groups = connection.execute(s).fetchall()
    for owner, name, member in groups:
        owner_displayname = get_displayname(owner)
        member_displayname = get_displayname(member)
        if owner_displayname or member_displayname:
            u = g.update()
            u = u.where(and_(
                g.c.owner == owner,
                g.c.name == name,
                g.c.member == member))
            values = {}
            if owner_displayname:
                values['owner'] = owner_displayname
            if member_displayname:
                values['member'] = member_displayname
            u = u.values(values)
            connection.execute(u)
