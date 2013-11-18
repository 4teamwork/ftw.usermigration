from Products.CMFCore.utils import getToolByName
from Acquisition import aq_parent


def migrate_homefolders(context, mapping, mode='move', replace=False):
    """Migrate users home folders."""

    # Statistics
    moved = []
    copied = []
    deleted = []
    
    mtool = getToolByName(context, 'portal_membership')
    for old_userid, new_userid in mapping.items():
        
        old_home = mtool.getHomeFolder(old_userid)
        if not old_home:
            continue
        
        container = aq_parent(old_home)
        new_home = None

        # Delete exisiting home folder of new_userid
        if mode in ['move', 'copy']:
            if new_userid in container.objectIds():
                if replace:
                    container.manage_delObjects(ids=[old_userid])
                else:
                    continue

        # Rename home folder
        if mode=='move':
            container.manage_renameObject(old_userid, new_userid)
            new_home = container[new_userid]
            moved.append((old_userid, new_userid))

        # Copy home folder
        elif mode=='copy':
            new_ids = container.manage_pasteObjects(
                cb_copy_data=container.manage_copyObjects(ids=[old_userid]))
            container.manage_renameObject(new_ids[0]['new_id'], new_userid)
            new_home = container[new_userid]
            copied.append((old_userid, new_userid))

        # Delete home folder
        elif mode=='delete':
            container.manage_delObjects(ids=[old_userid])
            deleted.append((old_userid, None))

        # Assing local roles
        if new_home is not None:
            roles = old_home.get_local_roles_for_userid(old_userid)
            new_home.manage_delLocalRoles(userids=[old_userid])
            new_home.manage_setLocalRoles(new_userid, roles)
            new_home.reindexObjectSecurity()

    return(dict(moved=moved, copied=copied, deleted=deleted))
