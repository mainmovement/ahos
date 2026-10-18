"""Test suite for university source registry (M59.1)."""
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from architecture.learning.university import (
    Source, SourceQuality, Registry,
    load_sources_from_yaml, validate_source_schema,
    deduplicate_sources, export_registry_to_yaml
)


class TestSourceQuality:
    """Test SourceQuality scoring."""

    def test_default_scores(self):
        """Test default scores are zero."""
        q = SourceQuality()
        assert q.authority == 0
        assert q.recency == 0
        assert q.track_record == 0
        assert q.citations == 0

    def test_weighted_score(self):
        """Test weighted total score calculation."""
        q = SourceQuality(
            authority=5,
            recency=5,
            track_record=5,
            citations=5
        )
        # 5*0.4 + 5*0.3 + 5*0.2 + 5*0.1 = 2.0 + 1.5 + 1.0 + 0.5 = 5.0
        assert q.total_score == 5.0

    def test_score_below_threshold(self):
        """Test scores below 2.5 should be considered low."""
        q = SourceQuality(
            authority=1,
            recency=1,
            track_record=1,
            citations=1
        )
        assert q.total_score < 2.5


class TestSource:
    """Test Source dataclass."""

    def test_source_creation(self):
        """Test creating a valid source."""
        q = SourceQuality(authority=4, recency=5, track_record=3, citations=2)
        s = Source(
            id="test_crypto",
            domains=["crypto", "tokens"],
            name="Test Crypto Source",
            url="https://example.com/crypto",
            category="crypto",
            access="api",
            license="MIT",
            tos_ok=True,
            quality=q
        )
        assert s.id == "test_crypto"
        assert "crypto" in s.domains
        assert s.score > 0
        assert len(s.content_hash) == 64  # SHA-256 hex digest

    def test_url_normalization(self):
        """Test URL normalization preserves case-insensitivity."""
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        s1 = Source(
            id="test",
            domains=["test"],
            name="Test",
            url="https://Example.com/TEST",
            category="test",
            access="manual",
            license="MIT",
            tos_ok=True,
            quality=q
        )

        s2 = Source(
            id="test2",
            domains=["test"],
            name="Test2",
            url="https://example.com/test",  # Different case
            category="test",
            access="manual",
            license="MIT",
            tos_ok=True,
            quality=q
        )

        assert s1.content_hash == s2.content_hash


