def migrate_localroles(context, mapping, mode='move', replace=False):
    """Recursively migrate local roles on the given context."""

    # Statistics
    moved = []
    copied = []
    deleted = []

    # Paths needing reindexing of security
    reindex_paths = set()

    if replace:
        raise NotImplementedError(
            "Local roles migration only supports 'replace=False' as of yet")

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
            for old_id, new_id in mapping.items():
                if role[0] == old_id:
                    if mode in ['move', 'copy']:
                        context.manage_setLocalRoles(new_id, list(role[1]))
                        if not is_reindexing_ancestor(path):
                            reindex_paths.add(path)
                    if mode in ['move', 'delete']:
                        # Even though the kw argument is named `userids`,
                        # these are in fact principal IDs (groups or users)
                        context.manage_delLocalRoles(userids=[old_id])
                        if not is_reindexing_ancestor(path):
                            reindex_paths.add(path)
                    if mode == 'move':
                        moved.append((path, old_id, new_id))
                    elif mode == 'copy':
                        copied.append((path, old_id, new_id))
                    elif mode == 'delete':
                        deleted.append((path, old_id, None))

        for obj in context.objectValues():
            migrate_and_recurse(obj)

    migrate_and_recurse(context)

    for path in reindex_paths:
        obj = context.unrestrictedTraverse(path)
        obj.reindexObjectSecurity()

    return(dict(moved=moved, copied=copied, deleted=deleted))
