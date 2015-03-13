from copy import deepcopy
from Products.CMFCore.utils import getToolByName


def migrate_properties(context, mapping, mode='move', replace=False):
    """Migrate user properties."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    uf = getToolByName(context, 'acl_users')
    plugin = uf.get('mutable_properties')

    for old_userid, new_userid in mapping.items():

        if old_userid not in plugin._storage:
            continue

        # Do nothing if new user already has some properties and
        # replace is False.
        if new_userid in plugin._storage and not replace:
            continue

        data = plugin._storage.get(old_userid)

        if mode in ['copy', 'move']:
            plugin._storage[new_userid] = deepcopy(data)

        if mode in ['move', 'delete']:
            plugin.deleteUser(old_userid)

        if mode == 'move':
            moved.append((old_userid, new_userid))
        if mode == 'copy':
            copied.append((old_userid, new_userid))
        if mode == 'delete':
            deleted.append((old_userid, None))

    return(dict(moved=moved, copied=copied, deleted=deleted))
