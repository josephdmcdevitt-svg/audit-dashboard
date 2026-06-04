from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import bcrypt
import streamlit as st
import yaml

DEFAULT_PATH = os.environ.get("AUTH_CONFIG_PATH", "auth_config.yaml")

# Passwords that are too weak to ever be allowed in a config file.
# bcrypt.checkpw is used to detect them regardless of salt.
FORBIDDEN_PASSWORDS = ("admin", "password", "changeme", "12345678")


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------
# On Databricks Apps the platform already authenticates every request via
# workspace SSO and forwards the user's identity in request headers. Running
# a second login form there is redundant, and the local auth_config.yaml
# lives on an ephemeral filesystem anyway. So:
#   - Databricks mode: trust the forwarded headers, map role from EDITOR_EMAILS.
#   - Local mode: streamlit-authenticator with auth_config.yaml, as before.

def is_databricks() -> bool:
    return bool(os.environ.get("DATABRICKS_APP_NAME") or os.environ.get("DEV_FAKE_USER_EMAIL"))


def _editor_emails() -> set[str]:
    raw = os.environ.get("EDITOR_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def role_for_email(email: str) -> str:
    return "editor" if email.lower() in _editor_emails() else "viewer"


def databricks_identity() -> tuple[str, str] | None:
    """Return (display_name, email) from Databricks-forwarded headers, or None."""
    fake = os.environ.get("DEV_FAKE_USER_EMAIL")
    if fake:
        return (fake.split("@")[0], fake)
    try:
        headers = st.context.headers
    except Exception:
        return None
    email = headers.get("X-Forwarded-Email") or headers.get("x-forwarded-email")
    if not email:
        return None
    name = (
        headers.get("X-Forwarded-Preferred-Username")
        or headers.get("x-forwarded-preferred-username")
        or email
    )
    return (name, email)


# ---------------------------------------------------------------------------
# Local mode (streamlit-authenticator)
# ---------------------------------------------------------------------------

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


@lru_cache(maxsize=8)
def _load_config_cached(path: str, mtime_ns: int) -> dict[str, Any]:
    """Parse and validate the config once per file version.

    The mtime_ns argument exists purely to bust the cache when the file
    changes. The weak-password sweep runs bcrypt (deliberately slow), so it
    must NOT run on every Streamlit rerun; caching on (path, mtime) means it
    runs once per edit of the file instead.
    """
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    _check_for_weak_passwords(cfg)
    return cfg


def load_config(path: str = DEFAULT_PATH) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
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
                "BOOTSTRAP_ADMIN_PASSWORD is set to a forbidden default value. "
                "Choose a stronger password and try again."
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
        p.write_text(yaml.safe_dump(bootstrap))
    return _load_config_cached(path, p.stat().st_mtime_ns)


def get_authenticator():
    import streamlit_authenticator as stauth

    cfg = load_config()
    return stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie"]["name"],
        cfg["cookie"]["key"],
        cfg["cookie"]["expiry_days"],
    )


def render_login(auth) -> tuple[str | None, bool, str | None]:
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


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def resolve_user() -> tuple[str, str, str] | None:
    """Return (display_name, username, role) for the current request.

    Databricks mode: identity comes from SSO headers; returns None only if
    the headers are missing (misconfiguration), after showing an error.
    Local mode: renders the login form; returns None until signed in.
    """
    if is_databricks():
        ident = databricks_identity()
        if ident is None:
            st.error(
                "Could not read your identity from the request headers. "
                "This app expects to run behind Databricks Apps SSO."
            )
            return None
        name, email = ident
        return (name, email, role_for_email(email))

    authenticator = get_authenticator()
    name, status, username = render_login(authenticator)
    if status is False:
        st.error("Username/password incorrect.")
        return None
    if status is None:
        st.info("Please sign in to continue.")
        return None
    return (name, username, get_role(username))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--hash":
        print(hash_password(sys.argv[2]))
    else:
        print("Usage: python -m auth --hash <password>")
