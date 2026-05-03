from rpod.config import Config, Target, load_config, save_config


def test_config_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(targets={"a100": Target(host="example.com", ssh_key="~/.ssh/id_ed25519")})

    save_config(cfg, path)

    loaded = load_config(path)
    assert loaded.targets["a100"].host == "example.com"
    assert loaded.targets["a100"].user == "root"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
