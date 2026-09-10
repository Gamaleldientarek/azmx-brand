#!/usr/bin/env python3
"""Extract actual inline scripts from index.html and verify CSP hashes"""
import hashlib
import base64
import re

# Read the HTML file
with open('index.html', 'r') as f:
    html = f.read()

# Extract all script tags
scripts = re.findall(r'<script>\n(.*?)\n</script>', html, re.DOTALL)

print(f'Found {len(scripts)} inline script(s)\n')

# Calculate hashes for each script
for i, script in enumerate(scripts, 1):
    # Include the newlines like the style hash calculation
    script_with_newlines = '\n' + script + '\n'
    hash_value = 'sha256-' + base64.b64encode(hashlib.sha256(script_with_newlines.encode('utf-8')).digest()).decode('ascii')
    print(f'Script {i} hash (with newlines): {hash_value}')
    print(f'First 60 chars: {script[:60]}...')
    print()

# Extract CSP policy and show script hashes
csp_match = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', html)
if csp_match:
    csp = csp_match.group(1)
    # Find all sha256 hashes in the CSP policy
    all_hashes = re.findall(r"'(sha256-[^']+)'", csp)
    print(f'CSP contains {len(all_hashes)} hash(es) total:')
    for h in all_hashes:
        print(f'  {h}')
