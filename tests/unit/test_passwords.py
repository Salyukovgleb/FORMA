import pytest
from forma_backend.infrastructure.identity.passwords import ScryptPasswordHasher


def test_salted_password_hash_and_verification():
    hasher = ScryptPasswordHasher()
    first = hasher.hash("correct horse battery")
    second = hasher.hash("correct horse battery")
    assert first != second and "correct horse" not in first
    assert hasher.verify("correct horse battery", first)
    assert not hasher.verify("wrong password value", first)


@pytest.mark.parametrize(
    "encoded", ["bad", "scrypt$v1$999999999$8$1$aa$bb", "scrypt$v1$32768$8$1$aa$bb"]
)
def test_untrusted_hash_parameters_do_not_trigger_work(encoded, monkeypatch):
    hasher = ScryptPasswordHasher()

    def forbidden(*args, **kwargs):
        raise AssertionError("Malformed hash must not perform KDF work")

    monkeypatch.setattr(hasher, "_derive", forbidden)
    assert not hasher.verify("correct horse battery", encoded)


def test_hash_capacity_is_bounded(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Event
    from forma_backend.infrastructure.identity import passwords

    entered = Barrier(3)
    release = Event()

    def derive(*args, **kwargs):
        assert (kwargs["n"], kwargs["r"], kwargs["p"], kwargs["dklen"], kwargs["maxmem"]) == (
            32768,
            8,
            1,
            64,
            64 * 1024 * 1024,
        )
        assert len(kwargs["salt"]) == 16
        entered.wait(timeout=3)
        assert release.wait(timeout=3)
        return b"x" * 64

    monkeypatch.setattr(passwords.hashlib, "scrypt", derive)
    hasher = ScryptPasswordHasher()
    with ThreadPoolExecutor(max_workers=2) as pool:
        work = [pool.submit(hasher.hash, "correct horse battery") for _ in range(2)]
        try:
            entered.wait(timeout=3)
            with pytest.raises(passwords.PasswordCapacityExceeded):
                hasher.hash("correct horse battery")
        finally:
            release.set()
        for future in work:
            assert future.result().startswith("scrypt$v1$")
