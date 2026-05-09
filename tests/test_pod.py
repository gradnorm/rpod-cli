from rpod.pod import ssh_endpoint


def test_ssh_endpoint_handles_missing_runtime():
    assert ssh_endpoint({"runtime": None}) is None


def test_ssh_endpoint_handles_missing_ports():
    assert ssh_endpoint({"runtime": {}}) is None


def test_ssh_endpoint_extracts_public_ssh_port():
    pod = {
        "runtime": {
            "ports": [
                {
                    "ip": "1.2.3.4",
                    "privatePort": 22,
                    "publicPort": 22121,
                }
            ]
        }
    }

    assert ssh_endpoint(pod) == ("1.2.3.4", 22121)
