# repo-benchmark

This repo is used to benchmark the quality of arbitrary repositories. It aims to answer the questions: - is [this repository] good compared to [other repositories]? - Is [this user] good compared to [other users]? It is like a report card for repositories and users. If you are a hiring manager, I'm willing to offer this to you as a service for a fee. If you are a developer, I'm willing to offer this to you as a service for free to learn where you can improve the professionalism of your repository.

This repo includes a CLI to pull lots of different metrics about a repository including embeddings and stores them in a database. Then, we let users compute the similarity between their repository and all surveyed repositories and find the most similar repositories. This provides a ranking via clustering, but once embeddings are computed, it can provide a **derivative** that individual users can use to determine where they need to focus their efforts to improve their repository.

## Usage of `github-to-sqlite`

The main entry point for this command is `github-to-sqlite repos DBFILE.db -r USER/REPO`. I've scraped a bunch of repos from the "awesome [foo]" lists; you can do something more scientific if you want to spend the time developing a better sampling strategy.

## Usage of `rb.py`

The main entry point is the `repo-benchmark` CLI (`rb.py`).

```bash
./rb.py --help
```

### Extract all github links from a repository README.md

```bash
./rb.py extract-links https://github.com/vinta/awesome-python > awesome_python_links.json
```

### Process all github links from a file (this will call `github-to-sqlite` for each link)

```bash
./rb.py process-links awesome_python_links.json
```

### View Surveyed Repositories

You can use `datasette` to view the surveyed repositories by running the following command:

```bash
uv run datasette serve --config datasette.yaml --template-dir templates --static assets:static github.db
```

This will serve a regular datasette instance that you can view in your browser.
Once running, you can:

- Navigate to `/github/repos` to see the customized visualization for the surveyed repositories.
- Navigate to `/-/pages/custom/your-slug-here` to see an example of a custom page. For example, try `/-/pages/custom/example`.

Note that the templates and static files are responsible for customizing the visualization of the data.
