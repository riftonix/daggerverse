# Add Skills Sync Design

## Glossary and References

### Glossary

- **Skills index**: the `index.json` file published by `riftonix.github.io` under `/.well-known/skills/`.
- **Provenance keys**: the `metadata` keys `sourceType`, `source`, `path`, `ref`, and `revision` that identify the upstream of an index entry.
- **Source group**: the index entries that share `sourceType`, `source`, and effective `ref`. One group maps to one Updatecli pipeline and one pull request.
- **Skill tree**: the file tree from which entry `path` values are selected: a git checkout for `git`, and an unpacked package or generated CLI output for `npm`.
- **Effective ref**: the entry `ref`, or `HEAD` for `git` and `latest` for `npm` when `ref` is empty.

### References

- Agent Skills specification: https://agentskills.io/specification
- Agent Skills Discovery RFC: https://github.com/cloudflare/agent-skills-discovery-rfc
- Updatecli: https://github.com/updatecli/updatecli (release v0.123.0)
- OpenSpec CLI: https://github.com/Fission-AI/OpenSpec (`docs/cli.md`, `openspec init`)
- GitHub Actions: workflows triggered by `GITHUB_TOKEN` do not start new workflow runs, except `workflow_dispatch` and `repository_dispatch`.
- Specs: `specs/updatecli-module/spec.md`, `specs/skills-sync-scenario/spec.md`.

## Context

### Problem Context

See `proposal.md`, section Why. The current skills index has these technical properties:

- 66 entries from 7 upstream sources: 6 GitHub repositories and the OpenSpec npm package.
- The entry shape is `name`, `description`, `license`, `metadata`, `path`, `files`, and, for gamedev entries only, a top-level `version`. It follows Agent Skills Discovery RFC v0.1 with extra fields.
- The published files match their upstream blobs at the recorded revisions, with three exceptions:
  - `confluence-content-management` renames upstream `confluence` and omits some upstream files;
  - `python-code-style` contains local edits;
  - the OpenSpec skills are CLI output.
- `openspec init --tools cursor --profile core` from `@fission-ai/openspec@1.12.0` reproduces all six published OpenSpec skills byte for byte.

### Existing Technical Constraints

- Daggerverse conventions apply:
  - the primary input is named `source`;
  - runtime image inputs are `image_registry`, `image_repository`, `image_tag`, and `container_user_id`, prefixed in scenarios;
  - Renovate-annotated `*_IMAGE_TAG` constants;
  - Dagger test modules with `all()`;
  - the repository-aligned engine version (`v0.21.9`).
- The official Updatecli image (`debian:stable-slim` based) contains `sh` and `curl`, but no git, Python, or Node.js. The `-slim` variant has no shell.
- `@fission-ai/openspec@1.16.0` requires Node.js 22.12 or later.
- Agent Skills `metadata` is a string-to-string map.
- The site repository protects `master` with the required check `CI Passed`, strict up-to-date branches, and push restrictions that allow only the Renovate app. Its Actions settings already allow GitHub Actions to create pull requests.

## Goals / Non-Goals

### Goals

- Keep all synchronization rules in one testable helper executed by Updatecli, so that preview, local synchronization, and pull request runs share one code path.
- Avoid nightly pull request churn when upstream commits do not touch tracked skills.
- Keep the Updatecli module generic and free of skills-specific logic.

### Non-Goals

- Running Updatecli autodiscovery or Updatecli Compose.
- Supporting Updatecli SCM kinds other than `github` in the scenario.
- Signing or verifying upstream content beyond git and npm transport integrity.

## Architecture and Component Boundaries

### Architecture Overview

```text
site workflow (cron) ──> scenarios/skills-sync ──> modules/updatecli ──> Updatecli in runtime image
                              │ validates index, renders            │
                              │ one pipeline per source group       ├─ shell target: skills_sync.py sync
                              │ mounts skills_sync.py                │  (resolves, then synchronizes)
                              │                                     └─ github/pullrequest action
site workflow ──> gh workflow run ci.yaml --ref <updatecli branch>
```

### Component Responsibilities

- **`modules/updatecli`**: builds the runtime container, mounts a manifest, values files, a working tree, helper directories, environment variables, and secrets, then runs `updatecli pipeline diff`, `updatecli pipeline apply`, or `updatecli manifest show`.
- **`scenarios/skills-sync`**:
  - reads and validates the index;
  - computes source groups;
  - renders the Updatecli manifest;
  - mounts the `skills_sync.py` helper;
  - selects local or GitHub SCM mode.
