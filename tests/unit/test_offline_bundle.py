"""Offline profile: model export for the bundle, the ui no-egress entrypoint, compose hardening.

The runtime proof (no egress from any container, ui port reachable from the host, the app still
answers) is offline-bundle/verify-offline.sh; these tests pin the pieces it relies on.
"""

from __future__ import annotations

import importlib.util
import json
import struct
import tarfile
from pathlib import Path

import pytest
import yaml
from export_ollama_models import collect, export, main, manifest_path

ROOT = Path(__file__).resolve().parents[2]


def _load_entrypoint():
    spec = importlib.util.spec_from_file_location(
        "no_egress_entrypoint", ROOT / "frontend" / "no_egress_entrypoint.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


entrypoint = _load_entrypoint()


# --- export_ollama_models ---------------------------------------------------------------


def _add_model(store: Path, name: str, tag: str, blobs: dict[str, bytes]) -> None:
    digests = list(blobs)
    manifest = {
        "schemaVersion": 2,
        "config": {"digest": digests[0], "size": len(blobs[digests[0]])},
        "layers": [{"digest": d, "size": len(blobs[d])} for d in digests[1:]],
    }
    mdir = store / "manifests" / "registry.ollama.ai" / "library" / name
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / tag).write_text(json.dumps(manifest))
    (store / "blobs").mkdir(exist_ok=True)
    for digest, data in blobs.items():
        (store / "blobs" / digest.replace(":", "-")).write_bytes(data)


@pytest.fixture
def store(tmp_path: Path) -> Path:
    s = tmp_path / "models"
    _add_model(s, "llm", "4b", {"sha256:aa": b"cfg", "sha256:bb": b"weights", "sha256:ss": b"L"})
    _add_model(s, "embed", "latest", {"sha256:cc": b"cfg2", "sha256:dd": b"w2", "sha256:ss": b"L"})
    _add_model(s, "other", "latest", {"sha256:ee": b"x", "sha256:ff": b"unrelated"})
    return s


def test_manifest_path_defaults_namespace_and_tag(tmp_path: Path) -> None:
    base = tmp_path / "manifests" / "registry.ollama.ai"
    assert manifest_path(tmp_path, "bge-m3") == base / "library" / "bge-m3" / "latest"
    assert manifest_path(tmp_path, "gemma4:e4b") == base / "library" / "gemma4" / "e4b"
    assert manifest_path(tmp_path, "org/model:q4") == base / "org" / "model" / "q4"


def test_export_copies_only_requested_models_with_shared_blobs_once(
    store: Path, tmp_path: Path
) -> None:
    out = tmp_path / "models.tar"
    export(store, ["llm:4b", "embed"], out)
    with tarfile.open(out) as tar:
        names = tar.getnames()
    assert "models/manifests/registry.ollama.ai/library/llm/4b" in names
    assert "models/manifests/registry.ollama.ai/library/embed/latest" in names
    blobs = sorted(n.rsplit("/", 1)[1] for n in names if "/blobs/" in n)
    assert blobs == ["sha256-aa", "sha256-bb", "sha256-cc", "sha256-dd", "sha256-ss"]
    assert not any("other" in n or "sha256-ee" in n for n in names)


def test_missing_model_or_blob_is_reported(store: Path, tmp_path: Path) -> None:
    (store / "blobs" / "sha256-bb").unlink()
    with pytest.raises(FileNotFoundError, match=r"llm:4b: blob sha256-bb"):
        collect(store, ["llm:4b"])
    assert main(["--store", str(store), "--out", str(tmp_path / "x.tar"), "nope"]) == 1


# --- no_egress_entrypoint ---------------------------------------------------------------

ROUTES = (
    "Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT\n"
    "eth1\t00000000\t010015AC\t0003\t0\t0\t0\t00000000\t0\t0\t0\n"
    "eth0\t000013AC\t00000000\t0001\t0\t0\t0\t0000FFFF\t0\t0\t0\n"
    "eth1\t000015AC\t00000000\t0001\t0\t0\t0\t0000FFFF\t0\t0\t0\n"
)


