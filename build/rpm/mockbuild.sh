#!/bin/bash
set -e

NAME=RatticWeb
SPEC=${NAME}.spec

rm -rf /tmp/mockbuild-${NAME}.*
TMPDIR=$(mktemp -d --tmpdir=/tmp mockbuild-${NAME}.XXXXXXXX)
echo 'Temp directory:' $TMPDIR
SRPMBUILDDIR=${TMPDIR}/srpmbuild
RPMBUILDDIR=${TMPDIR}/build
SRCDIR=${TMPDIR}/sources
mkdir ${SRCDIR} ${SRPMBUILDDIR} ${RPMBUILDDIR}
mkdir -p out

spectool -gf ${SPEC} -C ${SRCDIR}
mock --buildsrpm --spec ${SPEC} --sources ${SRCDIR} --resultdir ${SRPMBUILDDIR}
mock --rebuild ${SRPMBUILDDIR}/${NAME}-*.src.rpm --resultdir ${RPMBUILDDIR}
cp ${SRPMBUILDDIR}/${NAME}-*.src.rpm out/
cp ${RPMBUILDDIR}/${NAME}-*.rpm out/

rm -rf ${TMPDIR}
