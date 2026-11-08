#!/usr/bin/env python
import os
import sys


def main():
    # `manage.py test` — hermetik test sozlamalari (config/settings_test.py); qolgan buyruqlar — oddiy sozlamalar
    default = 'config.settings_test' if len(sys.argv) > 1 and sys.argv[1] == 'test' else 'config.settings'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', default)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
