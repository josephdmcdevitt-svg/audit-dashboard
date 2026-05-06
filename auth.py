from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import bcrypt
import streamlit as st
import streamlit_authenticator as stauth
import yaml

DEFAULT_PATH = os.environ.get("AUTH_CONFIG_PATH", "auth_config.yaml")

# Passwords that are too weak to ever be allowed in a config file.
# bcrypt.checkpw is used to detect them regardless of salt.
FORBIDDEN_PASSWORDS = ("admin", "password", "changeme", "12345678")


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt(rounds=12)).decode()


def _password_matches(plaintext: str, hashed: str) -> bool:
    """Return True if the given hash was generated from the given plaintext."""
    try:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def _check_for_weak_passwords(cfg: dict[str, Any]) -> None:
    """Refuse to start if any user's password is in FORBIDDEN_PASSWORDS."""
    users = cfg.get("credentials", {}).get("usernames", {}) or {}
    for username, info in users.items():
        hashed = info.get("password", "")
        if not hashed:
            continue
        for weak in FORBIDDEN_PASSWORDS:
            if _password_matches(weak, hashed):
                raise SystemExit(
                    f"Refusing to start: user '{username}' has a forbidden default "
                    f"password ('{weak}'). Generate a new hash with "
                    f"'python -m auth --hash YOUR_NEW_PASSWORD' and update "
                    f"{DEFAULT_PATH} before starting the app."
                )


def load_config(path: str = DEFAULT_PATH) -> dict[str, Any]:
    if not Path(path).exists():
        bootstrap_pw = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
        if not bootstrap_pw:
            raise SystemExit(
                "No auth_config.yaml found and BOOTSTRAP_ADMIN_PASSWORD environment "
                "variable is not set. Set BOOTSTRAP_ADMIN_PASSWORD to a strong password "
                "of your choosing, then start the app again. The bootstrap admin user "
                "will be created automatically."
            )
        if bootstrap_pw.lower() in FORBIDDEN_PASSWORDS:
            raise SystemExit(
                f"BOOTSTRAP_ADMIN_PASSWORD is set to a forbidden default value. "
                f"Choose a stronger password and try again."
            )
        bootstrap = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "name": "Workspace Admin",
                        "email": "admin@example.com",
                        "password": hash_password(bootstrap_pw),
                        "roles": ["editor"],
                    }
                }
            },
            "cookie": {
                "name": "ledger_auth",
                "key": bcrypt.gensalt().decode(),
                "expiry_days": 7,
            },
        }
        Path(path).write_text(yaml.safe_dump(bootstrap))
        return bootstrap
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    _check_for_weak_passwords(cfg)
    return cfg


def get_authenticator() -> stauth.Authenticate:
    cfg = load_config()
    return stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie"]["name"],
        cfg["cookie"]["key"],
        cfg["cookie"]["expiry_days"],
    )


def render_login(auth: stauth.Authenticate) -> tuple[str | None, bool, str | None]:
    auth.login(location="main", key="login")
    return (
        st.session_state.get("name"),
        st.session_state.get("authentication_status"),
        st.session_state.get("username"),
    )


def get_role(username: str) -> str:
    cfg = load_config()
    creds = cfg.get("credentials", {}).get("usernames", {}).get(username, {})
    roles = creds.get("roles") or ["viewer"]
    return roles[0]


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--hash":
        print(hash_password(sys.argv[2]))
    else:
        print("Usage: python -m auth --hash <password>")
