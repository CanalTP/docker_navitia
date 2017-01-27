FROM debian:8

# ports
EXPOSE 22 80 85

# prepare data volumes
ENV DATA_VOLUME /srv/ed/data
ENV PG_HOME /var/lib/postgresql
RUN mkdir -m 777 -p ${DATA_VOLUME}

# systemd is removed and sysvinit is installed instead.
# As of may 2015, systemd is difficult to launch in a docker container, see http://developerblog.redhat.com/2014/05/05/running-systemd-within-docker-container/
# and if systemd is installed, some packages try to launch via systemctl (eg PostgreSQL) and fail
RUN apt-get update && apt-get install -y sysvinit-core python openssh-server sudo locales supervisor
RUN apt-get remove -y systemd
RUN apt-get install -y apache2 libapache2-mod-wsgi
RUN apt-get install -y postgresql-server-dev-all postgis
RUN apt-get install -y redis-server rabbitmq-server

# set basic Apache config
RUN mkdir /etc/apache2/conf.d
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf
RUN echo "Include conf.d/" >> /etc/apache2/apache2.conf

# fix apache2 configuration bug
RUN sed -i "s!DocumentRoot /var/www/html!DocumentRoot /var/www!g" /etc/apache2/sites-available/000-default.conf

# change redis-server conf for not daemonize (for supervisord)
RUN sed -i '/^daemonize yes/c\daemonize no' /etc/redis/redis.conf

# add user navitia, as a free sudoer (for tests and debug)
RUN useradd -m -s /bin/bash navitia && echo "navitia:navitia" | chpasswd
RUN adduser navitia sudo && adduser navitia www-data
RUN echo "navitia ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# configure SSH server
RUN mkdir /var/run/sshd
RUN mkdir -p /home/navitia/.ssh
# SSH login fix. Otherwise user is kicked off after login
RUN sed -i 's!session\s*required\s*pam_loginuid.so!session optional pam_loginuid.so!g' /etc/pam.d/sshd
COPY unsecure_key.pub /home/navitia/.ssh/authorized_keys
RUN chmod 644 /home/navitia/.ssh/authorized_keys

# set locale to French
RUN sed -i "/^# fr_FR.UTF-8 UTF-8/c\fr_FR.UTF-8 UTF-8" /etc/locale.gen
RUN locale-gen fr_FR.UTF-8

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /sbin/entrypoint.sh
RUN chmod 755 /sbin/entrypoint.sh

VOLUME ["$DATA_VOLUME", "$PG_HOME"]
CMD ["/sbin/entrypoint.sh"]
