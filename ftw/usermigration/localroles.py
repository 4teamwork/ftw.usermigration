def migrate_localroles(context, mapping, mode='move'):
    """Recursively migrate local roles on the given context."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    # Paths needing reindexing of security
    reindex_paths = set()

    def is_reindexing_ancestor(path):
        """Determine if an ancestor of the given path is already in
           reindex_paths."""
        path_parts = path.split('/')
        for i, part in enumerate(path_parts):
            subpath = '/'.join(path_parts[:i + 1])
            if subpath in reindex_paths:
                return True
        return False

    def migrate_and_recurse(context):
        local_roles = context.get_local_roles()
        path = '/'.join(context.getPhysicalPath())
        for role in local_roles:
            for old_userid, new_userid in mapping.items():
                if role[0] == old_userid:
                    if mode in ['move', 'copy']:
                        context.manage_setLocalRoles(new_userid, list(role[1]))
                        if not is_reindexing_ancestor(path):
                            reindex_paths.add(path)
                    if mode in ['move', 'delete']:
                        context.manage_delLocalRoles(userids=[old_userid])
                        if not is_reindexing_ancestor(path):
                            reindex_paths.add(path)
                    if mode == 'move':
                        moved.append((path, old_userid, new_userid))
                    elif mode == 'copy':
                        copied.append((path, old_userid, new_userid))
                    elif mode == 'delete':
                        deleted.append((path, old_userid, None))

        for obj in context.objectValues():
            migrate_and_recurse(obj)

    migrate_and_recurse(context)

    for path in reindex_paths:
        obj = context.unrestrictedTraverse(path)
        obj.reindexObjectSecurity()

    return(dict(moved=moved, copied=copied, deleted=deleted))
