"""
Tests for JSON schema validation.

Validates that all JSON files are valid JSON and conform to their
respective schemas for the AZMX brand skill.
"""

import json
import os
import pytest
from jsonschema import validate, ValidationError


JSON_FILES = [
    {
        "file": "scripts/image-tags.json",
        "schema": "tests/schemas/image-tags-schema.json",
        "description": "Image tags mapping"
    },
    {
        "file": "scripts/recolor-prompts.json",
        "schema": "tests/schemas/recolor-prompts-schema.json",
        "description": "Recolor prompts configuration"
    },
    {
        "file": "assets/tokens/azmx-tokens.json",
        "schema": "tests/schemas/design-tokens-schema.json",
        "description": "Design tokens"
    }
]


class TestJSONSchemas:
    """Test suite for JSON file validation."""

    @pytest.mark.parametrize("json_config", JSON_FILES, ids=[c["description"] for c in JSON_FILES])
    def test_json_file_exists(self, json_config):
        """Test that JSON file exists in the repository."""
        json_file = json_config["file"]
        assert os.path.exists(json_file), f"{json_file} does not exist"

    @pytest.mark.parametrize("json_config", JSON_FILES, ids=[c["description"] for c in JSON_FILES])
    def test_json_file_readable(self, json_config):
        """Test that JSON file can be read."""
        json_file = json_config["file"]
        assert os.path.getsize(json_file) > 0, f"{json_file} is empty"

    @pytest.mark.parametrize("json_config", JSON_FILES, ids=[c["description"] for c in JSON_FILES])
    def test_json_file_valid_json(self, json_config):
        """Test that JSON file contains valid JSON."""
        json_file = json_config["file"]
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"{json_file} is not valid JSON: {e}")

    @pytest.mark.parametrize("json_config", JSON_FILES, ids=[c["description"] for c in JSON_FILES])
    def test_schema_file_exists(self, json_config):
        """Test that schema file exists for validation."""
        schema_file = json_config["schema"]
        assert os.path.exists(schema_file), f"Schema file {schema_file} does not exist"

    @pytest.mark.parametrize("json_config", JSON_FILES, ids=[c["description"] for c in JSON_FILES])
    def test_json_conforms_to_schema(self, json_config):
        """Test that JSON file conforms to its schema."""
        json_file = json_config["file"]
        schema_file = json_config["schema"]
        description = json_config["description"]

        # Load JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Load schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        # Validate against schema
        try:
            validate(instance=json_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"{description} ({json_file}) does not conform to schema: {e.message}")

    def test_image_tags_has_entries(self):
        """Test that image-tags.json has at least one image mapping."""
        with open("scripts/image-tags.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data) > 0, "image-tags.json should contain at least one image mapping"

    def test_recolor_prompts_has_prompts(self):
        """Test that recolor-prompts.json has at least one prompt."""
        with open("scripts/recolor-prompts.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "prompts" in data, "recolor-prompts.json must have 'prompts' field"
        assert len(data["prompts"]) > 0, "recolor-prompts.json should contain at least one prompt"

    def test_design_tokens_has_meta(self):
        """Test that azmx-tokens.json has required metadata."""
        with open("assets/tokens/azmx-tokens.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "$meta" in data, "azmx-tokens.json must have '$meta' field"
        assert "name" in data["$meta"], "Design tokens metadata must contain 'name'"
        assert "version" in data["$meta"], "Design tokens metadata must contain 'version'"
        assert "source" in data["$meta"], "Design tokens metadata must contain 'source'"

    def test_design_tokens_version_format(self):
        """Test that design tokens version follows semantic versioning."""
        with open("assets/tokens/azmx-tokens.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        version = data["$meta"]["version"]
        parts = version.split('.')
        assert len(parts) == 3, f"Version '{version}' should be in format X.Y.Z"
        assert all(p.isdigit() for p in parts), f"Version '{version}' should contain only digits separated by dots"
