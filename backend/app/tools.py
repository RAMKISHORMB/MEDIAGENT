
import csv
import os
from itertools import combinations
from urllib.parse import urlparse


# ---------------------------------------------------------
# DATASET CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "data", "DDI_data.csv")

TRUSTED_DOMAINS = (
    "nhs.uk",
    "medlineplus.gov",
    "cdc.gov",
    "who.int",
)


# ---------------------------------------------------------
# DRUG-DRUG INTERACTION LOOKUP
# ---------------------------------------------------------

def _normalize(value: str) -> str:
    """Normalize a value for case-insensitive matching."""
    return " ".join(str(value or "").strip().casefold().split())


def _load_interaction_dataset() -> dict:
    """Load interaction records from the organizer-provided CSV."""

    if not os.path.isfile(DATASET_PATH):
        return {
            "status": "dataset_error",
            "message": "The drug-interaction CSV file was not found.",
            "pairs": {},
        }

    if os.path.getsize(DATASET_PATH) == 0:
        return {
            "status": "dataset_error",
            "message": "The drug-interaction CSV file is empty.",
            "pairs": {},
        }

    pairs = {}

    try:
        with open(
            DATASET_PATH,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                return {
                    "status": "dataset_error",
                    "message": "The CSV does not contain a header row.",
                    "pairs": {},
                }

            # Ignore whitespace and BOM artifacts in header names.
            reader.fieldnames = [
                (name or "").strip().lstrip("\ufeff")
                for name in reader.fieldnames
            ]

            required_columns = {
                "drug1_name",
                "drug2_name",
                "interaction_type",
            }

            if not required_columns.issubset(set(reader.fieldnames)):
                return {
                    "status": "dataset_error",
                    "message": (
                        "Unexpected DDI CSV columns. "
                        f"Found: {reader.fieldnames}"
                    ),
                    "pairs": {},
                }

            for row in reader:
                drug1 = _normalize(row.get("drug1_name", ""))
                drug2 = _normalize(row.get("drug2_name", ""))
                interaction_type = str(
                    row.get("interaction_type", "")
                ).strip()

                if not drug1 or not drug2 or not interaction_type:
                    continue

                key = tuple(sorted((drug1, drug2)))

                if key not in pairs:
                    pairs[key] = set()

                pairs[key].add(interaction_type)

        if not pairs:
            return {
                "status": "dataset_error",
                "message": (
                    "The CSV was read, but no usable interaction "
                    "records were found."
                ),
                "pairs": {},
            }

        return {
            "status": "loaded",
            "message": "Interaction dataset loaded successfully.",
            "pairs": pairs,
        }

    except (OSError, csv.Error, UnicodeError) as error:
        return {
            "status": "dataset_error",
            "message": (
                "Could not read the interaction dataset: "
                f"{type(error).__name__}"
            ),
            "pairs": {},
        }


def lookup_interactions(medications: list[str]) -> dict:
    """
    Look up medication pairs in the local interaction dataset.

    This reports matching dataset records only. It does not determine
    clinical severity or establish that a medication combination is safe.
    """

    if not isinstance(medications, list):
        return {
            "status": "invalid_input",
            "checked_pairs": 0,
            "matches": [],
            "message": "Medications must be supplied as a list of names.",
        }

    # Deduplicate medication names while preserving their original display.
    unique_medications = {}

    for medication in medications:
        if not isinstance(medication, str):
            continue

        display_name = medication.strip()

        if display_name:
            unique_medications.setdefault(
                _normalize(display_name),
                display_name,
            )

    if len(unique_medications) < 2:
        return {
            "status": "not_run",
            "checked_pairs": 0,
            "matches": [],
            "message": (
                "At least two distinct medication names are required."
            ),
            "source": "organizer_provided_DDI_data.csv",
        }

    dataset = _load_interaction_dataset()

    if dataset["status"] != "loaded":
        return {
            "status": "dataset_error",
            "checked_pairs": 0,
            "matches": [],
            "source": "organizer_provided_DDI_data.csv",
            "message": dataset["message"],
        }

    medication_names = list(unique_medications.keys())
    pairs = dataset["pairs"]
    matches = []
    checked_pairs = 0

    for drug1, drug2 in combinations(medication_names, 2):
        checked_pairs += 1
        pair_key = tuple(sorted((drug1, drug2)))

        if pair_key not in pairs:
            continue

        matches.append({
            "drug1": unique_medications[drug1],
            "drug2": unique_medications[drug2],
            "interaction_types": sorted(pairs[pair_key]),
            "source": "organizer_provided_DDI_data.csv",
        })

    return {
        "status": "completed",
        "checked_pairs": checked_pairs,
        "matches": matches,
        "source": "organizer_provided_DDI_data.csv",
        "message": (
            "Interaction types are dataset records, not a complete "
            "clinical risk assessment. A missing match does not "
            "establish that a medication combination is safe."
        ),
    }


# ---------------------------------------------------------
# MEDICAL INFORMATION SEARCH
# ---------------------------------------------------------

def search_medical_information(query: str) -> dict:
    """
    Search for general medical information from trusted health domains.

    Search results are not independently validated clinical protocols.
    """

    if not isinstance(query, str) or not query.strip():
        return {
            "status": "invalid_query",
            "query": "",
            "results": [],
            "message": "A non-empty search query is required.",
        }

    try:
        from ddgs import DDGS
    except ImportError:
        return {
            "status": "search_error",
            "query": query,
            "results": [],
            "message": (
                "The ddgs package is not installed. "
                "Install it using: python -m pip install ddgs"
            ),
        }

    search_query = (
        f"{query.strip()} "
        "(site:nhs.uk OR site:medlineplus.gov "
        "OR site:cdc.gov OR site:who.int)"
    )

    try:
        with DDGS() as search:
            raw_results = list(
                search.text(
                    search_query,
                    max_results=10,
            ))

        results = []
        seen_urls = set()

        for item in raw_results:
            url = str(
                item.get("href") or item.get("url") or ""
            ).strip()
            title = str(item.get("title") or "").strip()
            snippet = str(
                item.get("body") or item.get("snippet") or ""
            ).strip()

            if not url or not title:
                continue

            parsed_url = urlparse(url)
            hostname = (parsed_url.hostname or "").lower()

            # Require HTTPS and an exact trusted domain or subdomain.
            is_trusted = any(
                hostname == domain
                or hostname.endswith("." + domain)
                for domain in TRUSTED_DOMAINS
            )

            if parsed_url.scheme != "https" or not is_trusted:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
            })

            if len(results) >= 5:
                break

        return {
            "status": "completed" if results else "no_results",
            "query": query.strip(),
            "results": results,
            "message": (
                "These are search results, not verified or personalized "
                "medical advice. Review the original page, its publication "
                "date, and its relevance. Do not delay emergency care "
                "to search online."
            ),
        }

    except Exception as error:
        return {
            "status": "search_error",
            "query": query.strip(),
            "results": [],
            "message": f"Medical-information search failed: {type(error).__name__}",
        }
