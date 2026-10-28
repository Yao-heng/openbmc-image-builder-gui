# QEMU boot verification — DRAFT, NOT RUN

Status: **draft only. No image has been built, no QEMU run has happened,
and nothing here is claimed as verified.** Run this only after a real
`bitbake obmc-phosphor-image` produces an artifact, and record the
actual output next to each checkpoint before calling anything "passed".

## What this draft covers — and what it does not

- It verifies a QEMU board model booting an OpenBMC image. It does not
  verify a real board, a DC-SCM board, PFR signing, or any hardware
  peripheral that QEMU does not model.
- QEMU machines (from QEMU's ASPEED support, not from the OpenBMC
  trees): `ast2600-evb` with `qemu-system-arm`, and `ast2700-evb`
  with `qemu-system-aarch64`. These are whole-SoC-plus-EVB models at
  register level, not electrical simulation.
- Important mismatch, stated plainly: there is a QEMU machine
  `ast2700-evb`, but there is no QEMU machine `ast2700-dcscm`.
  Booting an `ast2700-dcscm` build under `ast2700-evb` (if attempted)
  would test the SoC image, not the DC-SCM board or its PFR-signed
  capsule. DC-SCM verification needs real hardware; do not present a
  QEMU `ast2700-evb` boot as DC-SCM verification.
- QEMU gaps to keep in mind (from the earlier QEMU check, to re-confirm
  against the installed QEMU version before running): PWM / fan
  controller, slave GPIO, eSPI, MCTP, PCIe, and Super I/O are not
  modelled. Do not write test cases against them for QEMU.

## Prerequisites (all to confirm at run time)

1. A built image from `bitbake obmc-phosphor-image` for the machine
   under test. For `evb-ast2600`, the expected artifact is the
   `.static.mtd` file in `tmp/deploy/images/evb-ast2600/`; confirm the
   exact filename there — do not assume a name.
2. For `ast2700-dcscm`, confirm in `tmp/deploy/images/ast2700-dcscm/`
   which file is the unsigned `.static.mtd` and which is the
   PFR-signed capsule (see `part2-mapping.md`). Use the unsigned
   `.static.mtd` for QEMU, and record which file was actually used.
3. A QEMU build with ASPEED support (the ASPEED SDK tree ships qemu
   recipes; the upstream tree's QEMU version must be checked at run
   time — do not assume a version number here).
4. No password or private key is recorded in this draft. Log in as
   `root` with the credential configured for the image; that
   credential is deliberately not written here.

## Draft commands (to verify against the installed QEMU before running)

AST2600 (EVB model):

```sh
qemu-system-arm -m 1G -M ast2600-evb \
  -drive file=<path-to>/obmc-phosphor-image-evb-ast2600.static.mtd,format=raw,if=mtd \
  -nographic
```

AST2700 (EVB model only — see the mismatch note above):

```sh
qemu-system-aarch64 -M ast2700-evb \
  -drive file=<path-to>/obmc-phosphor-image-<machine>.static.mtd,format=raw,if=mtd \
  -nographic
```

Replace `<path-to>` and the image filename with the real build output.
If QEMU rejects `-M ast2600-evb` / `-M ast2700-evb`, stop and record
the QEMU version and its `-machine help` output instead of guessing
another machine name.

## Checkpoints (record actual output for each; a checkpoint is not
## "passed" until its output is observed)

1. **U-Boot / SPL output appears** on the serial console, then the
   kernel starts. Record the first and last lines seen.
2. **Kernel boots to a login prompt** without a fatal error loop.
   Note any repeated reboot: in OpenBMC RAS-style bring-up, a reboot
   with no error data is a symptom, not a pass.
3. **Login succeeds** as `root` with the image's configured
   credential (not recorded here).
4. **Hostname shows the runtime setting** — remember, hostname is a
   runtime setting (see `part2-mapping.md`), so check what the image
   actually reports, then apply the spec's hostname via
   phosphor-networkd and re-check. Do not expect the build fragment
   alone to have set it.
5. **Network interface is up**; record the interface name and address
   shown by the BMC. Then apply the spec's DHCP / static setting via
   phosphor-networkd and re-check. Do not expect the build fragment
   alone to have set it.
6. **Redfish is reachable**: the bmcweb service is up (this is the
   `obmc-bmcweb` feature). Record the HTTP response code for a
   Redfish root query; do not record any credential in the log.
7. **Web UI is served**: the `obmc-webui` feature is present; record
   that the Web UI page loads (content check only, no credential in
   the log).
8. **IPMI is present**: the `obmc-net-ipmi` / `obmc-host-ipmi`
   features are in the image. On QEMU, host IPMI hardware paths are
   limited by the model — record what actually responds and what does
   not, rather than marking IPMI "passed" from image contents alone.
9. **SSH is present**: `ssh-server-dropbear` is in the image. A
   login test needs a network path to the QEMU guest (user-mode
   networking port forwarding or a tap setup); record which path was
   used, or mark SSH "not tested over the network" if none was set up.
10. **Clean shutdown / poweroff** from the login prompt, without
    filesystem corruption messages on the next boot (if a second boot
    is run).

## After a run

- Append a dated run log (QEMU version, machine, image filename,
  checkpoint outputs, failures) to this file or a sibling run log.
  Until that log exists, this draft stays a draft.
- Failures in QEMU do not prove a real-board failure, and a QEMU pass
  does not prove a real-board pass. Say which one was tested, every
  time.
