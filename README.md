RatticWeb
=========

RatticWeb is the website part of the Rattic password management solution, which allows you to easily manage your users and passwords.

If you decide to use RatticWeb seperately from its other components (which don't exist yet) you should take the following into account:
* The webpage should be served over HTTPS only, apart from a redirect from normal HTTP.
* The filesystem in which the database is stored should be protected with encryption.
* The access logs should be protected.
* The machine which serves RatticWeb should be protected from access.
* Tools like <a href=="http://www.ossec.net/">OSSEC</a> are your friend.

Requirements:
* <a href="https://pypi.python.org/pypi/pip">pip</a> (don't need, but useful)
* <a href="http://pypi.python.org/pypi/Django/1.4.3">Django 1.4.3</a>
* <a href="http://south.readthedocs.org/en/0.7.6/">Django South</a>
* <a href="http://tastypieapi.org/">Django Tastypie 0.9.12</a>
* <a href="https://www.dlitz.net/software/pycrypto/">PyCrypto</a>

Support and Known Issues:
* Through <a href="http://twitter.com/RatticDB">twitter</a> or <a href="https://github.com/tildaslash/RatticWeb/issues?state=open">Github Issues</a>

Dev Setup:
* Install requirements, if you need help seek out pydocs and your OS documentation. 
* Checkout the code
* ```mkdir db```
* ```./manage.py syncdb```
* ```./manage.py migrate```
* ```./manage.py runserver```
* Profit!



