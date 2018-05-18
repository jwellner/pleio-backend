# Backend2
This repository contains the work in progress of Backend2, a brand new social engine based on [Django](https://www.djangoproject.com/) and [GraphQL](http://graphql.org/). The backend offers a pluggable and extendable interface that allows developers to easily develop their own extensions. The backend will initially be used by [Pleio](https://www.pleio.nl) and [GCCollab](https://gccollab.ca). The goal of this backend is to be:

- Generic
- Scalable
- Accessible
- Multi-lingual
- Modular
- Extensible

## Features
- Object versioning
- Access control (read/write permissions, groups support)
- Full-text search
- OpenID connect support
- Logging (audit trail)
- Notifications
- Handling large file uploads (attachments)

This backend only provides a GraphQL interface and is probably used in conjunction with a Javascript frontend or an app.

## Dependencies
The following projects could be interesting to provide some functionality:

- django-revisions or django-simple-history
- django-channels

## Setup
Before setup make sure you installed all the development requirements:

- Python3
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html)
- PostgreSQL with a new database "backend2"

## Installation
Create a new Python 3 virtual environment with

    mkvirtualenv backend2 --python=/usr/local/bin/python3

Then install dependencies with

    pip3 install -r requirements.txt

Now copy backend/config.example.py to backend/config.py and adjust your settings accordingly. Finally initialize the database by running the command:

    python manage.py migrate

To create a new superuser run:

    python manage.py createsuperuser

and follow the steps.

## Run the project
To run the project in testing mode, use this command:

    python manage.py runserver

For more information on setting up a production environment or how to develop on Backend2 consult the [documentation](/docs).
