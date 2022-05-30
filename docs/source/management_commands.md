# Management commands

Each command can be executed by running
`docker-compose exec showroom-django python manage.py <command>`
or if running the project locally by executing `python manage.py <command>` in `src`.

To get some quick usage info on the shell, use `python manage.py help <command>`.

## `create_institution`

This command is used to create an empty institution object.

Most likely this command will only be used once, during setup. All it does is to
create an empty _ShowroomObject_ of type _institution_, with a title set, and
associated to an already existing _SourceRepository_.

The command will print the new showroom ID of this institution, which has to be used
in the setup of the _Showroom Frontend_ as well as to set a default institution for
the `initial` endpoint. See [](./install.md) for more context on how/why it is used.

### Arguments

- `repo_id` - the ID of the SourceRepository this institution should be associated with
- `title` - the title of the institution (will be slugified into its showroom ID)


## `create_source_repository`

This command is used to create a _SourceRepository_ with an API key, that can be used
to push activities and entities to _Showroom_.

When setting up _Showroom_, this is one of the first things needed to be done, once the
core system is running. Without a _SourceRepository_, no activities and no entities can
be pushed to _Showroom_. Also, no initial page request can be served.

Once a _SourceRepository_ is set up, one can also create an institution entity with
the `create_institution` command. For more context on how/why this is used
see [](./install.md).

> **Note:** Be sure to check the meaning of the parameters below. If activity media are
> not displayed in the _Showroom Frontend_, one reason could be a mis-configured
> `repo_url`.

### Arguments

Positional parameters:

- `id` - the ID for this repository, which is a self-chosen integer
- `api_key` - the key used by the repository to authenticate against _Showroom_. Be
  sure to use a strong password / random character sequence here.
- `label` - the name/label of this institution.
- `repo_url` - the repository base url, e.g. https://base.uni-ak.ac.at. Here it is
  important to note that this is not the institution's website, and also not
  necessarily the base URL to the repository itself, but the base URL by which to
  retrieve the published activities' media, that are stored in the repository.

Options:

- `-u`, `--url` - the URL of the institution (e.g. the website). Default: `repo-url`.
- `-i`, `--icon_url` - the icon URL. Default: None
- `-p`, `--label_repo` -  the name/label of this repository. Default: `label`


## `publishing_log`

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

### Arguments

- `-m`, `--mode` - the mode to use, as described above
- `-a`, `--activity-id` - if the view mode is used, this specifies the activity ID
