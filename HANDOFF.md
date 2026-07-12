# fs42stream handoff

The fs42stream scaffold is committed in this repository branch, but it is not
automatically published as a public GitHub repository by the coding environment.
If collaborators cannot see the PR/files on GitHub, the likely cause is that the
workspace branch/PR is private to this environment or has not been pushed to a
GitHub remote that they can access.

## Files included

The implementation currently consists of:

* `README.md` - project overview and current status.
* `config/fs42stream.example.yaml` - example runtime configuration.
* `docs/architecture.md` - design notes and remaining work.
* `pyproject.toml` - Python package metadata and test configuration.
* `src/fs42stream/` - service configuration, FS42 client, schedule parser,
  playlist/XMLTV rendering, FFmpeg command builder, and HTTP server scaffold.
* `tests/test_core.py` - unit tests for the current scaffold.

## Create a portable archive

Run this from the repository root:

```bash
./scripts/export_bundle.sh
```

The script creates a timestamped archive under `dist/`, for example:

```text
dist/fs42stream-scaffold-20260712T120000Z.tar.gz
```

That archive can be emailed, copied to a NAS share, uploaded to another Git host,
or attached to a ticket/chat for other people.

## Publish to a GitHub repository

If you want these files available on GitHub, push the current branch to a GitHub
remote that your collaborators can access:

```bash
git remote add origin git@github.com:<owner>/<repo>.git
git push -u origin HEAD
```

If the target repo already exists as `origin`, use:

```bash
git push -u origin HEAD
```

Then open a pull request from the pushed branch, or make the branch the default
branch if this is a new repository.

## Make the repository public or share access

If collaborators still cannot see the files after pushing:

1. Check whether the GitHub repository is private.
2. Add collaborators or a team with read access.
3. Confirm the branch was pushed to the expected repository.
4. Share the branch URL, pull request URL, or a release/archive download link.

## Local verification before sharing

Run these checks before sending the archive or pushing the branch:

```bash
python -m pytest -q
python -m compileall -q src tests
```