- **`skills_sync.py`**: a stdlib-plus-PyYAML command-line helper bundled in the scenario. It resolves upstream revisions, builds skill trees, synchronizes directories and index entries, and prints change reports.
- **Runtime image `updatecli-python-nodejs`** (in `container-images`): provides Updatecli, git, Python 3.14 with PyYAML, Node.js 26, and npm.
- **Site workflow** (in `riftonix.github.io`): schedules runs, grants token permissions, and dispatches CI on synchronization branches.

### Component Boundaries

- The Updatecli module does not know about skills, the index format, or GitHub.
- The scenario does not schedule, trigger CI, enable auto-merge, or merge.
- Only the helper writes skill directories and the index.
- The scenario owns the list of npm packages with a dedicated tree generator. Index data never supplies commands to execute.

### Dependencies and Data Flows

1. The scenario reads `index_path` from `source`, validates entries, and groups them.
2. The scenario renders one Updatecli pipeline per group and calls the Updatecli module with the manifest, the helper directory, and either `source` (local mode) or a GitHub SCM token (update mode).
3. Updatecli runs the shell target in the working tree: the local `source`, or the Updatecli clone of the site repository. The pipeline has no sources.
4. The helper resolves the upstream revision, builds the group tree at that revision, and synchronizes the skill directories and index entries.
5. In update mode, Updatecli commits changed files through the GitHub API on the group working branch and creates or updates the pull request.

## Component Changes

### Updatecli Module

