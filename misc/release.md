# Do a release

Bump version number in `src/baserow/__init__.py`.

Tag release.

```bash
git tag vX.X.X -m "Release vX.X.X"
git push origin vX.X.X
```

Add new release on GitHub and write release notes.

Use [Flit](https://flit.pypa.io/en/stable/) to do the release.

```fish
pip3 install flit
set -x FLIT_USERNAME __token__
flit publish
# Paste PyPI API token
```