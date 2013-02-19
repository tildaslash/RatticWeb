RatticWeb
=========

RatticWeb is the website part of the Rattic password management solution.

If you decide to use RatticWeb seperately from its other components (which don't exist yet) you should take the following into account:
* The webpage should be served over HTTPS only, apart from a redirect for normal HTTP.
* The filesystem in which the database is stored should be protected with encryption.
* The access logs should be protected.
* The machine which servers RatticWeb should be protected from access.
* Tools like <a href=="http://www.ossec.net/">OSSEC</a> are your friend.

Requirements:
* <a href="http://pypi.python.org/pypi/Django/1.4.3">Django 1.4.3</a>
* <a href="http://south.readthedocs.org/en/0.7.6/">Django South</a>

Support:
If you have any requests or generally support tweet <a href="http://twitter.com/ratticdb">@RatticDB</a>
