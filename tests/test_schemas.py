from medialab_bot.schemas.system import HealthResponse


def test_health_response_parses():
    data = {"status": "online", "uptime_seconds": 123.45, "vpn_interface_bound": True}
    model = HealthResponse(**data)
    assert model.status == "online"
    assert model.uptime_seconds == 123.45
    assert model.vpn_interface_bound is True


def test_health_response_vpn_false():
    data = {"status": "online", "uptime_seconds": 0.0, "vpn_interface_bound": False}
    model = HealthResponse(**data)
    assert model.vpn_interface_bound is False
