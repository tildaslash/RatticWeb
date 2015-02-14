from django.core.urlresolvers import reverse
from django.test import TestCase

from ratticweb.tests.helper import TestData
from cred.models import Cred

import json
import os


here = os.path.abspath(os.path.dirname(__file__))
ssh_keys = os.path.join(here, "ssh_keys")


class ApiTest(TestCase):
    def setUp(self):
        self.data = TestData()
        self.cred = Cred(title="one", username="two", password="three", group=self.data.group)
        self.cred.save()
        self.detail_url = reverse("api_dispatch_detail", kwargs={"resource_name": "cred", "api_name": "v1", "pk": self.cred.pk})

    def test_cant_use_expired_key(self):
        res = self.data.norm.get(self.detail_url)
        data = json.loads(res.content)
        for key, val in [("title", "one"), ("username", "two"), ("password", "three")]:
            self.assertEqual(data[key], val)

    def test_can_post_ssh_key_into_cred(self):
        self.cred.ssh_key = None
        self.cred.save()

        res = self.data.norm.get(self.detail_url)
        data = json.loads(res.content)
        assert 'ssh_key' not in data

        with open(os.path.join(ssh_keys, "1.pem")) as fle:
            res = self.data.norm.post(self.detail_url, {'ssh_key': fle})

        data = json.loads(res.content)
        with open(os.path.join(ssh_keys, "1.pem")) as fle:
            self.assertEqual(data['ssh_key'], fle.read())

        res = self.data.norm.get(self.detail_url)
        data = json.loads(res.content)
        with open(os.path.join(ssh_keys, "1.pem")) as fle:
            self.assertEqual(data['ssh_key'], fle.read())
