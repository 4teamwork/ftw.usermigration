from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from ftw.usermigration.testing import UserMigrationTestCase
from ftw.usermigration.userids import migrate_userids
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName


class TestUserIds(UserMigrationTestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('user1', 'password', ['Member'], [])
        mtool.addMember('jack', 'password', ['Member'], [])
        mtool.addMember('peter', 'password', ['Member'], [])

    def test_migrate_userids(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_userids(portal, mapping)

        self.assertIn(('acl_users', 'user1', 'john.doe'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'john.doe',
            uf.searchUsers(id='john.doe')[0]['userid']
        )
        self.assertEquals(
            'user1',
            uf.searchUsers(id='john.doe')[0]['login']
        )
        self.assertEquals(
            (),
            uf.searchUsers(id='user1')
        )

    def test_migrate_to_existing_user_without_replace(self):
        portal = self.layer['portal']
        mapping = {'user1': 'jack'}
        results = migrate_userids(portal, mapping)
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )

    def test_migrate_to_existing_user_with_replace(self):
        portal = self.layer['portal']
        mapping = {'user1': 'jack'}
        results = migrate_userids(portal, mapping, replace=True)
        self.assertIn(('acl_users', 'user1', 'jack'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            (),
            uf.searchUsers(id='user1')
        )
        self.assertEquals(
            'jack',
            uf.searchUsers(id='jack')[0]['userid']
        )

    def test_copy_users(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_userids(portal, mapping, mode='copy')

        self.assertIn(('acl_users', 'user1', 'john.doe'), results['copied'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'john.doe',
            uf.searchUsers(id='john.doe')[0]['userid']
        )
        self.assertEquals(
            'john.doe',
            uf.searchUsers(id='john.doe')[0]['login']
        )
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )

    def test_delete_users(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_userids(portal, mapping, mode='delete')

        self.assertIn(('acl_users', 'user1', None), results['deleted'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            (),
            uf.searchUsers(id='user1')
        )
        self.assertEquals(
            (),
            uf.searchUsers(id='john.deo')
        )

    def test_migrate_userid_which_is_a_substring_of_another_userid(self):
        portal = self.layer['portal']

        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('steve', 'password', ['Member'], [])
        mtool.addMember('steven', 'password', ['Member'], [])

        mapping = {'steve': 'john.doe'}
        results = migrate_userids(portal, mapping)

        self.assertItemsEqual([('acl_users', 'steve', 'john.doe')], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        self.assertEquals('john.doe', api.user.get('john.doe').getId())
        self.assertIsNone(api.user.get('steve'))
        self.assertEquals(('steven'), api.user.get('steven').getId())
