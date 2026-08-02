# abbaseya — Claude Code plugin marketplace

This repository is a **Claude Code plugin marketplace** maintained by [Ahmed Abbas](https://github.com/abbaseya). Marketplace name: `abbaseya`.

A "marketplace" in Claude Code is just a catalog of plugins hosted on GitHub. Anyone can register this marketplace into their own Claude Code installation and install any plugin listed here.

## Quickstart

Inside Claude Code, run these commands once to register the marketplace and install a plugin from it:

```
/plugin marketplace add abbaseya/claude-plugins
/plugin install my-vault@abbaseya
```

The first line tells your Claude Code installation about this marketplace (it resolves the name `abbaseya` to this GitHub repo). The second installs a specific plugin. Repeat the second command for each plugin you want.

## Plugins in this marketplace

Each plugin lives in its own dedicated repository. This catalog points at them via `github` sources, so `/plugin install <name>@abbaseya` clones the right repo for you.

| Plugin | Repository | Install command | What it does |
|---|---|---|---|
| `my-vault` | [`abbaseya/claude-vault-skill`](https://github.com/abbaseya/claude-vault-skill) | `/plugin install my-vault@abbaseya` | Turns your Claude Code sessions into an interlinked Obsidian vault. Captures the decisions and reasoning buried in your transcripts as atomic notes, each anchored to a machine-verified verbatim quote. |
| `my-voice` | [`abbaseya/claude-voice-skill`](https://github.com/abbaseya/claude-voice-skill) | `/plugin install my-voice@abbaseya` | Drafts in your own voice. Builds a structured model of you-as-writer from your own writing samples before drafting, then critiques the draft as you would. |

## Repository layout

This repo holds *only* the marketplace catalog and its metadata. Plugin source code lives in the plugins' own repos, linked above.

```
.
├── .claude-plugin/
│   └── marketplace.json    # the catalog — lists every plugin and where to find it
├── .github/workflows/
│   └── tests.yml           # validates the catalog on every PR
├── bin/
│   └── check-catalog.py    # schema + reachability checks for marketplace.json
├── LICENSE                 # MIT, applies to the catalog metadata
├── RELEASE.md              # how a catalog change gets released
└── README.md               # this file
```

For plugin-specific documentation — setup, configuration, privacy — see each plugin's own README.

## Updating

When a plugin ships a new version, refresh your local copy of the catalog:

```
/plugin marketplace update abbaseya
```

Then update the plugin itself from the `/plugin` menu.

## A note on trust

These plugins run on your machine with your Claude Code permissions. Two of them ship hooks, which execute on session start. Before installing anything from any marketplace — including this one — read the plugin's source. Every repo here is public and MIT licensed precisely so you can.

Neither plugin sends your data anywhere. `my-vault` reads your local transcripts and writes local markdown; `my-voice` reads your local writing samples. There is no network call in either, and no telemetry.

## License

MIT — see [LICENSE](LICENSE). This covers the catalog metadata in this repository. Each plugin carries its own license in its own repo.
