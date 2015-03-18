from Acquisition import aq_inner
from ftw.usermigration import _
from ftw.usermigration.dashboard import migrate_dashboards
from ftw.usermigration.homefolder import migrate_homefolders
from ftw.usermigration.localroles import migrate_localroles
from ftw.usermigration.properties import migrate_properties
from ftw.usermigration.users import migrate_users
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form, field, button
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.interfaces import WidgetActionExecutionError
from zope import interface, schema
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import transaction


class IUserMigrationFormSchema(interface.Interface):

    principal_mapping = schema.List(
        title=_(u'label_principal_mapping', default=u'Principal Mapping'),
        description=_(u'help_principal_mapping',
                      default=u'Provide a pair of old and new principal IDs '
                      '(user or group) and new ID separated by a colon per '
                      'line (e.g. olduserid:newuserid).'),
        default=[],
        value_type=schema.ASCIILine(title=u"Principal Mapping Line"),
        required=True,
    )

    migrations = schema.List(
        title=_(u'label_migrations', default=u'Migrations'),
        description=_(u'help_migrations', default=u'Select one or more '
                      'migrations that should be run.'),
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('users', 'users', _(u'Users')),
                SimpleTerm('localroles', 'localroles', _(u'Local Roles')),
                SimpleTerm('dashboard', 'dashboard', _(u"Dashboard")),
                SimpleTerm('homefolder', 'homefolder', _(u"Home Folder")),
                SimpleTerm('properties', 'properties', _(u"User Properties")),
            ]),
        ),
        required=True,
    )

    mode = schema.Choice(
        title=_(u'label_migration_mode', default='Mode'),
        description=_(u'help_migration_mode',
                      default=u'Choose a migration '
                      'mode. Copy will keep user or group data of the old '
                      'principal. Delete will just remove data of the old '
                      'principal.'),
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
        description=_(u'help_replace',
                      default=u'Check this option to replace existing user or '
                      'group data. If unchecked, user or group data is not '
                      'migrated when it already exists for a given principal '
                      'ID.'),
        default=False,
    )

    dry_run = schema.Bool(
        title=_(u'label_dry_run', default=u'Dry Run'),
        default=False,
        description=_(u'help_dry_run',
                      default=u'Check this option to not modify any data and '
                      'to see what would have been migrated.'),
    )


class UserMigrationForm(form.Form):
    fields = field.Fields(IUserMigrationFormSchema)
    ignoreContext = True  # don't use context to get widget data
    label = u"Migrate principals"

    def __init__(self, context, request):
        super(UserMigrationForm, self).__init__(context, request)
        self.result_template = None
        self.results_localroles = {}
        self.results_dashboard = {}
        self.results_homefolder = {}
        self.results_users = {}
        self.results_properties = {}

    def _get_manual_mapping(self, formdata):
        principal_mapping = {}
        for line in formdata['manual_mapping']:
            try:
                old_id, new_id = line.split(':')
            except ValueError:
                raise WidgetActionExecutionError(
                    'manual_mapping',
                    Invalid('Invalid principal mapping provided.'))
            principal_mapping[old_id] = new_id
        return principal_mapping

    @button.buttonAndHandler(u'Migrate')
    def handleMigrate(self, action):
        context = aq_inner(self.context)
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        principal_mapping = self._get_manual_mapping(data)

        if 'users' in data['migrations']:
            self.results_users = migrate_users(
                context, principal_mapping, mode=data['mode'],
                replace=data['replace'])

        if 'properties' in data['migrations']:
            self.results_properties = migrate_properties(
                context, principal_mapping, mode=data['mode'],
                replace=data['replace'])

        if 'dashboard' in data['migrations']:
            self.results_dashboard = migrate_dashboards(
                context, principal_mapping, mode=data['mode'],
                replace=data['replace'])

        if 'homefolder' in data['migrations']:
            self.results_homefolder = migrate_homefolders(
                context, principal_mapping, mode=data['mode'],
                replace=data['replace'])

        if 'localroles' in data['migrations']:
            self.results_localroles = migrate_localroles(
                context, principal_mapping, mode=data['mode'])

        if data['dry_run']:
            transaction.abort()

        self.result_template = ViewPageTemplateFile('migration.pt')

    @button.buttonAndHandler((u"Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())

    def updateWidgets(self):
        super(UserMigrationForm, self).updateWidgets()
        self.widgets['principal_mapping'].rows = 15
        self.fields['migrations'].widgetFactory = CheckBoxFieldWidget

    def render(self):
        self.request.set('disable_border', True)
        if self.result_template:
            return self.result_template(self)
        return super(UserMigrationForm, self).render()
