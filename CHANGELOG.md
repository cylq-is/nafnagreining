# Changelog

## 0.1.1

- Add CI: tests run on every pull request on Linux and macOS with Python 3.10 and 3.14.
- Add automatic releases: merging a pull request to `main` bumps the version,
  publishes to PyPI and creates a GitHub release.
- Add this changelog.

## 0.1.0

- First release.
- `isIcelandic(s)`: detect whether a text is Icelandic.
- `extractEntities(s)`: extract person names, places and locations from
  Icelandic text, in the nominative.
