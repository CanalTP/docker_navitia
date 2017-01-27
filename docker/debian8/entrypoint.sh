#!/bin/bash
set -e

# inspired from https://github.com/sameersbn/docker-postgresql

export PG_VERSION=9.4
export PG_USER=postgres
export PG_HOME=/var/lib/postgresql
export PG_RUNDIR=/var/run/postgresql
export PG_LOGDIR=/var/log/postgresql
export PG_BINDIR="/usr/lib/postgresql/${PG_VERSION}/bin"
export PG_DATADIR="${PG_HOME}/${PG_VERSION}/main"


if [[ ! -d ${PG_RUNDIR}/${PG_VERSION}-main.pg_stat_tmp ]]; then
    mkdir -p ${PG_RUNDIR} ${PG_RUNDIR}/${PG_VERSION}-main.pg_stat_tmp
    chmod -R 0755 ${PG_RUNDIR}
    chmod g+s ${PG_RUNDIR}
    chown -R ${PG_USER}:${PG_USER} ${PG_RUNDIR}
fi

if [[ ! -d ${PG_DATADIR} ]]; then
    echo "Initializing database..."
    sudo -Hu ${PG_USER} ${PG_BINDIR}/initdb --pgdata=${PG_DATADIR} \
      --username=${PG_USER} --encoding=unicode --auth=trust >/dev/null
fi
sudo chmod -R 0700 ${PG_HOME}
sudo chown -R ${PG_USER}:${PG_USER} ${PG_HOME}

echo "Starting supervisord..."
/usr/bin/supervisord
