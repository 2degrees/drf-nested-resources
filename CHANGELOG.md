Changelog
=========

Version 2.0.0
-------------

Added support for Django 2.2 and removed support for Django < 2.2

Version 1.3
------------------

Updated dependencies and added coverage config


Version 1.2 Beta 3
------------------

Fixed error when urlconf was not explicitly set on the request


Version 1.2 Beta 2
------------------

Fixed support for non-session-based authenticators when checking permissions in
viewsets in the ancestry.


Version 1.2 Beta 1
------------------

Implemented ability to force a field value in a nested resource to be set to
the URL of an ascending resource. This is done using the optional attribute
``field_forced_to_ancestor`` on the serializer's ``Meta`` class.


Version 1.1
-----------

Re-worked the mechanism for URL generation to support cross-linking resource
trees.

**Breaking change**: Any previous usage of many-to-many fields on variables
in the current request's URL will now break.


Version 1.0 Release Candidate 3
-------------------------------

Added proper support for namespaced URLs


Version 1.0 Release Candidate 1
-------------------------------

Added support for Django 1.10 and Rest Framework 3.4.3


Version 1.0 Beta 1 (unreleased)
-------------------------------

Initial release.
