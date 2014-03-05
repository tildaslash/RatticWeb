from django_nose import NoseTestSuiteRunner
from django.conf import settings


class ExcludeAppsTestSuiteRunner(NoseTestSuiteRunner):
    """Override the default django 'test' command, exclude from testing
    apps which we know will fail."""

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = settings.LOCAL_APPS
        return super(ExcludeAppsTestSuiteRunner, self).run_tests(
            test_labels, extra_tests, **kwargs)
