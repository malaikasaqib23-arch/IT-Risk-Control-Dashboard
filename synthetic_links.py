"""Project-defined links for missing SYNTHETIC incident controls only."""
INCIDENT_CONTROL_MAP = {
    "Unauthorized Access": "CTRL-002",
    "Malware": "CTRL-011",
    "Service Disruption": "CTRL-006",
    "Suspicious Activity": "CTRL-016",
    "Data Exposure": "CTRL-018",
    "Configuration Issue": "CTRL-013",
}


def complete_synthetic_links(incidents):
    """Return a copy; preserve existing links and all non-link fields.

    These are fictional type-based assignments, not inferred incident causes.
    Unknown types raise an error rather than receiving an arbitrary control.
    """
    out = incidents.copy()
    missing = out.control_id.fillna("").str.strip().eq("")
    mapped = out.loc[missing, "incident_type"].map(INCIDENT_CONTROL_MAP)
    if mapped.isna().any():
        raise ValueError("Missing synthetic control mapping for incident type")
    out.loc[missing, "control_id"] = mapped
    return out
