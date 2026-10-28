# Part 2 mapping — verified against the fetched trees

Tree roots (local, not published):
- Upstream: `~/workspace/openbmc-code/openbmc-main` (snapshot 2026-10-24)
- ASPEED SDK: `~/workspace/openbmc-code/aspeedtech-openbmc` (2026-10-08)

Paths below are relative to the tree root named in each row.
A row marked RUNTIME or TODO is not a local.conf assignment, by design:
no variable was found in either tree, and none is invented here.

## Machines (unchanged from Part 1)

| Form preset | Source | Notes |
|---|---|---|
| `evb-ast2500` | Upstream `meta-evb/meta-evb-aspeed/meta-evb-ast2500/conf/machine/evb-ast2500.conf` | meta-evb conf. |
| `evb-ast2600` | Upstream `meta-evb/meta-evb-aspeed/meta-evb-ast2600/conf/machine/evb-ast2600.conf` | `KERNEL_DEVICETREE = "aspeed/aspeed-ast2600-evb.dtb"`, `UBOOT_MACHINE = "ast2600_openbmc_spl_defconfig"`, `FLASH_SIZE = "65536"`, `SERIAL_CONSOLES = "115200;ttyS4"`. |
| `ast2700-dcscm` | SDK `meta-aspeed-sdk/meta-aspeed-pfr/meta-ast2700-pfr/conf/machine/ast2700-dcscm.conf` | Requires `ast2700-sdk.inc`, `obmc-bsp-common.inc`, `intel-pfr.inc`; `UBOOT_MACHINE = "evb-ast2700_defconfig"`, `KERNEL_DEVICETREE` includes `aspeed/ast2700-dcscm.dtb`, `FLASH_SIZE = "65536"`, `MACHINE_FEATURES` includes `obmc-host-ipmi`, `PREFERRED_PROVIDER_virtual/obmc-host-ipmi-hw = "phosphor-ipmi-kcs"`. |
| `evb-ast2700` (NOT offered) | No such Yocto machine conf found in either tree | Do not add. `ast2700a1-evb` is a QEMU `-machine` value, not a Yocto `MACHINE`. |

## Services — pinned to IMAGE_FEATURES

Default image, both trees:
`meta-phosphor/recipes-phosphor/images/obmc-phosphor-image.bb`
`IMAGE_FEATURES +=` includes `obmc-bmcweb`, `obmc-host-ipmi`,
`obmc-net-ipmi`, `obmc-webui`, `ssh-server-dropbear`, and
`obmc-network-mgmt`, among others. A diff of the SDK copy against the
upstream copy shows the feature list unchanged; the SDK difference is
in the rootfs postprocess (pam login environment), not in services.

Feature definitions, upstream:
`meta-phosphor/classes/obmc-phosphor-image.bbclass`

| Form service | IMAGE_FEATURES token(s) | Definition / package |
|---|---|---|
| Redfish | `obmc-bmcweb` | bbclass comment: "OpenBMC webserver". `FEATURE_PACKAGES_obmc-bmcweb = "packagegroup-obmc-apps-bmcweb"`. Packagegroup (`meta-phosphor/recipes-phosphor/packagegroups/packagegroup-obmc-apps.bb`): `RDEPENDS:${PN}-bmcweb = "bmcweb phosphor-certificate-manager"`. There is no separate `redfish` IMAGE_FEATURE token in the tree; `obmc-bmcweb` is the token. The Redfish implementation itself lives in the external bmcweb repo, not in these trees, so Redfish version/features are not pinned here. |
| IPMI | `obmc-net-ipmi`, `obmc-host-ipmi` | `FEATURE_PACKAGES_obmc-net-ipmi = phosphor-ipmi-net` unless `DISTRO_FEATURES` contains `phosphor-no-ipmi-rmcp`. `FEATURE_PACKAGES_obmc-host-ipmi = virtual-obmc-host-ipmi-hw` when `COMBINED_FEATURES` contains `obmc-host-ipmi`. SDK `ast2700-dcscm.conf` pins the host provider to `phosphor-ipmi-kcs`. Recipes present in-tree: `phosphor-ipmi-net_git.bb`, `phosphor-ipmi-host_git.bb`, `phosphor-ipmi-kcs_git.bb`. |
| SSH | `ssh-server-dropbear` | OE-core image feature, already in the default image list. Dropbear is the default SSH server in this image; `ssh-server-openssh` is a different feature and is not offered by the form (TODO if ever needed). |
| Web UI | `obmc-webui` | `FEATURE_PACKAGES_obmc-webui = "packagegroup-obmc-apps-webui"`. Packagegroup: `RDEPENDS:${PN}-webui = "webui-vue"` (empty under `df-phosphor-no-webui`). |

