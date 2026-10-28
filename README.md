# OpenBMC Image Builder GUI — Part 2

## Purpose

For junior engineers, and to speed up a company's project launch with
OpenBMC: a form that turns the must-have build inputs into a build spec
and a `local.conf` fragment, so a newcomer to OpenBMC / Yocto does not
have to hand-edit Yocto settings to get to a first build. The goal is a
shorter path from "we need a BMC image" to "we have a buildable spec",
not a claim that any launch time has already been measured — no full
`bitbake` build has been run yet, and no boot has been verified (see
"Part 2 progress" below).

Part 1 (2026-10-26) built the GUI first; Part 2
pins the Yocto mappings against the fetched trees, and writes the
verification and operations drafts.

## Status — ongoing, and next 30 days (as of 2026-10-28)

**Ongoing (in progress, not finished):**
- GUI form + spec generator + `local.conf` fragment generator — done
  and tested at the generator level (Part 1 + Part 2).
- Service-to-`IMAGE_FEATURES` mapping pinned against the fetched
  upstream and ASPEED SDK trees — done, see `part2-mapping.md`.
- QEMU boot verification — **draft only, not run yet**
  (`qemu-boot-verification-draft.md` says so on its first line).
- Real-board verification — not started; QEMU passing is never
  presented as board verification.

**Next 30 days (plan, starting after return on 2026-11-02):**
1. Set up a build environment and run a real
   `bitbake obmc-phosphor-image` build for `evb-ast2600`, and record
   the exact artifact filenames it produces.
2. Run the QEMU boot verification for that artifact (AST2600 EVB
   model), and replace the draft with a dated run log filled in from
   observed output.
3. Verify service removal: what actually removes a service from the
   default image, if removal is ever required.
4. Draft hostname / network runtime provisioning (phosphor-networkd /
   Redfish / D-Bus first-boot configuration, or a custom layer with a
   systemd `.network` file) and SSH authorized-key delivery — as
   automation, not as pasted secrets.

Note on hardware dependence: build settings vary by board, so a result
for one EVB machine does not guarantee the same result on a different
board. The QEMU step proves the build-and-boot process for the EVB
model; board-specific bring-up remains board-specific work.

## What Part 1 does

1. An engineer fills in the form in `index.html` (no server, no install:
   open the file in a browser).
2. The form produces a build-spec JSON (machine, image artifact kind,
   network mode, hostname, requested services).
3. `generate_local_conf.py` turns that JSON into a `local.conf` fragment
   you can drop into a Yocto build directory.

## What Part 1 deliberately does NOT do

- It does **not** run `bitbake`, and it does not claim a build will succeed.
- It does **not** verify that an image boots (no QEMU run yet — Part 2).
- It does **not** solve build time, sstate caching, layer drift, or key
  management (all Part 2, listed honestly below).
- It does **not** collect a root password or an SSH private key. The form
  takes only a *path reference* for a public-key file, if any. Secrets
  must never be pasted into this form.

## Machine presets — verified, not guessed

The presets are the machine confs actually present in the fetched
OpenBMC tree used for this project:

- `evb-ast2500` — `meta-evb/meta-evb-aspeed/meta-evb-ast2500/conf/machine/evb-ast2500.conf`
- `evb-ast2600` — `meta-evb/meta-evb-aspeed/meta-evb-ast2600/conf/machine/evb-ast2600.conf`
  (also the default in `meta-aspeed/conf/local.conf.sample`:
  `MACHINE ??= "evb-ast2600"`)
- `ast2700-dcscm` — from the ASPEED SDK tree, not upstream meta-evb:
  `meta-aspeed-sdk/meta-aspeed-pfr/meta-ast2700-pfr/conf/machine/ast2700-dcscm.conf`

No plain `evb-ast2700` Yocto machine preset is offered: no such machine
conf was found (the `ast2700a1-evb` string in the tree is a QEMU
`-machine` value, not a Yocto MACHINE). Use the "Other" field for any
further machine name only after confirming a matching machine conf
exists in your layer version; the generator prints a warning for
non-preset machines instead of silently accepting them.

## Usage

```sh
# 1. Fill in the form in index.html, download the spec JSON.
# 2. Generate the fragment:
python3 generate_local_conf.py examples/sample-spec.json -o /tmp/local.conf.fragment
cat /tmp/local.conf.fragment
```

The fragment now contains two kinds of real assignments: `MACHINE`,
and `IMAGE_FEATURES:append` for the selected services (see
`part2-mapping.md` for the verified tokens and their source files).
Hostname and network are deliberately NOT assignments: no local.conf
variable for them was found in either tree, so they are emitted as
commented runtime notes — set them after first boot via
phosphor-networkd. Deselecting a service does not remove it either;
the fragment warns instead, because the removal mapping is unpinned
and the default image would still include the service.

## Part 2 progress — done, drafted, still open

Done in Part 2 (verified against the fetched upstream and ASPEED SDK
trees; details and source paths in `part2-mapping.md`):
- Services pinned: Redfish → `obmc-bmcweb`, IPMI →
  `obmc-net-ipmi` + `obmc-host-ipmi`, SSH → `ssh-server-dropbear`,
  Web UI → `obmc-webui`, as one `IMAGE_FEATURES:append` assignment.
  All four are already in the default `obmc-phosphor-image`, so the
  append makes the selection explicit, not additive.
