# Add Content-Security-Policy and security meta tags to generated gallery page

## Overview

The generated index.html (served publicly via GitHub Pages) contains two inline <script> blocks and extensive inline styles but has no Content-Security-Policy (CSP) meta tag, no clickjacking protection (frame-ancestors), and no Referrer-Policy. GitHub Pages does not support custom HTTP response headers, so protection must be implemented via <meta http-equiv> tags. Without CSP, any XSS vulnerability (including sec-002) has unrestricted access to execute arbitrary scripts, load external resources, and exfiltrate data. The page can be embedded in any iframe for clickjacking, and full URLs leak to any external link target.

## Rationale

CSP is the most effective browser-side XSS mitigation for static sites. Since the gallery uses only two inline scripts with deterministic content and no external JS/CSS resources, a strict hash-based CSP is straightforward to implement. This provides defence-in-depth: even if HTML escaping is missed (sec-002), the CSP would block injected script execution.

---
*This spec was created from ideation and is pending detailed specification.*
