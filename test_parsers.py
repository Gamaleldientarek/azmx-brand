#!/usr/bin/env python3
"""Test script for all reference file parsers."""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# Import by reading the file directly since it has a hyphen in the name
import importlib.util
spec = importlib.util.spec_from_file_location("sync_references", "scripts/sync-references.py")
sync_references = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_references)

# Get file paths
file_paths = sync_references.get_file_paths()

# Test image-tags parsers
print("=" * 60)
print("Testing image-tags parsers")
print("=" * 60)

json_path = file_paths["image-tags"]["json"]
markdown_path = file_paths["image-tags"]["markdown"]

print("\nTesting image-tags JSON parser...")
try:
    json_data = sync_references.parse_image_tags_json(json_path)
    print(f"✓ Parsed {len(json_data)} images from JSON")
    # Show a sample
    sample_key = list(json_data.keys())[0]
    print(f"  Sample: {sample_key} -> {json_data[sample_key]}")
except Exception as e:
    print(f"✗ JSON parser failed: {e}")
    sys.exit(1)

print("\nTesting image-tags markdown parser...")
try:
    markdown_data = sync_references.parse_image_tags_markdown(markdown_path)
    print(f"✓ Parsed {len(markdown_data)} images from markdown")
    # Show a sample
    sample_key = list(markdown_data.keys())[0]
    print(f"  Sample: {sample_key} -> {markdown_data[sample_key]}")
except Exception as e:
    print(f"✗ Markdown parser failed: {e}")
    sys.exit(1)

# Test recolor-prompts parsers
print("\n" + "=" * 60)
print("Testing recolor-prompts parsers")
print("=" * 60)

json_path = file_paths["recolor-prompts"]["json"]
markdown_path = file_paths["recolor-prompts"]["markdown"]

print("\nTesting recolor-prompts JSON parser...")
try:
    json_data = sync_references.parse_recolor_prompts_json(json_path)
    print(f"✓ Parsed recolor-prompts JSON successfully")
    print(f"  Model: {json_data['model']}")
    print(f"  Prompts found: {len(json_data['prompts'])}")
    print(f"  First prompt: {json_data['prompts'][0]['key']} ({json_data['prompts'][0]['label']})")
except Exception as e:
    print(f"✗ JSON parser failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTesting recolor-prompts markdown parser...")
try:
    markdown_data = sync_references.parse_recolor_prompts_markdown(markdown_path)
    print(f"✓ Parsed recolor-prompts markdown successfully")
    print(f"  Model: {markdown_data['model']}")
    print(f"  Prompts found: {len(markdown_data['prompts'])}")
    print(f"  First prompt: {markdown_data['prompts'][0]['key']} ({markdown_data['prompts'][0]['label']})")
except Exception as e:
    print(f"✗ Markdown parser failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All parsers imported and tested successfully")
print("=" * 60)
