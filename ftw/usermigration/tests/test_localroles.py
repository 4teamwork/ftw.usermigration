from ftw.usermigration.localroles import migrate_localroles
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from unittest import TestCase


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

        # Create some content and assign some local roles
        folder = portal[portal.invokeFactory('Folder', 'folder')]
        subfolder = folder[folder.invokeFactory('Folder', 'subfolder')]
        folder.manage_setLocalRoles('john', ['Reader'])
        folder.manage_setLocalRoles('jack', ['Reader', 'Contributor', 'Editor'])
        subfolder.manage_setLocalRoles('john', ['Contributor'])

    def test_migrate_local_roles_of_existing_user(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_localroles(portal, mapping)

        self.assertIn(('/plone/folder', 'john', 'peter'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        self.assertIn(
            ('peter', ('Reader',)),
            portal.folder.get_local_roles()
        )
        self.assertNotIn(
            ('john', ('Reader',)),
            portal.folder.get_local_roles()
        )

    def test_migrate_local_roles_of_nonexisting_user(self):
        portal = self.layer['portal']
        mapping = {'spam': 'peter'}
        results = migrate_localroles(portal, mapping)
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

    def test_migrate_local_roles_of_multiple_users(self):
        portal = self.layer['portal']
        mapping = {'jack': 'peter',
                   'john': 'paul'}
        results = migrate_localroles(portal, mapping)

        self.assertIn(('/plone/folder', 'jack', 'peter'), results['moved'])
        self.assertIn(('/plone/folder', 'john', 'paul'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

        self.assertIn(
            ('peter', ('Reader', 'Contributor', 'Editor')),
            portal.folder.get_local_roles()
        )
        self.assertNotIn(
            ('jack', ('Reader', 'Contributor', 'Editor')),
            portal.folder.get_local_roles()
        )
        self.assertIn(
            ('paul', ('Reader',)),
            portal.folder.get_local_roles()
        )
        self.assertNotIn(
            ('john', ('Reader',)),
            portal.folder.get_local_roles()
        )

    def test_reindex_security_on_parent(self):
        portal = self.layer['portal']
        folder = portal['folder']
        folder._reindexed_obj_security = False
        subfolder = folder['subfolder']
        subfolder._reindexed_obj_security = False

        # Patch reindexObjectSecurity
        # Our implementation only sets a marker to see if it was called
        def reindexObjectSecurity(self):
            self._reindexed_obj_security = True
        folder.reindexObjectSecurity = reindexObjectSecurity.__get__(
            folder, folder.__class__)
        subfolder.reindexObjectSecurity = reindexObjectSecurity.__get__(
            subfolder, subfolder.__class__)

        mapping = {'john': 'peter'}
        migrate_localroles(portal, mapping)

        self.assertTrue(folder._reindexed_obj_security)
        self.assertFalse(subfolder._reindexed_obj_security)

    def test_copy_localroles(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_localroles(portal, mapping, mode='copy')

        self.assertIn(('/plone/folder', 'john', 'peter'), results['copied'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['deleted'])
        self.assertIn(('peter', ('Reader',)), portal.folder.get_local_roles())
        self.assertIn(('john', ('Reader',)), portal.folder.get_local_roles())

    def test_delete_localroles(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_localroles(portal, mapping, mode='delete')

        self.assertIn(('/plone/folder', 'john', None), results['deleted'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])
        self.assertNotIn(('john', ('Reader',)), portal.folder.get_local_roles())
        self.assertNotIn(('peter', ('Reader',)), portal.folder.get_local_roles())
