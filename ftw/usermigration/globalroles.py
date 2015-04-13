from operator import itemgetter
from Products.CMFCore.utils import getToolByName


def migrate_globalroles(context, mapping, mode='move', replace=False):
    """Migrate global roles in portal_role_manager."""

    # Statistics
    moved = []

    if mode != 'move':
        raise NotImplementedError(
            "Global roles migration only supports 'move' mode as of yet")

    if replace:
        raise NotImplementedError(
            "Global roles migration only supports 'replace=False' as of yet")

    acl_users = getToolByName(context, 'acl_users')
    role_manager = acl_users.portal_role_manager

    for role_id in role_manager.listRoleIds():
        assigned_principals = role_manager.listAssignedPrincipals(role_id)
        assigned_principal_ids = map(itemgetter(0), assigned_principals)

        for old_principal_id in assigned_principal_ids:
            if old_principal_id in mapping:
                new_principal_id = mapping[old_principal_id]

                if new_principal_id in assigned_principal_ids:
                    # Only assign roles the new user doesn't already have
                    continue

                role_manager.assignRoleToPrincipal(role_id, new_principal_id)
                role_manager.removeRoleFromPrincipal(role_id, old_principal_id)
                moved.append((role_id, old_principal_id, new_principal_id))

    return(dict(moved=moved, copied=[], deleted=[]))
