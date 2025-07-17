# galdr/interceptor/backend/modules/mirror_mirror/engine.py
# The core logic for comparing two HTTP responses.

import difflib
import json
import logging
from typing import Dict, Any, List

class MirrorEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _compare_headers(self, headers_a: Dict, headers_b: Dict) -> Dict:
        """Compares two dictionaries of headers, case-insensitively."""
        # Normalize keys to lowercase for comparison
        a_norm = {k.lower(): v for k, v in headers_a.items()}
        b_norm = {k.lower(): v for k, v in headers_b.items()}
        
        # We will ignore these headers as they change on every request
        ignored_headers = {'date', 'expires', 'set-cookie', 'x-request-id', 'etag', 'last-modified', 'age'}

        keys_a = set(a_norm.keys()) - ignored_headers
        keys_b = set(b_norm.keys()) - ignored_headers

        added = {k: b_norm[k] for k in keys_b - keys_a}
        removed = {k: a_norm[k] for k in keys_a - keys_b}
        modified = {}
        
        for k in keys_a.intersection(keys_b):
            if a_norm[k] != b_norm[k]:
                modified[k] = {'from': a_norm[k], 'to': b_norm[k]}
                
        return {"added": added, "removed": removed, "modified": modified}

    def _compare_bodies(self, body_a: str, body_b: str) -> List[str]:
        """Performs a unified diff on two response bodies."""
        diff = difflib.unified_diff(
            body_a.splitlines(keepends=True),
            body_b.splitlines(keepends=True),
            fromfile='response_A',
            tofile='response_B',
        )
        return list(diff)

    def compare_responses(self, response_a: Dict, response_b: Dict) -> Dict:
        """
        Takes two response objects and returns a structured dictionary of their differences.
        """
        self.logger.info("Starting response comparison.")
        
        status_diff = response_a.get('status_code') != response_b.get('status_code')
        
        header_diffs = self._compare_headers(
            response_a.get('headers_json', {}),
            response_b.get('headers_json', {})
        )
        
        # Handle potential JSON bodies for a smarter diff in the future
        body_a_str = json.dumps(response_a.get('body'), indent=2) if isinstance(response_a.get('body'), dict) else str(response_a.get('body'))
        body_b_str = json.dumps(response_b.get('body'), indent=2) if isinstance(response_b.get('body'), dict) else str(response_b.get('body'))
        
        body_diff_lines = self._compare_bodies(body_a_str, body_b_str)

        return {
            "status_a": response_a.get('status_code'),
            "status_b": response_b.get('status_code'),
            "status_changed": status_diff,
            "header_diffs": header_diffs,
            "body_diff_lines": body_diff_lines
        }
