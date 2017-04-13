from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.plugins.ZODBUserManager import IZODBUserManager


def migrate_loginnames(context, mapping, mode='move', replace=False):
    """Migrate Plone loginnames.
    """

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
                current_userid = old_userid
                old_loginname = plugin._userid_to_login[old_userid]
                new_loginname = new_userid

                # Do nothing if the new login-id already exists. Replace does not work
                # here because the login-name is couppled to the userid which will be
                # migrated in another step.
                if new_loginname in plugin._login_to_userid:
                    continue

                if mode not in ['move']:
                    # This migration step only provides move-mode. All the other
                    # modes are handled automatically through the userids-migration.
                    continue

                del plugin._login_to_userid[old_loginname]

                plugin._userid_to_login[current_userid] = new_loginname
                plugin._login_to_userid[new_loginname] = current_userid

                moved.append((current_userid, old_loginname, new_loginname))

    return(dict(moved=moved, copied=copied, deleted=deleted))
