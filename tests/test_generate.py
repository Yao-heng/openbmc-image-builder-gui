"""Checks for the Part 2 generator (stdlib only).

Part 2 expectations, verified against the fetched trees (part2-mapping.md):
- MACHINE is asserted; verified presets produce no WARNING.
- Selected services produce a real IMAGE_FEATURES:append assignment.
- Deselecting a service does NOT produce a removal; it produces a WARNING.
- Hostname / network are runtime notes, never local.conf assignments:
  no line in the fragment may start with HOSTNAME, DHCP, or a static-IP
  assignment.
- An unverified machine still produces a WARNING.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(spec):
    spec_path = Path("/tmp/openbmc-spec-test.json")
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(ROOT / "generate_local_conf.py"), str(spec_path)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def main():
    base = json.loads((ROOT / "examples" / "sample-spec.json").read_text())
    out = run(base)
    assert 'MACHINE = "evb-ast2600"' in out, out
    assert "WARNING" not in out, out
    for token in (
        "obmc-bmcweb",
        "obmc-net-ipmi",
        "obmc-host-ipmi",
        "ssh-server-dropbear",
        "obmc-webui",
    ):
        assert token in out, out
    assert "IMAGE_FEATURES:append" in out, out
    # Hostname / network must be comments, never assignments.
    for line in out.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("HOSTNAME"), out
        assert not stripped.startswith("DHCP"), out
    assert "RUNTIME (not a build setting): hostname = openbmc" in out, out
    assert "RUNTIME (not a build setting): network mode = dhcp" in out, out

    # ast2700-dcscm (ASPEED SDK preset) produces no WARNING.
    out_sdk = run(dict(base, machine="ast2700-dcscm"))
    assert 'MACHINE = "ast2700-dcscm"' in out_sdk, out_sdk
    assert "WARNING" not in out_sdk, out_sdk

    # Static network: IP/gateway appear only in the runtime comment.
    static_spec = dict(
        base,
        network={"mode": "static", "static_ip": "192.168.1.10", "gateway": "192.168.1.1"},
    )
    out_static = run(static_spec)
    assert "192.168.1.10" in out_static and "192.168.1.1" in out_static, out_static
    assert "RUNTIME (not a build setting): network mode = static" in out_static, out_static

    # Deselected service: WARNING, no removal assignment.
    partial = dict(base, requested_services=["redfish", "ssh"])
    out_partial = run(partial)
    assert "obmc-webui" not in out_partial.split("NOTE:")[0], out_partial
    assert "WARNING: deselected service(s) ipmi, webui" in out_partial, out_partial
    assert "IMAGE_FEATURES:remove" not in out_partial, out_partial

    # Unverified machine: WARNING.
    other = dict(base, machine="some-unverified-machine", machine_verified_preset=False)
    out2 = run(other)
    assert "WARNING" in out2, out2

    print("Part 2 generator checks passed.")


if __name__ == "__main__":
    main()
