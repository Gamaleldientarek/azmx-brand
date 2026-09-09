#!/usr/bin/env python3
import sys
import os
import importlib.util

# Load the module from the file directly
module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'rebuild-index.py')
spec = importlib.util.spec_from_file_location("rebuild_index", module_path)
rebuild_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild_index)

result = rebuild_index.compute_csp_hash('test')
print('OK' if result else 'FAIL')
print(f'Hash result: {result}')
