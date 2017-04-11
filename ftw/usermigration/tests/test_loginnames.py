from ftw.usermigration.loginnames import migrate_loginnames
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestLoginNames(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('user1', 'password', ['Member'], [])
        mtool.addMember('jack', 'password', ['Member'], [])
        mtool.addMember('peter', 'password', ['Member'], [])

        # Change login-name for specific user
        api.portal.get_tool('acl_users').source_users.updateUser('jack', 'jack@example.ch')

    def test_migrate_loginnames(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_loginnames(portal, mapping)

        self.assertIn(('user1', 'user1', 'john.doe'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'john.doe',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_migrate_loginnames_which_differs_to_the_userids(self):
        portal = self.layer['portal']
        api.portal.get_tool('acl_users').source_users.updateUser('user1', 'hugo.boss@example.ch')

        mapping = {'user1': 'john.doe'}
        results = migrate_loginnames(portal, mapping)

        self.assertIn(('user1', 'hugo.boss@example.ch', 'john.doe'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'john.doe',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_migrate_to_existing_loginname_without_replace_does_nothing(self):
        # Change login-name for specific user
        api.portal.get_tool('acl_users').source_users.updateUser('jack', 'jack@example.ch')

        portal = self.layer['portal']
        mapping = {'user1': 'jack@example.ch'}
        results = migrate_loginnames(portal, mapping, replace=False)
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_migrate_to_existing_loginname_with_replace_does_nothing(self):
        # Change login-name for specific user
        api.portal.get_tool('acl_users').source_users.updateUser('jack', 'jack@example.ch')

        portal = self.layer['portal']
        mapping = {'user1': 'jack@example.ch'}
        results = migrate_loginnames(portal, mapping, replace=True)
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_migrate_login_to_existing_userid(self):
        portal = self.layer['portal']
        api.portal.get_tool('acl_users').source_users.updateUser('jack', 'jack@example.ch')

        mapping = {'user1': 'jack'}
        results = migrate_loginnames(portal, mapping, replace=True)
        self.assertIn(('user1', 'user1', 'jack'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'jack',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_copy_loginnames_does_nothing(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_loginnames(portal, mapping, mode='copy')

        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['login']
        )

    def test_delete_loginnames_does_nothing(self):
        portal = self.layer['portal']
        mapping = {'user1': 'john.doe'}
        results = migrate_loginnames(portal, mapping, mode='delete')

        self.assertEquals([], results['deleted'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])

        uf = getToolByName(portal, 'acl_users')
        self.assertEquals(
            'user1',
            uf.searchUsers(id='user1')[0]['userid']
        )

