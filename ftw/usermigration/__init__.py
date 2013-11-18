from zope.i18nmessageid import MessageFactory
from Products.CMFCore.permissions import setDefaultRoles

_ = MessageFactory('ftw.usermigration')

setDefaultRoles('ftw.usermigration: Migrate users',
                ('Manager', 'Site Administrator', ))

