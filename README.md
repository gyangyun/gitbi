# gitbi

**[DEVELOPMENT IN PROGRESS]**

_Gitbi_ is a lightweight business intelligence application that reads configuration from a git repository. This design enables you to write and commit SQL queries and visualizations ([vega-lite](https://github.com/vega/vega-lite) specs) directly to git repo and have _Gitbi_ display them. Of course, if you wish to edit them via web interface, that's also possible.

Test it now with sample db and config:

```
docker run pieca/gitbi:0.4
```

See full deployment example: [ppatrzyk/gitbi-example](https://github.com/ppatrzyk/gitbi-example).

## Configuration

_Gitbi_ requires the following to run:

### Repository with saved queries

Repository needs to have the following structure:
- directories in repo root refer to databases
- files in each directory are queries/visualizations to be run against respective database
    - files ending with `.sql` are queries
    - files `<query_file_name>.json` are read as [vega-lite](https://github.com/vega/vega-lite) specs[^1]
- README.md file content will be displayed on _Gitbi_ main page

[^1]: You should pass Vega-Lite [specification](https://vega.github.io/vega-lite/docs/spec.html) without `data` field. Data will be appended automatically by gitbi based on query result.

### Environment variables

Name | Description
--- | ---
GITBI\_REPO\_DIR | Path to the repository
GITBI\_<DB\_NAME>\_CONN | Connection string
GITBI\_<DB\_NAME>\_TYPE | Database type (see below for permissible values)
GITBI\_SMTP\_USER | (Optional) SMTP user
GITBI\_SMTP\_PASS | (Optional) SMTP password
GITBI\_SMTP\_URL | (Optional) SMTP server (smtp.example.com:587)
GITBI\_SMTP\_EMAIL | (Optional) SMTP email to send from

Following database types are supported:

Type (value of GITBI\_<DB\_NAME>\_TYPE) | Connection string format (GITBI\_<DB\_NAME>\_CONN)
--- | ---
clickhouse | clickhouse://[login]:[password]@[host]:[port]/[database]
postgres | postgresql://[userspec@][hostspec][/dbname][?paramspec]
sqlite | path to db file

### Example

Assume you have repository with the following structure:

```
repo
├── db1
│   ├── query1.sql
│   ├── query2.sql
│   └── query2.sql.json
├── db2
│   ├── query3.sql
│   ├── query3.sql.json
│   ├── query4.sql
│   └── query5.sql
└── README.md
```

There are 2 databases named _db1_ and _db2_. _db1_ has 2 queries, one of them has also visualization; _db2_ has 3 queries, 1 with added visualization.

For configuration you'd need to set the following environment variables:

```
GITBI_REPO_DIR=<path_to_repo>
GITBI_DB1_CONN=<conn_str_to_db1>
GITBI_DB1_TYPE=<type_db1>
GITBI_DB2_CONN=<conn_str_to_db2>
GITBI_DB2_TYPE=<type_db2>
```

## Reports and alerts

TODO describe

## Repo setup

TODO describe options

```
git config receive.denyCurrentBranch updateInstead
```

## Development

```
# run local
GITBI_REPO_DIR="./tests/gitbi-testing" ./start_app.sh

# build image
docker build -t pieca/gitbi:<version> .
```

## Some alternatives

- if you want to generate static html reports from db queries using Python: [merkury](https://github.com/ppatrzyk/merkury)
- if you want to analyze single sqlite db: [datasette](https://github.com/simonw/datasette)
- if you want to run queries from your browser: [sqlpad](https://github.com/sqlpad/sqlpad), [chartbrew](https://github.com/chartbrew/chartbrew)
- if you want a full-blown BI solution: [metabase](https://github.com/metabase/metabase)

## Acknowledgements

Backend:
- [pygit2](https://github.com/libgit2/pygit2)
- [starlette](https://github.com/encode/starlette)

Frontend:
- [codejar](https://github.com/antonmedv/codejar)
- [highlight](https://github.com/highlightjs/highlight.js)
- [htmx](https://github.com/bigskysoftware/htmx)
- [pico](https://github.com/picocss/pico)
- [simple-datatables](https://github.com/fiduswriter/simple-datatables)
- [vega](https://github.com/vega)