class TestRegistry:
    """Test Registry management."""

    def test_add_valid_source(self):
        """Test adding a valid source."""
        registry = Registry()
        q = SourceQuality(authority=4, recency=5, track_record=4, citations=3)
        source = Source(
            id="valid_source",
            domains=["research"],
            name="Valid Source",
            url="https://example.com",
            category="research",
            access="api",
            license="MIT",
            tos_ok=True,
            quality=q
        )

        success, message = registry.add_source(source)
        assert success
        assert "valid_source" in registry.sources
        assert registry.low_score_count == 0

    def test_add_source_without_license(self):
        """Test that sources without licenses are rejected."""
        registry = Registry()
        q = SourceQuality(authority=4, recency=5, track_record=4, citations=3)
        source = Source(
            id="no_license",
            domains=["test"],
            name="No License",
            url="https://example.com",
            category="test",
            access="manual",
            license="",  # Empty
            tos_ok=True,
            quality=q
        )

        success, message = registry.add_source(source)
        assert not success
        assert "license" in message.lower()

    def test_add_source_low_score(self):
        """Test that sources with score < 2.5 are rejected."""
        registry = Registry()
        q = SourceQuality(authority=0, recency=0, track_record=1, citations=0)
        source = Source(
            id="low_score",
            domains=["test"],
            name="Low Score",
            url="https://example.com",
            category="test",
            access="manual",
            license="MIT",
            tos_ok=True,
            quality=q
        )

        success, message = registry.add_source(source)
        assert not success
        assert "score" in message.lower()
        assert registry.low_score_count == 1

    def test_add_duplicate_source(self):
        """Test that duplicate URLs are rejected."""
        registry = Registry()
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        source1 = Source(
            id="source1",
            domains=["test"],
            name="Source 1",
            url="https://example.com",
            category="test",
            access="api",
            license="MIT",
            tos_ok=True,
            quality=q
        )

        source2 = Source(
            id="source2",
            domains=["test"],
            name="Source 2",
            url="https://example.com",  # Same URL
            category="test",
            access="rss",
            license="Apache-2.0",
            tos_ok=True,
            quality=q
        )

        registry.add_source(source1)
        success, message = registry.add_source(source2)

        assert not success
        assert "duplicate" in message.lower()
        assert registry.duplicate_count == 1

    def test_get_sources_by_domain(self):
        """Test retrieving sources by domain."""
        registry = Registry()
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        registry.add_source(Source(
            id="c1", domains=["crypto", "tokens"], name="Crypto A",
            url="https://c1.com", category="crypto", access="api",
            license="MIT", tos_ok=True, quality=q
        ))
        registry.add_source(Source(
            id="c2", domains=["crypto", "tokens"], name="Crypto B",
            url="https://c2.com", category="crypto", access="rss",
            license="Apache", tos_ok=True, quality=q
        ))
        registry.add_source(Source(
            id="r1", domains=["research"], name="Research A",
            url="https://r1.com", category="research", access="api",
            license="MIT", tos_ok=True, quality=q
        ))

        crypto_sources = registry.get_sources_by_domain("crypto")
        assert len(crypto_sources) == 2

        research_sources = registry.get_sources_by_domain("research")
        assert len(research_sources) == 1

    def test_get_sources_by_category(self):
        """Test retrieving sources by category."""
        registry = Registry()
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        registry.add_source(Source(
            id="c1", domains=["crypto"], name="Crypto A",
            url="https://c1.com", category="crypto", access="api",
            license="MIT", tos_ok=True, quality=q
        ))
        registry.add_source(Source(
            id="r1", domains=["research"], name="Research A",
            url="https://r1.com", category="research", access="api",
            license="MIT", tos_ok=True, quality=q
        ))

        crypto_sources = registry.get_sources_by_category("crypto")
        assert len(crypto_sources) == 1

        research_sources = registry.get_sources_by_category("research")
        assert len(research_sources) == 1

    def test_disable_low_score_sources(self):
        """Test disabling sources below threshold."""
        registry = Registry()
        q_high = SourceQuality(authority=5, recency=5, track_record=5, citations=5)
        q_low = SourceQuality(authority=1, recency=1, track_record=1, citations=1)

        registry.add_source(Source(
            id="high", domains=["test"], name="High",
            url="https://high.com", category="test", access="api",
            license="MIT", tos_ok=True, quality=q_high
        ))
        registry.add_source(Source(
            id="low", domains=["test"], name="Low",
            url="https://low.com", category="test", access="rss",
            license="MIT", tos_ok=True, quality=q_low
        ))

        disabled = registry.disable_low_score_sources(threshold=2.5)
        assert disabled == 1
        assert registry.sources["low"].status == "disabled"
        assert registry.disabled_count == 1


