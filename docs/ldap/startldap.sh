#!/bin/bash

LDAPBASE=$(mktemp --tmpdir=/tmp -d ratticldap.XXXXX)
echo ${LDAPBASE} > .ldapbase

mkdir ${LDAPBASE}/db
cp slapd.conf ${LDAPBASE}/
cp DB_CONFIG ${LDAPBASE}/db

sed -i "s|XXX_LDAP_PID_XXX|${LDAPBASE}/slapd.pid|" ${LDAPBASE}/slapd.conf
sed -i "s|XXX_LDAP_DATA_DIR_XXX|${LDAPBASE}/db|" ${LDAPBASE}/slapd.conf

LDAPNOINIT=yes slapd -f ${LDAPBASE}/slapd.conf -h 'ldap://localhost:3389/'

# Give LDAP a few seconds to start
sleep 3

ldapadd -x -D 'cn=manager,dc=example,dc=com' -w testpass -H 'ldap://localhost:3389/' -f initial.ldif > /dev/null
echo "LDAP Started"

