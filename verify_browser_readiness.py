#!/usr/bin/env python3
"""Verify the HTML is browser-ready and CSP-compliant"""
import re
from html.parser import HTMLParser

class HTMLVerifier(HTMLParser):
    def __init__(self):
        super().__init__()
        self.issues = []
        self.warnings = []
        self.copy_buttons = 0
        self.tag_buttons = 0
        self.images = 0
        self.inline_handlers = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Check for inline event handlers (onclick, onload, etc.)
        for attr, value in attrs:
            if attr.startswith('on'):
                self.inline_handlers.append(f'<{tag} {attr}=...>')

        # Count copy buttons
        if tag == 'button' and 'copy' in attrs_dict.get('class', ''):
            self.copy_buttons += 1

        # Count tag filter buttons
        if tag == 'button' and 'data-tag' in attrs_dict:
            self.tag_buttons += 1

        # Count images
        if tag == 'img':
            self.images += 1
            # Check for loading="lazy"
            if attrs_dict.get('loading') != 'lazy':
                self.warnings.append(f'Image missing loading="lazy": {attrs_dict.get("src", "unknown")[:50]}')

# Read and parse HTML
with open('index.html', 'r') as f:
    html = f.read()

verifier = HTMLVerifier()
verifier.feed(html)

print('=' * 60)
print('BROWSER READINESS VERIFICATION')
print('=' * 60)
print()

print('Interactive Elements:')
print(f'  ✓ Copy buttons found: {verifier.copy_buttons}')
print(f'  ✓ Tag filter buttons found: {verifier.tag_buttons}')
print(f'  ✓ Images found: {verifier.images}')
print()

print('CSP Compliance:')
if verifier.inline_handlers:
    print(f'  ✗ Inline event handlers found (CSP violation!):')
    for handler in verifier.inline_handlers[:5]:
        print(f'    - {handler}')
    if len(verifier.inline_handlers) > 5:
        print(f'    ... and {len(verifier.inline_handlers) - 5} more')
else:
    print(f'  ✓ No inline event handlers (CSP compliant)')
print()

# Check for javascript: URLs
js_urls = re.findall(r'href=["\']javascript:', html, re.IGNORECASE)
if js_urls:
    print(f'  ✗ javascript: URLs found (CSP violation!): {len(js_urls)}')
else:
    print(f'  ✓ No javascript: URLs')
print()

# Verify aria attributes for accessibility
aria_live = html.count('aria-live')
aria_pressed = html.count('aria-pressed')
print('Accessibility:')
print(f'  ✓ aria-live regions: {aria_live}')
print(f'  ✓ aria-pressed attributes: {aria_pressed}')
print()

if verifier.warnings:
    print('Warnings:')
    for w in verifier.warnings[:5]:
        print(f'  ⚠ {w}')
    if len(verifier.warnings) > 5:
        print(f'  ... and {len(verifier.warnings) - 5} more')
    print()

# Summary
if verifier.issues:
    print(f'RESULT: FAILED - {len(verifier.issues)} critical issue(s)')
    for issue in verifier.issues:
        print(f'  ✗ {issue}')
elif verifier.inline_handlers or js_urls:
    print(f'RESULT: FAILED - CSP violations detected')
else:
    print('RESULT: PASSED - HTML is browser-ready and CSP-compliant')
    print()
    print('NOTE: Manual browser testing still recommended to verify:')
    print('  - Copy button actually works')
    print('  - Tag filter actually works')
    print('  - Section highlight on scroll works')
    print('  - No CSP violations in browser console')
    print('  - Images load correctly')
