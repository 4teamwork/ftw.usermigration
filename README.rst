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
