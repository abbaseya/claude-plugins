# Releasing the catalog

This repo ships no code. Releasing it means changing `marketplace.json` and letting
users pick the change up.

## What counts as a catalog release

- Adding a plugin
- Removing or renaming a plugin
- Bumping a plugin's `version` so installed copies update
- Editing a plugin's description, keywords or category

Changes inside a plugin's own repository are **not** catalog releases. Those ship from
that repo. The catalog only needs touching when the `version` recorded here should move.

## Procedure

Everything lands through a pull request. Nothing is pushed to `main` directly — CI runs
on `pull_request`, so a direct push is a change that was never validated.

1. Branch: `git checkout -b catalog/<what-changed>`
2. Edit `.claude-plugin/marketplace.json`.
3. Bump `metadata.version` for the catalog itself, and the plugin's `version` if its
   source repo has released something new.
4. Run the checks locally:
   ```bash
   python bin/check-catalog.py
   python -m unittest discover -s bin/tests
   ```
5. Open a PR. CI validates the catalog, runs the checker's own suite, and lints.
6. Merge once green.

## Version resolution

Each plugin entry carries an explicit `version`. Users only receive an update when that
field changes, which means a commit to a plugin's source repo does **not** silently
reach everyone — the catalog decides.

Omitting `version` flips that: every commit in the source repo then counts as a new
release. `check-catalog.py` warns when a `version` is missing so the choice is
deliberate rather than accidental.

## Renaming or removing a plugin

Do not just delete the entry. Users with it installed get `plugin-not-found` with no
path forward. Add a top-level `renames` map alongside `plugins`:

```json
"renames": {
  "old-name": "new-name",
  "retired-plugin": null
}
```

Map a former name to its current one, or to `null` if it is gone. Treat `renames` as
append-only history — keep old entries even after everyone has migrated, because
Claude Code follows rename chains.

## After merging

Users refresh with:

```
/plugin marketplace update abbaseya
```

Then update the plugin itself from the `/plugin` menu. A plugin whose source is a
`github` entry reports `plugin-cache-miss` after a rename and needs one
`/plugin install` to re-fetch under the new name.
