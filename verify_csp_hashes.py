#!/usr/bin/env python3
"""Verify CSP hashes match the inline scripts in index.html"""
import hashlib
import base64

# First inline script (copy button) - lines 182-209
script1 = """document.querySelectorAll('.copy').forEach(function(btn){
  btn.addEventListener('click', function(){
    var key = btn.dataset.prompt;
    var text = document.getElementById('prompt-' + key).textContent;
    var label = btn.querySelector('.copy-label');
    var done = function(){
      label.textContent = 'Copied';
      btn.dataset.copied = '1';
      document.getElementById('copy-status').textContent = key + ' prompt copied to clipboard';
      setTimeout(function(){
        label.textContent = 'Copy';
        btn.removeAttribute('data-copied');
      }, 2000);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(fallback);
    } else { fallback(); }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly','');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); }
      catch (e) { label.textContent = 'Select manually'; }
      document.body.removeChild(ta);
    }
  });
});"""

# Second inline script (tag filter and nav) - lines 471-505
script2 = """(function(){
  var buttons = document.querySelectorAll('.tagbar button');
  var figures = document.querySelectorAll('figure[data-tags]');
  var status = document.getElementById('filter-status');
  buttons.forEach(function(b){
    b.addEventListener('click', function(){
      var tag = b.dataset.tag;
      buttons.forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var shown = 0;
      figures.forEach(function(f){
        var match = !tag || (' ' + f.dataset.tags + ' ').indexOf(' ' + tag + ' ') > -1;
        f.hidden = !match;
        if (match) shown++;
      });
      document.querySelectorAll('section[id]').forEach(function(sec){
        var figs = sec.querySelectorAll('figure[data-tags]');
        if (!figs.length) return;
        var any = Array.prototype.some.call(figs, function(f){ return !f.hidden; });
        sec.hidden = !any;
      });
      status.textContent = tag ? (shown + ' images tagged ' + tag) : (shown + ' images, filter cleared');
    });
  });
  // Highlight the section currently in view in the sidebar
  var links = document.querySelectorAll('aside nav a[href^="#"]');
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (!e.isIntersecting) return;
      links.forEach(function(l){
        l.classList.toggle('on', l.getAttribute('href') === '#' + e.target.id);
      });
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  document.querySelectorAll('section[id]').forEach(function(s){ obs.observe(s); });
})();"""

hash1 = base64.b64encode(hashlib.sha256(script1.encode('utf-8')).digest()).decode('ascii')
hash2 = base64.b64encode(hashlib.sha256(script2.encode('utf-8')).digest()).decode('ascii')

print('Script 1 hash: sha256-' + hash1)
print('Script 2 hash: sha256-' + hash2)
print()
print('Expected hashes from CSP:')
print("  'sha256-cU7yKP4xHoZbfY+P3jx4rgGU+mBApyGY7CgyqO8Yb+Q='")
print("  'sha256-ahYhK+sJS+TwI5zThoonoft2O4yP2Y5fkRxml7aQjFY='")
print()
if hash1 == 'cU7yKP4xHoZbfY+P3jx4rgGU+mBApyGY7CgyqO8Yb+Q=' and hash2 == 'ahYhK+sJS+TwI5zThoonoft2O4yP2Y5fkRxml7aQjFY=':
    print('✓ CSP hashes match!')
elif hash1 == 'ahYhK+sJS+TwI5zThoonoft2O4yP2Y5fkRxml7aQjFY=' and hash2 == 'cU7yKP4xHoZbfY+P3jx4rgGU+mBApyGY7CgyqO8Yb+Q=':
    print('✓ CSP hashes match (reversed order)!')
else:
    print('✗ CSP hashes DO NOT match')
