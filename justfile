set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Convert the org sources and render the HTML book.
build:
    python3 scripts/build_book.py
    mdbook build

# Convert and serve the book locally with live reload.
serve: build
    mdbook serve --open

# Remove generated Markdown and HTML.
clean:
    rm -rf src book

# Build and verify the generated book artifacts.
check: build
    @test -f book/index.html
    @test -f src/SUMMARY.md
    @test "$(grep -c '^- \[' src/SUMMARY.md)" -eq "$(find . -maxdepth 1 -type f -name 'chapter*.org' | wc -l)"
    @test "$(find src -maxdepth 1 -type f -name 'chapter*.md' | wc -l)" -eq "$(find . -maxdepth 1 -type f -name 'chapter*.org' | wc -l)"
    @! grep -R -n -E '\]\((file:)?chapter[0-9]+\.org' src --include='*.md'
    @! grep -R -n -E '^#\+(begin_|end_|RESULTS:)' src --include='*.md'
    @echo "All checks passed."
