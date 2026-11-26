# Git plan: version-to-version changes and fallbacks

## Branches
| Branch | Purpose | Rules |
|---|---|---|
| `main` | Next release in progress. Always passes the tests. | Changes arrive by short-lived `feat/*`, `fix/*` or `docs/*` branches and a pull request. No force-pushes. |
| `stable` | Points at the latest release that is known to be good. Users who track a branch use this one. | Only ever moved with a fast-forward to a release tag, or deliberately moved back to an earlier tag to roll back (see below). |
| `release/X.Y` | Maintenance line for an older minor version, created from its tag when a fix has to be shipped to people who stay on it. | Only fixes. Each fix is released as `vX.Y.Z+1`. |

## Versions
- Semantic versioning, one annotated tag per release: `v0.1.0`, `v0.2.0`, ...
- While the major version is 0, a minor bump (`0.2.0` to `0.3.0`) may change behaviour; a patch bump (`0.2.0` to `0.2.1`) never does.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), and `CHANGELOG.md` is updated in the release commit.
- The tag, `pyproject.toml` and `asynchttp.__version__` must match (a test enforces it).
- Each tag also gets a GitHub Release.

## Releasing (version to version)
1. Work on a branch, open a pull request into `main`, tests must pass.
2. On `main`: bump the version in `pyproject.toml` and `asynchttp/__init__.py`, update `CHANGELOG.md`, commit `chore(release): vX.Y.Z`.
3. `git tag -a vX.Y.Z -m "vX.Y.Z"` and push `main` with the tag.
4. Fast-forward `stable` to the tag: `git branch -f stable vX.Y.Z && git push origin stable`.
5. `gh release create vX.Y.Z --notes-from-tag`.

## Moving between versions (users)
- Upgrade: `pip install --upgrade "git+https://github.com/nottheragingdemon/async-http-kit@v0.3.0"`.
- Pin: always install a tag, never `main`, in anything that must keep working.
- Fallback chain: `scripts/install.sh` tries the newest tag first and falls back to the previous ones in order (`v0.3.0`, `v0.2.0`, `v0.1.0`) if the install or the smoke test fails.

## Rolling back (maintainers)
- **A release turned out bad, nobody should install it:** move `stable` back to the last good tag (`git branch -f stable v0.2.0 && git push --force-with-lease origin stable`), then either ship a fix as the next patch or revert the bad commits on `main` with `git revert` (history is never rewritten on `main`). Tags are never deleted or moved once published: a bad tag is superseded by a new one and marked as such in `CHANGELOG.md`.
- **A bug in an older line:** `git switch -c release/0.2 v0.2.0`, cherry-pick the fix (`git cherry-pick -x <sha>`), tag `v0.2.1`.
- **Find what changed between two versions:** `git log --oneline v0.2.0..v0.3.0` and `git diff v0.2.0 v0.3.0 -- asynchttp`.
- **Bisect a regression:** `git bisect start v0.3.0 v0.2.0 && git bisect run python -m unittest discover -s . -t .`.
