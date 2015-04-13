from copy import deepcopy
from Products.CMFCore.utils import getToolByName


def migrate_properties(context, mapping, mode='move', replace=False):
    """Migrate user and group properties."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    uf = getToolByName(context, 'acl_users')
    plugin = uf.get('mutable_properties')

    for old_id, new_id in mapping.items():

        if old_id not in plugin._storage:
            continue

        # Do nothing if new user or group already has some properties and
        # replace is False.
        if new_id in plugin._storage and not replace:
            continue

        data = plugin._storage.get(old_id)

        if mode in ['copy', 'move']:
            plugin._storage[new_id] = deepcopy(data)

        if mode in ['move', 'delete']:
            plugin.deleteUser(old_id)

        if mode == 'move':
            moved.append(('mutable_properties', old_id, new_id))
        if mode == 'copy':
            copied.append(('mutable_properties', old_id, new_id))
        if mode == 'delete':
            deleted.append(('mutable_properties', old_id, None))

    return(dict(moved=moved, copied=copied, deleted=deleted))
