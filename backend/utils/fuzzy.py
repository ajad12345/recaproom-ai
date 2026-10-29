"""Fuzzy string matching utility with graceful fallback.
Uses rapidfuzz if installed; falls back to standard library difflib.
"""
try:
    from rapidfuzz import fuzz
except ImportError:
    import difflib

    class _FuzzFallback:
        @staticmethod
        def ratio(s1: str, s2: str) -> float:
            if not s1 and not s2:
                return 100.0
            if not s1 or not s2:
                return 0.0
            return difflib.SequenceMatcher(None, s1, s2).ratio() * 100.0

        @staticmethod
        def partial_ratio(s1: str, s2: str) -> float:
            if not s1 and not s2:
                return 100.0
            if not s1 or not s2:
                return 0.0
            if len(s1) > len(s2):
                s1, s2 = s2, s1
            if s1 in s2:
                return 100.0
            matcher = difflib.SequenceMatcher(None, s1, s2)
            best = 0.0
            for block in matcher.get_matching_blocks():
                start = max(0, block.b - block.a)
                sub = s2[start : start + len(s1)]
                r = difflib.SequenceMatcher(None, s1, sub).ratio() * 100.0
                if r > best:
                    best = r
            return best

        @staticmethod
        def token_set_ratio(s1: str, s2: str) -> float:
            if not s1 and not s2:
                return 100.0
            if not s1 or not s2:
                return 0.0
            tokens1 = set(s1.lower().split())
            tokens2 = set(s2.lower().split())
            intersection = tokens1 & tokens2
            diff1 = tokens1 - intersection
            diff2 = tokens2 - intersection

            sorted_sect = " ".join(sorted(intersection))
            sorted_1 = " ".join(sorted(diff1))
            sorted_2 = " ".join(sorted(diff2))

            combined_1to2 = (sorted_sect + " " + sorted_1).strip()
            combined_2to1 = (sorted_sect + " " + sorted_2).strip()
            sorted_sect = sorted_sect.strip()

            scores = [
                difflib.SequenceMatcher(None, sorted_sect, combined_1to2).ratio() * 100.0 if sorted_sect else 0.0,
                difflib.SequenceMatcher(None, sorted_sect, combined_2to1).ratio() * 100.0 if sorted_sect else 0.0,
                difflib.SequenceMatcher(None, combined_1to2, combined_2to1).ratio() * 100.0,
            ]
            return max(scores)

    fuzz = _FuzzFallback()
