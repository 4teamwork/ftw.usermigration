from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from zope.configuration import xmlconfig


class UserMigrationLayer(PloneSandboxLayer):

    defaultBases = (BUILDER_LAYER, COMPONENT_REGISTRY_ISOLATION)

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
    bases=(USERMIGRATION_FIXTURE,
           COMPONENT_REGISTRY_ISOLATION),
    name="ftw.usermigration:integration")

USERMIGRATION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(USERMIGRATION_FIXTURE,
           COMPONENT_REGISTRY_ISOLATION,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.usermigration:functional")
