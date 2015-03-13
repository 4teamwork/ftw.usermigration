from Products.CMFCore.permissions import setDefaultRoles
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('ftw.usermigration')

setDefaultRoles('ftw.usermigration: Migrate users',
                ('Manager', 'Site Administrator', ))
