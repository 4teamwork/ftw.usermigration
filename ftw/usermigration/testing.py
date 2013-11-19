from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from zope.configuration import xmlconfig


class UserMigrationLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import z3c.autoinclude
        xmlconfig.file('meta.zcml', z3c.autoinclude,
                       context=configurationContext)
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <includePlugins package="plone" />'
            '</configure>',
            context=configurationContext)


USERMIGRATION_FIXTURE = UserMigrationLayer()
USERMIGRATION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(USERMIGRATION_FIXTURE, ), name="ftw.usermigration:integration")
USERMIGRATION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(USERMIGRATION_FIXTURE, ), name="ftw.usermigration:functional")