class TestSchemaValidation:
    """Test source schema validation."""

    def test_valid_source(self):
        """Test valid source data."""
        source_data = {
            'id': 'test_source',
            'domain': ['crypto', 'tokens'],
            'name': 'Test Source',
            'url': 'https://example.com',
            'category': 'crypto',
            'access': 'api',
            'license': 'MIT',
            'tos_ok': True,
            'quality': {
                'authority': 4,
                'recency': 5,
                'track_record': 4,
                'citations': 3
            }
        }

        errors = validate_source_schema(source_data)
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test missing required fields."""
        source_data = {
            'domain': ['test'],
            'name': 'Test',
            'url': 'https://example.com',
            'category': 'test',
            'access': 'api'
            # Missing license
        }

        errors = validate_source_schema(source_data)
        assert len(errors) > 0
        assert any("license" in e.lower() for e in errors)

    def test_invalid_access_type(self):
        """Test invalid access type."""
        source_data = {
            'id': 'test',
            'domain': ['test'],
            'name': 'Test',
            'url': 'https://example.com',
            'category': 'test',
            'access': 'invalid',  # Invalid
            'license': 'MIT',
            'tos_ok': True,
            'quality': {}
        }

        errors = validate_source_schema(source_data)
        assert len(errors) > 0
        assert any("access type" in e.lower() or "api|rss|manual|dataset" in e.lower() for e in errors)

    def test_quality_score_out_of_range(self):
        """Test quality scores out of range."""
        source_data = {
            'id': 'test',
            'domain': ['test'],
            'name': 'Test',
            'url': 'https://example.com',
            'category': 'test',
            'access': 'api',
            'license': 'MIT',
            'tos_ok': True,
            'quality': {
                'authority': 6  # Out of range
            }
        }

        errors = validate_source_schema(source_data)
        assert len(errors) > 0
        assert any("0-5" in e for e in errors)


class TestDeduplication:
    """Test source deduplication."""

    def test_no_duplicates(self):
        """Test no duplicates in unique list."""
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        sources = [
            Source(id="1", domains=["test"], name="1",
                   url="https://1.com", category="test", access="api",
                   license="MIT", tos_ok=True, quality=q),
            Source(id="2", domains=["test"], name="2",
                   url="https://2.com", category="test", access="rss",
                   license="Apache", tos_ok=True, quality=q),
        ]

        unique, duplicates = deduplicate_sources(sources)
        assert len(unique) == 2
        assert len(duplicates) == 0

    def test_with_duplicates(self):
        """Test detection of duplicates."""
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)

        sources = [
            Source(id="1", domains=["test"], name="1",
                   url="https://example.com", category="test", access="api",
                   license="MIT", tos_ok=True, quality=q),
            Source(id="2", domains=["test"], name="2",
                   url="https://example.com", category="test", access="rss",
                   license="Apache", tos_ok=True, quality=q),
            Source(id="3", domains=["test"], name="3",
                   url="https://example.com", category="test", access="manual",
                   license="CC-BY", tos_ok=True, quality=q),
        ]

        unique, duplicates = deduplicate_sources(sources)
        assert len(unique) == 1
        assert len(duplicates) == 2
        assert unique[0].id == "1"


class TestYAML:
    """Test YAML loading and exporting."""

    def test_load_sources_yaml(self):
        """Test loading sources from YAML file."""
        yaml_path = Path(__file__).parent.parent / "test_sources.yaml"

        # Create test YAML
        config = {
            'schema': 'ahos.university.sources.v1',
            'sources': [
                {
                    'id': 'test_source',
                    'domain': ['crypto'],
                    'name': 'Test Source',
                    'url': 'https://example.com',
                    'category': 'crypto',
                    'access': 'api',
                    'license': 'MIT',
                    'tos_ok': True,
                    'quality': {
                        'authority': 4,
                        'recency': 5,
                        'track_record': 4,
                        'citations': 3
                    }
                }
            ]
        }

        with open(yaml_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config, f)

        try:
            registry = load_sources_from_yaml(str(yaml_path))
            assert len(registry.sources) == 1
            assert registry.sources['test_source'].name == 'Test Source'
        finally:
            # Cleanup
            yaml_path.unlink()

    def test_export_registry_to_yaml(self, tmp_path):
        """Test exporting registry to YAML file."""
        q = SourceQuality(authority=5, recency=5, track_record=5, citations=5)
        registry = Registry()
        registry.add_source(Source(
            id="test", domains=["test"], name="Test",
            url="https://example.com", category="test", access="api",
            license="MIT", tos_ok=True, quality=q
        ))

        yaml_path = tmp_path / "test_output.yaml"
        result = export_registry_to_yaml(registry, str(yaml_path))

        assert result
        assert yaml_path.exists()

        # Verify file content
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            assert 'sources' in content
            assert len(content['sources']) == 1
            assert content['sources'][0]['id'] == 'test'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
