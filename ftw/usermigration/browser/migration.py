from Acquisition import aq_inner
from collections import defaultdict
from datetime import datetime
from ftw.usermigration import _
from ftw.usermigration.dashboard import migrate_dashboards
from ftw.usermigration.globalroles import migrate_globalroles
from ftw.usermigration.group_members import migrate_group_members
from ftw.usermigration.homefolder import migrate_homefolders
from ftw.usermigration.interfaces import IPostMigrationHook
from ftw.usermigration.interfaces import IPreMigrationHook
from ftw.usermigration.interfaces import IPrincipalMappingSource
from ftw.usermigration.localroles import migrate_localroles
from ftw.usermigration.loginnames import migrate_loginnames
from ftw.usermigration.properties import migrate_properties
from ftw.usermigration.userids import migrate_userids
from ftw.usermigration.utils import get_var_log
from ftw.usermigration.utils import mkdir_p
from ftw.usermigration.vocabularies import USE_MANUAL_MAPPING
from logging import FileHandler
from logging import getLogger
from pprint import pformat
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form, field, button
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.interfaces import WidgetActionExecutionError
from zope import interface, schema
from zope.component import getMultiAdapter
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import logging
import os
import transaction


BUILTIN_MIGRATIONS = {
    'loginnames': migrate_loginnames,
    'userids': migrate_userids,
    'group_members': migrate_group_members,
    'properties': migrate_properties,
    'dashboard': migrate_dashboards,
    'homefolder': migrate_homefolders,
    'localroles': migrate_localroles,
    'globalroles': migrate_globalroles,
}


