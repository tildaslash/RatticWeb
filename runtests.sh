#!/bin/bash

# Pretty script to run the tests included. Should be run before
# you commit anything. They get run in Travis-CI anyway, so this
# just helps you avoid looking like a fool.

lint_only=0
tests_only=0

unit_test_args=""
unit_test_command="./manage.py test"

for var in $@; do
   case $var in
      "--tests-only")
         tests_only=1
         ;;
      "--lint-only")
         lint_only=1
         ;;
      "--without-selenium")
         unit_test_command="$unit_test_command --tc=no_selenium:true"
         ;;
      "--nose-help")
         unit_test_command="$unit_test_command --help"
         tests_only=1
         ;;
      "--help")
         echo "./runtests [--tests-only] [--without-selenium] [--help] [--nose-help]"
         exit 0
         ;;
      *)
         unit_test_args="$unit_test_args $var"
         ;;
   esac
done

function runtest() {
    name="$1"
    command="$2"

    echo -n "Running $name ($command)...  "
    ENABLE_TESTS=1 $command

    if [ $? -eq 0 ]; then
        echo 'Success'
    else
        echo 'Failure'
        exit 1
   fi
}

if (( $tests_only == 0 )); then
   runtest "PEP8" "pep8 --exclude=migrations,lib,static,.ropeproject --ignore=E501,E225,E128,E124 ."
   runtest "pyflakes" "./pyflakes.sh"
fi

if (( $lint_only == 0 )); then
   runtest "Unit Tests" "$unit_test_command $unit_test_args"
fi

exit 0
