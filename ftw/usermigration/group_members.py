from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.plugins.ZODBGroupManager import IZODBGroupManager


def migrate_group_members(context, mapping, mode='move', replace=False):
    """Migrate Plone users within a group."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    uf = getToolByName(context, 'acl_users')

    for old_userid, new_userid in mapping.items():
        for plugin_id, plugin in uf.plugins.listPlugins(IGroupEnumerationPlugin):
            if not (IZODBGroupManager.providedBy(plugin) and
                    IGroupIntrospection.providedBy(plugin)):
                continue

            for group in plugin.enumerateGroups():
                group_id = group.get('id')
                group_members = plugin.getGroupMembers(group_id)
                # Do nothing if a user with new_userid already exists and
                # replace is False.
                if new_userid in group_members and not replace:
                    continue

                # Do nothing if an old user does not exist in a group.
                if old_userid not in group_members:
                    continue

                if mode in ['move', 'delete']:
                    plugin.removePrincipalFromGroup(old_userid, group_id)

                if mode in ['copy', 'move']:
                    plugin.addPrincipalToGroup(new_userid, group_id)

                if mode == 'move':
                    moved.append((group_id, old_userid, new_userid))
                if mode == 'copy':
                    copied.append((group_id, old_userid, new_userid))
                if mode == 'delete':
                    deleted.append((group_id, old_userid, None))

    return(dict(moved=moved, copied=copied, deleted=deleted))
