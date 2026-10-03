# app/utils/email_validation.py

from email_validator import validate_email, EmailNotValidError
import dns.resolver

# ---------------------------------------------------------------------------
# 1. Allowed domains (whitelist)
# ---------------------------------------------------------------------------
ALLOWED_DOMAINS = {
    # Major free providers
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.co.in",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "aol.com",
    "zoho.com",
    "yandex.com",
    "mail.com",
    "gmx.com",
    "gmx.net",
}

# Optional: allow any domain that ends with these education suffixes
EDU_SUFFIXES = (
    ".edu",
    ".ac.uk",
    ".edu.au",
    ".edu.sg",
    ".edu.my",
    ".ac.nz",
    ".edu.cn",
    ".ac.jp",
    ".edu.in",
)

# Existing disposable list
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "10minutemail.com", "throwaway.email", "yopmail.com",
    "trashmail.com", "getnada.com", "temp-mail.org",
    "fakeinbox.com", "sharklasers.com", "guerrillamailblock.com",
    "maildrop.cc", "dispostable.com", "mailnesia.com",
    "tempail.com", "emailondeck.com", "mohmal.com", "discard.email",
}


def is_email_deliverable(email: str) -> tuple[bool, str]:
    """
    Strict validation:
    1. Format check
    2. Must be in ALLOWED_DOMAINS or end with an EDU_SUFFIX
    3. Must NOT be disposable
    4. Soft MX / A record check (fail-open on DNS problems)

    All rejection cases return exactly: "email does not exist"
    """
    email = (email or "").strip().lower()

    # 1. Basic format
    try:
        validated = validate_email(email, check_deliverability=False)
        email = validated.normalized
    except EmailNotValidError:
        return False, "email does not exist"

    domain = email.split("@")[-1]

    # 2. Whitelist check
    is_allowed = (
        domain in ALLOWED_DOMAINS
        or any(domain.endswith(suffix) for suffix in EDU_SUFFIXES)
    )
    if not is_allowed:
        return False, "email does not exist"

    # 3. Explicit disposable block
    if domain in DISPOSABLE_DOMAINS:
        return False, "email does not exist"

    # 4. Soft MX / A record check
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=3.0)
        if not answers:
            try:
                dns.resolver.resolve(domain, "A", lifetime=2.0)
            except Exception:
                return False, "email does not exist"
    except dns.resolver.NXDOMAIN:
        return False, "email does not exist"
    except (
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
        dns.resolver.LifetimeError,
        Exception,
    ):
        # Fail-open on DNS issues
        pass

    return True, ""