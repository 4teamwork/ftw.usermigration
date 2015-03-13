from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from zope.component import queryUtility


def migrate_dashboards(context, mapping, mode='move', replace=False):

    deleted = []
    moved = []
    copied = []

    for name in ('plone.dashboard1',
                 'plone.dashboard2',
                 'plone.dashboard3',
                 'plone.dashboard4'):
        column = queryUtility(IPortletManager, name=name)
        if column is not None:
            category = column.get(USER_CATEGORY, None)
            if category is not None:
                for old_userid, new_userid in mapping.items():
                    if old_userid in category:

                        # Delete new user's existing assignment
                        if mode in ['move', 'copy'] and new_userid in category:
                            if replace:
                                del category[new_userid]
                            else:
                                continue

                        # Move existing assignemnt to new user
                        if mode == 'move':
                            category[new_userid] = category[old_userid]
                            category[new_userid].__name__ = new_userid
                            del category[old_userid]
                            moved.append((name, old_userid, new_userid))

                        # Copy assignment to new user
                        elif mode == 'copy':
                            category[new_userid] = category[old_userid]._getCopy(category)
                            category[new_userid].__name__ = new_userid
                            copied.append((name, old_userid, new_userid))

                        # Remove assignment from old user
                        elif mode == 'delete':
                            del category[old_userid]
                            deleted.append((name, old_userid, None))

    return(dict(moved=moved, copied=copied, deleted=deleted))
