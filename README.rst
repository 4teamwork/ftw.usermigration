Introduction
============

This product allows migrating various user specific data associated with a
principal ID (user or group) to an other principal ID. It's especially useful
if IDs have to be renamed.

Currently the following user data can be migrated:

- Users (ZODB User Manager)

- User Properties (ZODB Mutable Property Provider)

- Local Roles

- Dashboards

- Home Folders

Todo:

- Groups


Installation
============

Add ``ftw.usermigration`` to the list of eggs in your buildout.
Then rerun buildout and restart your instance.


Usage
=====

Open ``@@user-migration`` in your browser.

Registering principal mappings
------------------------------

If you would like to provide the principal mapping in a programmatic way
instead of entering it through-the-web, you can register one or more named
adapters that implement ``IPrincipalMappingSource``.

Example:

.. code:: python

	class MigrationMapping(object):

	    def __init__(self, portal, request):
	        self.portal = portal
	        self.request = request

	    def get_mapping(self):
	        mapping = {'old_user': 'new_user',
	                   'old_group': 'new_group'}
	        return mapping

ZCML:

.. code:: xml

    <adapter
        factory="my.package.migration.MigrationMapping"
        provides="ftw.usermigration.interfaces.IPrincipalMappingSource"
        for="Products.CMFPlone.interfaces.siteroot.IPloneSiteRoot
             zope.publisher.interfaces.browser.IBrowserRequest"
        name="ad-migration-2015"
    />

This will result in this mapping being selectable as a mapping source with the
name ``ad-migration-2015`` in the ``@@user-migration`` form.

Registering pre- and post-migration hooks
-----------------------------------------

If you want to provide your own code that runs before or after any of the
built-in migration types in ``ftw.usermigration``, you can do so by registering
hooks that implement the ``IPreMigrationHook`` or ``IPostMigrationHook`` interface.

Example:

.. code:: python

  class ExamplePreMigrationHook(object):

      def __init__(self, portal, request):
          self.portal = portal
          self.request = request

      def execute(self, principal_mapping, mode):
          # ...
          # your code here
          # ...
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

A hook adapter's ``execute()`` method receives the ``principal_mapping`` and
``mode`` as arguments.

Its results are expected to be a dict of dicts: The outer
dictionary allows for a hook to group several steps it executes and
report their results separately. The inner dictionary follows the same
structure as the results of the built-in migrations.


ZCML:

.. code:: xml

    <adapter
        factory=".migrations.ExamplePreMigrationHook"
        provides="ftw.usermigration.interfaces.IPreMigrationHook"
        for="Products.CMFPlone.interfaces.siteroot.IPloneSiteRoot
             zope.publisher.interfaces.browser.IBrowserRequest"
        name="example-pre-migration-hook"
    />


Links
=====

- Main github project repository:
  https://github.com/4teamwork/ftw.usermigration
- Issue tracker:
  https://github.com/4teamwork/ftw.usermigration/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.usermigration
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.usermigration


Copyright
=========

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.usermigration`` is licensed under GNU General Public License, version 2.
