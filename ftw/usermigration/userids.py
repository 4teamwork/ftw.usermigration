from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.plugins.ZODBUserManager import IZODBUserManager


def migrate_userids(context, mapping, mode='move', replace=False):
    """Migrate Plone userids."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    uf = getToolByName(context, 'acl_users')

    for old_userid, new_userid in mapping.items():
        for plugin_id, plugin in uf.plugins.listPlugins(IUserEnumerationPlugin):
            # Only ZODB User Manager is supported
            if not IZODBUserManager.providedBy(plugin):
                continue

            for user in plugin.enumerateUsers(id=old_userid, exact_match=True):
                pw = plugin._user_passwords[old_userid]
                login = plugin._userid_to_login[old_userid]

                # Do nothing if a user with new_userid already exists and
                # replace is False.
                if new_userid in plugin._user_passwords and not replace:
                    continue

                if mode in ['move', 'delete']:
                    del plugin._user_passwords[old_userid]
                    del plugin._userid_to_login[old_userid]
                    del plugin._login_to_userid[login]

                if mode in ['copy', 'move']:
                    # We set the login-name to the new userid on user-copy.
                    # We do this because we don't want two users with the same
                    # loginname.
                    if mode == 'copy':
                        login = new_userid

                    plugin._user_passwords[new_userid] = pw
                    plugin._login_to_userid[login] = new_userid
                    plugin._userid_to_login[new_userid] = login

                if mode == 'move':
                    moved.append(('acl_users', old_userid, new_userid))
                if mode == 'copy':
                    copied.append(('acl_users', old_userid, new_userid))
                if mode == 'delete':
                    deleted.append(('acl_users', old_userid, None))

    return(dict(moved=moved, copied=copied, deleted=deleted))
