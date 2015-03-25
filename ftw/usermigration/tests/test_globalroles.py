from ftw.builder import Builder
from ftw.builder import create
from ftw.usermigration.globalroles import migrate_globalroles
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestGlobalRoles(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        self.acl_users = getToolByName(self.portal, 'acl_users')
        self.role_manager = self.acl_users.portal_role_manager

        self.old_user = create(Builder('user').with_userid('old.user'))
        self.new_user = create(Builder('user').with_userid('new.user'))

        self.role_manager.assignRoleToPrincipal(
            'Site Administrator', 'old.user')

        self.old_group = create(Builder('group').with_groupid('old.group'))
        self.new_group = create(Builder('group').with_groupid('new.group'))

        self.role_manager.assignRoleToPrincipal(
            'Reviewer', 'old.group')

    def test_migrating_global_roles_for_users(self):
        # old.user had the Site Administrator role according to our setup
        self.assertIn(
            ('old.user', 'old.user'),
            self.role_manager.listAssignedPrincipals('Site Administrator'))

        # New user doesn't yet have that role
        self.assertNotIn(
            ('new.user', 'new.user'),
            self.role_manager.listAssignedPrincipals('Site Administrator'))

        mapping = {'old.user': 'new.user'}
        migrate_globalroles(self.portal, mapping, mode='move')

        # After the migration he does
        self.assertIn(
            ('new.user', 'new.user'),
            self.role_manager.listAssignedPrincipals('Site Administrator'))

        # And old.user doesn't any more
        self.assertNotIn(
            ('old.user', 'old.user'),
            self.role_manager.listAssignedPrincipals('Site Administrator'))

    def test_migrating_global_roles_for_groups(self):
        # old.group had the Reviewer role according to our setup
        self.assertIn(
            ('old.group', 'old.group'),
            self.role_manager.listAssignedPrincipals('Reviewer'))

        # New group doesn't yet have that role
        self.assertNotIn(
            ('new.group', 'new.group'),
            self.role_manager.listAssignedPrincipals('Reviewer'))

        mapping = {'old.group': 'new.group'}
        migrate_globalroles(self.portal, mapping, mode='move')

        # After the migration it does
        self.assertIn(
            ('new.group', 'new.group'),
            self.role_manager.listAssignedPrincipals('Reviewer'))

        # And old.group doesn't any more
        self.assertNotIn(
            ('old.group', 'old.group'),
            self.role_manager.listAssignedPrincipals('Reviewer'))

    def test_migrating_global_roles_returns_correct_results(self):
        mapping = {'old.user': 'new.user'}
        results = migrate_globalroles(self.portal, mapping, mode='move')

        self.assertIn(('Site Administrator', 'old.user', 'new.user'),
                      results['moved'])

    def test_modes_other_than_move_raise_exception(self):
        mapping = {'old.user': 'new.user'}
        with self.assertRaises(NotImplementedError):
            migrate_globalroles(self.portal, mapping, mode='copy')

        with self.assertRaises(NotImplementedError):
            migrate_globalroles(self.portal, mapping, mode='delete')
