from datetime import timedelta
from ConfigParser import RawConfigParser, NoOptionError

config = RawConfigParser()
config.read(['conf/defaults.cfg', 'conf/local.cfg', '/etc/ratticweb.cfg'])


def confget(section, var, default):
    try:
        return config.get(section, var)
    except NoOptionError:
        return default


def confgetbool(section, var, default):
    try:
        return config.getboolean(section, var)
    except NoOptionError:
        return default

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# A tuple of callables that are used to populate the context in
# RequestContext. These callables take a request object as their
# argument and return a dictionary of items to be merged into
# the context.
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'ratticweb.context_processors.base_template_reqs',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'account.middleware.StrictAuthentication',
    'account.middleware.PasswordExpirer',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ratticweb.urls'

# Urls
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ratticweb.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

LOCAL_APPS = (
    # Sub apps
    'ratticweb',
    'cred',
    'account',
    'staff',
    'help',
)

INSTALLED_APPS = (
    # External apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'south',
    'tastypie',
) + LOCAL_APPS

TEST_RUNNER = 'tests.runner.ExcludeAppsTestSuiteRunner'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

#######################
# Custom app settings #
#######################

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
PUBLIC_HELP_WIKI_BASE = 'https://github.com/tildaslash/RatticWeb/wiki/'
CRED_ICON_JSON = 'db/icons.json'
CRED_ICON_SPRITE = 'rattic/img/sprite.png'
CRED_ICON_BASEDIR = 'rattic/img/credicons'
CRED_ICON_CLEAR = 'rattic/img/clear.gif'

LOGIN_REDIRECT_URL = "/cred/list/"
LOGIN_URL = "/account/login/"

AUTH_LDAP_USER_ATTR_MAP = {"email": "mail", }
AUTH_LDAP_USER_FLAGS_BY_GROUP = {}
AUTH_LDAP_MIRROR_GROUPS=True

###############################
# External environment config #
###############################

# [ratticweb]
DEBUG = config.getboolean('ratticweb', 'debug')
TEMPLATE_DEBUG = DEBUG
TIME_ZONE = config.get('ratticweb', 'timezone')
SECRET_KEY = config.get('ratticweb', 'secretkey')

try:
    PASSWORD_EXPIRY = timedelta(days=config.getint('ratticweb', 'passwordexpirydays'))
except NoOptionError:
    PASSWORD_EXPIRY = False

# [filepaths]
HELP_SYSTEM_FILES = confget('filepaths', 'help', False)
MEDIA_ROOT = confget('filepaths', 'media', '')
STATIC_ROOT = confget('filepaths', 'static', '')

# [database]
DATABASES = {
    'default': {
        'ENGINE': confget('database', 'engine', 'django.db.backends.sqlite3'),
        'NAME': confget('database', 'name', 'db/ratticweb'),
        'USER': confget('database', 'user', ''),
        'PASSWORD': confget('database', 'password', ''),
        'HOST': confget('database', 'host', ''),
        'PORT': confget('database', 'port', ''),
    }
}

# [email]
# SMTP Mail Opts
EMAIL_BACKEND = confget('email', 'backend', 'django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = confget('email', 'filepath', '/tmp/ratticweb-messages')
EMAIL_HOST = confget('email', 'host', '')
EMAIL_PORT = confget('email', 'port', '')
EMAIL_HOST_USER = confget('email', 'user', '')
EMAIL_HOST_PASSWORD = confget('email', 'password', '')

EMAIL_USE_TLS = confgetbool('email', 'usetls', False)

# [ldap]
LDAP_ENABLED = 'ldap' in config.sections()

if LDAP_ENABLED:
    # Add LDAP to the auth modules
    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

    # Get config options for LDAP
    AUTH_LDAP_SERVER_URI = config.get('ldap', 'uri')
    AUTH_LDAP_BIND_DN = confget('ldap', 'binddn', '')
    AUTH_LDAP_BIND_PASSWORD = confget('ldap', 'bindpw', '')
    AUTH_LDAP_USER_FLAGS_BY_GROUP['is_staff'] = confget('ldap', 'staff', '')

    # Searching for things
    AUTH_LDAP_USER_SEARCH = LDAPSearch(config.get('ldap', 'userbase'), ldap.SCOPE_SUBTREE, config.get('ldap', 'userfilter'))
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(config.get('ldap', 'groupbase'), ldap.SCOPE_SUBTREE, config.get('ldap', 'groupfilter'))

    # Groups type
    AUTH_LDAP_GROUP_TYPE = getattr(__import__('django_auth_ldap').config, config.get('ldap', 'grouptype'))()

    # Booleans
    AUTH_LDAP_ALLOW_PASSWORD_CHANGE = confgetbool('ldap', 'pwchange', False)
    AUTH_LDAP_GLOBAL_OPTIONS = {
        ldap.OPT_X_TLS_REQUIRE_CERT: confgetbool('ldap', 'requirecert', True),
        ldap.OPT_REFERRALS: confgetbool('ldap', 'referrals', False),
    }
