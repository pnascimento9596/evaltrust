# Releasing

EvalTrust publishes to PyPI automatically when a GitHub Release is published,
using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/). No API
tokens are stored anywhere — PyPI trusts releases coming from this repo's
`publish.yml` workflow via OpenID Connect.

## One-time setup (do this once, before the first release)

1. **Create the PyPI project as a pending trusted publisher.**
   - Log in at <https://pypi.org> (create an account if needed).
   - Go to your account → **Publishing** → **Add a pending publisher**.
   - Fill in:
     - **PyPI Project Name:** `evaltrust`
     - **Owner:** `k-dickinson`
     - **Repository name:** `evaltrust`
     - **Workflow name:** `publish.yml`
     - **Environment name:** `pypi`
   - Save.

2. **Create the `pypi` environment on GitHub.**
   - Repo → **Settings** → **Environments** → **New environment** → name it
     `pypi`. (No secrets required; it exists so the workflow can reference it and
     you can optionally add release protection rules.)

That's it. From now on, releases publish automatically.

## Cutting a release

1. Update the version in `pyproject.toml` (`[project] version`).
2. Move the `Unreleased` notes in `CHANGELOG.md` under a new version heading.
3. Commit and tag:

   ```bash
   git commit -am "Release vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

4. On GitHub, go to **Releases → Draft a new release**, choose the `vX.Y.Z` tag,
   write the notes, and **Publish**.

Publishing the release triggers `publish.yml`, which builds the sdist and wheel,
validates them with `twine`, and uploads to PyPI. Within a minute or two:

```bash
pip install evaltrust
```

## Testing the build locally

You can always build and validate without publishing:

```bash
python -m build
twine check dist/*
```

## Optional: TestPyPI dry run

To rehearse against [TestPyPI](https://test.pypi.org) first, add it as a second
trusted publisher there and point a temporary workflow (or a manual
`twine upload --repository testpypi dist/*`) at it before doing the real release.
