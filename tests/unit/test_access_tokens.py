from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from forma_backend.infrastructure.identity.access_tokens import JwtAccessTokens
from forma_backend.modules.identity.sessions import Principal, AuthenticationFailed


def test_key_rotation_and_claim_validation():
    principal = Principal(uuid4(), uuid4())
    now = datetime.now(UTC)
    old = JwtAccessTokens("a" * 64, "forma", "forma-web")
    token = old.issue(principal, now)
    rotated = JwtAccessTokens("b" * 64, "forma", "forma-web", "v2", ("v1", "a" * 64))
    assert rotated.verify(token) == principal
    with pytest.raises(AuthenticationFailed):
        old.verify(rotated.issue(principal, now))
    with pytest.raises(AuthenticationFailed):
        old.verify(old.issue(principal, now - timedelta(minutes=11)))
    with pytest.raises(AuthenticationFailed):
        JwtAccessTokens("c" * 64, "forma", "forma-web").verify(token)
    with pytest.raises(AuthenticationFailed):
        JwtAccessTokens("a" * 64, "wrong", "forma-web").verify(token)
    with pytest.raises(AuthenticationFailed):
        JwtAccessTokens("a" * 64, "forma", "wrong").verify(token)


@pytest.mark.parametrize("algorithm", ["none", "HS384"])
def test_algorithm_is_not_selected_by_untrusted_header(algorithm):
    token = jwt.encode(
        {"sub": str(uuid4())},
        "" if algorithm == "none" else "a" * 64,
        algorithm=algorithm,
        headers={"kid": "v1"},
    )
    with pytest.raises(AuthenticationFailed):
        JwtAccessTokens("a" * 64, "forma", "forma-web").verify(token)


@pytest.mark.parametrize("claim,value", [("sid", []), ("sid", 123), ("jti", {})])
def test_invalid_claim_types_fail_closed(claim, value):
    tokens = JwtAccessTokens("a" * 64, "forma", "forma-web")
    good = tokens.issue(Principal(uuid4(), uuid4()), datetime.now(UTC))
    payload = jwt.decode(good, "a" * 64, algorithms=["HS256"], audience="forma-web")
    payload[claim] = value
    invalid = jwt.encode(payload, "a" * 64, algorithm="HS256", headers={"kid": "v1"})
    with pytest.raises(AuthenticationFailed):
        tokens.verify(invalid)


def test_unknown_account_still_performs_password_verification():
    from contextlib import contextmanager
    from unittest.mock import Mock
    from forma_backend.modules.identity.sessions import SessionUseCases, SessionStore, DUMMY_HASH

    store = Mock(spec=SessionStore)
    store.user_by_email.return_value = None
    verifier = Mock()
    verifier.verify.return_value = False

    @contextmanager
    def work():
        yield store

    with pytest.raises(AuthenticationFailed):
        SessionUseCases(work, verifier, Mock()).login("missing@example.org", "secret-sentinel")
    verifier.verify.assert_called_once_with("secret-sentinel", DUMMY_HASH)
