# Management commands

Each command can be executed by running
`docker-compose exec portfolio-django python manage.py <command>`
or if running the project locally by executing `python manage.py <command>` in `src`.

To get some quick usage info on the shell, use `python manage.py help <command>`.

## Available Commands

### `create_institution`

> TODO!

### `create_source_repository`

> TODO!

### `publishing_log`

This command is used to view and maintain the activity publishing log.

There are four modes of operation for this command:

* `stats`: view some general statistics of the current publishing log
* `view`: view the specific publishing history of a single activity
* `compress`: compress all rotated logfiles, that are not yet compressed
* `retention`: check for data retention policy and remove too old log files

If mode is not set, the statistics will be displayed by default. The `view` mode will
print all publishing info found in the available logs, in a chronological order.
The `compress` mode will apply a gzip compression on all rotated files, which have
not yet been compressed. In `retention` mode all log files are deleted, that are older
than the configured retention period.

#### Arguments

- `-m`, `--mode` - the mode to use, as described above
- `-a`, `--activity-id` - if the view mode is used, this specifies the activity ID
