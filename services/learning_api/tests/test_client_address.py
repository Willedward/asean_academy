from types import SimpleNamespace

from learning_api.abuse import (
    CLIENT_ADDRESS_HEADER,
    CLIENT_ADDRESS_SIGNATURE_HEADER,
    client_address_signature,
    client_ip,
)

SECRET = "test-secret"
ADDRESS = "203.0.113.7"


def request(headers):
    return SimpleNamespace(client=SimpleNamespace(host="198.51.100.1"), headers=headers)


def test_signature_matches_the_web_proxy():
    assert client_address_signature(SECRET, ADDRESS) == "2122bc91ce2ddbe6a40a41de2babfb9bb875f51ac727e452281448662dca27f5"


def test_signed_client_address_is_used():
    headers = {
        CLIENT_ADDRESS_HEADER: ADDRESS,
        CLIENT_ADDRESS_SIGNATURE_HEADER: client_address_signature(SECRET, ADDRESS),
    }
    assert client_ip(request(headers), trust_proxy_headers=False, proxy_secret=SECRET) == ADDRESS


def test_unsigned_or_wrongly_signed_client_address_is_ignored():
    for signature in ("", "not-a-signature", client_address_signature("other", ADDRESS)):
        headers = {CLIENT_ADDRESS_HEADER: ADDRESS, CLIENT_ADDRESS_SIGNATURE_HEADER: signature}
        assert (
            client_ip(request(headers), trust_proxy_headers=False, proxy_secret=SECRET)
            == "198.51.100.1"
        )


def test_signature_does_not_cover_another_address():
    headers = {
        CLIENT_ADDRESS_HEADER: "203.0.113.8",
        CLIENT_ADDRESS_SIGNATURE_HEADER: client_address_signature(SECRET, ADDRESS),
    }
    assert (
        client_ip(request(headers), trust_proxy_headers=False, proxy_secret=SECRET)
        == "198.51.100.1"
    )


def test_client_address_needs_a_secret():
    headers = {CLIENT_ADDRESS_HEADER: ADDRESS, CLIENT_ADDRESS_SIGNATURE_HEADER: "anything"}
    assert client_ip(request(headers), trust_proxy_headers=False) == "198.51.100.1"
