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

#### Create admin tenant

```bash
docker-compose exec admin /app/manage.py create_tenant
```

Use the following parameters:

- schema: public
- name: public
- domain: localhost
- is_primary: True

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

Now browse to: http://test1.pleio.local

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
brew services start dnsmasq
sudo mkdir -v /etc/resolver
sudo bash -c 'echo "nameserver 127.0.0.1" > /etc/resolver/local'
```

## Advanced

Now you have your first tenant running there are some more advanced topics:

- [File storage](#file-storage)
- [Elasticsearch](#elasticsearch)
- [Background](#background)
- [Translations](#translations)
- [Import Elgg site](elgg/README.md)

## File storage

Right now we have 2 file storage backend options:

- Swift storage
- S3 storage

They can be enabled using environment variables `SWIFT_ENABLED` and `S3_ENABLED`. Check `backend/config.py` for configuration options.

You can use them both for local development. Default we use S3.

### S3 storage local development

Install the [aws cli client](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

#### First time setup

Create s3 bucket

```bash
aws --endpoint-url=http://localhost:4572 s3 mb s3://demo-bucket
```

Make bucket public

```bash
aws --endpoint-url=http://localhost:4572 s3api put-bucket-acl --bucket demo-bucket --acl public-read
```

#### More examples

Copy existing files to bucket

```bash
aws --endpoint-url=http://localhost:4572 s3 cp support  s3://demo-bucket/test2/migrated/ --recursive
```

Add localstack to /etc/hosts to test from browser: `127.0.0.1 localstack`

### Swift storage local development

To talk with the Swift storage backend you can use swiftclient by installing it using pip:

```bash
pip install python-swiftclient
```

#### Example commands

Test connection:

```bash
swift -A http://localhost:12345/auth/v1.0 -U test:tester -K testing stat
```

Create (public) container:

```bash
swift -A http://localhost:12345/auth/v1.0 -U test:tester -K testing post -r ".r:*" backend2-dev-public
```

## Elasticsearch

We use [elasticsearch](https://www.elastic.co/) for searching.

#### Create search index

First time you have to create the search index.

```bash
docker-compose exec api python manage.py tenant_command search_index --create --schema=test1
```

#### Rebuilding search index

All tenants use the same search index. So when you want to rebuild the index for one tenant user the `--populate` argument.

```bash
docker-compose exec api python manage.py tenant_command search_index --populate --schema=test1
```

## Translations

### (re)Generate the translastions files

With this command, you will create and edit .po files. The files will be filled with strings added in de code as msgid's

```bash
docker-compose exec api python manage.py makemessages -a
```

With this command, you will compile the translation files which the application will use

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

- core.tasks.dispatch_crons, ["{period}"]
- core.tasks.dispatch_task, ["{task_name}", **"{arguments}"]
- core.tasks.send_notifications, ["{schema_name}"]
- core.tasks.send_overview, ["{schema_name}", "{overview}"]
- core.tasks.elasticsearch_recreate_indices
- core.tasks.elasticsearch_recreate_indices ["{index_name}"] 
- core.tasks.elasticsearch_rebuild_all
- core.tasks.elasticsearch_rebuild_all ["{index_name}"] 
- core.tasks.elasticsearch_rebuild, ["{schema_name}"] 
- core.tasks.elasticsearch_rebuild, ["{schema_name}","{index_name}"]
- core.tasks.elasticsearch_index_file, ["{schema_name}", "{file_guid}"]

Some example commands:

### Search index recreate all indexes after changes in documents
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_recreate_indices
```

### Search index recreate 1 index after changes in documents
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_recreate_indices --args='["blog"]'
```

### Search index populate all content for all tenants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_rebuild_all
```

### Search index populate 1 index for all tentants
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_rebuild_all --args='["blog"]'
```

### Search index populate 1 index of 1 tentant
```
docker-compose exec background celery -A backend2.celery call core.tasks.elasticsearch_rebuild_all --args='["tenant1", "blog"]'
```

#### Run the daily cron on all tenants:

```bash
docker-compose exec background celery -A backend2.celery call core.tasks.dispatch_crons --args='["daily"]'
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

## DISABLE EMAIL

Settings for disabling email configured with setting following environment variable

#### EMAIL_DISABLED

- True/False