# encoding: utf-8

# Usage   : "py.test -s tests [-k test_case] [--option]" from within folder fabric_navitia
# Example : py.test -s -k test_deploy_two --commit

from __future__ import unicode_literals, print_function
import os
import sys
import requests
import time
sys.path.insert(1, os.path.abspath(os.path.join(__file__, '..', '..')))

from fabric import api, context_managers

from docker_navitia.docker_navitia import ROOT, BuildDockerSimple, BuildDockerCompose, find_image, find_container
from fabfile import utils

HOST_DATA_FOLDER = os.path.join(ROOT, 'data')
GUEST_DATA_FOLDER = '/srv/ed/data'
HOST_ZMQ_FOLDER = os.path.join(ROOT, 'zmq')
GUEST_ZMQ_FOLDER = api.env.kraken_basedir
DATA_FILE = os.path.join(ROOT, 'fixtures/data.zip')
MAPPED_HTTP_PORT = 8082
NAVITIA_URL = 'http://localhost:{}/navitia'.format(MAPPED_HTTP_PORT)

if not os.path.isdir(HOST_DATA_FOLDER):
    os.mkdir(HOST_DATA_FOLDER)


def split_output(out):
    return out.split(r'\n' if r'\n' in out else '\n')


def check_contains(out, elements):
    """ Checks that all strings of elements are found in the same item of out
    :param out: list of strings
    :param elements: string or list of string
    :return: True if found
    """
    out = split_output(out)
    if isinstance(elements, basestring):
        head = elements
        tail = []
    else:
        head = elements[0]
        tail = elements[1:]
    for o in out:
        if head in o:
            if all(e in o for e in tail):
                return True


def test_and_launch(ps_out, required, host=None, service=None, delay=30, retry=2):
    # TODO refactor to overcome the SSH problem with respect to "service start"
    # see: https://github.com/fabric/fabric/issues/395
    if check_contains(ps_out, required):
        return
    if service:
        while retry:
            with context_managers.settings(host_string=host):
                utils.start_or_stop_with_delay(service, delay * 1000, 1000, only_once=True)
            retry -= 1
    else:
        assert False, str(required)


