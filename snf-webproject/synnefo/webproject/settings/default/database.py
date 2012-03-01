# -*- coding: utf-8 -*-
#
# Database settings
####################

import os

DEFAULT_DB_PATH = '/usr/share/synnefo/'
DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql','mysql', 'sqlite3' or 'oracle'
        'ENGINE': 'sqlite3',
         # ATTENTION: This *must* be the absolute path if using sqlite3.
         # See: http://docs.djangoproject.com/en/dev/ref/settings/#name
        'NAME': os.path.join(DEFAULT_DB_PATH, 'database.sqlite'),
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        # Set to empty string for localhost. Not used with sqlite3.
        'HOST': '',
        # Set to empty string for default. Not used with sqlite3.
        'PORT': '',
    }
}

if DATABASES['default']['ENGINE'].endswith('mysql'):
    DATABASES['default']['OPTIONS'] = {
            'init_command': 'SET storage_engine=INNODB; ' +
                'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED',
    }