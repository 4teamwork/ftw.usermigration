import transaction
from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import interface, schema
from zope.component import getUtility
from z3c.form import form, field, button
from z3c.form.interfaces import WidgetActionExecutionError
from ftw.usermigration import _
from ftw.usermigration.dashboard import migrate_dashboards
from ftw.usermigration.localroles import migrate_localroles
from ftw.usermigration.homefolder import migrate_homefolders
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import Invalid


class IUserMigrationFormSchema(interface.Interface):


    user_mapping = schema.List(
        title=_(u'label_user_mapping', default=u'User Mapping'),
        description=_(u'help_user_mapping', default=u'Provide a pair of old '
                      'and new userid separated by a colon per line (e.g. '
                      'olduserid:newuserid).'),
        default=[],
        value_type=schema.ASCIILine(title=u"User Mapping Line"),
        required=True,
    )

    migrate_localroles = schema.Bool(
        title=_(u'label_migrate_localroles', default=u'Migrate Local Roles'),
        default=False,
    )

    migrate_dashboards = schema.Bool(
        title=_(u'label_migrate_dashboards', default=u'Migrate Dashboards'),
        default=False,
    )

    migrate_homefolders = schema.Bool(
        title=_(u'label_migrate_homefolders', default=u'Migrate Home Folders'),
        default=False,
    )

    mode = schema.Choice(
        title=_(u'label_migration_mode', default='Mode'),
        description=_(u'help_migration_mode', default=u'Choose a migration '
          'mode. Copy will keep user data of the old user. Delete will just '
          'remove user data of the old user.'),
        vocabulary=SimpleVocabulary([
            SimpleTerm('move', 'move', _(u'Move')),
            SimpleTerm('copy', 'copy', _(u"Copy")),
            SimpleTerm('delete', 'delete', _(u"Delete")),
        ]),
        default='move',
        required=True,
    )

    replace = schema.Bool(
        title=_(u'label_replace', default=u"Replace Existing Data"),
        description=_(u'help_replace', default=u'Check this option to replace '
          'existing user data. If unchecked, user data is not migrated when it'
          'already exists for a given userid.'),
        default=False,
    )

class UserMigrationForm(form.Form):
    fields = field.Fields(IUserMigrationFormSchema)
    ignoreContext = True # don't use context to get widget data
    label = u"Migrate UserIDs"

    def __init__(self, context, request):
        super(UserMigrationForm, self).__init__(context, request)
        self.result_template = None

    @button.buttonAndHandler(u'Migrate')
    def handleMigrate(self, action):
        context = aq_inner(self.context)
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        userids = {}
        for line in data['user_mapping']:
            try:
                old_userid, new_userid = line.split(':')
            except ValueError:
                raise WidgetActionExecutionError('user_mapping',
                    Invalid('Invalid user mapping provided.'))
            userids[old_userid] = new_userid

        if data['migrate_dashboards']:
            dashboard_results = migrate_dashboards(context, userids, 
                mode=data['mode'], replace=data['replace'])

        if data['migrate_homefolders']:
            homefolder_results = migrate_homefolders(context, userids,
                mode=data['mode'])

        if data['migrate_localroles']:
            migrate_localroles(context, userids, mode=data['mode'])

        self.result_template = ViewPageTemplateFile('migration.pt')

    @button.buttonAndHandler((u"Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())

    def render(self):
        self.request.set('disable_border', True)
        if self.result_template:
            return self.result_template(self)
        return super(UserMigrationForm, self).render()