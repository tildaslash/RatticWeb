#!/bin/bash

LDAPBASE=$(mktemp --tmpdir=/tmp -d ratticldap.XXXXX)
echo ${LDAPBASE} > .ldapbase

mkdir ${LDAPBASE}/db
cp slapd.conf ${LDAPBASE}/

sed -i "s|XXX_LDAP_PID_XXX|${LDAPBASE}/slapd.pid|" ${LDAPBASE}/slapd.conf
sed -i "s|XXX_LDAP_DATA_DIR_XXX|${LDAPBASE}/db|" ${LDAPBASE}/slapd.conf

slapd -f ${LDAPBASE}/slapd.conf -h 'ldap://localhost:3389/'

