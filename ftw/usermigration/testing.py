from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from pkg_resources import get_distribution
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from unittest import TestCase
from zope.configuration import xmlconfig


IS_PLONE_5 = get_distribution('Plone').version >= '5'


class UserMigrationTestCase(TestCase):

    def assertItemsEqual(self, expected_seq, actual_seq, msg=None):
        return self.assertEqual(set(expected_seq), set(actual_seq), msg=msg)


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

        if not IS_PLONE_5:
            # The tests will fail with a
            # `ValueError: Index of type DateRecurringIndex not found` unless
            # the product 'Products.DateRecurringIndex' is installed.
            z2.installProduct(app, 'Products.DateRecurringIndex')

    def setUpPloneSite(self, portal):
        super(UserMigrationLayer, self).setUpPloneSite(portal)
        applyProfile(portal, 'plone.app.contenttypes:default')


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
