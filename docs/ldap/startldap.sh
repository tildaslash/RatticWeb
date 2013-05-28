#!/bin/bash

export LDAPNOINIT=yes

LDAPBASE=$(mktemp --tmpdir=/tmp -d ratticldap.XXXXX)

if [ -f /etc/openldap/schema/core.schema ]; then
  SCHEMABASE=/etc/openldap/schema
else
  SCHEMABASE=/etc/ldap/schema
fi

echo ${LDAPBASE} > .ldapbase

mkdir ${LDAPBASE}/db
cp slapd.conf ${LDAPBASE}/
cp DB_CONFIG ${LDAPBASE}/db

sed -i "s|XXX_LDAP_PID_XXX|${LDAPBASE}/slapd.pid|" ${LDAPBASE}/slapd.conf
sed -i "s|XXX_LDAP_DATA_DIR_XXX|${LDAPBASE}/db|" ${LDAPBASE}/slapd.conf
sed -i "s|XXX_SCHEMA_LOCATION_XXX|${SCHEMABASE}|" ${LDAPBASE}/slapd.conf

nohup slapd -d3 -f ${LDAPBASE}/slapd.conf -h 'ldap://localhost:3389/' &> ${LDAPBASE}/slapd.log &

# Give LDAP a few seconds to start
sleep 3

if [ ! -z "$DEBUG" ]; then
  cat ${LDAPBASE}/slapd.log
fi

ldapadd -x -D 'cn=manager,dc=example,dc=com' -w testpass -H 'ldap://localhost:3389/' -f initial.ldif > /dev/null
echo "LDAP Started"

