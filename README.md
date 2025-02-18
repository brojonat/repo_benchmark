# repo-benchmark

This repo is used to benchmark the quality of arbitrary repositories. It aims to answer the questions: - is [this repository] good compared to [other repositories]? - Is [this user] good compared to [other users]? It is like a report card for repositories and users. If you are a hiring manager, I'm willing to offer this to you as a service for a fee. If you are a developer, I'm willing to offer this to you as a service for free to learn where you can improve the professionalism of your repository. Either way, contact me at [brojonat@gmail.com](mailto:brojonat@gmail.com) and let's talk.

This repo includes a CLI to pull lots of different metrics about a repository including embeddings and stores them in a database. Then, we let users compute the similarity between their repository and all surveyed repositories and find the most similar repositories. This provides a ranking via clustering, but it also provides a **derivative** that individual users can use to determine where they need to focus their efforts to improve their repository.

Now, embeddings are expensive to compute, so we'll punt on that for now, but in principle we can fork the github-to-sqlite project and add a plugin that computes the embeddings and stores them in the database. For now, we'll just use the `github-to-sqlite` CLI to pull the data and then develop a product that uses the `repo-benchmark` CLI (`rb.py`) to compare an arbitrary repository to the surveyed repositories. The "value" is we're mapping the mass function of repositories in a high-dimensional space and then we can use clustering to find the most similar repositories. Some canonical questions we can ask are:

- What are the most similar repositories to this one?
- What is the fraction of repositories that have between 70 and 75 star?
- What is the fraction of users that have between 10 and 20 followers?
- What are the most similar repositories to this one in a different category?

## TODO

- [ ] Add a `repo-benchmark inspect` command that shows a detailed report of a repository.
- [ ] Add a `repo-benchmark compare` command that shows a detailed report of a repository.
- [ ] Add a `repo-benchmark survey` command that fetches details of a repository.

Here the details of the data structure:

- [ ] Everything yoinked by `github-to-sqlite`
- [ ] Embeddings
- [ ] The current datetime
- [ ] The current version of the tool responsible for computing the data.

This way we can build up the dataset over time. As a rule, the data will be pulled with `github-to-sqlite` and then we'll use this tool to compute the embeddings and other metrics. This may require some custom code, but it shouldn't be too difficult and we could get a our own plugin or notable feature PR out of it. We may need to consider how to maintain our own custom implementation of `github-to-sqlite` or if we should just use the `github-to-sqlite` CLI to pull the data and then use this tool to compute the embeddings and other metrics.

## Usage of `github-to-sqlite`

The main entry point for this command is `github-to-sqlite repos DBFILE.db -r USER/REPO`. We'll find a way to get random github usernames, and then pull all their repos. But for now we'll just start assembling a DB with this strategy.

## Usage

The main entry point is the `repo-benchmark` CLI.

```bash
repo-benchmark --help
```

### Survey a Repository

Add a new repository to the benchmark database:

```bash
# Survey a repository by its GitHub URL
repo-benchmark survey https://github.com/username/repo-name

# Survey a local repository
repo-benchmark survey ./path/to/local/repo
```

### List Surveyed Repositories

View all repositories in the benchmark database:

```bash
# List all surveyed repositories
repo-benchmark list

# List repositories with a specific filter
repo-benchmark list --filter "python"
```

### Inspect Repository Details

View detailed information about a specific repository:

```bash
# Inspect a repository by name
repo-benchmark inspect username/repo-name

# Inspect with detailed stats
repo-benchmark inspect username/repo-name --stats

# Show repository embeddings
repo-benchmark inspect username/repo-name --embeddings
```

The inspect command shows collected metrics including:

- Basic repository information
- Code quality metrics
- Documentation coverage
- Test coverage
- Dependency health
- Repository embeddings (when --embeddings flag is used)
