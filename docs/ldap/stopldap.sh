#!/bin/bash

if [ -f .ldapbase ]; then
    LDAPBASE=$(cat .ldapbase)
    PID=$(cat ${LDAPBASE}/slapd.pid)
    kill -INT ${PID}
    
    rm -rf ${LDAPBASE}
    rm .ldapbase
fi