The module is new; its public interface is described in [Interfaces](#interfaces).
- The default image is the constant set `ghcr.io/updatecli/updatecli` at tag `v0.123.0`, Renovate-annotated, with container user `65532`.
- The working tree is mounted at `/work`, and the manifest and values files are mounted under `/updatecli`.
- Every command runs with `--disable-version-check`, because the runtime version is pinned by the image tag and the check is an extra network request.
- Functions run without `--clean` and `--unique-tmp-dir`, because the container is ephemeral.
- `apply` and `applied_source` do not pass `--commit=false` or `--push=false`: SCM behavior belongs to the manifest, and local changes are retrieved through `applied_source`.
- Each command gets a new `UPDATECLI_RUN_ID` value to invalidate Dagger execution caching for external upstream state.
- Command execution merges Updatecli stderr into stdout so the returned string includes its reports. Dagger masks secret environment values in this stream.
- Function results follow the Updatecli exit status. The module does not reinterpret pipeline results: a pipeline that Updatecli reports as skipped, including one whose source or condition failed, returns its report.

### Skills Sync Scenario

The scenario is new; its public interface is described in [Interfaces](#interfaces).
- The default runtime image is `ghcr.io/riftonix/container-images/updatecli-python-nodejs` with container user `65532`, and a Renovate annotation on the tag constant.
- The helper and the manifest renderer live in the scenario source and are covered by the scenario test module.

### External Components

- `container-images`: `docker/updatecli-python-nodejs` image built `FROM nikolaik/python-nodejs:python3.14-nodejs26`, pinned by digest directly in the Dockerfile.
  - The base provides Python 3.14 with `pip` and `uv`, Node.js 26 with `npm`, git, and the non-root user `pn` (uid 1000).
  - The image copies `/usr/local/bin/updatecli` from `ghcr.io/updatecli/updatecli:v<UPDATECLI_VERSION>`, installs `pyyaml==<PYYAML_VERSION>` with `pip`, and runs as `pn`.
  - The bake variables `UPDATECLI_VERSION` and `PYYAML_VERSION` carry Renovate descriptions. The base digest is managed by the built-in Dockerfile manager; both Dockerfile and Bake updates receive the `image-dependencies` label.
  - `PYTHON_VERSION` and `NODE_VERSION` are explicit image-line choices used in the tag and checked against the base runtime at build time. Changing the image line requires updating them together with the Dockerfile `FROM` tag and digest.
  - The tag is `py<python>-node<node>-updatecli<updatecli>-pyyaml<pyyaml>`. Published tag: `py3.14-node26-updatecli0.123.0-pyyaml6.0.3`, with index digest `sha256:21a18e4f581ba2f7032409e688543498ab6275b04056f0021335109f0983e1f1`.
- `riftonix.github.io`:
  - migrated index entries;
  - new `.github/workflows/skills-sync.yaml`;
  - a `workflow_dispatch` trigger in `ci.yaml`.
- `iac/github`: optional `github_workflow_repository_permissions` resource for `riftonix.github.io`, available in the pinned `integrations/github` provider 6.12.1.

## Data Model

### Entities and Relationships

An index entry after synchronization:

```json
{
  "name": "k8s-core",
  "description": "<upstream frontmatter description>",
  "license": "Apache-2.0",
  "metadata": {
    "author": "rohitg00",
    "version": "1.0.0",
    "tools": "17",
    "category": "core",
    "sourceType": "git",
    "source": "https://github.com/rohitg00/kubectl-mcp-server",
    "path": "kubernetes-skills/claude/k8s-core",
    "ref": "main",
    "revision": "<commit sha>"
  },
  "path": ".well-known/skills/k8s-core/SKILL.md",
  "files": ["SKILL.md"]
}
```

An OpenSpec entry uses `"sourceType": "npm"`, `"source": "@fission-ai/openspec"`, `"path": ".cursor/skills/openspec-explore"`, `"ref": "latest"`, and `"revision": "<package version>"`. Its upstream keys `author`, `version` (the OpenSpec template version `1.0`), and `generatedBy` (the CLI version) come from the generated frontmatter.

### Persistence Model

- **Formatting:** the helper writes `index.json` as UTF-8 JSON with 2-space indentation and a trailing newline. It keeps entry order and orders entry keys as `name`, `description`, `license`, `metadata`, `path`, `files`.
- **`metadata` key order:** upstream frontmatter order, followed by the provenance keys.
- **Value types:** non-string frontmatter metadata values are converted with YAML scalar rendering (for example, `17` becomes `"17"`).
- **`files`:** sorted by Unicode code point.

### Ownership and Lifecycle

- Upstream owns `description`, `license`, non-provenance `metadata`, and file content.
- The site owns `name`, `path`, and the provenance keys `sourceType`, `source`, `path`, and `ref`.
- The helper writes `revision`.
- A group's entries are rewritten only when the upstream content differs from the published content (see the spec scenario about upstream revisions that moved without skill changes).
- An entry is removed when its upstream `path` disappears.

### Indexes and Constraints

- Entry `name` values are unique.
- Every entry has `sourceType` set to `git` or `npm`, and non-empty `source` and `path`.
- A `git` `path` of `.` selects the repository root.

## Technical Contracts

### External Integrations

- **git:**
  - **Resolve:** `git ls-remote <source> refs/heads/<ref>`, or `HEAD` when `ref` is empty. It must return exactly one SHA.
  - **Fetch:** an empty repository receives `git fetch --depth 1 --filter=blob:none origin <sha>` with a sparse checkout of the group paths. If fetching by SHA is refused, the helper clones `--depth 1 --branch <ref>` and fails when `HEAD` differs from the resolved SHA.
- **npm:**
  - **Resolve:** `npm view <source>@<ref or latest> version`.
  - **Generic tree:** `npm pack <source>@<version>`, unpacked, with the `package/` prefix stripped.
  - **OpenSpec tree:** `npx -y @fission-ai/openspec@<version> init --tools <openspec_tools> --profile <openspec_profile> .`, run in an empty directory with `</dev/null`.
    - A private `HOME`, `XDG_CONFIG_HOME`, and `npm_config_cache` are used.
    - Environment: `OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1`, `OPENSPEC_NO_UPDATE_CHECK=1`, `OPENSPEC_NO_COMPLETIONS=1`, and `CI=1`.
- **GitHub:**
  - Updatecli `github` SCM with `owner`, `repository`, `branch`, and `commitusingapi: true`.
  - The token comes from the `UPDATECLI_GITHUB_TOKEN` secret environment variable.
  - The `github/pullrequest` action uses title `chore(skills): sync <source> (<ref>)` and labels `skills`.

### Internal Contracts

Updatecli pipeline per group (local mode omits `scms`, `scmid`, and `actions`):

```yaml
name: skills-sync git https://github.com/rohitg00/kubectl-mcp-server main
pipelineid: skills-git-rohitg00-kubectl-mcp-server-main
scms:
  site:
    kind: github
    spec: {owner: riftonix, repository: riftonix.github.io, branch: master, commitusingapi: true}
targets:
  skills:
    kind: shell
    scmid: site
    disablesourceinput: true
    spec:
      command: python3 /opt/skills-sync/skills_sync.py sync --index static/.well-known/skills/index.json --type git --source https://github.com/rohitg00/kubectl-mcp-server --ref main
      changedif: {kind: console/output}
actions:
  pr:
    kind: github/pullrequest
    scmid: site
    spec: {title: "chore(skills): sync https://github.com/rohitg00/kubectl-mcp-server (main)", labels: [skills]}
```

- **`pipelineid`:** `skills-<sourceType>-<slug(source)>-<slug(effective ref)>`, lowercase, limited to `[a-z0-9-]`. Updatecli derives the working branch `updatecli_<branch>_<pipelineid>`.
- **Helper `sync` contract:**
  - **Input:** the group options, and `DRY_RUN` set to `true` or `false`. The helper resolves the revision itself; no source value is passed.
  - **Changes:** it prints a non-empty report only when it changed or would change files. The report names the group, its current and resolved revisions, and the affected skills. An up-to-date group, including one whose revision moved without skill changes, prints nothing, because any target stdout marks the pipeline as changed.
  - **Dry run:** with `DRY_RUN=true` it writes nothing. Resolution and tree building still run, because they only read upstream.
  - **Exit codes:** `0` on success, `1` on a group failure, including resolution errors. Diagnostics go to stderr.
  - **Collision warnings:** printed to stdout as `warning: <skill>: upstream metadata key <key> overridden by provenance`, only together with the change report of the rewritten entry, so warnings never mark an unchanged group as changed.

## Interfaces

### Command-Line Interface

```sh
# Generic module usage
dagger -m github.com/riftonix/daggerverse/modules/updatecli@<tag> call \
  --source=. \
  with-secret-variable --name=UPDATECLI_GITHUB_TOKEN --secret=env:GITHUB_TOKEN \
  diff --config=./updatecli.yaml --values=./values.yaml

# Scenario: preview, local sync, pull requests
dagger -m github.com/riftonix/daggerverse/scenarios/skills-sync@<tag> call --source=. diff
dagger -m github.com/riftonix/daggerverse/scenarios/skills-sync@<tag> call --source=. sync export --path=.
dagger -m github.com/riftonix/daggerverse/scenarios/skills-sync@<tag> call --source=. \
  update --github-token=env:GITHUB_TOKEN --repository=riftonix/riftonix.github.io --branch=master
```

### Internal Interfaces

**Updatecli module:**
- **Constructor:** `create(source: Directory | None, image_registry, image_repository, image_tag, container_user_id)`.
- **Chainable setup:** `with_secret_variable(name, secret) -> Self`, `with_env_variable(name, value) -> Self`, `with_directory(path, directory) -> Self`.
- **Runs:** `diff(config: File, values: list[File] | None) -> str`, `apply(config, values) -> str`, `applied_source(config, values) -> Directory`, `manifest_show(config, values) -> str`.

**Skills sync scenario:**
- **Constructor:** `create(source: Directory, index_path, openspec_tools = "cursor", openspec_profile = "core", updatecli_image_registry, updatecli_image_repository, updatecli_image_tag, updatecli_container_user_id)`.
- **Functions:**
  - `manifest(repository: str | None, branch: str | None) -> str`;
  - `diff() -> str`;
  - `sync() -> Directory`;
  - `update(github_token: Secret, repository: str, branch: str) -> str`.

**Site workflow sketch** (external task):

```yaml
on:
  schedule: [{cron: "17 2 * * *"}]
  workflow_dispatch: {}
permissions: {contents: write, pull-requests: write, actions: write}
steps:
  - uses: actions/checkout@v7
  - uses: dagger/dagger-for-github@v8.4.1
  - run: dagger -m "$SKILLS_SYNC_MODULE" call --source=. update --github-token=env:GITHUB_TOKEN --repository="$GITHUB_REPOSITORY" --branch=master
    env: {GITHUB_TOKEN: "${{ github.token }}"}
  - run: |
      gh pr list --state open --json headRefName --jq '.[].headRefName | select(startswith("updatecli_master_skills-"))' |
        while read -r ref; do gh workflow run ci.yaml --ref "$ref"; done
    env: {GH_TOKEN: "${{ github.token }}"}
```

## Error Handling

### Error Categories

- **Index validation errors:** missing provenance, an unsupported `sourceType`, or a duplicate `name`. These fail before any pipeline runs.
- **Resolution errors:** git or npm cannot be reached, the ref is unknown, or the output is ambiguous. These fail the group target.
- **Tree errors:** a fetch failure, a SHA mismatch after the fallback clone, a non-zero `npm pack` or `npx` exit, or a missing `SKILL.md` or frontmatter. These fail the group target.
- **SCM and action errors:** GitHub API or permission failures. These fail the group.

### Error Propagation and Mapping

- Updatecli runs groups independently and exits `1` if any group failed. The module surfaces this as a failed Dagger function call that includes the Updatecli output.
- Updatecli v0.123.0 reports a pipeline whose source or condition failed as skipped and exits `0`, while a failed target fails the run. The module returns the report of a skipped pipeline without an error. Scenario pipelines have no sources or conditions, so every group error is a target failure and fails the run.
- Validation errors are raised by the scenario as one error listing every invalid entry.

### Retry and Recovery

- There are no in-run retries: the next scheduled run retries every group.
- Working branches are recreated from `branch` on each run, because Updatecli force-pushes them. A pull request that becomes outdated after another group merges recovers on the next run.

### Logging and Diagnostics

- The helper prints one line per changed, removed, or warned skill to stdout.
- Updatecli logs shell stdout at info level (`pkg/plugins/resources/shell/main.go`), so the report and warnings appear in the Updatecli output returned by the scenario functions and in the caller job logs.
- The pull request description contains only the standard Updatecli report, whose shell target description is `ran shell command "<command>"`. The change report and warnings are not copied into the pull request; reviewers read them in the job logs.
- `manifest` returns the rendered manifest for inspection.
- Dagger scrubs secret values from outputs.

## Decisions

### Decision: Updatecli orchestrates, a bundled helper synchronizes

Updatecli provides dry-run reports, stable working branches, signed API commits including deletions, and pull request management. It has no plugin that copies directories from another repository, so a `shell` target runs the helper.

Alternative considered: a pure Dagger synchronization with `dag.git()` and `gh pr create`. Rejected because it reimplements the Updatecli SCM and pull request lifecycle.

### Decision: Render the manifest in scenario code

Validation and grouping are easier to test in Python than in Go templates. The module still accepts values files for other consumers.

Alternative considered: a static template with `index.json` passed as `--values`. Updatecli supports this, but grouping with sprig dictionaries is hard to read and test.

### Decision: Resolve revisions inside the shell target

The helper `sync` command resolves the revision and builds the tree in one target run. Updatecli v0.123.0 reports a failed source as a skipped pipeline and exits `0`, while a failed target fails the run. Resolving in the target makes an unreachable upstream fail the run. `git ls-remote` supports an empty ref (the default branch through `HEAD`), and `npm view` supports dist-tags. One helper keeps git and npm symmetric.

The resolved revision is not available as a source value, so manifests cannot reference it through `{{ source }}`. The pull request title is static per group, and the revision appears in the helper report.

Alternatives considered:
- a shell source running a `resolve` helper command, rejected because a failed resolution would skip the group silently;
- the `gitbranch` source with `key: hash` and `lsremote: true`, which requires an explicit branch name and has the same skip behavior;
- the `npm` source, which selects by version filter rather than by dist-tag and has the same skip behavior.

### Decision: Compare content, not only revisions

The group head SHA changes on every upstream commit. The helper builds the tree at the resolved revision and rewrites entries, including `revision`, only when a skill directory or a derived index field differs, or when a `revision` is empty. This prevents nightly pull request updates for unrelated upstream commits.

### Decision: Flat provenance keys that override upstream metadata

Agent Skills `metadata` allows only string values, so nested objects are not possible. Provenance values override colliding upstream keys in the index only, and the helper warns. The published `SKILL.md` keeps upstream text. No current upstream frontmatter uses a provenance key.

### Decision: Generate OpenSpec skills with the CLI

The npm package ships templates, not `SKILL.md` files. `init --tools cursor --profile core` reproduces the published text byte for byte. Other tool IDs only change the command syntax: `claude` produces `/opsx:apply`, and `agents` produces `/openspec-apply-change`.

Alternative considered: git tags of `Fission-AI/OpenSpec` `skills/`. Rejected because that text differs from the published CLI output.

### Decision: Built-in token with explicit CI dispatch

The `GITHUB_TOKEN` of the site repository is sufficient to push branches and open pull requests. Pull requests it opens do not start `pull_request` workflows, so the caller workflow dispatches `ci.yaml` on the synchronization branches. That run reports `CI Passed` on the head commit.

Alternative considered: a GitHub App or a PAT. Rejected because it requires secret provisioning.

### Decision: Dedicated runtime image

The official Updatecli image has no git, Python, or Node.js, and no available image combines Updatecli, git, Python with PyYAML, and Node.js. `nikolaik/python-nodejs` already combines Python, Node.js, and git on a full Debian base, so the image only adds the Updatecli binary and PyYAML.

Alternatives considered:
- `node:24-trixie-slim` with Debian `git`, `python3`, and `python3-yaml`: smaller and fully official, but needs more image maintenance;
- the full `node:24-trixie`: has git but no explicit Python, and is large.

## Risks / Trade-offs

- [Upstream text is executed by agents after publication] → No auto-merge; every change is reviewed in a pull request, and the scenario never merges.
- [`npx` executes third-party code during synchronization] → Pinned resolved version, an ephemeral container, a private `HOME`, and no site credentials in the generator environment.
- [OpenSpec CLI flags or output layout change] → The group fails visibly; generator inputs are scenario parameters, and the test fixtures cover the generator contract.
- [Push restrictions block merges by GitHub Actions] → Not relevant without auto-merge. Enabling auto-merge later requires adding the GitHub Actions app to `push_allowances` in `iac/github`.
- [Several group pull requests edit `index.json`] → Entries change in separate hunks. Strict branch protection requires an update after each merge, which the next run performs.
- [Hosts that refuse fetching by SHA] → Fallback clone by branch with SHA verification.
- [`nikolaik/python-nodejs` is a third-party base with a floating tag rebuilt twice a day] → The base is pinned by digest, and Renovate proposes digest updates for review.
- [The full Debian base makes the image large] → Accepted for a nightly job; the image is pulled once per run.
- [Dispatched CI does not run the preview job] → Accepted: preview needs a pull request number, and `CI Passed` accepts a skipped preview.

## Migration Plan

### Rollout

1. Add and publish the `updatecli-python-nodejs` image in `container-images`.
2. Implement and release `modules/updatecli` and `scenarios/skills-sync`.
3. In `riftonix.github.io`, add the provenance keys from the table below, add `workflow_dispatch` to `ci.yaml`, and add `skills-sync.yaml`.
4. Run `diff` locally, then `update` through `workflow_dispatch`. Review the first pull requests.
5. Optionally codify the Actions workflow permissions in `iac/github`.

### Data Migration

| Entries | `sourceType` | `source` | `path` | `ref` | `revision` |
|---|---|---|---|---|---|
| `godot-*` (15) | git | `https://github.com/gamedev-skills/awesome-gamedev-agent-skills` | `skills/godot/<name>` | `main` | `cf44d99a0315dabff6ac6f407c6ccc026190f16c` |
| other gamedev skills (15) | git | same | `skills/disciplines/<name>` | `main` | same |
| `fpf-problem-solving`, `code-that-fits-in-your-head` | git | `https://github.com/CodeAlive-AI/ai-driven-development` | `skills/<name>` | `main` | `5f831b43e3889772d2de149075efe693478f4e09` |
| `confluence-content-management` | git | `https://github.com/SpillwaveSolutions/confluence-skill` | `.` | `main` | `b93d2efd9984c6de17ae0b1da04c215c5ca7cd72` |
| `k8s-*` (25) | git | `https://github.com/rohitg00/kubectl-mcp-server` | `kubernetes-skills/claude/<name>` | `main` | `d49f2d9460d687c96b0f040a37f413432e09cd82` |
| `python-code-style` | git | `https://github.com/wshobson/agents` | `plugins/python-development/skills/python-code-style` | `main` | empty, to force the first synchronization over local edits |
| `openspec-*` (6) | npm | `@fission-ai/openspec` | `.cursor/skills/<name>` | `latest` | `1.12.0` |

The first run normalizes the remaining fields:
- removes the top-level `version`;
- drops the confluence `metadata.version`;
- adds the k8s `tools` and `category`.

### Backward Compatibility

- Index consumers that ignore unknown fields are unaffected.
- `metadata.version` disappears only where upstream frontmatter does not declare it.
- Removed skills disappear from the index and the site.

### Rollback

- Disable or delete `skills-sync.yaml` and close open synchronization pull requests.
- Merged changes are reverted with git.
- The module, scenario, and image releases can remain published without effect.
