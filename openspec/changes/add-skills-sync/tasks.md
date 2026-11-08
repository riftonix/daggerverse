# Tasks

Commands that run Dagger functions, containers, or network calls (`make tests ...`, `dagger call ...`, `npx ...`) need explicit approval from the repository owner before each run.

## 1. Runtime Image (container-images repository)

- [x] 1.1 Add `docker/updatecli-python-nodejs/Dockerfile` and `docker-bake.json` in `container-images`:
  - base `nikolaik/python-nodejs:python3.14-nodejs26` pinned by digest in the Dockerfile;
  - Updatecli binary copied from `ghcr.io/updatecli/updatecli:v<UPDATECLI_VERSION>`;
  - `pip install pyyaml==<PYYAML_VERSION>`;
  - `USER pn`;
  - tag `py<python>-node<node>-updatecli<updatecli>-pyyaml<pyyaml>`;
  - Renovate descriptions on `UPDATECLI_VERSION` and `PYYAML_VERSION`, with the base digest managed by the built-in Dockerfile manager;
  - `PYTHON_VERSION` and `NODE_VERSION` select the image tag components and are checked against the runtime at build time.

  Verified: the [repository CI](https://github.com/riftonix/container-images/actions/runs/42233816594/job/127946662175) built both platforms successfully, including the Dockerfile tool checks. The earlier local amd64 smoke run as `pn` verified Python 3.14.10, PyYAML 6.0.3, Node.js 26.13.0, npm/npx 11.20.0, git 2.47.3, and Updatecli 0.123.0, plus Updatecli diff/apply and byte-identical generation of the six OpenSpec 1.12.0 skills.
- [x] 1.2 Add the image reference page under `container-images/docs/reference/` and its index entry. Verified: `docs/reference/updatecli-python-nodejs.md` and its catalog entries exist, and all relative links in the affected pages resolve.
- [x] 1.3 Publish `ghcr.io/riftonix/container-images/updatecli-python-nodejs` and verify the tag is pullable. Verified: the [publication workflow](https://github.com/riftonix/container-images/actions/runs/42234611189/job/127949392692) succeeded; registry manifest and config reads resolve tag `py3.14-node26-updatecli0.123.0-pyyaml6.0.3` for both `linux/amd64` and `linux/arm64`, with user `pn` and working directory `/home/pn`. Published index digest: `sha256:21a18e4f581ba2f7032409e688543498ab6275b04056f0021335109f0983e1f1`. No new image build or container run was performed during this verification.

## 2. Updatecli Module

- [x] 2.1 Scaffold `modules/updatecli` (`dagger.json` with engine `v0.21.9`, Python SDK, `pyproject.toml`, `.gitignore`, `.gitattributes`) and verify `make lint-check module updatecli` passes.
- [x] 2.2 Implement the constructor with Renovate-annotated `DEFAULT_IMAGE_*` constants and `DEFAULT_CONTAINER_USER_ID`, plus `with_secret_variable`, `with_env_variable`, and `with_directory`. Verify with `make lint-check module updatecli`.
- [x] 2.3 Implement `diff`, `apply`, `applied_source`, and `manifest_show` over `updatecli pipeline diff`, `updatecli pipeline apply`, and `updatecli manifest show`, with the manifest and values mounted under `/updatecli`, the working tree at `/work`, and `--disable-version-check` on every command. Verify with the tests in 2.4.
- [x] 2.4 Add `modules/updatecli/tests` with an aggregate `all()` that runs offline manifests (a shell source and a file target): pending-change report, failing manifest, skipped pipeline, applied working tree content, rendered template values, and a secret value absent from the output. Verify with `make tests module updatecli`.

  Verified: the approved `make tests module updatecli` run on local Dagger v0.21.10 passed all checks. `failing_pipeline` uses a failing shell target and checks the error output; `skipped_pipeline` checks that a failing source, which Updatecli v0.123.0 reports as skipped with exit code 0, returns the report and leaves the working tree unchanged. Telemetry shutdown warnings still appear in the Updatecli output and do not affect results.
- [x] 2.5 Add `modules/updatecli/README.md` linking `docs/README.md`, `docs/reference/updatecli.md`, an index entry in `docs/reference/README.md`, and the root README module list entry. Verify all relative links resolve.

## 3. Skills Sync Helper and Manifest Rendering

- [ ] 3.1 Scaffold `scenarios/skills-sync` with a local dependency on `../../modules/updatecli` and verify `make lint-check scenario skills-sync` passes.
- [ ] 3.2 Implement index loading and validation (missing provenance, unsupported `sourceType`, duplicate names, all errors in one message) and grouping by `sourceType`, `source`, and effective `ref`. Verify with the validation and grouping tests in 3.6.
- [ ] 3.3 Implement revision resolution in the bundled `skills_sync.py`, run by the `sync` command, for git (`git ls-remote`, default branch through `HEAD`) and npm (`npm view`, `latest` default). A resolution error exits `1` with diagnostics on stderr. Verify with the tests in 3.6 against a local bare git repository fixture and an npm stub fixture.
- [ ] 3.4 Implement the `skills_sync.py` `sync` command:
  - build git trees (fetch by SHA with the fallback branch clone and SHA verification);
  - build generic npm trees (`npm pack`) and the OpenSpec tree (`npx ... init` with isolated environment variables);
  - apply exclusions, replace directories, and rewrite the frontmatter `name`;
  - rewrite entries with provenance precedence and collision warnings;
  - remove entries whose upstream path disappeared, and skip groups whose content did not change;
  - honor `DRY_RUN`, and keep index formatting and key order stable.

  Verify with the tests in 3.6.
- [ ] 3.5 Implement manifest rendering for local mode and GitHub mode (SCM with `commitusingapi`, no sources, shell target with `disablesourceinput` and `console/output`, `github/pullrequest` action, stable `pipelineid`), and the scenario functions `manifest`, `diff`, `sync`, and `update` with prefixed `updatecli_*` image inputs, `openspec_tools`, and `openspec_profile`. Verify with the manifest rendering tests in 3.6.
- [ ] 3.6 Add `scenarios/skills-sync/tests` with an aggregate `all()` covering every `skills-sync-scenario` spec scenario that runs on local fixtures:
  - validation;
  - grouping and an independent failing group, where an unresolvable upstream fails the call while other groups are synchronized;
  - up-to-date, moved-without-changes, and changed groups;
  - file add, change, and remove with exclusions;
  - local rename;
  - missing `SKILL.md`;
  - metadata from frontmatter, no inferred version, and removed extra fields;
  - collision warning;
  - upstream removal;
  - preview without writes;
  - rendered GitHub manifest without token values.

  Verify with `make tests scenario skills-sync`.
- [ ] 3.7 Add `scenarios/skills-sync/README.md` linking `docs/README.md`, `docs/reference/skills-sync.md` (provenance keys, source types, synchronization rules, functions and inputs), `docs/how-to/sync-published-skills.md` (local preview, local sync, scheduled workflow with the built-in token and CI dispatch), and the matching index and root README entries. Verify all relative links resolve and the documented commands match the scenario functions.

## 4. Integration Verification

- [ ] 4.1 With explicit approval, run `dagger -m ./scenarios/skills-sync call --source=<riftonix.github.io checkout with migrated index> diff` and verify that it reports the expected k8s update, the `k8s-browser` removal, the `python-code-style` overwrite, and no OpenSpec change at `revision` `1.12.0`.
- [ ] 4.2 With explicit approval, run the scenario `sync` against a temporary copy of a migrated `riftonix.github.io` checkout, pinned to OpenSpec 1.12.0, and verify that the six generated OpenSpec `SKILL.md` files are byte-identical to the currently published files.
- [ ] 4.3 Run `make openspec-validate` and verify the change validates.

## Workflow follow-up

- In `riftonix.github.io`:
  - migrate `index.json` provenance keys using the table in `design.md`;
  - add `workflow_dispatch` to `ci.yaml`;
  - add `skills-sync.yaml` with the cron schedule, `contents`, `pull-requests`, and `actions` write permissions, the scenario `update` call, and CI dispatch for open `updatecli_master_skills-*` branches;
  - add a Renovate annotation for the scenario tag.
- Optionally add `github_workflow_repository_permissions` for `riftonix.github.io` in `iac/github` to codify the existing Actions settings. Review it with `tofu plan`, only with explicit approval.
- Run the first scheduled or dispatched synchronization and review the resulting pull requests before merging.
- Archive the change after implementation and review, then update `docs/` per the archived change.