- Hostname / network honestly classified as runtime configuration,
  not build settings, with the search that found no local.conf
  variable recorded in `part2-mapping.md`. No variable was invented.
- `generate_local_conf.py` and the `index.html` fragment logic are
  synced to the same Part 2 behaviour; machine presets are unchanged
  (`evb-ast2500`, `evb-ast2600`, `ast2700-dcscm`); no `evb-ast2700`
  preset was added.
- Tests updated to Part 2 expectations and passing
  (`python3 tests/test_generate.py`); the sample fragment was
  regenerated from the new generator.
- QEMU boot verification written as a draft only
  (`qemu-boot-verification-draft.md`): AST2600 / AST2700 EVB models,
  `.static.mtd` artifact, ten checkpoints. Explicitly NOT RUN — no
  image has been built, and the draft says so on its first line. It
  also states the mismatch plainly: there is no QEMU `ast2700-dcscm`
  machine, so QEMU cannot verify the DC-SCM board or its PFR capsule.

Drafted in Part 2 (design notes, not measured or tested results):
- Build time / sstate: see "Build time, sstate, and key safety" below.
  Build times are estimates, labelled as estimates, not measurements.
- Key safety: the form and spec never collect a password or a
  private key; SSH takes only a public-key path reference, and key
  provisioning stays a post-boot step. No credential is written into
  any file in this project.

Still open (not done, not claimed):
1. A real `bitbake obmc-phosphor-image` build for at least one preset
   machine, and the exact artifact filenames it produces.
2. A real QEMU boot run against that artifact, with a dated run log
   (the draft's checkpoints filled in from observed output).
3. Service-removal verification: what actually removes a service from
   the default image, if removal is ever required.
4. Hostname / network runtime provisioning automation (scripted
   Redfish / D-Bus first-boot configuration, or a custom layer with
   a systemd `.network` file).
5. SSH authorized-key provisioning automation.
6. Layer drift maintenance: re-checking the pinned tokens against
   each new upstream / SDK snapshot, since recipe and feature names
   move between releases.
7. Real-board verification (EVB, then DC-SCM hardware) — QEMU alone
   is never presented as board verification.

## Build time, sstate, and key safety (Part 2 design notes)

Build time — estimates only, not measurements:
- A first full OpenBMC build is a multi-hour job on a single
  workstation; plan on the order of 1–3 hours for a first build on a
  capable Linux build machine, longer on a small VM, shorter for
  rebuilds that hit cache. These are planning estimates from the
  project's earlier assessment, not timings from a run in this
  project, because no build has been run here yet. Measure the first
  real build and replace the estimate with the measured time.
- The build needs a Linux host (or WSL), plenty of disk (tens of GB
  for a full build tree plus downloads and sstate), and enough RAM
  for parallel BitBake tasks. Do not start a full build on a laptop
  that is also doing other heavy work without expecting it to take
  longer.

Sstate / shared downloads — direction, using standard Yocto
variables (not tree-pinned: no sstate mirror is configured in either
fetched tree):
- Keep `SSTATE_DIR` and `DL_DIR` outside the build directory so a
  wiped build tree does not wipe the cache and downloads with it.
  Both variables are referenced by the sample `local.conf`'s disk
  monitoring, which is the in-tree evidence that they are the knobs.
- Share one `SSTATE_DIR` / `DL_DIR` across machines that build the
  same layer revisions, so the second machine's build reuses the
  first machine's compiled tasks instead of rebuilding the world.
- For a team, add a shared sstate mirror (`SSTATE_MIRRORS`) on a
  file server or object store, with the mirror read before local
  sstate. This is standard Yocto practice; it is not configured or
  tested in this project, and mirror URLs and access are a deployment
  decision, not something the form collects.
- The GUI does not emit `SSTATE_DIR` / `DL_DIR` assignments: those
  paths are local to the build machine and must not be baked into a
  portable spec. They belong in the build machine's own `local.conf`,
  added by the engineer running the build.
- For incremental work, prefer single-recipe rebuilds
  (`bitbake -c compile -f <recipe>` / `bitbake <image>` after a
  small change) over full rebuilds, and keep the sstate cache warm
  between runs. This is workflow advice, not a tested result here.

Key and password safety — hard rules for this project:
- The form, the spec JSON, and the fragment never contain a password,
  a private key, or a pasted SSH key. SSH accepts only a public-key
  path reference, and that reference is a comment in the fragment,
  not an instruction that installs the key.
- Do not set a root password through this tool. OpenBMC's own
  default credential mechanism lives in the distro layer, but this
  project does not emit, record, or override it, and no credential
  value appears in any file here.
- Signing keys (for example, the PFR signing path used by the
  `ast2700-dcscm` machine) are build-server secrets. They are never
  form inputs, never spec fields, and never committed. If signing is
  needed, provide the key to the build server through its own secure
  mechanism (environment / secret store on that machine), and keep
  the signed artifact handling separate from the GUI spec.
- Any future key-provisioning feature must be designed as: public
  keys only, delivered to a running BMC through its authenticated
  management interface, with the private key never leaving the
  engineer's machine. Until that feature is designed and reviewed,
  key provisioning stays a documented post-boot TODO.

## Licence

Apache-2.0 (see `LICENSE`), matching the user's other portfolio repos.
