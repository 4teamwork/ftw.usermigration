from ftw.usermigration.group_members import migrate_group_members
from ftw.usermigration.testing import USERMIGRATION_INTEGRATION_TESTING
from ftw.usermigration.testing import UserMigrationTestCase
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID


class TestGroupMembers(UserMigrationTestCase):

    layer = USERMIGRATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        api.group.create('agents')
        api.group.create('assistents')
        api.group.create('drivers')

        api.user.create(username='james', email="james@test.ch")
        api.user.create(username='jack', email="jack@test.ch")
        api.user.create(username='peter', email="peter@test.ch")

        api.group.add_user(groupname='agents', username='james')

        api.group.add_user(groupname='assistents', username='jack')
        api.group.add_user(groupname='assistents', username='peter')

        api.group.add_user(groupname='drivers', username='peter')

    def get_group_member_ids(self, group_id):
        return api.portal.get_tool('portal_groups').getGroupMembers(group_id)

    def test_migrate_group_members(self):
        portal = self.layer['portal']
        mapping = {'peter': 'john.doe', 'jack': 'bud.spencer'}
        results = migrate_group_members(portal, mapping)

        self.assertItemsEqual(
            [('assistents', 'peter', 'john.doe'),
             ('drivers', 'peter', 'john.doe'),
             ('assistents', 'jack', 'bud.spencer')],
            results['moved'])
        self.assertItemsEqual([], results['copied'])
        self.assertItemsEqual([], results['deleted'])

        self.assertItemsEqual(['james'], self.get_group_member_ids('agents'))
        self.assertItemsEqual(
            ['john.doe', 'bud.spencer'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['john.doe'], self.get_group_member_ids('drivers'))

    def test_migrate_to_existing_group_member_without_replace(self):
        portal = self.layer['portal']
        mapping = {'jack': 'peter'}
        results = migrate_group_members(portal, mapping)

        self.assertItemsEqual([], results['moved'])
        self.assertItemsEqual([], results['copied'])
        self.assertItemsEqual([], results['deleted'])

        self.assertItemsEqual(['james'], self.get_group_member_ids('agents'))
        self.assertItemsEqual(['peter', 'jack'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('drivers'))

    def test_migrate_to_existing_group_member_with_replace(self):
        portal = self.layer['portal']
        mapping = {'jack': 'peter'}
        results = migrate_group_members(portal, mapping, replace=True)

        self.assertItemsEqual([('assistents', 'jack', 'peter')], results['moved'])
        self.assertItemsEqual([], results['copied'])
        self.assertItemsEqual([], results['deleted'])

        self.assertItemsEqual(['james'], self.get_group_member_ids('agents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('drivers'))

    def test_do_nothing_for_unexisting_group_members(self):
        portal = self.layer['portal']
        mapping = {'alice': 'peter'}
        results = migrate_group_members(portal, mapping)

        self.assertItemsEqual([], results['moved'])
        self.assertItemsEqual([], results['copied'])
        self.assertItemsEqual([], results['deleted'])

        self.assertItemsEqual(['james'], self.get_group_member_ids('agents'))
        self.assertItemsEqual(['peter', 'jack'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('drivers'))

    def test_copy_group_members(self):
        portal = self.layer['portal']
        mapping = {'james': 'john.doe'}
        results = migrate_group_members(portal, mapping, mode='copy')

        self.assertItemsEqual([('agents', 'james', 'john.doe')], results['copied'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['deleted'])

        self.assertItemsEqual(['james', 'john.doe'], self.get_group_member_ids('agents'))
        self.assertItemsEqual(['peter', 'jack'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('drivers'))

    def test_delete_group_members(self):
        portal = self.layer['portal']
        mapping = {'james': 'john.doe'}
        results = migrate_group_members(portal, mapping, mode='delete')

        self.assertItemsEqual([('agents', 'james', None)], results['deleted'])
        self.assertEquals([], results['moved'])
        self.assertEquals([], results['copied'])

        self.assertItemsEqual([], self.get_group_member_ids('agents'))
        self.assertItemsEqual(['peter', 'jack'], self.get_group_member_ids('assistents'))
        self.assertItemsEqual(['peter'], self.get_group_member_ids('drivers'))
