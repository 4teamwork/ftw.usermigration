from unittest2 import TestCase
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from ftw.usermigration.dashboard import migrate_dashboards
from Products.CMFCore.utils import getToolByName
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from zope.component import queryUtility
from plone.app.portlets.storage import UserPortletAssignmentMapping


class DummyAssignment(object):
    
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class TestLocalRoles(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING
    
    def setUp(self):        
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('john', 'password', ['Member'], [])
        mtool.addMember('jack', 'password', ['Member'], [])
        mtool.addMember('peter', 'password', ['Member'], [])
        
        # Assign portlets in column 'plone.dashboard2'
        column = queryUtility(IPortletManager, name='plone.dashboard2')
        category = column.get(USER_CATEGORY)
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard2', category=USER_CATEGORY, name='john')
        if u'john' in category:
            del category['john']
        category['john'] = upm
        category['john']['portlet-1'] = DummyAssignment('john-col2')
        if 'peter' in category:
            del category['peter']

        # Assign portlets in column 'plone.dashboard3'
        column = queryUtility(IPortletManager, name='plone.dashboard3')
        category = column.get(USER_CATEGORY)
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard3', category=USER_CATEGORY, name='john')
        if u'john' in category:
            del category['john']
        category['john'] = upm
        category['john']['portlet-1'] = DummyAssignment('john-col3')
        if 'peter' in category:
            del category['peter']
        upm = UserPortletAssignmentMapping(
            manager='plone.dashboard3', category=USER_CATEGORY, name='peter')
        category['peter'] = upm
        category['peter']['portlet-1'] = DummyAssignment('peter-col3')



    def test_move_dashboard_no_replace(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}

        column = queryUtility(IPortletManager, name='plone.dashboard2')
        category = column.get(USER_CATEGORY, None)
        self.assertIn('john', category)
        self.assertNotIn('peter', category)

        results = migrate_dashboards(portal, mapping, replace=False)
        self.assertIn('peter', category)
        self.assertNotIn('john', category)
        self.assertEquals('john-col2', category['peter']['portlet-1'].name)

        self.assertIn(('plone.dashboard2', 'john', 'peter'), results['moved'])
        self.assertNotIn(('plone.dashboard3', 'john', 'peter'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])
        
