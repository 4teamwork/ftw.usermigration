from ftw.usermigration.interfaces import IPostMigrationHook
from ftw.usermigration.interfaces import IPreMigrationHook
from ftw.usermigration.interfaces import IPrincipalMappingSource
from zope.component import getAdapters
from zope.schema.vocabulary import SimpleVocabulary


USE_MANUAL_MAPPING = 'use_manual_mapping'


class MappingSourcesVocabularyFactory(object):

    def __call__(self, context):
        terms = []

        # Always add the 'Use manually entered mapping' option (default)
        terms.append(SimpleVocabulary.createTerm(
            USE_MANUAL_MAPPING, USE_MANUAL_MAPPING,
            'Use manually entered mapping'))

        mapping_sources = getAdapters(
            (context, context.REQUEST), IPrincipalMappingSource)

        for name, src in mapping_sources:
            value, token, title = name, name, name
            terms.append(SimpleVocabulary.createTerm(value, token, title))

        return SimpleVocabulary(terms)


class PreMigrationHooksVocabularyFactory(object):

    def __call__(self, context):
        terms = []

        hooks = getAdapters(
            (context, context.REQUEST), IPreMigrationHook)

        for name, hook in hooks:
            value, token, title = name, name, name
            terms.append(SimpleVocabulary.createTerm(value, token, title))

        return SimpleVocabulary(terms)


class PostMigrationHooksVocabularyFactory(object):

    def __call__(self, context):
        terms = []

        hooks = getAdapters(
            (context, context.REQUEST), IPostMigrationHook)

        for name, hook in hooks:
            value, token, title = name, name, name
            terms.append(SimpleVocabulary.createTerm(value, token, title))

        return SimpleVocabulary(terms)
