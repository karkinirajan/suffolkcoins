#!/usr/bin/env python
"""Django's command-line utility."""

import os
import sys


def main():
    from dotenv import load_dotenv

    load_dotenv()  # a local .env, for development
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "suffolkcoins.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
