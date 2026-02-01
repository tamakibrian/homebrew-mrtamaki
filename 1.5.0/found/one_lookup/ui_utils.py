#!/usr/bin/env python3
"""
Shared UI utilities for 1lookup display formatting.

Provides value formatting, section extraction, and color theming
used by both the CLI summary output and the interactive TUI menu.
"""

from typing import Any, Dict, List, Tuple, Optional


# ============================================================================
# Theme Configuration
# ============================================================================

THEME = {
    "accent": "cyan",
    "highlight": "yellow",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "muted": "bright_black",
    "border": "bright_black",
}


# ============================================================================
# Section Definitions
# ============================================================================

# Section definitions with priority order (lower = shown first)
# Format: (section_name, nested_keys, color, priority)
SECTION_DEFS: List[Tuple[str, Tuple[str, ...], str, int]] = [
    ("Risk Assessment", ("data", "risk_assessment"), "red", 10),
    ("Threat Intelligence", ("data", "threat"), "yellow", 20),
    ("Threat Intelligence", ("data", "threat_intel"), "yellow", 20),
    ("Network Info", ("data", "network"), "blue", 30),
    ("Network Info", ("data", "asn"), "blue", 30),
    ("Geolocation", ("data", "geo"), "magenta", 40),
    ("Geolocation", ("data", "location"), "magenta", 40),
    ("Email Info", ("data", "email"), "cyan", 50),
    ("Email Info", ("data", "email_info"), "cyan", 50),
    ("Person Info", ("data", "person"), "green", 60),
    ("Person Info", ("data", "identity"), "green", 60),
    ("Request Info", ("data", "request"), "bright_black", 80),
    ("Metadata", ("data", "metadata"), "bright_black", 90),
]

# Keys to filter out from display
SKIP_KEYS = {"deprecation_notice", "data_sources"}


# ============================================================================
# Value Formatting
# ============================================================================

def get_risk_style(risk_level: str) -> str:
    """
    Get color style based on risk level string.

    Args:
        risk_level: Risk level string (e.g., "low", "high", "critical")

    Returns:
        Rich color style string
    """
    risk_level = str(risk_level).lower()
    if risk_level in ("low", "none", "minimal"):
        return "green"
    elif risk_level in ("medium", "moderate"):
        return "yellow"
    elif risk_level in ("high", "elevated", "critical", "severe"):
        return "red"
    return "white"


def get_score_style(score: Any, inverse: bool = False) -> str:
    """
    Get color style based on numeric score (0-100).

    Args:
        score: Numeric score value
        inverse: If True, higher scores are better (e.g., confidence).
                 If False, lower scores are better (e.g., fraud score).

    Returns:
        Rich color style string
    """
    try:
        score = float(score)
    except (ValueError, TypeError):
        return "white"

    if inverse:  # Higher is better (confidence)
        if score >= 70:
            return "green"
        elif score >= 40:
            return "yellow"
        return "red"
    else:  # Higher is worse (fraud/risk score)
        if score <= 30:
            return "green"
        elif score <= 60:
            return "yellow"
        return "red"


def format_value(value: Any, key: str = "") -> Tuple[str, str]:
    """
    Format a value for display with appropriate coloring.

    Args:
        value: The value to format
        key: The field key (used to determine appropriate coloring)

    Returns:
        Tuple of (display_string, rich_style)
    """
    if value is None:
        return "-", "dim"

    key_lower = key.lower()
    str_val = str(value)

    # Risk level coloring
    if "risk_level" in key_lower or "threat_level" in key_lower:
        return str_val, get_risk_style(str_val)

    # Score coloring
    if "fraud_score" in key_lower or "risk_score" in key_lower:
        return str_val, get_score_style(value)
    if "confidence" in key_lower:
        return str_val, get_score_style(value, inverse=True)

    # Boolean coloring for threat indicators
    if isinstance(value, bool):
        threat_indicators = ("is_threat", "is_proxy", "is_vpn", "is_tor",
                            "is_bot", "is_spam", "is_malicious")
        if any(ind in key_lower for ind in threat_indicators):
            return str_val, "red" if value else "green"
        # Generic boolean: True is good/neutral, False is dimmed
        return str_val, "green" if value else "dim"

    # Lists
    if isinstance(value, list):
        if not value:
            return "-", "dim"
        return ", ".join(str(v) for v in value), "white"

    return str_val, "white"


def format_key(key: str) -> str:
    """
    Convert a snake_case key to Title Case for display.

    Args:
        key: Field key in snake_case

    Returns:
        Human-readable title case string
    """
    return key.replace("_", " ").title()


# ============================================================================
# Data Extraction
# ============================================================================

def extract_nested(data: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    """
    Safely extract nested dictionary values.

    Args:
        data: Source dictionary
        *keys: Sequence of keys to traverse

    Returns:
        Nested dictionary or empty dict if path doesn't exist
    """
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, {})
        else:
            return {}
    return result if isinstance(result, dict) else {}


def filter_section_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out None values and deprecated fields from section data.

    Args:
        data: Section data dictionary

    Returns:
        Filtered dictionary with displayable values only
    """
    return {
        k: v for k, v in data.items()
        if v is not None
        and k not in SKIP_KEYS
        and "deprecat" not in k.lower()
        and not isinstance(v, dict)  # Skip nested dicts at this level
    }


# ============================================================================
# Section Extraction
# ============================================================================

class Section:
    """Represents a data section for display."""

    __slots__ = ("name", "data", "color", "priority")

    def __init__(self, name: str, data: Dict[str, Any], color: str, priority: int):
        self.name = name
        self.data = data
        self.color = color
        self.priority = priority

    def __repr__(self) -> str:
        return f"Section({self.name!r}, {len(self.data)} fields)"


def extract_sections(
    response: Dict[str, Any],
    include_low_priority: bool = True,
    max_priority: int = 100
) -> List[Section]:
    """
    Extract displayable sections from an API response.

    Args:
        response: Full API response dictionary
        include_low_priority: Whether to include Request Info and Metadata
        max_priority: Maximum priority level to include

    Returns:
        List of Section objects, sorted by priority
    """
    sections: Dict[str, Section] = {}

    for section_name, keys, color, priority in SECTION_DEFS:
        if priority > max_priority:
            continue
        if not include_low_priority and priority >= 80:
            continue

        # Already have this section (from an earlier key path)
        if section_name in sections:
            continue

        # Extract data from this path
        raw_data = extract_nested(response, *keys)
        if not raw_data:
            continue

        # Filter to displayable values
        filtered = filter_section_data(raw_data)
        if filtered:
            sections[section_name] = Section(section_name, filtered, color, priority)

    # Sort by priority and return
    return sorted(sections.values(), key=lambda s: s.priority)


def get_status_info(response: Dict[str, Any]) -> Optional[Tuple[bool, str]]:
    """
    Extract status information from response.

    Args:
        response: API response dictionary

    Returns:
        Tuple of (success_bool, style) or None if no status
    """
    if response.get("success") is not None:
        success = response.get("success")
        style = "green" if success else "red"
        return success, style
    return None


def get_error_message(response: Dict[str, Any]) -> Optional[str]:
    """
    Extract error message from response if present.

    Args:
        response: API response dictionary

    Returns:
        Error message string or None
    """
    if response.get("error"):
        return response.get("message", "Unknown error")
    return None
