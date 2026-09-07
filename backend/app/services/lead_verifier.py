import re
import socket
import ipaddress
import asyncio
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List, Set
import httpx
from ..models.enums import VerificationStatus

try:
    import dns.resolver
    HAS_DNS_PYTHON = True
except ImportError:
    HAS_DNS_PYTHON = False

# ---------------------------------------------------------------------------
# Hard acceptance threshold — every lead must meet or exceed this
# score (70) to be accepted / verified. Enforced strictly server-side.
# ---------------------------------------------------------------------------
VERIFICATION_ACCEPTANCE_THRESHOLD: int = 70
IMPORT_ACCEPTANCE_THRESHOLD: int = VERIFICATION_ACCEPTANCE_THRESHOLD

# ---------------------------------------------------------------------------
# Disposable / Burner email domains
# ---------------------------------------------------------------------------
DISPOSABLE_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com",
    "yopmail.com", "trashmail.com", "fakeinbox.com", "dispostable.com",
    "temp-mail.org", "throwawaymail.com", "burnermail.io", "getairmail.com",
    "sharklasers.com", "grr.la", "pokemail.net", "spam4.me", "bccto.me",
    "mailnull.com", "spamgourmet.com", "trashmail.me", "wegwerfmail.de",
    "mytempemail.com", "nada.ltd", "crazymailing.com", "mohmal.com",
    "inboxkitten.com", "getnada.com", "fakemailgenerator.com"
}

# ---------------------------------------------------------------------------
# Common parked domain signatures
# ---------------------------------------------------------------------------
PARKED_DOMAIN_SIGNATURES = [
    "domain is for sale", "buy this domain", "hugedomains", "dan.com",
    "sedoparking", "parked domain", "godaddy domain parking",
    "this domain is parked", "under construction", "domain name has been registered",
    "renew your domain", "domain expired"
]

# ---------------------------------------------------------------------------
# SSRF Guard definitions
# ---------------------------------------------------------------------------
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "metadata.google.internal", "instance-data", "169.254.169.254"}

# Country calling codes for international format detection
COUNTRY_CODES = {
    "1", "7", "20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "41",
    "43", "44", "45", "46", "47", "48", "49", "51", "52", "53", "54", "55", "56",
    "57", "58", "60", "61", "62", "63", "64", "65", "66", "81", "82", "84", "86",
    "90", "91", "92", "93", "94", "95", "98", "212", "213", "216", "218", "220",
    "221", "222", "223", "224", "225", "226", "227", "228", "229", "230", "231",
    "232", "233", "234", "235", "236", "237", "238", "239", "240", "241", "242",
    "243", "244", "245", "246", "247", "248", "249", "250", "251", "252", "253",
    "254", "255", "256", "257", "258", "260", "261", "262", "263", "264", "265",
    "266", "267", "268", "269", "291", "297", "298", "299", "350", "351", "352",
    "353", "354", "355", "356", "357", "358", "359", "370", "371", "372", "373",
    "374", "375", "376", "377", "378", "380", "381", "382", "385", "386", "387",
    "389", "420", "421", "423", "500", "501", "502", "503", "504", "505", "506",
    "507", "508", "509", "590", "591", "592", "593", "594", "595", "596", "597",
    "598", "599", "670", "672", "673", "674", "675", "676", "677", "678", "679",
    "680", "681", "682", "683", "685", "686", "687", "688", "689", "690", "691",
    "692", "850", "852", "853", "855", "856", "880", "886", "960", "961", "962",
    "963", "964", "965", "966", "967", "968", "970", "971", "972", "973", "974",
    "975", "976", "977", "992", "993", "994", "995", "996", "998",
}

# Plausible job role keywords
PROFESSIONAL_ROLES = {
    "ceo", "cto", "cfo", "coo", "cmo", "cio", "president", "director", "manager",
    "head", "lead", "engineer", "developer", "architect", "doctor", "physician",
    "consultant", "specialist", "executive", "officer", "founder", "partner",
    "principal", "scientist", "analyst", "administrator", "vp", "vice president",
    "nurse", "surgeon", "attorney", "counsel", "advisor", "coordinator", "strategist"
}


