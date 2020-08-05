This module is for importing elgg sites to backend2.

## Import

Commands for importing a elgg site:

`docker-compose exec admin python manage.py import_site --settings=elgg.import_settings`

Optional parameters:

- `--elgg <databasename>` elgg database name, will be asked when not provided
- `--schema <to_schema>` import to this schema, will be asked when not provided
- `--flush` delete data from schema before import

### Replace links

After the import you have to run the replace links command:

`docker-compose exec admin python manage.py replace_links --settings=elgg.import_settings --elgg_domain <search_domain_name>`

`--elgg_domain` should be the domain name only ie `support.pleio.nl`

Optional parameters:

- `--elgg <databasename>` elgg database name, will be asked when not provided
- `--schema <to_schema>` import to this schema, will be asked when not provided