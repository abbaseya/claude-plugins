#!/usr/bin/env python
"""Validate marketplace.json before it can break someone's /plugin install.

A malformed catalog does not fail loudly for the person who published it — it
fails for whoever tries to install from it, with an error they cannot fix. So
the checks that matter are the ones nothing else notices: a duplicate plugin
name, a name that is not kebab-case (the claude.ai marketplace sync rejects
those), a source pointing at a repo that does not exist, or a reserved
marketplace name.

Blocking checks are offline and deterministic. Repo reachability is a separate
--online pass and is report-only in CI, because a network blip should never
fail a catalog that is structurally fine.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".claude-plugin" / "marketplace.json"

# Reserved for official Anthropic use; a third-party catalog using one is rejected.
RESERVED = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
    "first-party-plugins", "healthcare",
}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def main():
    online = "--online" in sys.argv

    if not CATALOG.is_file():
        err("no marketplace.json at %s" % CATALOG)
        return report()
    try:
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    except ValueError as e:
        err("marketplace.json is not valid JSON: %s" % e)
        return report()

    name = cat.get("name")
    if not name:
        err("marketplace has no `name`")
    else:
        if not KEBAB.match(name):
            err("marketplace name %r is not kebab-case" % name)
        if name in RESERVED:
            err("marketplace name %r is reserved for Anthropic" % name)
        if re.search(r"official|anthropic", name, re.I):
            err("marketplace name %r impersonates an official source" % name)

    if not isinstance(cat.get("owner"), dict) or not cat["owner"].get("name"):
        err("marketplace needs owner.name")

    plugins = cat.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        err("marketplace has no plugins")
        return report()

    seen = set()
    for i, p in enumerate(plugins):
        tag = p.get("name") or "plugins[%d]" % i
        pname = p.get("name")
        if not pname:
            err("%s: missing `name`" % tag)
        else:
            if not KEBAB.match(pname):
                err("%s: name is not kebab-case" % tag)
            if pname in seen:
                err("%s: duplicate plugin name" % tag)
            seen.add(pname)

        src = p.get("source")
        if src is None:
            err("%s: missing `source`" % tag)
        elif isinstance(src, str):
            if not src.startswith("./"):
                err("%s: string source must be a relative path starting './'" % tag)
            elif not (ROOT / src).is_dir():
                err("%s: local source %s does not exist" % (tag, src))
        elif isinstance(src, dict):
            kind = src.get("source")
            required = {"github": ["repo"], "url": ["url"], "npm": ["package"],
                        "git-subdir": ["url", "path"]}
            if kind not in required:
                err("%s: unknown source type %r" % (tag, kind))
            else:
                for f in required[kind]:
                    if not src.get(f):
                        err("%s: source type %r requires `%s`" % (tag, kind, f))
                if kind == "github" and src.get("repo") and "/" not in src["repo"]:
                    err("%s: repo must be owner/name, got %r" % (tag, src["repo"]))
        else:
            err("%s: source must be a string or an object" % tag)

        v = p.get("version")
        if not v:
            warn("%s: no `version` — every commit to the source repo then counts "
                 "as a new release" % tag)
        elif not SEMVER.match(str(v)):
            warn("%s: version %r is not semver" % (tag, v))
        if not p.get("description"):
            warn("%s: no description — users see this when browsing" % tag)

    if online:
        for p in plugins:
            src = p.get("source")
            if not isinstance(src, dict) or src.get("source") != "github":
                continue
            url = "https://github.com/%s" % src["repo"]
            try:
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "check-catalog"})
                urllib.request.urlopen(req, timeout=10)
                print("  reachable: %s" % url)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    warn("%s: %s returns 404 (private repo, or not created yet)"
                         % (p.get("name"), url))
                else:
                    warn("%s: %s returned HTTP %s" % (p.get("name"), url, e.code))
            except Exception as e:
                warn("%s: could not reach %s (%s)" % (p.get("name"), url, e))

    return report()


def report():
    for w in warnings:
        print("WARN  %s" % w)
    for e in errors:
        print("ERROR %s" % e)
    if errors:
        print("\n%d error(s) — catalog would break /plugin install." % len(errors))
        return 1
    print("\ncatalog OK%s" % (" (%d warning(s))" % len(warnings) if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
