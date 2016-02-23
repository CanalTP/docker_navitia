FROM gliderlabs/alpine:3.3

WORKDIR /usr/local/navitia

RUN apk add --update \
    alpine-sdk \
    python \
    python-dev \
    py-pip \
    docker \
  && rm -rf /var/cache/apk/*

# Install openrc - see: https://github.com/gliderlabs/docker-alpine/issues/42
RUN apk update && apk add openrc &&\
# Tell openrc its running inside a container, till now that has meant LXC
    sed -i 's/#rc_sys=""/rc_sys="lxc"/g' /etc/rc.conf &&\
# Tell openrc loopback and net are already there, since docker handles the networking
    echo 'rc_provide="loopback net"' >> /etc/rc.conf &&\
# no need for loggers
    sed -i 's/^#\(rc_logger="YES"\)$/\1/' /etc/rc.conf &&\
# can't get ttys unless you run the container in privileged mode
    sed -i '/tty/d' /etc/inittab &&\
# can't set hostname since docker sets it
    sed -i 's/hostname $opts/# hostname $opts/g' /etc/init.d/hostname &&\
# can't mount tmpfs since not privileged
    sed -i 's/mount -t tmpfs/# mount -t tmpfs/g' /lib/rc/sh/init.sh &&\
# can't do cgroups
    sed -i 's/cgroup_add_service /# cgroup_add_service /g' /lib/rc/sh/openrc-run.sh

COPY ./requirements.txt /usr/local/navitia/docker_navitia/requirements.txt
RUN pip install -r /usr/local/navitia/docker_navitia/requirements.txt

RUN git clone https://github.com/CanalTP/fabric_navitia.git /usr/local/navitia/fabric_navitia
RUN pip install -r /usr/local/navitia/fabric_navitia/requirements.txt

ENV PYTHONPATH /usr/local/navitia:/usr/local/navitia/docker_navitia:/usr/local/navitia/fabric_navitia:/usr/bin/python

# RUN echo -e '#!/bin/bash\n/sbin/init && service docker start' > /usr/local/navitia/entrypoint.sh && chmod +x /usr/local/navitia/entrypoint.sh

COPY . /usr/local/navitia/docker_navitia

WORKDIR /usr/local/navitia/docker_navitia

ENTRYPOINT ["/sbin/init"]
