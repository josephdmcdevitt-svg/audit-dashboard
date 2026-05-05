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


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt(rounds=12)).decode()


def load_config(path: str = DEFAULT_PATH) -> dict[str, Any]:
    if not Path(path).exists():
        bootstrap = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "name": "Workspace Admin",
                        "email": "admin@example.com",
                        "password": hash_password("admin"),
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
        return yaml.safe_load(fh)


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
