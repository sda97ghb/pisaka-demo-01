from dataclasses import dataclass


@dataclass(kw_only=True)
class JWTAuthenticationOptions:
    public_key: str
    audience: str
    issuer: str
    algorithm: str = "RS256"
    leeway_sec: int = 60