def test_default_routes_parses_proc_net_route(tmp_path: Path) -> None:
    table = tmp_path / "route"
    table.write_text(ROUTES)
    # gateway kept in /proc byte order: 010015AC is 172.21.0.1
    assert entrypoint.default_routes(str(table)) == [("eth1", 0x010015AC)]
    header, _default, *subnets = ROUTES.splitlines(keepends=True)
    table.write_text(header + "".join(subnets))  # after removal: only directly connected subnets
    assert entrypoint.default_routes(str(table)) == []


def test_rtentry_matches_lp64_layout() -> None:
    entry = entrypoint.rtentry(0x010015AC)
    assert len(entry) == 120  # sizeof(struct rtentry) on amd64 / arm64
    family = struct.unpack_from("<H", entry, 24)[0]  # rt_gateway follows rt_pad1 + rt_dst
    assert family == 2  # AF_INET
    assert entry[28:32] == bytes([172, 21, 0, 1])  # network byte order on the wire
    assert struct.unpack_from("<H", entry, 56)[0] == 0x0003  # RTF_UP | RTF_GATEWAY


def test_entrypoint_refuses_to_run_without_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entrypoint.os, "getuid", lambda: 10001)
    with pytest.raises(SystemExit, match="must start as root"):
        entrypoint.main(["streamlit"])


def test_entrypoint_drops_routes_then_privileges_then_execs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(entrypoint.os, "getuid", lambda: 0)
    monkeypatch.setattr(entrypoint, "drop_default_routes", lambda: calls.append("routes"))
    monkeypatch.setattr(entrypoint, "drop_privileges", lambda: calls.append("privileges"))
    monkeypatch.setattr(entrypoint.os, "execvp", lambda f, a: calls.append(f"exec {a}"))
    entrypoint.main(["streamlit", "run", "app.py"])
    assert calls == ["routes", "privileges", "exec ['streamlit', 'run', 'app.py']"]


# --- compose hardening ------------------------------------------------------------------


class _ComposeLoader(yaml.SafeLoader):
    pass


for _tag in ("!reset", "!override"):
    _ComposeLoader.add_constructor(
        _tag,
        lambda loader, node: (
            loader.construct_sequence(node)
            if isinstance(node, yaml.SequenceNode)
            else loader.construct_mapping(node)
            if isinstance(node, yaml.MappingNode)
            else loader.construct_scalar(node) or None
        ),
    )


def _compose(name: str) -> dict:
    return yaml.load((ROOT / name).read_text(encoding="utf-8"), Loader=_ComposeLoader)


def test_base_compose_publishes_ports_on_loopback_only() -> None:
    for name, svc in _compose("docker-compose.yml")["services"].items():
        for port in svc.get("ports", []):
            assert port.startswith("127.0.0.1:"), f"{name} publishes {port} beyond loopback"


def test_offline_compose_keeps_backends_internal_and_ui_without_egress() -> None:
    offline = _compose("docker-compose.offline.yml")
    services, networks = offline["services"], offline["networks"]
    assert networks["internal_only"]["internal"] is True
    for name in ("db", "ollama", "api"):
        assert services[name]["networks"] == ["internal_only"]
        assert services[name]["ports"] == []
    ui = services["ui"]
    assert ui["entrypoint"] == ["python", "/app/no_egress_entrypoint.py"]
    assert ui["cap_drop"] == ["ALL"]
    assert set(ui["cap_add"]) == {"NET_ADMIN", "SETUID", "SETGID"}
    assert "no-new-privileges:true" in ui["security_opt"]
    assert ui["dns"] == ["127.0.0.1"]
    assert all(p.startswith("127.0.0.1:") for p in ui["ports"])
    assert offline["services"]["api"]["environment"]["ALLOW_EXTERNAL_LLM"] == "false"


def test_ui_image_ships_the_entrypoint() -> None:
    dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    assert "frontend/no_egress_entrypoint.py" in dockerfile