Generator behaviour (both `generate_local_conf.py` and `index.html`):
- Selected services are emitted as one real assignment:
  `IMAGE_FEATURES:append = " <tokens> "`.
- Because the tokens are already in the default image, the append makes
  the selection explicit for a custom image recipe; it does not add
  packages beyond the default image.
- Deselected services are NOT removed. No removal mapping was verified,
  so the fragment emits a WARNING and no `IMAGE_FEATURES:remove`.
  Shipping a deselected fragment as a "service-excluded" image would be
  false: the default image would still include the service.

## Hostname and network — RUNTIME, not local.conf

Status: NOT pinned as build assignments. Searched, in both trees:
`meta-phosphor` machine/distro confs, `meta-evb` machine confs,
`meta-aspeed-sdk` machine confs, and `recipes-phosphor/network`.
No local.conf variable for BMC hostname, DHCP, or static IP was found,
and no `/etc/hostname` handling was found in these trees.

What actually manages them:
- `meta-phosphor/recipes-phosphor/network/phosphor-network_git.bb`
  (upstream SRCREV differs from SDK SRCREV; both set the same
  `PACKAGECONFIG ??= "default-link-local-autoconf default-ipv6-accept-ra persist-mac"`).
  It builds phosphor-networkd from the external
  `github.com/openbmc/phosphor-networkd` repo, installs the service
  `xyz.openbmc_project.Network.service`, and ships
  `60-phosphor-networkd-default.network` from that external repo.
  That `.network` file is not in these trees, so its contents are not
  quoted here.
- Consequence for the form: hostname and network fields are recorded
  in the fragment as commented runtime notes only. After first boot,
  set them via phosphor-networkd (Redfish network settings or the
  D-Bus `xyz.openbmc_project.Network` interface). For a reproducible
  fleet setting, the correct mechanism is a systemd `.network` file
  shipped in a custom layer — future work, not generated here.
- Do NOT write `HOSTNAME = "..."`, a DHCP variable, or a static-IP
  variable into local.conf on the basis of this project: none was
  found, and a guessed variable would silently do nothing.

## SSH key provisioning — TODO, post-boot

No build-time local.conf variable for injecting an authorized SSH key
was found in either tree. The form therefore keeps only a public-key
path reference, never a pasted key and never a private key. Key
provisioning is a post-boot step (user management / Redfish key
upload in the running BMC). Do not invent an `AUTHORIZED_KEYS`
variable.

## Image artifact kind — downstream selection, not a build assignment

- Upstream `meta-phosphor/conf/machine/include/image-type/static.inc`:
  `IMAGE_FSTYPES += "mtd-static mtd-static-tar mtd-static-alltar"`.
- Upstream `meta-phosphor/classes/image_types_phosphor.bbclass`:
  `do_generate_static` builds `${IMAGE_NAME}.static.mtd` sized by
  `FLASH_SIZE`.
- SDK: `meta-aspeed-sdk/meta-aspeed-pfr/recipes-core/images/obmc-phosphor-image.bbappend`
  hooks `do_generate_static` to generate a PFR manifest and a signed
  capsule (`bmc_signed_cap.static.mtd.tar`). The unsigned
  `.static.mtd` from `obmc-phosphor-image` is therefore the file to
  use for QEMU; confirm the exact filename in
  `tmp/deploy/images/<machine>/` on the first SDK build, because the
  PFR-signed artifact is a different file.
- The form's `static.mtd` / `tar` choice therefore selects which
  artifact to use downstream (QEMU / flash), not a variable to set
  in local.conf. Emitting `IMAGE_FSTYPES = "mtd-static"` would
  override the default list and is not done.

## Still unpinned (TODO, not guessed)

1. Service removal (`IMAGE_FEATURES:remove` behaviour) — needs a real
   build to verify; the fragment warns instead of removing.
2. Hostname / network runtime provisioning automation (scripted
   Redfish / D-Bus first-boot configuration, or a custom layer with
   a `.network` file).
3. SSH authorized-key provisioning automation.
4. `ssh-server-openssh` as an alternative to dropbear.
5. Exact QEMU artifact filename for `ast2700-dcscm` (see
   `qemu-boot-verification-draft.md`).
