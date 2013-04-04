#!/bin/bash

find . -name '*.py' | egrep -v '^./lib/' | egrep -v '^./\w*/migrations/' | egrep -v './ratticweb/(local_)?settings.py' | xargs pyflakes
