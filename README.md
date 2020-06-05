# Backend2
This repository contains the work in progress of Backend2, a brand new social engine based on [Django](https://www.djangoproject.com/) and [GraphQL](http://graphql.org/). The backend offers a pluggable and extendable interface that allows developers to easily develop their own extensions. The backend will initially be used by [Pleio](https://www.pleio.nl). The goal of this backend is to be:

- Generic
- Scalable
- Accessible
- Multi-lingual
- Modular
- Extensible

## Features
- Object versioning, including archival requirements
- Access control (read/write permissions, groups support)
- Full-text search
- OpenID connect support
- Logging (audit trail)
- Notifications
- Handling large file uploads (attachments)

This backend only provides a GraphQL interface and is probably used in conjunction with a Javascript frontend or an app.

## Setup development (through docker-compose)
Copy `.env-example` to `.env` and update the OIDC endpoint credentials you got for account.pleio-test.nl

Make sure [Docker](https://www.docker.com/) is installed. Then run the
following commands within the repository:

    `docker-compose up`

On an empty postgres database perform
- ```docker-compose exec admin /app/manage.py migrate_schemas --shared```
- ```docker-compose exec admin /app/manage.py create_tenant```
    -   schema: public
    -   name: public
    -   domain: localhost
    -   is_primary: True


Now login in the admin tool on http://localhost:8888/login

Create tenants through the admin

## GraphQL schema

This project uses a schema-first GraphQL implementation with Ariadne.

You can find the schema in `backend2/schema.graphql` it is initially synced with the backend1 graphql Schema.

It is possible to extend the basis schema using the extend directive.

You can download the backend1 graphql schema using the npm package `get-graphql-schema`. Install it using `npm -g get-graphql-schema` and run the following command:

`get-graphql-schema https://nieuw-template.pleio-test.nl/graphql > schema.graphql`

## Storage

Right now we have 2 storage backend options:

- Swift storage
- S3 storage

They can be enabled using environment variables `SWIFT_ENABLED` and `S3_ENABLED`. Check `backend/config.py` for configuration options.

### Swift storage local development

To talk with the Swift storage backend you can use swiftclient by installing it using pip:

`pip install python-swiftclient`

#### Example commands

Test connection:

`swift -A http://localhost:12345/auth/v1.0 -U test:tester -K testing stat`

Create (public) container:

`swift -A http://localhost:12345/auth/v1.0 -U test:tester -K testing post -r ".r:*" backend2-dev-public`

### S3 storage local development

Create s3 bucket:

`aws --endpoint-url=http://localhost:4572 s3 mb s3://demo-bucket`

Make bucket public:
`aws --endpoint-url=http://localhost:4572 s3api put-bucket-acl --bucket demo-bucket --acl public-read`

Add localstack to /etc/hosts to test from browser:

`127.0.0.1 localstack`

## Elasticsearch

### Build search index

`docker-compose exec api python manage.py tenant_command search_index --rebuild --schema=qw `

## Caching

To use memcache as caching service add the following environment variable. for example 127.0.0.1:11211

`MEMCACHE_HOST_PORT`

## Translations

### (re)Generate the translastions files

With this command, you will create and edit .po files. The files will be filled with strings added in de code as msgid's

`python manage.py makemessages`

With this command, you will compile the translation files which the application will use

`python manage.py comilemessages`