# ---------------------------------------------------------------------------
# Verification Cache
# ---------------------------------------------------------------------------
class VerificationCache:
    """In-memory cache for DNS, MX, and website reachability/metadata."""
    def __init__(self):
        self.mx_cache: Dict[str, Tuple[bool, str, List[str]]] = {}
        self.website_cache: Dict[str, Tuple[bool, str, int, str, bool]] = {}
        self.host_safety_cache: Dict[str, bool] = {}

    def get_mx(self, domain: str) -> Optional[Tuple[bool, str, List[str]]]:
        return self.mx_cache.get(domain.lower().strip())

    def set_mx(self, domain: str, result: Tuple[bool, str, List[str]]) -> None:
        self.mx_cache[domain.lower().strip()] = result

    def get_website(self, url: str) -> Optional[Tuple[bool, str, int, str, bool]]:
        return self.website_cache.get(url.lower().strip())

    def set_website(self, url: str, result: Tuple[bool, str, int, str, bool]) -> None:
        self.website_cache[url.lower().strip()] = result

    def get_host_safety(self, hostname: str) -> Optional[bool]:
        return self.host_safety_cache.get(hostname.lower().strip())

    def set_host_safety(self, hostname: str, is_safe: bool) -> None:
        self.host_safety_cache[hostname.lower().strip()] = is_safe


# ---------------------------------------------------------------------------
# SSRF Security Helpers
# ---------------------------------------------------------------------------
def is_safe_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in PRIVATE_IP_RANGES:
            if ip in net:
                return False
        return True
    except ValueError:
        return False