class TestDeploy(object):
    def check_tyr(self, out, launch=False):
        # TODO remove postgresql
        # TODO add wsgi
        host = api.env.roledefs['tyr'][0]
        test_and_launch(out, '/usr/bin/redis-server 127.0.0.1:6379', host, launch and 'redis-server')
        test_and_launch(out, '/bin/sh /usr/sbin/rabbitmq-server', host, launch and 'rabbitmq-server')
        test_and_launch(out, ['/usr/bin/python', 'celery', 'worker',
                              '-A tyr.tasks --events --pidfile=/tmp/tyr_worker.pid'],
                        host, launch and 'tyr_worker', retry=2)
        test_and_launch(out, ['/usr/bin/python', 'celery', 'beat', '-A tyr.tasks',
                              '--gid=www-data', '--pidfile=/tmp/tyr_beat.pid'],
                        host, launch and 'tyr_beat')
        assert '/usr/lib/erlang/erts-6.2/bin/beam.smp' in out
        assert '/usr/lib/erlang/erts-6.2/bin/epmd -daemon' in out
        assert 'inet_gethost 4' in out

    def check_jormun(self, out, launch=False):
        host = api.env.roledefs['ws'][0]
        test_and_launch(out, '/usr/bin/redis-server 127.0.0.1:6379', host, launch and 'redis-server')
        test_and_launch(out, '/usr/sbin/apache2 -k start', host, launch and 'apache2')
        assert '(wsgi:jormungandr -k start' in out

    def check_db(self, out, launch=False):
        host = api.env.roledefs['db'][0]
        test_and_launch(out, '/usr/lib/postgresql/9.4/bin/postgres -D /var/lib/postgresql/9.4/main -c '
                             'config_file=/etc/postgresql/9.4/main/postgresql.conf',
                        host, launch and 'postgresql')
        assert 'postgres: checkpointer process' in out
        assert 'postgres: writer process' in out
        assert 'postgres: wal writer process' in out
        assert 'postgres: autovacuum launcher process' in out
        assert 'postgres: stats collector process' in out
        assert 'postgres: jormungandr jormungandr' in out

    def check_kraken(self, out, launch=False):
        host = api.env.roledefs['eng'][0]
        test_and_launch(out, '/usr/bin/redis-server 127.0.0.1:6379', host, launch and 'redis-server')
        test_and_launch(out, '/usr/sbin/apache2 -k start', host, launch and 'apache2')
        test_and_launch(out, '/srv/kraken/default/kraken', host, launch and 'kraken_default')
        assert '(wsgi:monitor-kra -k start' in out

    def check_processes(self, out, launch=False):
        if isinstance(out, dict):
            self.check_db(out['ed'], launch)
            self.check_tyr(out['tyr'], launch)
            self.check_jormun(out['jormun'], launch)
            self.check_kraken(out['kraken'], launch)
        else:
            self.check_db(out, launch)
            self.check_tyr(out, launch)
            self.check_kraken(out, launch)
            self.check_jormun(out, launch)

    def check_processes_lite(self, out):
        """ Use this to check processes on Jenkins because output is truncated
        """
        test_and_launch(out, '/usr/lib/postgresql/9.4/bin/postgres -D')
        test_and_launch(out, '/usr/bin/redis-server 127.0.0.1:6379')
        test_and_launch(out, '/bin/sh /usr/sbin/rabbitmq-server')
        test_and_launch(out, '/usr/sbin/apache2 -k start -DFOREGROUND')
        test_and_launch(out, '/srv/kraken/default/kraken')
        test_and_launch(out, '/usr/bin/python /usr/local/bin/celery --uid=www-data')
        test_and_launch(out, '/usr/bin/python -m celery worker -A tyr.tasks --event')
        test_and_launch(out, 'sh -c /usr/lib/rabbitmq/bin/rabbitmq-server')
        test_and_launch(out, '/usr/lib/erlang/erts-6.2/bin/beam.smp -W w -K true -A')
        test_and_launch(out, '(wsgi:jormungandr -k start -DFOREGROUND')
        test_and_launch(out, '(wsgi:monitor-kra -k start -DFOREGROUND')
        test_and_launch(out, '/usr/sbin/apache2 -k start -DFOREGROUND')
        test_and_launch(out, '/usr/lib/erlang/erts-6.2/bin/epmd -daemon')
        test_and_launch(out, 'inet_gethost 4')
        test_and_launch(out, 'postgres: checkpointer process')
        test_and_launch(out, 'postgres: writer process')
        test_and_launch(out, 'postgres: wal writer process')
        test_and_launch(out, 'postgres: autovacuum launcher process')
        test_and_launch(out, 'postgres: stats collector process')
        test_and_launch(out, 'postgres: jormungandr jormungandr')

    def deploy_simple(self):
        return BuildDockerSimple(volumes=[HOST_DATA_FOLDER + ':' + GUEST_DATA_FOLDER],
                                 ports=['{}:80'.format(MAPPED_HTTP_PORT)])

    def deploy_composed(self):
        return BuildDockerCompose(). \
            add_image('ed', ports=[5432]). \
            add_image('tyr', links=['ed'], ports=[5672], volumes=[HOST_DATA_FOLDER + ':' + GUEST_DATA_FOLDER]). \
            add_image('kraken', links=['tyr', 'ed'],
                      volumes=[HOST_DATA_FOLDER + ':' + GUEST_DATA_FOLDER, HOST_ZMQ_FOLDER + ':' + GUEST_ZMQ_FOLDER]). \
            add_image('jormun', links=['ed'], ports=['{}:80'.format(MAPPED_HTTP_PORT)],
                      volumes=[HOST_ZMQ_FOLDER + ':' + GUEST_ZMQ_FOLDER])

    def test_deploy_old(self, commit):
        # deprecated
        n = self.deploy_simple()
        assert n.image_name == 'navitia/debian8'
        assert n.container_name == 'navitia_simple'
        n.build()
        image = find_image(name=n.image_name)
        assert isinstance(image, dict)
        n.create()
        container = find_container(n.container_name)
        assert isinstance(container, dict)
        n.start()
        container = find_container(n.container_name, ignore_state=False)
        assert isinstance(container, dict)
        n.set_platform().execute()
        n.run('ps ax')
        self.check_processes(n.output)
        n.run('id')
        assert 'uid=1000(git) gid=1000(git) groups=1000(git),27(sudo),33(www-data)' in n.output
        assert requests.get('http://%s/navitia' % n.inspect()).status_code == 200
        assert requests.get('http://localhost:{}/navitia').status_code == 200
        n.stop().start().set_platform().execute('restart_all')
        n.run('ps ax')
        self.check_processes(n.output)
        assert requests.get('http://%s/navitia' % n.inspect()).status_code == 200
        n.run('chmod a+w /var/log/tyr/default.log', sudo=True)
        n.run('rm -f %s/default/data.nav.lz4' % GUEST_DATA_FOLDER)
        n.put(DATA_FILE, GUEST_DATA_FOLDER + '/default', sudo=True)
        time.sleep(30)
        n.run('ls %s/default' % GUEST_DATA_FOLDER)
        assert 'data.nav.lz4' in n.output
        if commit:
            n.stop().commit()

    def test_deploy_composed(self, nobuild, nocreate, norestart):
        n = self.deploy_composed()
        assert n.images['tyr'].image_name == 'navitia/debian8_tyr'
        assert n.images['tyr'].container_name == 'navitia_composed_tyr'
        if norestart:
            n.stop().start()
            time.sleep(10)
        elif nocreate:
            n.stop().start()
            time.sleep(10)
            n.execute('restart_all')
            time.sleep(2)
        elif nobuild:
            n.stop().rm().up()
            n.set_platform().execute()
            time.sleep(2)
        else:
            n.stop().rm().destroy()
            n.build()
            n.up().set_platform()
            n.execute()
            time.sleep(2)
        print(n.get_host())
        n.run('ps ax')
        # often, some processes are not launched, so we check them all
        self.check_processes(n.output, launch=True)
        n.run('ps ax')
        self.check_processes(n.output)
        assert requests.get('http://%s/navitia' % n.images['jormun'].inspect()).status_code == 200

    def test_deploy_simple(self, nobuild, nofabric, nocreate, commit):
        n = self.deploy_simple()
        if commit:
            print('Committing image')
            n.start().clean_image().stop().commit()
            return
        elif nocreate:
            print('Starting image, no create')
            n.stop().start()
        elif nofabric:
            print('Creating container, no build')
            # n.image_name += '_simple'
            n.stop().remove().create().start()
            return
        elif nobuild:
            print('Creating image via fabric, no build')
            n.stop().start()
            time.sleep(3)
            n.execute()
            n.run('chmod a+wr /var/log/tyr/default.log', sudo=True)
        else:
            print('Building image')
            n.stop().remove().destroy()
            n.build()
            return
        print(n.get_host())
        # we have to wait a while for tyr_beat to establish the connection
        # to the jormungandr db
        time.sleep(60)
        n.run('ps ax')
        self.check_processes(n.output)
        assert requests.get(NAVITIA_URL).status_code == 200

    def test_run_simple(self):
        n = self.deploy_simple()
        # suppose base image (navitia/debian8) is already built
        n.stop().remove().create().start()
        time.sleep(3)
        n.execute()
        n.run('chmod a+wr /var/log/tyr/default.log', sudo=True)
        n.run('chmod -R a+w {}'.format(GUEST_DATA_FOLDER), sudo=True)
        time.sleep(60)
        n.run('ps ax')
        for x in split_output(n.output):
            print(x)
        self.check_processes_lite(n.output)
        assert requests.get(NAVITIA_URL).status_code == 200
        n.stop()
