"""
Module: src.company_intelligence.validators
Description: Production SSRF defense and URL security validation.
Enforces protocol whitelisting, safe port checks, DNS resolution, and comprehensive
blocking of private, loopback, link-local, and cloud metadata addresses.
"""

import ipaddress
import re
import socket
from typing import Optional, Set, Tuple
from urllib.parse import urlparse

# Allowed protocols and ports
ALLOWED_SCHEMES: Set[str] = {"http", "https"}
ALLOWED_PORTS: Set[int] = {80, 443, 8080, 8443}
MAX_URL_LENGTH: int = 2048

# Known cloud metadata and sensitive internal IP endpoints
CLOUD_METADATA_IPS: Set[str] = {
    "169.254.169.254",  # AWS, GCP, Azure, Oracle IMDS
    "fd00:ec2::254",    # AWS IPv6 IMDS
    "100.100.100.200",  # Alibaba Cloud IMDS
    "169.254.169.253",  # AWS DNS / internal link-local
    "169.254.170.2",    # AWS ECS task metadata
}


class SSRFSecurityError(ValueError):
    """Raised when a URL targets a restricted, private, or dangerous destination."""
    pass


def is_ip_blocked(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, str]:
    """
    Checks if an IP address belongs to any restricted or private network ranges.

    Args:
        ip_obj: Resolved IP address object.

    Returns:
        Tuple of (is_blocked, reason_string).
    """
    ip_str = str(ip_obj)

    # 1. Cloud metadata endpoints
    if ip_str in CLOUD_METADATA_IPS:
        return True, f"Target IP '{ip_str}' is a restricted Cloud Instance Metadata endpoint."

    # 2. Loopback (127.0.0.0/8, ::1)
    if ip_obj.is_loopback:
        return True, f"Target IP '{ip_str}' is a loopback/localhost address."

    # 3. Private RFC 1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    if ip_obj.is_private:
        return True, f"Target IP '{ip_str}' belongs to a private/internal network."

    # 4. Link-local (169.254.0.0/16, fe80::/10)
    if ip_obj.is_link_local:
        return True, f"Target IP '{ip_str}' is a link-local address."

    # 5. Multicast
    if ip_obj.is_multicast:
        return True, f"Target IP '{ip_str}' is a multicast address."

    # 6. Reserved (240.0.0.0/4, etc.)
    if ip_obj.is_reserved:
        return True, f"Target IP '{ip_str}' is an IETF reserved address."

    # 7. Unspecified (0.0.0.0, ::)
    if ip_obj.is_unspecified:
        return True, f"Target IP '{ip_str}' is an unspecified address."

    # 8. Carrier-Grade NAT (100.64.0.0/10)
    if isinstance(ip_obj, ipaddress.IPv4Address):
        cgnat_net = ipaddress.IPv4Network("100.64.0.0/10")
        if ip_obj in cgnat_net:
            return True, f"Target IP '{ip_str}' belongs to Carrier-Grade NAT space."

    return False, "IP is public and permissible."


def validate_url_security(url: str, resolve_dns: bool = True) -> Tuple[bool, str, Optional[str]]:
    """
    Validates that a URL is well-formed, uses http/https, targets safe ports,
    and resolves strictly to public, non-private, non-metadata IP addresses.

    Args:
        url: The URL string to validate.
        resolve_dns: Whether to perform live DNS resolution checks (set False for unit tests if mocking).

    Returns:
        Tuple of (is_valid, message, primary_resolved_ip).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty.", None

    url_clean = url.strip()
    if len(url_clean) > MAX_URL_LENGTH:
        return False, f"URL exceeds maximum allowed length of {MAX_URL_LENGTH} characters.", None

    # Parse URL
    try:
        parsed = urlparse(url_clean)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}", None

    # 1. Scheme Validation
    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return False, f"Invalid scheme '{scheme}'. Only HTTP and HTTPS protocols are permitted.", None

    # 2. Hostname Validation
    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return False, "URL is missing a valid hostname.", None

    # Check for localhost aliases
    if hostname in {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}:
        return False, f"Access to localhost ('{hostname}') is strictly prohibited for security.", None

    # Check for direct hex or octal IP obfuscation
    if re.match(r"^0[xX][0-9a-fA-F]+$", hostname) or re.match(r"^0[0-7]+$", hostname):
        return False, "Obfuscated IP hostnames are rejected.", None

    # Check for direct IP literal (e.g. 127.0.0.1, 10.0.0.1, 169.254.169.254)
    try:
        direct_ip = ipaddress.ip_address(hostname)
        is_blocked, reason = is_ip_blocked(direct_ip)
        if is_blocked:
            return False, f"SSRF Protection: {reason}", str(direct_ip)
    except ValueError:
        # Not a direct IP literal; will perform DNS resolution later
        pass

    # 3. Port Validation
    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80

    if port not in ALLOWED_PORTS:
        return False, f"Port {port} is not allowed. Permitted ports are: {sorted(ALLOWED_PORTS)}.", None

    # 5. DNS Resolution & All-IP Checking
    if resolve_dns:
        try:
            addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror as e:
            return False, f"DNS resolution failed for host '{hostname}': {str(e)}", None
        except Exception as e:
            return False, f"Socket error resolving '{hostname}': {str(e)}", None

        if not addr_info:
            return False, f"No IP addresses could be resolved for host '{hostname}'.", None

        resolved_ips = []
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                resolved_ips.append(ip_str)
                is_blocked, reason = is_ip_blocked(ip_obj)
                if is_blocked:
                    return False, f"SSRF Protection: Host '{hostname}' resolves to blocked IP ({reason})", ip_str
            except ValueError:
                return False, f"Invalid IP address format returned by DNS: '{ip_str}'", ip_str

        primary_ip = resolved_ips[0] if resolved_ips else None
        return True, "URL and resolved destination IPs verified safe.", primary_ip

    return True, "URL syntax, scheme, and port verified safe.", None


def is_safe_url(url: str, resolve_dns: bool = True) -> bool:
    """Convenience boolean helper for quick URL security check."""
    is_safe, _, _ = validate_url_security(url, resolve_dns=resolve_dns)
    return is_safe
