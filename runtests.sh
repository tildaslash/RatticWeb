#!/bin/bash

# Pretty script to run the tests included. Should be run before
# you commit anything. They get run in Travis-CI anyway, so this
# just helps you avoid looking like a fool. We may move the make
# this script the actual one Travis-CI runs once we confirm it works
# as expected.

function runtest() {
    name="$1"
    command="$2"

    echo -n "Running $name...  "
    output="$(mktemp)"
    $command 2>&1 > $output
    if [ $? -eq 0 ]; then
        echo 'Success'
        rm $output
    else
        echo 'Failure'
        cat $output
        rm $output
        exit 1
   fi
}

runtest "PEP8" "pep8 --exclude=migrations,lib --ignore=E501,E225,E128,E124 ."
runtest "pyflakes" "./pyflakes.sh"
runtest "Unit Tests" "./manage.py test"

exit 0
