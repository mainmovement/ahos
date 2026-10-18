"""M59.1 source registry with full schema validation, scoring, and deduplication."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import yaml


@dataclass(frozen=True, slots=True)
class SourceQuality:
    authority: int = 0  # 0-5
    recency: int = 0    # 0-5
    track_record: int = 0  # 0-5
    citations: int = 0  # 0-5

    @property
    def total_score(self) -> float:
        """Weighted quality score: authority 40%, recency 30%, track record 20%, citations 10%"""
        return (
            self.authority * 0.4 +
            self.recency * 0.3 +
            self.track_record * 0.2 +
            self.citations * 0.1
        )


@dataclass(frozen=True, slots=True)
class Source:
    """University source with full schema compliance."""
    id: str
    domains: List[str]
    name: str
    url: str
    category: str
    access: str  # api|rss|manual|dataset
    license: str
    tos_ok: bool
    quality: SourceQuality
    score: float = 0.0
    added_by: str = "system"
    reviewed_by: str = ""
    status: str = "active"  # active|disabled
    content_hash: str = ""

    def __post_init__(self):
        """Calculate score and content hash."""
        object.__setattr__(self, 'score', self.quality.total_score)

        # Normalize URL and calculate hash for deduplication
        normalized_url = self.url.strip().lower()
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        object.__setattr__(self, 'content_hash', url_hash)


@dataclass
class Registry:
    """Source registry with validation and management."""
    sources: Dict[str, Source] = field(default_factory=dict)
    disabled_count: int = 0
    duplicate_count: int = 0
    low_score_count: int = 0

    def add_source(self, source: Source) -> Tuple[bool, str]:
        """Add a source with validation."""
        # Validate required fields
        if not source.url.strip():
            return False, "Empty URL"

        if not source.license.strip():
            return False, "Empty license"

        if source.score < 2.5:
            self.low_score_count += 1
            return False, f"Score too low: {source.score:.2f} (min 2.5)"

        # Check for duplicates by URL hash
        if source.content_hash in {s.content_hash for s in self.sources.values()}:
            self.duplicate_count += 1
            return False, "Duplicate URL"

        # Add source
        self.sources[source.id] = source
        return True, "Added successfully"

    def get_sources_by_domain(self, domain: str) -> List[Source]:
        """Get active sources for a specific domain."""
        return [
            s for s in self.sources.values()
            if s.status == "active" and domain in s.domains
        ]

    def get_sources_by_category(self, category: str) -> List[Source]:
        """Get active sources for a specific category."""
        return [
            s for s in self.sources.values()
            if s.status == "active" and s.category == category
        ]

    def disable_low_score_sources(self, threshold: float = 2.5) -> int:
        """Disable sources below threshold score."""
        disabled = 0
        for source in self.sources.values():
            if source.score < threshold and source.status == "active":
                source.status = "disabled"
                self.disabled_count += 1
                disabled += 1
        return disabled


def load_sources_from_yaml(yaml_path: str) -> Registry:
    """Load sources from YAML configuration file."""
    registry = Registry()

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if 'sources' not in config:
            return registry

        for source_data in config['sources']:
            # Parse quality scores
            quality_data = source_data.get('quality', {})
            quality = SourceQuality(
                authority=int(quality_data.get('authority', 0)),
                recency=int(quality_data.get('recency', 0)),
                track_record=int(quality_data.get('track_record', 0)),
                citations=int(quality_data.get('citations', 0))
            )

            # Create source
            source = Source(
                id=source_data.get('id', ''),
                domains=source_data.get('domain', []),
                name=source_data.get('name', ''),
                url=source_data.get('url', ''),
                category=source_data.get('category', ''),
                access=source_data.get('access', 'manual'),
                license=source_data.get('license', ''),
                tos_ok=source_data.get('tos_ok', False),
                quality=quality,
                added_by=source_data.get('added_by', 'system'),
                reviewed_by=source_data.get('reviewed_by', '')
            )

            # Add to registry
            registry.add_source(source)

    except Exception as e:
        print(f"Error loading sources: {e}")

    return registry


def validate_source_schema(source_data: Dict[str, Any]) -> List[str]:
    """Validate source data against schema."""
    errors = []
    required_fields = ['id', 'url', 'name', 'category', 'access', 'license']

    for field in required_fields:
        if field not in source_data or not str(source_data[field]).strip():
            errors.append(f"Missing required field: {field}")

    # Validate domains list
    if 'domain' not in source_data or not isinstance(source_data['domain'], list):
        errors.append("Missing or invalid 'domain' list")

    # Validate access type
    if source_data.get('access') not in ['api', 'rss', 'manual', 'dataset']:
        errors.append("Invalid access type (must be api|rss|manual|dataset)")

    # Validate quality scores
    quality = source_data.get('quality', {})
    for score_field in ['authority', 'recency', 'track_record', 'citations']:
        if score_field in quality:
            try:
                value = int(quality[score_field])
                if not 0 <= value <= 5:
                    errors.append(f"Quality score {score_field} must be 0-5")
            except (ValueError, TypeError):
                errors.append(f"Quality score {score_field} must be an integer")

    return errors


def deduplicate_sources(sources: List[Source]) -> Tuple[List[Source], List[Source]]:
    """Remove duplicate sources based on URL hash."""
    seen_hashes: Set[str] = set()
    unique_sources: List[Source] = []
    duplicate_sources: List[Source] = []

    for source in sources:
        if source.content_hash in seen_hashes:
            duplicate_sources.append(source)
        else:
            seen_hashes.add(source.content_hash)
            unique_sources.append(source)

    return unique_sources, duplicate_sources


def export_registry_to_yaml(registry: Registry, yaml_path: str) -> bool:
    """Export registry to YAML file."""
    try:
        sources_data = []
        for source in registry.sources.values():
            sources_data.append({
                'id': source.id,
                'domain': source.domains,
                'name': source.name,
                'url': source.url,
                'category': source.category,
                'access': source.access,
                'license': source.license,
                'tos_ok': source.tos_ok,
                'quality': {
                    'authority': source.quality.authority,
                    'recency': source.quality.recency,
                    'track_record': source.quality.track_record,
                    'citations': source.quality.citations
                },
                'score': round(source.score, 2),
                'added_by': source.added_by,
                'reviewed_by': source.reviewed_by,
                'status': source.status
            })

        config = {
            'schema': 'ahos.university.sources.v1',
            'sources': sources_data
        }

        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        return True

    except Exception as e:
        print(f"Error exporting registry: {e}")
        return False


@dataclass(frozen=True, slots=True)
class RegisterReport:
    """Legacy paper-core batch result. No network fetch."""

    fetched: int
    dropped: int
    kept: tuple[str, ...]


def register(entries: list[tuple[str, str] | Source]) -> RegisterReport:
    """Dedupe source URLs for paper tests. Empty license rows are dropped."""
    kept: list[str] = []
    dropped = 0
    seen: set[str] = set()
    for item in entries:
        if isinstance(item, Source):
            url, lic = item.url, item.license
        else:
            url = str(item[0])
            lic = str(item[1]) if len(item) > 1 else ""
        if not str(lic).strip():
            dropped += 1
            continue
        key = url.strip().lower()
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(url)
    return RegisterReport(fetched=0, dropped=dropped, kept=tuple(kept))