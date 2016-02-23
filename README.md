# Navitia in Docker containers

## Aim of the project
From [www.docker.com](https://www.docker.com/): Docker is an open platform for building, shipping and running distributed applications. It gives programmers, development teams and operations engineers the common toolbox they need to take advantage of the distributed and networked nature of modern applications. See also [docs.docker.com](https://docs.docker.com/). See [docs.docker.com/installation](https://docs.docker.com/installation/) for installation.

The purpose of this project is to create and manage Docker images/containers for Navitia.
What we have in mind is to have Navitia progressively deployed in a more simple and robust
way, and on any kind of platform, offering:
- Easy and fast deployment on a development platform,
- Running of complete or partial test scenarios on a development platform or on any dedicated platform,
  giving developers unprecedented flexibility to run customized tests more efficiently,
- More easy and robust deployment on staging or production platforms, especially for customers running
  their own platforms, but also for partners seeking unmanaged self deployment,
- Build automation of customized platforms (see Creation below) for creation and test of specialized versions of Navitia.
  
Docker images are architectured in a way such that updating Navitia to the latest version is as simple
as replacing old images with new ones and restarting them.
For this to be possible, all data must be kept in folder external to docker containers, accessed
via folder bindings (known to docker as 'volumes'). This feature is still under active development.

The project sources are there : https://github.com/CanalTP/docker_navitia

## Description
Navitia in docker containers can follow different configurations (named platforms in docker_navitia source).
There are currently 2 configurations of docker images:
- simple: all components and services are in a single image. This simple configuration is
  ideal for development and tests purposes.
- composed: each component fits in an image. There are 4 components (DB, Tyr, Engine, WS),
  each corresponding to an image.

The build process is different in each case:

For the simple case, we start from a target distribution image (e.g. Debian8), build a new image via a Dockerfile that declares ports and volumes, installs standard packages and configure them, then starts the services controller (currently supervisord) ; then start the fabric global deployment task on it. This results in a container with services and Navitia installed, configured and running. The final step is to stop this container and commit it, resulting in a new Docker image that can be deployed and run instantly anywhere.

For the composed case, the process is similar, except that the Docker process (build, create, start, ...) is supported by docker-compose, via the generation of a docker-compose.yml file.
  
Other configurations can be developed. This can be done by creating a new platform file, new Dockerfile 
and supervisord.conf files, then instantiating a new BuildDockerCompose object with appropriate ports, 
volumes and links before launching build process then python-fabric installation process.
   
## Naming images and containers
Images names are in the form: navitia/{distrib}_{platform}_[component].

For example, the image for the simple platform based on debian8 will bear name navitia/debian8_simple. 
The image for the component kraken on the composed platform will have name navitia/debian8_composed_kraken.

Containers names are in the form navitia_{platform}_[component]_[instance].

For example, a container for the simple platform will bear name navitia_simple. 
An image for the component kraken on the composed platform will have name navitia_composed_kraken. For future developments (see Limitations below), an additional instance field (with incremented integer values starting from 1) will be added.

## Building images
We currently use pytest as a launcher, as the process of building images and testing them is identical.
To build and test a simple container, cd to docker_navitia, then run:
`py.test -s -k test_deploy_simple`

Once built, it can be simply restarted and tested via:
`py.test -s -k test_deploy_simple --nocreate`

Then, the resulting Docker image can be created via:
`py.test -s -k test_deploy_simple --commit`

A similar process is available for the composed platform, simply replace *test_deploy_simple* with *test_deploy_composed*.

Since this build process requires to be run in a Linux environment, if you're on a different platform you can use Docker to build Docker :)

So first build the image:
`docker build -t navitia-builder .`

Then run it:
`docker run --name navitia-builder-container -d --privileged navitia-builder`

Then shell into the machine:
`docker exec -it navitia-builder-container /bin/ash`

Then start the Docker daemon:
`service docker start`

So now you can build:
`py.test -s -k test_deploy_simple --build`

When finished, you can remove it:
`docker rm -f navitia-builder-container`

## Play with Navitia images
You can check existing Navitia images on docker hub, type `docker search navitia`.

You can dowload a docker image: `docker pull navitia/debian8_simple`.

Once a Navitia image has been commited or pulled, you can run it. The detailed command must define at least the data volume mapping:
`docker run -p 8080:80 -v {host data directory}:/srv/ed/data --name navitia_simple navitia/debian8_simple`

## Limitations
The current version of this project only allows for one instance of Navitia (simple or composed) to run
on a machine (real or virtual). This comes from the fact that some resources external to docker containers (such as containers names, ports, volumes) would conflict if duplicated. Future development will allow to run multiple instances on a single machine, a use case that can be useful for Jenkins machines for example.
