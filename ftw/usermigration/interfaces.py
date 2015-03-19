from zope.interface import Interface


class IPrincipalMappingSource(Interface):

    def __init__(portal, request):
        """The adapter adapts portal and request.
        """

    def get_mapping():
        """Returns the principal mapping as a dictionary, mapping old IDs (key)
        to new IDs (value).
        """
