# flapjack_api

## Rest API for Flapjack data management system

First, you need to have docker>=18.09.5 and docker-compose>=1.23.2 installed

### Clone flapjack_api's repo and start the Docker container

* git clone git@github.com:SynBioUC/flapjack_api.git

* `cd /flapjack_api`
* Install requirements:
`docker-compose build`
* (optional) Start app’s container:
`docker-compose up`

### Create database

Enter to the docker container terminal:

* `docker exec -it api bash`
* Start postgresql app:
 `psql -U guillermo -h db`
  * Password: 123456
* Create database:
 `CREATE DATABASE registry;`

### Make migrations

In a new terminal:
  `docker exec -it api bash`

You can skip the last step by quitting psql.

* Run the migrations (execute the SQL commands):
 `python manage.py migrate`
* Collect static files
 `python manage.py collectstatic`
* Quit docker’s env

### Run app

* `cd /flapjack_api`
* Start app’s container:
 `docker-compose up`
* run on:
localhost:8000