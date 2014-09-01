RatticWeb
=========

Although Daniel Hall does not approve this kind of "security", and I generally agree with him, but implementing EncryptedCharField was way simpler than encrypting backup on backup media. With this patch password field will be encrypted on the fly with help from python-keyczar and django-extensions. You can implement this on your running setup, and passwords that are currently saved in plain text will remain in that state until you change them, while all newly added password will be encrypted using symmetric AES algorithm.


RatticWeb is the website part of the Rattic password management solution, which allows you to easily manage your users and passwords.

To quickly get a RatticDB demo running do the following:
* Install VirtualBox from https://www.virtualbox.org/
* Install Vagrant from http://www.vagrantup.com/
* Install Ansible from http://ansible.com/ or from pip, apt or yum (we need 1.4+)
* Check out this repo
* Run ```vagrant up``` in the root of this repo
* Wait for vagrant to deploy the machine
* Browse to https://localhost:8443/
* Login with Username: admin Password: rattic
* ...
* Profit!

If you decide to use RatticWeb you should take the following into account:
* The webpage should be served over HTTPS only, apart from a redirect from normal HTTP.
* The filesystem in which the database is stored should be protected with encryption.
* The access logs should be protected.
* The machine which serves RatticWeb should be protected from access.
* Tools like <a href=="http://www.ossec.net/">OSSEC</a> are your friend.

Support and Known Issues:
* Through <a href="http://twitter.com/RatticDB">twitter</a> or <a href="https://github.com/tildaslash/RatticWeb/issues?state=open">Github Issues</a>
* Apache config needs to have "WSGIPassAuthorization On" for the API keys to work  

Dev Setup: <https://github.com/tildaslash/RatticWeb/wiki/Development>

