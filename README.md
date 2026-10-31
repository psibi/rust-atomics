# Rust Atomics

Notes on Rust atomics and concurrency.

The top-level `*.org` files are the single source of truth. Markdown and HTML
are generated artifacts and are not committed.

## Prerequisites

- [just](https://github.com/casey/just)
- Python 3
- [Pandoc](https://pandoc.org/)
- [mdBook](https://rust-lang.github.io/mdBook/)

## Commands

```bash
# Convert the org sources and render the HTML book into book/
just build

# Convert and serve the book locally with live reload
just serve

# Remove generated Markdown and HTML
just clean
```

Pushes to `main` build the book and deploy it to GitHub Pages via
`.github/workflows/pages.yml`. The repository's Pages source must be configured
to use GitHub Actions.
