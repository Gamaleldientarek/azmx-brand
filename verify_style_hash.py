#!/usr/bin/env python3
import hashlib
import base64
import re

# Read the HTML file
with open('index.html', 'r') as f:
    html = f.read()

# Extract inline style
style_match = re.search(r'<style>\n(.*?)\n</style>', html, re.DOTALL)
if style_match:
    style_content = '\n' + style_match.group(1) + '\n'
    style_hash = 'sha256-' + base64.b64encode(hashlib.sha256(style_content.encode('utf-8')).digest()).decode('ascii')
    print(f'Calculated style hash: {style_hash}')

# Extract CSP policy
csp_match = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', html)
if csp_match:
    csp = csp_match.group(1)
    style_hash_in_csp = re.search(r"style-src[^;]*'(sha256-[^']+)'", csp)
    if style_hash_in_csp:
        print(f'CSP style hash: {style_hash_in_csp.group(1)}')
        print(f'Match: {style_hash == style_hash_in_csp.group(1)}')
