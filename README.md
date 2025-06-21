# repo-benchmark

This repo is used to benchmark the quality of arbitrary repositories. It is like a report card for repositories and users. It aims to answer the questions:

- is [this repository] good compared to [other repositories]?
- Is [this user] good compared to [other users]?

This repo includes a CLI to pull lots of different metrics about a repository including embeddings and stores them in a database. Then, we let users compute the similarity between their repository and all surveyed repositories and find the most similar repositories. This provides a ranking via clustering, but once embeddings are computed, it can provide a **derivative** that individual users can use to determine where they need to focus their efforts to improve their repository.

## Usage of `github-to-sqlite`

The main entry point for this command is `github-to-sqlite repos DBFILE.db -r USER/REPO`. I've scraped a bunch of repos from the "awesome [foo]" lists; you can do something more scientific if you want to spend the time developing a better sampling strategy.

## Usage of `rb`

The main entry point is the `repo-benchmark` CLI (`rb`). First, install:

```bash
uv pip install -e .
```

Then you can just use `rb`:

```bash
rb --help
```

### Extract all github links from a repository README.md

```bash
rb extract-links https://github.com/vinta/awesome-python > data/awesome_python_links.json
```

### Process all github links from a file (this will call `github-to-sqlite` for each link)

```bash
rb process-links awesome_python_links.json
```

### View Surveyed Repositories

You can use `datasette` to view the surveyed repositories by running the following command:

```bash
uv run datasette serve --config datasette.yaml --template-dir templates --static assets:static github.db
```

This will serve a regular datasette instance that you can view in your browser.
Once running, you can:

- Navigate to `/github/repos` to see the customized visualization for the surveyed repositories.
- Navigate to `/pages/custom/your-slug-here` to see an example of a custom page. For example, try `/pages/custom/example`.

The templates and static files are responsible for customizing the visualization of the data; this demonstrates how you can extend existing datasette pages, or add altogether new pages.

### Interacting with Datasette via the CLI

The `rb` tool includes a `datasette` command group for interacting with a running Datasette instance's [JSON Write API](https://docs.datasette.io/en/latest/json_api.html#the-json-write-api). This allows for programmatic creation and modification of data.

**Configuration**

Before using these commands, you'll need to configure your environment. Copy the `.env.example` file to `.env` and fill in the required values:

```bash
cp .env.example .env
```

You will need to set:

- `DATASETTE_ENDPOINT`: The base URL of your Datasette instance (e.g., `http://127.0.0.1:8001`).
- `DATASETTE_AUTH_TOKEN`: An API token with appropriate permissions.

You can generate a transient token for a user by setting `DATASETTE_USERNAME` and `DATASETTE_SECRET` in your `.env` file and running:

```bash
rb datasette get-auth-token
```

For a persistent API token suitable for scripts, it's recommended to use the `datasette-auth-tokens` plugin.

**Example: Creating a Table**

You can create a new table by providing a JSON file that defines its schema.

First, create a JSON file (e.g., `payload.json`):

```json
{
  "table": "my_new_table",
  "columns": [
    {
      "name": "id",
      "type": "integer"
    },
    {
      "name": "name",
      "type": "text"
    }
  ],
  "pk": "id"
}
```

Then, run the `create-table` command:

```bash
rb datasette create-table --database github --payload-file payload.json
```

For more details on each command and the expected payload structures, run the command with the `--help` flag, for example: `rb datasette insert-rows --help`.
