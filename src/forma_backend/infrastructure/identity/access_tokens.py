"""Fixed-algorithm access JWT with a bounded, locally configured key ring."""

from datetime import datetime
from uuid import UUID, uuid4

import jwt
from forma_backend.modules.identity.sessions import AuthenticationFailed, Principal


class JwtAccessTokens:
    def __init__(
        self,
        key: str,
        issuer: str,
        audience: str,
        key_id: str = "v1",
        previous: tuple[str, str] | None = None,
    ) -> None:
        self._key = key
        self._issuer = issuer
        self._audience = audience
        self._key_id = key_id
        self._keys = {key_id: key}
        if previous:
            self._keys[previous[0]] = previous[1]

    def issue(self, principal: Principal, now: datetime) -> str:
        issued = int(now.timestamp())
        return jwt.encode(
            {
                "sub": str(principal.user_id),
                "sid": str(principal.session_id),
                "iss": self._issuer,
                "aud": self._audience,
                "iat": issued,
                "exp": issued + 600,
                "jti": str(uuid4()),
            },
            self._key,
            algorithm="HS256",
            headers={"kid": self._key_id},
        )

    def verify(self, token: str) -> Principal:
        try:
            if len(token) > 4096:
                raise ValueError()
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not isinstance(kid, str) or kid not in self._keys or header.get("alg") != "HS256":
                raise ValueError()
            value = jwt.decode(
                token,
                self._keys[kid],
                algorithms=["HS256"],
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": ["sub", "sid", "iss", "aud", "iat", "exp", "jti"],
                    "strict_aud": True,
                },
            )
            if (
                type(value["iat"]) is not int
                or type(value["exp"]) is not int
                or value["exp"] - value["iat"] != 600
            ):
                raise ValueError()
            if any(
                not isinstance(value.get(name), str) for name in ("sub", "sid", "iss", "aud", "jti")
            ):
                raise ValueError()
            UUID(value["jti"])
            return Principal(UUID(value["sub"]), UUID(value["sid"]))
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            raise AuthenticationFailed() from None
