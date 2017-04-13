from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from ftw.testbrowser.pages.z3cform import erroneous_fields
from ftw.usermigration.interfaces import IPostMigrationHook
from ftw.usermigration.interfaces import IPreMigrationHook
from ftw.usermigration.interfaces import IPrincipalMappingSource
from ftw.usermigration.testing import USERMIGRATION_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from unittest2 import TestCase
from zope.publisher.interfaces.browser import IBrowserRequest
import transaction


def make_mapping(dct):
    """Create a mapping string suitable for our ASCIILines widget from a dict
    """
    return '\n'.join(':'.join((key, value)) for key, value in dct.items())


class DummyMigrationMappingSource(object):

    def __init__(self, portal, request):
        pass

    def get_mapping(self):
        return {'old_john': 'new_john'}


class DummyMigrationHook(object):

    def __init__(self, portal, request):
        self.portal = portal
        self.request = request

    def execute(self, principal_mapping, mode):
        results = {
            'Step 1': {
                'moved': [('/foo', 'old', 'new')],
                'copied': [],
                'deleted': []},
            'Step 2': {
                'moved': [('/bar', 'old', 'new')],
                'copied': [],
                'deleted': []},
        }
        return results


class TestMigrationForm(TestCase):

    layer = USERMIGRATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.sm = self.portal.getSiteManager()
        self.uf = getToolByName(self.portal, 'acl_users')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        create(Builder('user').with_userid('old_john'))

    @browsing
    def test_form_defaults_to_using_manual_mapping(self, browser):
        browser.login().visit(view='user-migration')

        mapping = make_mapping({'old_john': 'new_john'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Migrations': ['userids']}
        ).submit()

        self.assertEquals(1, len(self.uf.searchUsers(id='new_john')))

    @browsing
    def test_form_complains_about_invalid_manual_mapping(self, browser):
        browser.login().visit(view='user-migration')

        browser.fill(
            {'Manual Principal Mapping': 'a:b:c:d:e:f'}
        ).submit()

        self.assertIn(
            ['Invalid principal mapping provided.'],
            erroneous_fields(browser.forms['form']).values())

    @browsing
    def test_helpful_message_if_manual_mapping_required(self, browser):
        browser.login().visit(view='user-migration')

        browser.fill(
            {'Migrations': ['userids']}
        ).submit()

        self.assertIn(
            ['Manual mapping is required if "Use manually entered mapping" '
             'has been selected.'],
            erroneous_fields(browser.forms['form']).values())

    @browsing
    def test_dry_run(self, browser):
        browser.login().visit(view='user-migration')

        db = self.portal._p_jar.db()
        last_transaction = db.lastTransaction()

        mapping = make_mapping({'old_john': 'new_john'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Migrations': ['userids', 'properties', 'dashboard',
                            'homefolder', 'localroles'],
             'Dry Run': True}
        ).submit()

        self.assertEquals(
            last_transaction, db.lastTransaction(),
            'Last transaction in DB should have been the same as before '
            'running the migration in dry run mode - this means there have '
            'been changes written to the DB!')

    @browsing
    def test_can_use_mapping_source_adapters(self, browser):
        self.sm.registerAdapter(
            DummyMigrationMappingSource, (IPloneSiteRoot, IBrowserRequest),
            IPrincipalMappingSource, name='some-migration-mapping')
        transaction.commit()

        browser.login().visit(view='user-migration')

        browser.fill(
            {'Principal Mapping Source': 'some-migration-mapping',
             'Migrations': ['userids']}
        ).submit()

        self.assertEquals(1, len(self.uf.searchUsers(id='new_john')))

    @browsing
    def test_can_use_pre_and_post_migration_hooks(self, browser):
        self.sm.registerAdapter(
            DummyMigrationHook, (IPloneSiteRoot, IBrowserRequest),
            IPreMigrationHook, name='dummy-pre-migration-hook')
        self.sm.registerAdapter(
            DummyMigrationHook, (IPloneSiteRoot, IBrowserRequest),
            IPostMigrationHook, name='dummy-post-migration-hook')
        transaction.commit()

        browser.login().visit(view='user-migration')

        mapping = make_mapping({'old_john': 'new_john'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Pre-Migration Hooks': ['dummy-pre-migration-hook'],
             'Post-Migration Hooks': ['dummy-post-migration-hook']}
        ).submit()

        self.assertEquals(
            [['Object', 'Old ID', 'New ID'],
             ['/foo', 'old', 'new']],
            browser.css('table.pre-migration-hook')[0].lists())

        self.assertEquals(
            [['Object', 'Old ID', 'New ID'],
             ['/bar', 'old', 'new']],
            browser.css('table.pre-migration-hook')[1].lists())

        self.assertEquals(
            [['Object', 'Old ID', 'New ID'],
             ['/foo', 'old', 'new']],
            browser.css('table.post-migration-hook')[0].lists())

        self.assertEquals(
            [['Object', 'Old ID', 'New ID'],
             ['/bar', 'old', 'new']],
            browser.css('table.post-migration-hook')[1].lists())

    @browsing
    def test_form_user_move(self, browser):
        browser.login().visit(view='user-migration')

        mapping = make_mapping({'old_john': 'new_john',
                                'old_jack': 'new_jack'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Migrations': ['userids', 'localroles']}
        ).submit()

        user = self.uf.searchUsers(id='new_john')[0]

        # New user's userid is correct
        self.assertEquals('new_john', user['userid'])

        # Login of new user is sill the old one (login migration
        # is a separate migration step)
        self.assertEquals('old_john', user['login'])

        # Old user is gone
        self.assertEquals((), self.uf.searchUsers(id='old_john'))

    @browsing
    def test_form_user_move_with_loginname(self, browser):
        browser.login().visit(view='user-migration')

        mapping = make_mapping({'old_john': 'new_john',
                                'old_jack': 'new_jack'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Migrations': ['loginnames', 'userids']}
        ).submit()

        user = self.uf.searchUsers(id='new_john')[0]

        # New user's userid is correct
        self.assertEquals('new_john', user['userid'])

        # Login of new user has been set to userid
        self.assertEquals('new_john', user['login'])

        # Old user is gone
        self.assertEquals((), self.uf.searchUsers(id='old_john'))

    @browsing
    def test_form_user_copy(self, browser):
        browser.login().visit(view='user-migration')

        mapping = make_mapping({'old_john': 'new_john',
                                'old_jack': 'new_jack'})
        browser.fill(
            {'Manual Principal Mapping': mapping,
             'Migrations': ['userids', 'localroles'],
             'Mode': 'copy'}
        ).submit()

        user = self.uf.searchUsers(id='new_john')[0]

        # New user's userid is correct
        self.assertEquals('new_john', user['userid'])

        # Login of new user has been set to userid
        self.assertEquals('new_john', user['login'])

        # Old user still exists
        old_user = self.uf.searchUsers(id='old_john')[0]
        self.assertEquals('old_john', old_user['userid'])
