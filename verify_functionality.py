#!/usr/bin/env python3
"""Comprehensive verification of index.html functionality"""
import re

def verify_html(html_path):
    with open(html_path, 'r') as f:
        html = f.read()

    print("="*70)
    print("COMPREHENSIVE FUNCTIONALITY VERIFICATION")
    print("="*70)

    all_checks_passed = True

    # 1. Security Meta Tags
    print("\n1. SECURITY META TAGS")
    print("-" * 70)
    security_tags = {
        "Content-Security-Policy": (
            r'<meta http-equiv="Content-Security-Policy" content="[^"]+"',
            "CSP meta tag protects against XSS"
        ),
        "X-Content-Type-Options": (
            r'<meta http-equiv="X-Content-Type-Options" content="nosniff"',
            "Prevents MIME type sniffing"
        ),
        "X-Frame-Options": (
            r'<meta http-equiv="X-Frame-Options" content="DENY"',
            "Prevents clickjacking via iframe embedding"
        ),
        "Referrer-Policy": (
            r'<meta name="referrer" content="strict-origin-when-cross-origin"',
            "Controls referrer information leakage"
        )
    }

    for tag_name, (pattern, description) in security_tags.items():
        if re.search(pattern, html):
            print(f"   ✓ {tag_name}: {description}")
        else:
            print(f"   ✗ {tag_name}: MISSING - {description}")
            all_checks_passed = False

    # 2. Copy Button Functionality
    print("\n2. COPY BUTTON FUNCTIONALITY (Recolour Prompts)")
    print("-" * 70)
    copy_buttons = re.findall(r'<button[^>]*class="copy"[^>]*data-prompt="([^"]+)"', html)
    print(f"   Found {len(copy_buttons)} copy buttons")
    if len(copy_buttons) > 0:
        print(f"   ✓ Copy buttons present for prompts: {', '.join(copy_buttons[:3])}...")
        # Check for click event handler in script
        if re.search(r"document\.querySelectorAll\('\.copy'\)\.forEach", html):
            print("   ✓ Click event handler attached to copy buttons")
        else:
            print("   ✗ Copy button event handler MISSING")
            all_checks_passed = False

        # Check for clipboard API usage
        if re.search(r"navigator\.clipboard\.writeText", html):
            print("   ✓ Clipboard API used for copying")
        else:
            print("   ✗ Clipboard API MISSING")
            all_checks_passed = False

        # Check for fallback mechanism
        if re.search(r"document\.execCommand\('copy'\)", html):
            print("   ✓ Fallback copy mechanism (execCommand) present")
        else:
            print("   ✗ Fallback copy mechanism MISSING")
            all_checks_passed = False
    else:
        print("   ✗ No copy buttons found")
        all_checks_passed = False

    # 3. Tag Filtering Functionality
    print("\n3. TAG FILTERING FUNCTIONALITY")
    print("-" * 70)
    tag_buttons = re.findall(r'<button[^>]*data-tag="([^"]*)"', html)
    print(f"   Found {len(tag_buttons)} tag filter buttons")
    if len(tag_buttons) > 0:
        # Show first few tags
        non_empty_tags = [t for t in tag_buttons if t][:5]
        print(f"   ✓ Tag buttons: All, {', '.join(non_empty_tags)}...")

        # Check for filter script
        if re.search(r"var buttons = document\.querySelectorAll\('\.tagbar button'\)", html):
            print("   ✓ Tag filter script present")
        else:
            print("   ✗ Tag filter script MISSING")
            all_checks_passed = False

        # Check for figure elements with data-tags
        figures_with_tags = re.findall(r'<figure[^>]*data-tags="([^"]+)"', html)
        print(f"   Found {len(figures_with_tags)} images with tag attributes")
        if len(figures_with_tags) > 0:
            print(f"   ✓ Images are tagged for filtering")
        else:
            print("   ✗ No tagged images found")
            all_checks_passed = False

        # Check for hidden attribute logic
        if re.search(r"f\.hidden = !match", html):
            print("   ✓ Show/hide logic implemented")
        else:
            print("   ✗ Show/hide logic MISSING")
            all_checks_passed = False
    else:
        print("   ✗ No tag filter buttons found")
        all_checks_passed = False

    # 4. Section Highlighting on Scroll
    print("\n4. SECTION HIGHLIGHTING ON SCROLL")
    print("-" * 70)
    # Check for IntersectionObserver
    if re.search(r"new IntersectionObserver", html):
        print("   ✓ IntersectionObserver used for scroll detection")
    else:
        print("   ✗ IntersectionObserver MISSING")
        all_checks_passed = False

    # Check for nav links
    nav_links = re.findall(r'<a href="#([^"]+)"[^>]*>', html)
    if len(nav_links) > 0:
        print(f"   ✓ Found {len(nav_links)} navigation links")
        # Check for 'on' class toggle
        if re.search(r"classList\.toggle\('on'", html):
            print("   ✓ Active section highlighting logic present")
        else:
            print("   ✗ Active section highlighting logic MISSING")
            all_checks_passed = False
    else:
        print("   ✗ No navigation links found")
        all_checks_passed = False

    # 5. Image Loading
    print("\n5. IMAGE LOADING")
    print("-" * 70)
    # Check for images
    img_tags = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', html)
    print(f"   Found {len(img_tags)} image tags")

    # Check for lazy loading
    lazy_imgs = re.findall(r'<img[^>]*loading="lazy"', html)
    print(f"   ✓ {len(lazy_imgs)} images use lazy loading")

    # Check image sources
    github_imgs = [src for src in img_tags if 'github' in src or src.startswith('assets/')]
    print(f"   ✓ {len(github_imgs)} images from allowed sources (assets/ or GitHub)")

    # Check CSP allows image sources
    csp_match = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
    if csp_match:
        csp_content = csp_match.group(1)
        if "img-src 'self' data: https:" in csp_content:
            print("   ✓ CSP allows images from self, data URLs, and HTTPS")
        else:
            print("   ✗ CSP may block some images")
            all_checks_passed = False

    # 6. No Inline Event Handlers (CSP Compliance)
    print("\n6. CSP COMPLIANCE (No Inline Event Handlers)")
    print("-" * 70)
    inline_handlers = re.findall(r'<[^>]*\s(on\w+)=', html)
    if len(inline_handlers) == 0:
        print("   ✓ No inline event handlers (onclick, onload, etc.)")
    else:
        print(f"   ✗ Found {len(inline_handlers)} inline event handlers: {', '.join(set(inline_handlers))}")
        all_checks_passed = False

    # Check for inline style attributes (should be minimal)
    inline_styles = re.findall(r'<[^>]*\sstyle="[^"]+"', html)
    # Some inline styles are OK (like color swatches), but shouldn't be many
    print(f"   ℹ  Found {len(inline_styles)} inline style attributes (acceptable for color swatches)")

    # 7. Accessibility
    print("\n7. ACCESSIBILITY FEATURES")
    print("-" * 70)
    # Check for ARIA attributes
    if re.search(r'aria-pressed=', html):
        print("   ✓ ARIA pressed state used on toggle buttons")

    if re.search(r'role="status"', html):
        print("   ✓ Status role used for screen reader announcements")

    if re.search(r'aria-live="polite"', html):
        print("   ✓ Live region for dynamic content updates")

    # Final Summary
    print("\n" + "="*70)
    if all_checks_passed:
        print("✅ ALL AUTOMATED CHECKS PASSED")
        print("\nManual verification still required:")
        print("  • Open index.html in a browser")
        print("  • Check browser console for CSP violations (should be none)")
        print("  • Test copy button on recolour prompts")
        print("  • Test tag filtering (click different tags)")
        print("  • Test section highlighting (scroll through page)")
        print("  • Verify all images load correctly")
    else:
        print("❌ SOME CHECKS FAILED - Review output above")
    print("="*70)

    return all_checks_passed

if __name__ == '__main__':
    verify_html('./index.html')
