from ftw.usermigration.properties import migrate_properties
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestProperties(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('john', 'password', ['Member'], [],
                        properties={'fullname': 'John Doe'})
        mtool.addMember('jack', 'password', ['Member'], [],
                        properties={'fullname': 'Jack Bauer'})
        mtool.addMember('peter', 'password', ['Member'], [])
        self.mtool = mtool

    def test_migrate_properties(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_properties(portal, mapping)

        self.assertIn(('mutable_properties', 'john', 'peter'),
                      results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        member = self.mtool.getMemberById('peter')
        self.assertEquals('John Doe', member.getProperty('fullname'))

        member = self.mtool.getMemberById('john')
        self.assertEquals('', member.getProperty('fullname'))

    def test_migrate_properties_with_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'jack'}
        results = migrate_properties(portal, mapping, replace=True)

        self.assertIn(('mutable_properties', 'john', 'jack'),
                      results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        member = self.mtool.getMemberById('jack')
        self.assertEquals('John Doe', member.getProperty('fullname'))

    def test_migrate_properties_without_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'jack'}
        results = migrate_properties(portal, mapping, replace=False)

        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        member = self.mtool.getMemberById('jack')
        self.assertEquals('Jack Bauer', member.getProperty('fullname'))

    def test_copy_properties(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_properties(portal, mapping, mode='copy')

        self.assertIn(('mutable_properties', 'john', 'peter'),
                      results['copied'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['deleted'])

        member = self.mtool.getMemberById('peter')
        self.assertEquals('John Doe', member.getProperty('fullname'))

        member = self.mtool.getMemberById('john')
        self.assertEquals('John Doe', member.getProperty('fullname'))

    def test_delete_properties(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_properties(portal, mapping, mode='delete')

        self.assertIn(('mutable_properties', 'john', None), results['deleted'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['moved'])

        member = self.mtool.getMemberById('peter')
        self.assertEquals('', member.getProperty('fullname'))

        member = self.mtool.getMemberById('john')
        self.assertEquals('', member.getProperty('fullname'))