class IUserMigrationFormSchema(interface.Interface):

    mapping_source = schema.Choice(
        title=_(u'label_mapping_source', default='Principal Mapping Source'),
        description=_(u'help_mapping_source',
                      default=u'Choose a source for the principal mapping. '
                      'Select either a programmatically defined mapping (see '
                      'README) or choose "Use manually entered mapping" and '
                      'enter your mapping in the form below'),
        vocabulary='ftw.usermigration.mapping_sources',
        default=USE_MANUAL_MAPPING,
        required=True,
    )

    manual_mapping = schema.List(
        title=_(u'label_manual_mapping', default=u'Manual Principal Mapping'),
        description=_(u'help_manual_mapping',
                      default=u'If you selected "Use manually entered '
                      'mapping" above, provide a pair of old and new '
                      'principal IDs (user or group) and new ID separated by '
                      'a colon per line (e.g. olduserid:newuserid).'),
        default=[],
        value_type=schema.ASCIILine(title=u"Principal Mapping Line"),
        required=False,
    )

    pre_migration_hooks = schema.List(
        title=_(u'label_pre_migration_hooks', default='Pre-Migration Hooks'),
        description=_(u'pre_migration_hooks',
                      default=u'Check any pre-migration hooks that should be '
                      'executed before the migration.'),
        value_type=schema.Choice(
            vocabulary='ftw.usermigration.pre_migration_hooks',
        ),
        required=False,
    )

    migrations = schema.List(
        title=_(u'label_migrations', default=u'Migrations'),
        description=_(u'help_migrations', default=u'Select one or more '
                      'migrations that should be run.'),
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('loginnames', 'loginnames', _(u'Login Names')),
                SimpleTerm('userids', 'userids', _(u'User IDs')),
                SimpleTerm('group_members', 'group_members', _(u'Group Members')),
                SimpleTerm('localroles', 'localroles', _(u'Local Roles')),
                SimpleTerm('globalroles', 'globalroles', _(u'Global Roles')),
                SimpleTerm('dashboard', 'dashboard', _(u"Dashboard")),
                SimpleTerm('homefolder', 'homefolder', _(u"Home Folder")),
                SimpleTerm('properties', 'properties', _(u"User Properties")),
            ]),
        ),
        required=True,
    )

    post_migration_hooks = schema.List(
        title=_(u'label_post_migration_hooks', default='Post-Migration Hooks'),
        description=_(u'post_migration_hooks',
                      default=u'Check any post-migration hooks that should be '
                      'executed after the migration.'),
        value_type=schema.Choice(
            vocabulary='ftw.usermigration.post_migration_hooks',
        ),
        required=False,
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

    log_to_file = schema.Bool(
        title=_(u'label_log_to_file', default=u'Log migration report to file'),
        default=False,
        description=_(u'help_log_to_file',
                      default=u'Whether a detailed migration report should be'
                      ' written to a logfile on the filesystem.'),
    )

    summary = schema.Bool(
        title=_(u'label_summary', default=u'Summary only'),
        default=False,
        description=_(u'help_summary',
                      default=u'Only display a summary after migration '
                      'instead of a full, detailed report. Recommended for '
                      'large migrations.'),
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
        self.results_pre_migration = {}
        self.results = defaultdict(dict)
        self.results_post_migration = {}
        self.log_to_file = False
        self.summary = defaultdict(list)

    def _get_manual_mapping(self, formdata):
        manual_mapping = formdata['manual_mapping']

        if manual_mapping is None:
            raise WidgetActionExecutionError(
                'manual_mapping',
                Invalid('Manual mapping is required if "Use manually '
                        'entered mapping" has been selected.'))

        principal_mapping = {}
        for line in manual_mapping:
            try:
                old_id, new_id = line.split(':')
            except ValueError:
                raise WidgetActionExecutionError(
                    'manual_mapping',
                    Invalid('Invalid principal mapping provided.'))
            principal_mapping[old_id] = new_id
        return principal_mapping

    def _get_hooks(self, hooks, interface):
        for name in hooks:
            hook = getMultiAdapter(
                (self.context, self.context.REQUEST), interface, name)
            yield name, hook

    def _setup_logger(self):
        logger = getLogger('ftw.usermigration')
        logger.setLevel(logging.DEBUG)

        # Remove any existing handlers. Required because this may be called
        # multiple times, and we also want a new timestamp for every run
        for h in logger.handlers:
            logger.removeHandler(h)

        log_path = None
        if self.log_to_file:
            timestamp = datetime.today().strftime('%Y%m%d%H%M')
            log_fn = 'usermigration-{0}.log'.format(timestamp)
            log_dir = get_var_log()
            mkdir_p(log_dir)
            log_path = os.path.join(log_dir, log_fn)

            handler = FileHandler(log_path)
            handler.setFormatter(logging.Formatter(
                "%(asctime)-15s %(message)s", "%Y-%m-%d %H:%M"))
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)

        return logger, log_path

    def _log_migration_details(self, logger, name, results):
        if not self.log_to_file:
            return

        for mode in results.keys():
            for obj, old, new in results[mode]:
                logger.debug("Migrated [{0}] {1}: {2} -> {3}".format(
                    name, obj, old, new))

    def _summarize_hook_results(self, hook_results):
        hook_results_summary = []
        for migration, steps in hook_results.items():
            for step, mode_results in steps.items():
                step_totals = [len(mode_results[mode])
                               for mode in ('moved', 'copied', 'deleted')]
                hook_results_summary.append(
                    [migration, step] + step_totals)
        return hook_results_summary

    def _summarize_results(self):
        self.summary['pre-migration'] = self._summarize_hook_results(
            self.results_pre_migration)

        builtin_results_summary = []
        for migration, mode_results in self.results.items():
            migration_totals = [len(mode_results[mode])
                                for mode in ('moved', 'copied', 'deleted')]
            builtin_results_summary.append([migration] + migration_totals)
        self.summary['builtin'] = builtin_results_summary

        self.summary['post-migration'] = self._summarize_hook_results(
            self.results_post_migration)

    @button.buttonAndHandler(u'Migrate')
    def handleMigrate(self, action):
        context = aq_inner(self.context)
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        self.log_to_file = data['log_to_file']
        logger, logfile_path = self._setup_logger()
        logger.info('Starting principal migration')

        if data['dry_run']:
            transaction.doom()
            logger.info('(Dry run)')

        if data['mapping_source'] == USE_MANUAL_MAPPING:
            # Parse mapping from form field
            principal_mapping = self._get_manual_mapping(data)
        else:
            # Get mapping from IPrincipalMappingSource adapter
            mapping_source = getMultiAdapter(
                (context, context.REQUEST), IPrincipalMappingSource,
                name=data['mapping_source'])
            principal_mapping = mapping_source.get_mapping()
        logger.debug('Using mapping:\n{0}'.format(pformat(principal_mapping)))

        # Pre-migration hooks
        pre_migration_hooks = self._get_hooks(
            data['pre_migration_hooks'], IPreMigrationHook)

        for name, hook in pre_migration_hooks:
            logger.info("Starting migration '{0}'".format(name))
            hook_results = hook.execute(principal_mapping, data['mode'])
            self.results_pre_migration[name] = hook_results
            for step in hook_results.keys():
                self._log_migration_details(
                    logger, step, hook_results[step])

        # Builtin migrations
        for name, migration in BUILTIN_MIGRATIONS.items():
            if name in data['migrations']:
                logger.info("Starting migration '{0}'".format(name))
                self.results[name] = migration(
                    context, principal_mapping, mode=data['mode'],
                    replace=data['replace'])
                self._log_migration_details(logger, name, self.results[name])

        # Post-migration hooks
        post_migration_hooks = self._get_hooks(
            data['post_migration_hooks'], IPostMigrationHook)

        for name, hook in post_migration_hooks:
            logger.info("Starting migration '{0}'".format(name))
            hook_results = hook.execute(principal_mapping, data['mode'])
            self.results_post_migration[name] = hook_results
            for step in hook_results.keys():
                self._log_migration_details(
                    logger, step, hook_results[step])

        logger.info("Migration finished")
        if self.log_to_file:
            logger.info("Migration logfile written to {0}".format(
                logfile_path))

        if data['summary']:
            self._summarize_results()
            self.result_template = ViewPageTemplateFile('migration_summary.pt')
        else:
            self.result_template = ViewPageTemplateFile('migration.pt')

    @button.buttonAndHandler((u"Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())

    def updateWidgets(self):
        self.fields['pre_migration_hooks'].widgetFactory = CheckBoxFieldWidget
        self.fields['migrations'].widgetFactory = CheckBoxFieldWidget
        self.fields['post_migration_hooks'].widgetFactory = CheckBoxFieldWidget
        super(UserMigrationForm, self).updateWidgets()
        self.widgets['manual_mapping'].rows = 15

    def render(self):
        self.request.set('disable_border', True)
        if self.result_template:
            return self.result_template(self)
        return super(UserMigrationForm, self).render()
