The code for backend2

## Table of contents

- [Project overview](#project-overview)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Advanced](#advanced)
    - [File storage](#file-storage)
    - [Elasticsearch](#elasticsearch)
    - [Background](#background)
    - [Translations](#translations)
    - [Import Elgg site](elgg/README.md)
    - [Elastic APM](#elastic-apm)

## Project overview

This repository contains the work in progress of Backend2, a brand new social engine based on [Django](https://www.djangoproject.com/) and [GraphQL](http://graphql.org/). The backend will initially be used by [Pleio](https://www.pleio.nl). The goal of this backend is to be:

- Generic
- Scalable
- Accessible
- Multi-lingual
- Modular
- Extensible

#### Features

- Object versioning, including archival requirements (in progress)
- Access control (read/write permissions, groups support)
- Full-text search
- OpenID connect support
- Logging (audit trail) (in progress)
- Notifications
- Handling large file uploads

## Requirements

- [docker](https://docs.docker.com/desktop/)
- Local DNS for tenants (for example [Dnsmasq](#dnsmasq) for mac)

## Getting started

How to get started with your development environment.

Copy `.env-example` to `.env` and update the OIDC endpoint credentials you got for account.pleio-test.nl

Make sure [Docker](https://www.docker.com/) is installed. Then run the following commands within the repository:

```bash
docker-compose pull
docker-compose up
```

If you started your development environment for the first time execute the following commands:

#### Migrate schemas

```bash
docker-compose exec admin /app/manage.py migrate_schemas --shared
```

This is a command that also executes when doing docker-compose up. If that was successful, you should see that there are no migrations to run.

#### Create admin tenant

```bash
docker-compose exec admin /app/manage.py create_tenant --noinput --schema_name=public --name=public --domain-domain=localhost
```

#### Create superuser for admin

```bash
docker-compose exec admin /app/manage.py createsuperuser
```

#### Create your first tenant

- Login on http://localhost:8888/admin/
- Add client (example):
    - Schema name: `test1`
    - Name: `My first test client`
    - Domain: `test1.pleio.local`
    - elgg-database can be empty here

#### Edit hosts file
To be able to reach `.local` urls add the following line to the hosts file:

`127.0.0.1 test1.pleio.local`

On Windows you can find your hosts file here: 

`C:/Windows/System32/drivers/etc/hosts`

On OSX enter the following in Terminal: 

```
sudo nano /etc/hosts
```

Now browse to: http://test1.pleio.local:8000

#### Run with a local frontend

To run a local frontend with backend2 it is needed to first run the frontend (`yarn start`) and then restart the backend. At launch it will check whether a local frontend is running.

When opening http://test1.pleio.local:8000 you should see your local front-end being used. This frontend is now loaded from `localhost:9001`. This can be checked by inspecting the network activity. The CSS and JS should be loaded from `localhost:9001`.

#### Cleanup and start over

When you want to start with a clean installations run the following command to delete all volumes:

```bash
docker-compose down -v
docker-compose rm -f
docker-compose pull
```

## Dnsmasq

How to setup Dnsmasq for `*.local` domains on a mac:

```bash
brew install dnsmasq
echo 'address=/.local/127.0.0.1' > $(brew --prefix)/etc/dnsmasq.conf
sudo brew services start dnsmasq
sudo mkdir -v /etc/resolver
sudo bash -c 'echo "nameserver 127.0.0.1" > /etc/resolver/local'
```

## Advanced

Now you have your first tenant running there are some more advanced topics:

- [Elasticsearch](#elasticsearch)
- [Background](#background)
- [Translations](#translations)
- [Import Elgg site](elgg/README.md)

## Elasticsearch

We use [elasticsearch](https://www.elastic.co/) for searching.

#### Create search index

First time you have to create the search index.

```bash
docker-compose exec api python manage.py tenant_command search_index --create --schema=test1
```

#### Rebuilding search index

Rebuilding the index is required when the schema for a model changes at document.py.
Rebuilding the index causes the search functionality to be unavailable until all data is indexed again.

```bash
# Rebuild for all (Notice: search will be unavailable until an index command is completed)
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_recreate_indices
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_rebuild_all

# Rebuild for one (Notice: all data is removed first)
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_rebuild_for_tenant --args='["test1"]'
```

When there has been a bug that caused the content to be indexed incorrectly it is possible to index all data without search engine down-time.

```bash
# Build for all (search will be available all the time)
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_index_data_for_all

# Build for one (search will be available all the time)
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_index_data_for_tenant --args='["test1"]'
```

## Translations

### (re)Generate the translastions files

With this command, you will create and edit .po files. The files will be filled with strings added in de code as msgid's

```bash
docker-compose exec api python manage.py makemessages -a
```

With this command, you will automatic translate fuzzy and missing strings in .po files. See https://github.com/ankitpopli1891/django-autotranslate/ for more usage options. A DEEPL token in your environment is necesarry.

```bash
docker-compose exec api python manage.py translate_messages --untranslated
```



With this command, you will compile the translation files which the application will use. To activate locally, restart the api container.

```bash
docker-compose exec api python manage.py compilemessages
```

## Background

Pleio uses [Celery](http://www.celeryproject.org/) for running background tasks.

### Manual call commands

To manually call commands from the CLI, use:

```bash
docker-compose exec background celery -A backend2.celery call {taskname} --args='{args}'
```

Possible tasknames and arguments:

- core.tasks.cronjobs.dispatch_hourly_cron
- core.tasks.cronjobs.dispatch_daily_cron
- core.tasks.cronjobs.dispatch_weekly_cron
- core.tasks.cronjobs.dispatch_monthly_cron
- core.tasks.cronjobs.dispatch_task, ["{task_name}", **"{arguments}"]
- core.tasks.notification_tasks.send_notifications, ["{schema_name}"]
- core.tasks.cronjobs.send_overview, ["{schema_name}", "{overview}"]
- core.tasks.elasticsearch_tasks.elasticsearch_recreate_indices
- core.tasks.elasticsearch_tasks.elasticsearch_recreate_indices ["{index_name}"]
- core.tasks.elasticsearch_tasks.elasticsearch_rebuild_all
- core.tasks.elasticsearch_tasks.elasticsearch_rebuild_all ["{index_name}"]
- core.tasks.elasticsearch_tasks.elasticsearch_rebuild, ["{schema_name}"]
- core.tasks.elasticsearch_tasks.elasticsearch_rebuild, ["{schema_name}","{index_name}"]

Some example commands:

### Search index recreate all indexes after changes in documents
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_recreate_indices
```

### Search index recreate 1 index after changes in documents
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_recreate_indices --args='["blog"]'
```

### Search index populate all content for all tenants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_index_data_for_all
```

### Search index populate 1 index for all tentants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_index_data_for_all --args='["blog"]'
```

### Search index populate 1 index of 1 tentant
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_index_data_for_tenant --args='["tenant1", "blog"]'
```

### Search index repopulate all content for all tenants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_rebuild_all
```

### Search index repopulate 1 index for all tentants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_rebuild_all --args='["blog"]'
```

### Search index repopulate 1 index of 1 tentant
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_tasks.elasticsearch_rebuild_for_tenant --args='["tenant1", "blog"]'
```

#### Run the daily cron on all tenants:

```bash
docker-compose exec background celery -A backend2.celery call core.tasks.cronjobs.dispatch_daily_cron
```

#### Report about inconsistent TAG_CATEGORIES:

```bash
docker-compose exec background celery -A backend2.celery call core.tasks.reporting.report_is_tag_categories_consistent --args='["erlend@pleio.nl"]'
```

## Elastic APM

If you want to monitor your application with [APM from Elastic](https://www.elastic.co/apm)

Set following environment variables (you need a running APM server)

#### APM_ENABLED

- True/False

#### APM_SERVICE_NAME

- Set required service name.
- Allowed characters:
- a-z, A-Z, 0-9, -, _, and space

#### APM_TOKEN

- Use if APM Server requires a token

#### APM_SERVER_URL

- Set custom APM Server URL (
- default: http://localhost:8200)

You can also run AMP in locally with docker-compose:

```bash
docker-compose -f docker-compose.yml -f docker-compose.apm.yml up
```

## EMAIL

Locally `mailcatcher` should be installed. At `http://localhost:1080` you can view the emails send by `pleio.local`.

Links from an email have to be adjusted manually to work locally by removing the `s` from `https` and adding the portnumber `:8000`.
So for instance, `https://test1.pleio.local/events` should become `http://test1.pleio.local:8000/events`.

### DISABLE EMAIL

Settings for disabling email configured with setting following environment variable

#### EMAIL_DISABLED

- True/False
