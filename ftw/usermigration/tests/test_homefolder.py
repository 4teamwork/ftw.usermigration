from ftw.usermigration.homefolder import migrate_homefolders
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from unittest import TestCase
import transaction


class HomefolderMigrationTest(TestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Create some users
        mtool = getToolByName(portal, 'portal_membership', None)
        mtool.addMember('john', 'password', ['Member'], [])
        mtool.addMember('john@domain.net', 'password', ['Member'], [])
        mtool.addMember('jack', 'password', ['Member'], [])
        mtool.addMember('peter', 'password', ['Member'], [])
        mtool.addMember('peter@domain.net', 'password', ['Member'], [])

        # Create home folders
        self.folder = portal[portal.invokeFactory('Folder', 'Members')]
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea(member_id='john')
        mtool.createMemberArea(member_id='jack')
        mtool.createMemberArea(member_id='john@domain.net')
        # Create some content
        johns_home = mtool.getHomeFolder('john')
        johns_home.invokeFactory('Folder', 'folder1')

        # Objects need a DB connection to be copyable
        transaction.savepoint()

    def test_migrate_homefolder(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_homefolders(portal, mapping)

        mtool = getToolByName(portal, 'portal_membership', None)
        members_folder = mtool.getMembersFolder()
        self.assertNotIn('john', members_folder.objectIds())
        self.assertIn('peter', members_folder.objectIds())

        self.assertIn(('homefolder', 'john', 'peter'), results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])

    def test_migrate_homefolder_assign_local_roles(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        migrate_homefolders(portal, mapping)

        self.assertIn(
            ('peter', ('Owner',)),
            self.folder['peter'].get_local_roles()
        )
        self.assertNotIn(
            ('john', ('Owner',)),
            self.folder['peter'].get_local_roles()
        )

    def test_migrate_homefolder_reindex_security(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        folder = self.folder['john']

        # Patch reindexObjectSecurity
        # Our implementation only sets a marker to see if it was called
        def reindexObjectSecurity(self):
            self._reindexed_obj_security = True
        folder.reindexObjectSecurity = reindexObjectSecurity.__get__(
            folder, folder.__class__)

        migrate_homefolders(portal, mapping)
        self.assertTrue(folder._reindexed_obj_security)

    def test_copy_homefolder(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_homefolders(portal, mapping, mode='copy')

        self.assertIn('john', self.folder.objectIds())
        self.assertIn('peter', self.folder.objectIds())

        self.assertIn(('homefolder', 'john', 'peter'), results['copied'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['deleted'])

    def test_delete_homefolder(self):
        portal = self.layer['portal']
        mapping = {'john': 'peter'}
        results = migrate_homefolders(portal, mapping, mode='delete')

        self.assertNotIn('john', self.folder.objectIds())
        self.assertNotIn('peter', self.folder.objectIds())

        self.assertIn(('homefolder', 'john', None), results['deleted'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])

    def test_migrate_homefolder_with_urlquoted_id(self):
        portal = self.layer['portal']
        mapping = {'john@domain.net': 'peter@domain.net'}
        results = migrate_homefolders(portal, mapping)

        mtool = getToolByName(portal, 'portal_membership', None)
        self.assertEquals(None, mtool.getHomeFolder(id='john@domain.net'))
        self.assertNotEquals(None, mtool.getHomeFolder(id='peter@domain.net'))

        self.assertIn(('homefolder', 'john@domain.net', 'peter@domain.net'),
                      results['moved'])
        self.assertEquals([], results['copied'])
        self.assertEquals([], results['deleted'])
