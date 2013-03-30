from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

import tempfile
import os

class HelpTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.mkdtemp()
        self.homefile = os.path.join(self.tmpdir, 'Home.md')
        self.testfile = os.path.join(self.tmpdir, 'Test.md')
        with open(self.homefile, 'w') as f:
            f.write("# Heading 1")
        with open(self.testfile, 'w') as f:
            f.write("[[Test Link]]")

    def tearDown(self):
        os.unlink(self.homefile)
        os.unlink(self.testfile)
        os.rmdir(self.tmpdir)

    def test_help_home(self):
        with self.settings(HELP_SYSTEM_FILES=self.tmpdir):
            resp = self.client.get(reverse('help.views.home'))
            self.assertContains(resp, "<h1 id=\"heading-1\">Heading 1</h1>",
                    html=True, count=1)
            self.assertEqual(resp.context['file'], self.homefile)
            self.assertTemplateUsed(resp, 'help_markdown.html')

    def test_help_markdown(self):
        with self.settings(HELP_SYSTEM_FILES=self.tmpdir):
            resp = self.client.get(reverse('help.views.markdown', args=('Test',)))
            self.assertContains(resp, "<p><a class=\"wikilink\" href=\"/help/Test_Link/\">Test Link</a></p>",
                    html=True, count=1)
            self.assertEqual(resp.context['file'], self.testfile)
            self.assertTemplateUsed(resp, 'help_markdown.html')

            resp = self.client.get(reverse('help.views.markdown',
                args=('NonExistantdfgdfgdfgd',)))
            self.assertEqual(resp.status_code, 404)
            self.assertTemplateNotUsed(resp, 'help_markdown.html')

class HelpOffTests(TestCase):
    def test_helpoff(self):
        client = Client()
        with self.settings(HELP_SYSTEM_FILES=False):
            resp = client.get(reverse('help.views.home'))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, 'help_nohelp.html')
            self.assertTemplateNotUsed(resp, 'help_markdown.html')