def is_safe_hostname(hostname: str, cache: Optional[VerificationCache] = None) -> bool:
    if not hostname:
        return False
    host_clean = hostname.strip().lower()
    if host_clean in BLOCKED_HOSTNAMES or host_clean.endswith(".localhost"):
        return False

    if cache is not None:
        cached = cache.get_host_safety(host_clean)
        if cached is not None:
            return cached

    try:
        addr_info = socket.getaddrinfo(host_clean, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            if not is_safe_ip(ip_str):
                if cache is not None:
                    cache.set_host_safety(host_clean, False)
                return False
        if cache is not None:
            cache.set_host_safety(host_clean, True)
        return True
    except Exception:
        if cache is not None:
            cache.set_host_safety(host_clean, False)
        return False


# ---------------------------------------------------------------------------
# Email Helpers
# ---------------------------------------------------------------------------
def verify_email_syntax(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    email_clean = email.strip()
    regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(regex, email_clean))


# ---------------------------------------------------------------------------
# Phone Validation Helper
# ---------------------------------------------------------------------------
def validate_phone(phone: Optional[str]) -> Tuple[bool, str, bool]:
    """
    Validates a phone number string.
    Returns: (is_valid, detail_message, is_international)
    """
    if not phone or not isinstance(phone, str):
        return False, "No phone number provided", False

    cleaned = phone.strip()
    if not cleaned:
        return False, "Empty phone number", False

    digits_only = re.sub(r"[\s\-\.\(\)\/\\]", "", cleaned)
    has_plus = digits_only.startswith("+")
    pure_digits = digits_only.lstrip("+")

    if not pure_digits.isdigit():
        return False, f"Phone contains non-numeric characters: '{phone}'", False

    digit_count = len(pure_digits)
    if digit_count < 7:
        return False, f"Phone too short ({digit_count} digits, minimum 7)", False
    if digit_count > 15:
        return False, f"Phone too long ({digit_count} digits, maximum 15)", False

    if len(set(pure_digits)) <= 2:
        return False, "Phone appears to be a test/placeholder number (repetitive digits)", False

    is_international = False
    if has_plus:
        for cc_len in [3, 2, 1]:
            prefix = pure_digits[:cc_len]
            if prefix in COUNTRY_CODES:
                is_international = True
                break

        if is_international:
            return True, f"Valid international format (E.164: {digits_only})", True
        else:
            return True, f"International format but unrecognized country code ({digits_only})", False

    return True, f"Valid phone number ({digits_only}, national format)", False


# ---------------------------------------------------------------------------
# HTML Snippet & Title Extractor
# ---------------------------------------------------------------------------
def extract_html_metadata(html_text: str) -> Tuple[str, bool]:
    """Extract page title and check for parked domain signals."""
    if not html_text:
        return "", False
    
    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else ""
    page_title = re.sub(r"\s+", " ", page_title)

    # Check for parked domain signatures
    sample = html_text[:8000].lower()
    is_parked = any(sig in sample for sig in PARKED_DOMAIN_SIGNATURES)

    return page_title[:200], is_parked


# ---------------------------------------------------------------------------
# DNS / MX Checks
# ---------------------------------------------------------------------------
def check_domain_mx(domain: str, cache: Optional[VerificationCache] = None) -> Tuple[bool, str, List[str]]:
    if not domain:
        return False, "No domain provided", []

    clean_domain = domain.strip().lower()
    if cache is not None:
        cached = cache.get_mx(clean_domain)
        if cached is not None:
            return cached

    if HAS_DNS_PYTHON:
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2.0
            resolver.lifetime = 2.0
            answers = resolver.resolve(clean_domain, 'MX')
            mx_records = [str(rdata.exchange).rstrip('.') for rdata in answers]
            if mx_records:
                mx_str = ", ".join(mx_records[:2])
                res = (True, f"Found {len(mx_records)} MX record(s): {mx_str}", mx_records)
                if cache is not None:
                    cache.set_mx(clean_domain, res)
                return res
        except Exception:
            pass

    # Fallback to A record check
    try:
        addr = socket.getaddrinfo(clean_domain, 80, socket.AF_INET, socket.SOCK_STREAM)
        if addr:
            res = (True, f"Domain '{clean_domain}' resolved via A record", [])
            if cache is not None:
                cache.set_mx(clean_domain, res)
            return res
    except Exception as e:
        res = (False, f"DNS resolution failed for '{clean_domain}': {str(e)}", [])
        if cache is not None:
            cache.set_mx(clean_domain, res)
        return res

    res = (False, f"No active MX or DNS records for '{clean_domain}'", [])
    if cache is not None:
        cache.set_mx(clean_domain, res)
    return res


async def check_domain_mx_async(domain: str, cache: Optional[VerificationCache] = None) -> Tuple[bool, str, List[str]]:
    if not domain:
        return False, "No domain provided", []

    clean_domain = domain.strip().lower()
    if cache is not None:
        cached = cache.get_mx(clean_domain)
        if cached is not None:
            return cached

    res = await asyncio.to_thread(check_domain_mx, clean_domain, cache)
    return res


# ---------------------------------------------------------------------------
# Website Reachability & Content Retrieval
# ---------------------------------------------------------------------------
def check_website_reachability(website_url: str, cache: Optional[VerificationCache] = None) -> Tuple[bool, str, int, str, bool]:
    """
    Synchronous reachability check.
    Returns: (is_reachable, detail, status_code, page_title, is_parked)
    """
    if not website_url:
        return False, "No website provided", 0, "", False

    url = website_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if cache is not None:
        cached = cache.get_website(url)
        if cached is not None:
            return cached

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            res = (False, "Invalid URL format", 0, "", False)
            if cache is not None:
                cache.set_website(url, res)
            return res

        # SSRF Security Guard
        if not is_safe_hostname(hostname, cache):
            res = (False, "Blocked host (internal or non-routable address)", 403, "", False)
            if cache is not None:
                cache.set_website(url, res)
            return res

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        timeout = httpx.Timeout(3.0, connect=2.0)
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            try:
                res = client.get(url, headers=headers)
                if res.status_code in [200, 301, 302, 307, 308]:
                    title, is_parked = extract_html_metadata(res.text)
                    detail = f"Website reachable (HTTP {res.status_code})"
                    if is_parked:
                        detail += " [Warning: Parked domain detected]"
                    result = (True, detail, res.status_code, title, is_parked)
                else:
                    result = (False, f"Website returned HTTP {res.status_code}", res.status_code, "", False)
                if cache is not None:
                    cache.set_website(url, result)
                return result
            except Exception as e:
                result = (False, f"Website unreachable ({type(e).__name__})", 0, "", False)
                if cache is not None:
                    cache.set_website(url, result)
                return result

    except Exception as e:
        result = (False, f"Connection error: {type(e).__name__}", 0, "", False)
        if cache is not None:
            cache.set_website(url, result)
        return result


async def check_website_reachability_async(
    website_url: str,
    client: Optional[httpx.AsyncClient] = None,
    cache: Optional[VerificationCache] = None
) -> Tuple[bool, str, int, str, bool]:
    """
    Asynchronous reachability check.
    Returns: (is_reachable, detail, status_code, page_title, is_parked)
    """
    if not website_url:
        return False, "No website provided", 0, "", False

    url = website_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if cache is not None:
        cached = cache.get_website(url)
        if cached is not None:
            return cached

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            res = (False, "Invalid URL format", 0, "", False)
            if cache is not None:
                cache.set_website(url, res)
            return res

        # SSRF Security Guard
        is_safe = await asyncio.to_thread(is_safe_hostname, hostname, cache)
        if not is_safe:
            res = (False, "Blocked host (internal or non-routable address)", 403, "", False)
            if cache is not None:
                cache.set_website(url, res)
            return res

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        async def _do_get(http_client: httpx.AsyncClient):
            try:
                res = await http_client.get(url, headers=headers)
                if res.status_code in [200, 301, 302, 307, 308]:
                    title, is_parked = extract_html_metadata(res.text)
                    detail = f"Website reachable (HTTP {res.status_code})"
                    if is_parked:
                        detail += " [Warning: Parked domain detected]"
                    result = (True, detail, res.status_code, title, is_parked)
                else:
                    result = (False, f"Website returned HTTP {res.status_code}", res.status_code, "", False)
                if cache is not None:
                    cache.set_website(url, result)
                return result
            except Exception as e:
                result = (False, f"Website unreachable ({type(e).__name__})", 0, "", False)
                if cache is not None:
                    cache.set_website(url, result)
                return result

        if client is not None:
            return await _do_get(client)
        else:
            timeout = httpx.Timeout(3.0, connect=2.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as temp_client:
                return await _do_get(temp_client)

    except Exception as e:
        result = (False, f"Connection error: {type(e).__name__}", 0, "", False)
        if cache is not None:
            cache.set_website(url, result)
        return result


# ---------------------------------------------------------------------------
# Balanced Multi-Signal Verification Engine
# ---------------------------------------------------------------------------
class LeadVerificationEngine:
    """
    Balanced, Multi-Signal Lead Verification Engine.
    
    100-Point Balanced Weighting:
      1. Email (25 pts max):
         - Exists & RFC Valid Syntax: 5 pts
         - Non-disposable / Legitimate Domain: 5 pts
         - MX / DNS Active Resolution: 10 pts
         - Domain match (Email domain == Website domain): 5 pts
      2. Website (20 pts max):
         - URL Exists: 2 pts
         - Valid URL Structure: 3 pts
         - HTTP/HTTPS Reachable (200/3xx): 5 pts
         - Meaningful Company Info / Title Found: 5 pts
         - Website Identity Match (title/domain matches company): 5 pts
         (A reachable website alone receives ONLY up to 10 pts, never 20!)
      3. Company Identity (20 pts max):
         - Company Name Exists & Legitimate (>=2 chars): 6 pts
         - Industry / Vertical Specified: 4 pts
         - Company Name Matches Domain / Title: 6 pts
         - Location / Country Specified: 4 pts
      4. Contact & Role (15 pts max):
         - Contact Person Exists & Plausible Name: 6 pts
         - Job Title Exists & Plausible Professional Role: 5 pts
         - Role Context / Integrity: 4 pts
      5. Phone Validation (10 pts max):
         - Phone Exists: 3 pts
         - Valid Format & Length (7-15 digits, non-repetitive): 4 pts
         - International E.164 Recognized Country Format: 3 pts
      6. Data Completeness (10 pts max):
         - Proportion of populated key lead fields (out of 8 key fields): 10 pts

    Hard Rule:
      - A single strong signal (like reachable website) cannot exceed 20% of the score.
      - A lead with website only and missing email/contact/phone/role will score <= 30% and be REJECTED.
      - Score >= 70% required to ACCEPT and store into Supabase.
    """

    @classmethod
    def _evaluate_lead(
        cls,
        lead_data: Dict[str, Any],
        website_reachability_res: Tuple[bool, str, int, str, bool],
        mx_res: Tuple[bool, str, List[str]],
    ) -> Dict[str, Any]:
        company_name = (lead_data.get("company_name") or "").strip()
        contact_name = (lead_data.get("contact_name") or "").strip()
        job_title    = (lead_data.get("job_title") or "").strip()
        email        = (lead_data.get("email") or "").strip()
        website      = (lead_data.get("website") or "").strip()
        industry     = (lead_data.get("industry") or "").strip()
        country      = (lead_data.get("country") or "").strip()
        phone        = (lead_data.get("phone") or "").strip()

        checks: Dict[str, Any] = {}
        breakdown: Dict[str, Any] = {}
        fatal_failure = False

        # ----------------------------------------------------------------
        # 1. EMAIL VERIFICATION (Max: 25 pts)
        # ----------------------------------------------------------------
        email_score = 0
        email_checks = []
        website_domain = ""
        if website:
            norm_w = website if website.startswith(("http://", "https://")) else ("https://" + website)
            try:
                website_domain = (urlparse(norm_w).hostname or "").lower().replace("www.", "")
            except Exception:
                website_domain = ""

        if email:
            if verify_email_syntax(email):
                email_score += 5
                email_checks.append("RFC syntax valid")
                checks["email_syntax"] = {"passed": True, "points": 5, "detail": "RFC standard syntax verified"}

                email_domain = email.split("@")[-1].lower()

                # Disposable blacklist check
                if email_domain in DISPOSABLE_DOMAINS:
                    email_checks.append(f"Disposable domain detected ({email_domain})")
                    checks["email_disposable"] = {"passed": False, "points": 0, "detail": f"Temporary/disposable provider: {email_domain}"}
                else:
                    email_score += 5
                    email_checks.append("Non-disposable business/public domain")
                    checks["email_disposable"] = {"passed": True, "points": 5, "detail": "Reputable non-disposable domain"}

                # DNS / MX check
                mx_ok, mx_detail, _ = mx_res
                if mx_ok:
                    email_score += 10
                    email_checks.append("Active MX/DNS records found")
                    checks["email_mx_dns"] = {"passed": True, "points": 10, "detail": mx_detail}
                else:
                    email_checks.append("No active MX/DNS records")
                    checks["email_mx_dns"] = {"passed": False, "points": 0, "detail": mx_detail}

                # Domain match check
                if website_domain and (
                    email_domain == website_domain
                    or email_domain.endswith("." + website_domain)
                    or website_domain.endswith("." + email_domain)
                ):
                    email_score += 5
                    email_checks.append(f"Domain matches company website ({email_domain})")
                    checks["email_domain_match"] = {"passed": True, "points": 5, "detail": f"Email domain aligns with website: {email_domain}"}
                else:
                    checks["email_domain_match"] = {"passed": False, "points": 0, "detail": "Email domain does not match website domain"}
            else:
                email_checks.append("Invalid email syntax")
                checks["email_syntax"] = {"passed": False, "points": 0, "detail": "Invalid RFC email format"}
                checks["email_disposable"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid syntax"}
                checks["email_mx_dns"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid syntax"}
                checks["email_domain_match"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid syntax"}
        else:
            email_checks.append("No email provided")
            checks["email_syntax"] = {"passed": False, "points": 0, "detail": "No contact email provided"}
            checks["email_disposable"] = {"passed": False, "points": 0, "detail": "No email provided"}
            checks["email_mx_dns"] = {"passed": False, "points": 0, "detail": "No email provided"}
            checks["email_domain_match"] = {"passed": False, "points": 0, "detail": "No email provided"}

        breakdown["email"] = {
            "score": email_score,
            "max_score": 25,
            "reasons": email_checks
        }

        # ----------------------------------------------------------------
        # 2. WEBSITE VERIFICATION (Max: 20 pts)
        # ----------------------------------------------------------------
        website_score = 0
        website_checks = []
        is_reachable, reach_detail, status_code, page_title, is_parked = website_reachability_res

        if website:
            website_score += 2
            website_checks.append("URL provided")
            checks["website_exists"] = {"passed": True, "points": 2, "detail": f"Website URL provided: '{website}'"}

            if website_domain and "." in website_domain:
                website_score += 3
                website_checks.append(f"Valid structure ({website_domain})")
                checks["website_syntax"] = {"passed": True, "points": 3, "detail": f"Valid domain structure: {website_domain}"}

                if is_reachable and not is_parked:
                    website_score += 5
                    website_checks.append(f"Reachable (HTTP {status_code})")
                    checks["website_reachability"] = {"passed": True, "points": 5, "detail": reach_detail}

                    # Meaningful company info / title found
                    if page_title and len(page_title) >= 3:
                        website_score += 5
                        website_checks.append(f"Page content found ('{page_title[:40]}...')")
                        checks["website_content"] = {"passed": True, "points": 5, "detail": f"Title extracted: '{page_title}'"}
                    else:
                        checks["website_content"] = {"passed": False, "points": 0, "detail": "No descriptive title or metadata found"}

                    # Identity match (Company name tokens in domain or page title)
                    comp_clean = re.sub(r"[^\w\s]", "", company_name.lower()).strip()
                    comp_tokens = [t for t in comp_clean.split() if len(t) > 2]
                    domain_clean = website_domain.lower().replace("-", "").replace("_", "")
                    title_clean = page_title.lower()

                    matches_domain = any(t in domain_clean for t in comp_tokens) if comp_tokens else False
                    matches_title = any(t in title_clean for t in comp_tokens) if comp_tokens else False

                    if matches_domain or matches_title:
                        website_score += 5
                        website_checks.append("Website identity aligns with company name")
                        checks["website_identity_match"] = {"passed": True, "points": 5, "detail": "Company name verified in website domain or page title"}
                    else:
                        checks["website_identity_match"] = {"passed": False, "points": 0, "detail": "Company name not found in website title or domain"}
                else:
                    checks["website_reachability"] = {"passed": False, "points": 0, "detail": reach_detail}
                    checks["website_content"] = {"passed": False, "points": 0, "detail": "Skipped (unreachable or parked)"}
                    checks["website_identity_match"] = {"passed": False, "points": 0, "detail": "Skipped (unreachable or parked)"}
            else:
                checks["website_syntax"] = {"passed": False, "points": 0, "detail": "Invalid URL structure"}
                checks["website_reachability"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid URL"}
                checks["website_content"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid URL"}
                checks["website_identity_match"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid URL"}
        else:
            website_checks.append("No website provided")
            checks["website_exists"] = {"passed": False, "points": 0, "detail": "No website URL provided"}
            checks["website_syntax"] = {"passed": False, "points": 0, "detail": "No website provided"}
            checks["website_reachability"] = {"passed": False, "points": 0, "detail": "No website provided"}
            checks["website_content"] = {"passed": False, "points": 0, "detail": "No website provided"}
            checks["website_identity_match"] = {"passed": False, "points": 0, "detail": "No website provided"}

        breakdown["website"] = {
            "score": website_score,
            "max_score": 20,
            "reasons": website_checks
        }

        # ----------------------------------------------------------------
        # 3. COMPANY IDENTITY (Max: 20 pts)
        # ----------------------------------------------------------------
        company_score = 0
        company_checks = []

        if company_name and len(company_name) >= 2:
            company_score += 6
            company_checks.append(f"Legitimate company name: '{company_name}'")
            checks["company_name"] = {"passed": True, "points": 6, "detail": f"Company name present: '{company_name}'"}
        else:
            company_checks.append("Missing or empty company name")
            checks["company_name"] = {"passed": False, "points": 0, "detail": "Missing company name"}
            fatal_failure = True

        if industry and len(industry) >= 2:
            company_score += 4
            company_checks.append(f"Industry specified: '{industry}'")
            checks["company_industry"] = {"passed": True, "points": 4, "detail": f"Industry specified: '{industry}'"}
        else:
            checks["company_industry"] = {"passed": False, "points": 0, "detail": "Industry not specified"}

        # Cross-field consistency (Company aligns with website or email domain)
        comp_clean = re.sub(r"[^\w\s]", "", company_name.lower()).strip()
        comp_tokens = [t for t in comp_clean.split() if len(t) > 2]
        email_dom = (email.split("@")[-1].lower() if "@" in email else "")
        comp_matches_email = any(t in email_dom for t in comp_tokens) if comp_tokens and email_dom else False
        comp_matches_web = any(t in website_domain for t in comp_tokens) if comp_tokens and website_domain else False

        if comp_matches_email or comp_matches_web:
            company_score += 6
            company_checks.append("Company identity consistent across web/email domains")
            checks["company_domain_consistency"] = {"passed": True, "points": 6, "detail": "Company name verified against digital presence"}
        else:
            checks["company_domain_consistency"] = {"passed": False, "points": 0, "detail": "No direct name correlation with email/web domain"}

        if country and len(country) >= 2:
            company_score += 4
            company_checks.append(f"Location/Country provided: '{country}'")
            checks["company_location"] = {"passed": True, "points": 4, "detail": f"Country provided: '{country}'"}
        else:
            checks["company_location"] = {"passed": False, "points": 0, "detail": "Country / region not specified"}

        breakdown["company_identity"] = {
            "score": company_score,
            "max_score": 20,
            "reasons": company_checks
        }

        # ----------------------------------------------------------------
        # 4. CONTACT & ROLE (Max: 15 pts)
        # ----------------------------------------------------------------
        contact_score = 0
        contact_checks = []

        if contact_name and len(contact_name) >= 2 and not contact_name.lower().startswith("lead"):
            contact_score += 6
            contact_checks.append(f"Identified contact person: '{contact_name}'")
            checks["contact_name"] = {"passed": True, "points": 6, "detail": f"Contact name present: '{contact_name}'"}
        else:
            checks["contact_name"] = {"passed": False, "points": 0, "detail": "No individual contact person specified"}

        if job_title and len(job_title) >= 2:
            contact_score += 5
            contact_checks.append(f"Job title provided: '{job_title}'")
            checks["job_title"] = {"passed": True, "points": 5, "detail": f"Role/Title: '{job_title}'"}

            # Professional role check
            title_lower = job_title.lower()
            is_professional = any(r in title_lower for r in PROFESSIONAL_ROLES)
            if is_professional:
                contact_score += 4
                contact_checks.append("Standard professional role identified")
                checks["role_plausibility"] = {"passed": True, "points": 4, "detail": f"Professional seniority/role pattern recognized ({job_title})"}
            else:
                checks["role_plausibility"] = {"passed": False, "points": 0, "detail": "Role is generic or custom"}
        else:
            checks["job_title"] = {"passed": False, "points": 0, "detail": "Job title not specified"}
            checks["role_plausibility"] = {"passed": False, "points": 0, "detail": "No role provided"}

        breakdown["contact_role"] = {
            "score": contact_score,
            "max_score": 15,
            "reasons": contact_checks
        }

        # ----------------------------------------------------------------
        # 5. PHONE VALIDATION (Max: 10 pts)
        # ----------------------------------------------------------------
        phone_score = 0
        phone_checks = []

        if phone:
            phone_score += 3
            phone_checks.append(f"Phone number provided: '{phone}'")
            checks["phone_exists"] = {"passed": True, "points": 3, "detail": f"Phone number provided: '{phone}'"}

            is_valid_phone, phone_msg, is_intl = validate_phone(phone)
            if is_valid_phone:
                phone_score += 4
                phone_checks.append("Valid number length and formatting")
                checks["phone_format"] = {"passed": True, "points": 4, "detail": phone_msg}

                if is_intl:
                    phone_score += 3
                    phone_checks.append("International E.164 country code recognized")
                    checks["phone_international"] = {"passed": True, "points": 3, "detail": "Recognized international country prefix"}
                else:
                    checks["phone_international"] = {"passed": False, "points": 0, "detail": "National format without explicit country code"}
            else:
                phone_checks.append(f"Invalid phone format ({phone_msg})")
                checks["phone_format"] = {"passed": False, "points": 0, "detail": phone_msg}
                checks["phone_international"] = {"passed": False, "points": 0, "detail": "Skipped due to invalid format"}
        else:
            phone_checks.append("No phone number provided")
            checks["phone_exists"] = {"passed": False, "points": 0, "detail": "No phone number provided"}
            checks["phone_format"] = {"passed": False, "points": 0, "detail": "No phone provided"}
            checks["phone_international"] = {"passed": False, "points": 0, "detail": "No phone provided"}

        breakdown["phone"] = {
            "score": phone_score,
            "max_score": 10,
            "reasons": phone_checks
        }

        # ----------------------------------------------------------------
        # 6. DATA COMPLETENESS (Max: 10 pts)
        # ----------------------------------------------------------------
        key_fields = {
            "company_name": bool(company_name),
            "website": bool(website),
            "email": bool(email),
            "phone": bool(phone),
            "contact_name": bool(contact_name),
            "job_title": bool(job_title),
            "industry": bool(industry),
            "country": bool(country),
        }
        filled_count = sum(1 for v in key_fields.values() if v)
        completeness_ratio = filled_count / len(key_fields)
        completeness_score = round(completeness_ratio * 10)

        completeness_reasons = [f"{filled_count}/8 key fields populated ({round(completeness_ratio * 100)}%)"]
        checks["completeness"] = {
            "passed": filled_count >= 4,
            "points": completeness_score,
            "detail": f"Data completeness: {filled_count}/8 core attributes provided"
        }
        breakdown["completeness"] = {
            "score": completeness_score,
            "max_score": 10,
            "reasons": completeness_reasons
        }

        # ----------------------------------------------------------------
        # TOTAL SCORE & CONFIDENCE CALCULATION
        # ----------------------------------------------------------------
        total_score = email_score + website_score + company_score + contact_score + phone_score + completeness_score
        total_score = max(0, min(100, total_score))

        if fatal_failure:
            total_score = 0
            status = VerificationStatus.REJECTED
            confidence = "LOW"
        elif total_score >= 85:
            status = VerificationStatus.VERIFIED
            confidence = "HIGH"
        elif total_score >= VERIFICATION_ACCEPTANCE_THRESHOLD:
            status = VerificationStatus.VERIFIED
            confidence = "HIGH" if (email_score >= 15 and website_score >= 10 and company_score >= 12) else "MEDIUM"
        else:
            status = VerificationStatus.REJECTED
            confidence = "LOW"

        verified_at_iso = datetime.now(timezone.utc).isoformat()

        # Build list of top positive and negative reasons for transparency
        positive_reasons = []
        negative_reasons = []
        for cat_name, cat_data in breakdown.items():
            for r in cat_data["reasons"]:
                if "missing" in r.lower() or "invalid" in r.lower() or "no " in r.lower() or "detected" in r.lower() and "disposable" in r.lower():
                    negative_reasons.append(r)
                else:
                    positive_reasons.append(r)

        return {
            "verification_status": status.value,
            "verification_score": total_score,
            "verification_confidence": confidence,
            "verification_details": {
                "score": total_score,
                "confidence": confidence,
                "status": status.value,
                "acceptance_threshold": IMPORT_ACCEPTANCE_THRESHOLD,
                "breakdown": breakdown,
                "checks": checks,
                "positive_signals": positive_reasons,
                "negative_signals": negative_reasons,
                "last_verified_at": verified_at_iso,
            },
            "last_verified_at": verified_at_iso,
        }

    # ------------------------------------------------------------------
    # Public API — synchronous
    # ------------------------------------------------------------------
    @classmethod
    def verify_lead(
        cls,
        lead_data: Dict[str, Any],
        cache: Optional[VerificationCache] = None,
    ) -> Dict[str, Any]:
        """Synchronous single-lead verification."""
        website = (lead_data.get("website") or "").strip()
        reach_res = check_website_reachability(website, cache) if website else (False, "No website provided", 0, "", False)

        email = (lead_data.get("email") or "").strip()
        if email and verify_email_syntax(email):
            email_domain = email.split("@")[-1].lower()
            mx_res = check_domain_mx(email_domain, cache)
        else:
            mx_res = (False, "No email provided", [])

        return cls._evaluate_lead(lead_data, reach_res, mx_res)

    # ------------------------------------------------------------------
    # Public API — async single
    # ------------------------------------------------------------------
    @classmethod
    async def verify_lead_async(
        cls,
        lead_data: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
        cache: Optional[VerificationCache] = None,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> Dict[str, Any]:
        """Asynchronous single-lead verification with controlled concurrency and caching."""
        async def _run():
            try:
                website = (lead_data.get("website") or "").strip()
                email   = (lead_data.get("email") or "").strip()

                tasks = []
                if website:
                    tasks.append(check_website_reachability_async(website, client, cache))
                else:
                    tasks.append(asyncio.sleep(0, result=(False, "No website provided", 0, "", False)))

                if email and verify_email_syntax(email):
                    email_domain = email.split("@")[-1].lower()
                    tasks.append(check_domain_mx_async(email_domain, cache))
                else:
                    tasks.append(asyncio.sleep(0, result=(False, "No email provided", [])))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                reach_res = results[0] if not isinstance(results[0], Exception) else (False, "Website check failed", 0, "", False)
                mx_res    = results[1] if not isinstance(results[1], Exception) else (False, "DNS lookup failed", [])

                return cls._evaluate_lead(lead_data, reach_res, mx_res)
            except Exception as e:
                now_iso = datetime.now(timezone.utc).isoformat()
                return {
                    "verification_status": VerificationStatus.UNVERIFIED.value,
                    "verification_score": 0,
                    "verification_confidence": "LOW",
                    "verification_details": {
                        "score": 0,
                        "confidence": "LOW",
                        "status": VerificationStatus.UNVERIFIED.value,
                        "last_verified_at": now_iso,
                        "error": str(e),
                        "breakdown": {},
                        "checks": {},
                        "acceptance_threshold": IMPORT_ACCEPTANCE_THRESHOLD,
                    },
                    "last_verified_at": now_iso,
                }

        if semaphore:
            async with semaphore:
                return await _run()
        else:
            return await _run()

    # ------------------------------------------------------------------
    # Public API — async batch
    # ------------------------------------------------------------------
    @classmethod
    async def verify_leads_batch_async(
        cls,
        leads_data: List[Dict[str, Any]],
        concurrency: int = 20,
        cache: Optional[VerificationCache] = None,
    ) -> List[Dict[str, Any]]:
        """Verify multiple leads concurrently with shared cache and semaphore."""
        if not leads_data:
            return []

        if cache is None:
            cache = VerificationCache()

        semaphore = asyncio.Semaphore(concurrency)
        timeout = httpx.Timeout(3.0, connect=2.0)
        limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)

        async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, verify=False) as client:
            tasks = [
                cls.verify_lead_async(
                    lead, client=client, cache=cache, semaphore=semaphore
                )
                for lead in leads_data
            ]
            results = await asyncio.gather(*tasks, return_exceptions=False)
            return list(results)
