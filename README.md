# Backend2
This repository contains the work in progress of Backend2, a brand new social engine based on [Django](https://www.djangoproject.com/), [GraphQL](http://graphql.org/) and [React](https://facebook.github.io/react/). The backend offers a pluggable and easily extendable interface that allows users to easily develop their own extensions. The backend will initially be used by [Pleio](https://www.pleio.nl) and [GCCollab](https://gccollab.ca). The goal of this backend is to be:

- Accessible
- Scalable
- Extensible
- Multi-lingual

## Features
- Users and profile management
- External OAuth2 / OpenID support
- Comments

## Setup
Before setup make sure you installed all the development requirements:

- Python3
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html)
- Node.js v8
- yarn
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