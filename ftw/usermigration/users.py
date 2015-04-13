from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_hasattr


def migrate_users(context, mapping, mode='move', replace=False):
    """Migrate Plone users."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    uf = getToolByName(context, 'acl_users')

    for old_userid, new_userid in mapping.items():
        users = uf.searchUsers(id=old_userid)
        if len(users) > 0:
            for user in users:
                plugin = uf.get(user['pluginid'])
                # Only ZODB User Manager is supported
                if (safe_hasattr(plugin, '_user_passwords') and
                        safe_hasattr(plugin, '_login_to_userid') and
                        safe_hasattr(plugin, '_userid_to_login')):
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
                        # If userid and login are the same or if in copy mode,
                        # set login to new userid.
                        if login == old_userid or mode == 'copy':
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
