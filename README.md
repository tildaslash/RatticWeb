RatticWeb
=========

RatticWeb is the website part of the Rattic password management solution.

If you decide to use RatticWeb seperately from its other components (which don't exist yet) you should take the following into account:
* The webpage should be served over HTTPS only, apart from a redirect for normal HTTP.
* The filesystem in which the database is stored should be protected with encryption.
* The access logs should be protected.
* The machine which servers RatticWeb should be protected from access.
