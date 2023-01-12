from ftw.usermigration.dashboard import migrate_dashboards
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from plone.app.portlets.storage import UserPortletAssignmentMapping
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from Products.CMFCore.utils import getToolByName
from unittest import TestCase
from zope.component import queryUtility


class DummyPortletAssignment(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __of__(self, obj):
        return self


class TestLocalRoles(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        users = ['john', 'jack', 'peter']
        mtool = getToolByName(portal, 'portal_membership', None)
        for user in users:
            mtool.addMember(user, 'password', ['Member'], [])

        # Let's start clean. Remove all assigned default portlets
        for name in ['plone.dashboard1', 'plone.dashboard2',
                     'plone.dashboard3', 'plone.dashboard4']:
            column = queryUtility(IPortletManager, name=name)
            category = column.get(USER_CATEGORY)
            for user in users:
                if user in category:
                    del category[user]

        # Assign portlets in column 'plone.dashboard2'
        column = queryUtility(IPortletManager, name='plone.dashboard2')
        category = column.get(USER_CATEGORY)
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard2', category=USER_CATEGORY, name='john')
        category['john'] = upm
        category['john']['portlet-1'] = DummyPortletAssignment('john-col2')

        # Assign portlets in column 'plone.dashboard3'
        column = queryUtility(IPortletManager, name='plone.dashboard3')
        category = column.get(USER_CATEGORY)
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard3', category=USER_CATEGORY, name='john')
        category['john'] = upm
        category['john']['portlet-1'] = DummyPortletAssignment('john-col3')
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard3', category=USER_CATEGORY, name='peter')
        category['peter'] = upm
        category['peter']['portlet-1'] = DummyPortletAssignment('peter-col3')

    def test_move_dashboard_no_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_dashboards(portal, mapping, replace=False)
        column2 = queryUtility(IPortletManager, name='plone.dashboard2')
        category2 = column2.get(USER_CATEGORY, None)
        column3 = queryUtility(IPortletManager, name='plone.dashboard3')
        category3 = column3.get(USER_CATEGORY, None)

        self.assertIn('peter', category2)
        self.assertNotIn('john', category2)
        self.assertEqual('john-col2', category2['peter']['portlet-1'].name)

        self.assertIn('john', category3)
        self.assertEqual('john-col3', category3['john']['portlet-1'].name)
        self.assertIn('peter', category3)
        self.assertEqual('peter-col3', category3['peter']['portlet-1'].name)

        self.assertIn(('plone.dashboard2', 'john', 'peter'), results['moved'])
        self.assertNotIn(('plone.dashboard3', 'john', 'peter'), results['moved'])
        self.assertEqual([], results['copied'])
        self.assertEqual([], results['deleted'])

    def test_move_dashboard_with_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_dashboards(portal, mapping, replace=True)
        column2 = queryUtility(IPortletManager, name='plone.dashboard2')
        category2 = column2.get(USER_CATEGORY, None)
        column3 = queryUtility(IPortletManager, name='plone.dashboard3')
        category3 = column3.get(USER_CATEGORY, None)

        self.assertIn('peter', category2)
        self.assertNotIn('john', category2)
        self.assertEqual('john-col2', category2['peter']['portlet-1'].name)

        self.assertIn('peter', category3)
        self.assertNotIn('john', category3)
        self.assertEqual('john-col3', category3['peter']['portlet-1'].name)

        self.assertIn(('plone.dashboard2', 'john', 'peter'), results['moved'])
        self.assertIn(('plone.dashboard3', 'john', 'peter'), results['moved'])
        self.assertEqual([], results['copied'])
        self.assertEqual([], results['deleted'])

    def test_copy_dashboard_no_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_dashboards(portal, mapping, mode="copy", replace=False)
        column2 = queryUtility(IPortletManager, name='plone.dashboard2')
        category2 = column2.get(USER_CATEGORY, None)
        column3 = queryUtility(IPortletManager, name='plone.dashboard3')
        category3 = column3.get(USER_CATEGORY, None)

        self.assertIn('peter', category2)
        self.assertIn('john', category2)
        self.assertEqual('john-col2', category2['peter']['portlet-1'].name)
        self.assertNotEqual(category2['john'], category2['peter'])

        self.assertIn('john', category3)
        self.assertEqual('john-col3', category3['john']['portlet-1'].name)
        self.assertIn('peter', category3)
        self.assertEqual('peter-col3', category3['peter']['portlet-1'].name)

        self.assertIn(('plone.dashboard2', 'john', 'peter'), results['copied'])
        self.assertNotIn(('plone.dashboard3', 'john', 'peter'), results['copied'])
        self.assertEqual([], results['moved'])
        self.assertEqual([], results['deleted'])

    def test_copy_dashboard_with_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_dashboards(portal, mapping, mode="copy", replace=True)
        column2 = queryUtility(IPortletManager, name='plone.dashboard2')
        category2 = column2.get(USER_CATEGORY, None)
        column3 = queryUtility(IPortletManager, name='plone.dashboard3')
        category3 = column3.get(USER_CATEGORY, None)

        self.assertIn('peter', category2)
        self.assertIn('john', category2)
        self.assertEqual('john-col2', category2['peter']['portlet-1'].name)
        self.assertNotEqual(category2['john'], category2['peter'])

        self.assertIn('peter', category3)
        self.assertIn('john', category3)
        self.assertEqual('john-col3', category3['peter']['portlet-1'].name)
        self.assertNotEqual(category3['john'], category3['peter'])

        self.assertIn(('plone.dashboard2', 'john', 'peter'), results['copied'])
        self.assertIn(('plone.dashboard3', 'john', 'peter'), results['copied'])
        self.assertEqual([], results['moved'])
        self.assertEqual([], results['deleted'])

    def test_delete_dashboard(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_dashboards(portal, mapping, mode="delete")
        column2 = queryUtility(IPortletManager, name='plone.dashboard2')
        category2 = column2.get(USER_CATEGORY, None)
        column3 = queryUtility(IPortletManager, name='plone.dashboard3')
        category3 = column3.get(USER_CATEGORY, None)

        self.assertNotIn('john', category2)
        self.assertNotIn('john', category3)

        self.assertIn(('plone.dashboard2', 'john', None), results['deleted'])
        self.assertIn(('plone.dashboard3', 'john', None), results['deleted'])
        self.assertEqual([], results['moved'])
        self.assertEqual([], results['copied'])
