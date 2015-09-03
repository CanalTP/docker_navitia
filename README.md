This iincludes a complete deployment of Navitia 2 in a single Docker image, with the database, tyr (beat & workers), one kraken and jormungandr.

## Quickstart
First create the data directory: `mkdir -m 777 -p {host data directory}`. This directory will contain a single instance named 'default':
` cd {host data directory} && mkdir -m 777 default`.

Then run docker image: `docker run -d -p 8080:80 -v {host data directory}:/srv/ed/data --name navitia_simple navitia/debian8_simple`.

For a more detailed description of what you can do with Navitia docker image, see [Running an image](https://github.com/CanalTP/navitia/wiki/Navitia-in-Docker-containers#running-an-image)
