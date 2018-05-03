# Design
The goal of this backend is to be:

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

## Software components
- [Django](https://www.djangoproject.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [GraphQL](http://graphql.org/)
- [Elasticsearch](https://www.elastic.co/)

The backend only provides a GraphQL endpoint and is therefore normally used in conjunction with a Javacript frontend or app.