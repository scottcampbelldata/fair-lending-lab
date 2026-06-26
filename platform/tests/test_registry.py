"""Registry sanity: every hypothesis has required fields and a callable runner."""
from __future__ import annotations

from flab.hypotheses import REGISTRY


def test_registry_nonempty():
    assert len(REGISTRY) >= 5


def test_every_hypothesis_has_required_fields():
    required = {
        "key", "title", "h0", "h1", "direction", "effect_of_interest",
        "domain_question", "causal_caveat", "runner",
    }
    for k, h in REGISTRY.items():
        for f in required:
            assert getattr(h, f, None) is not None, f"{k} missing {f}"
        assert callable(h.runner), f"{k} runner not callable"
        assert k == h.key


def test_keys_have_no_em_or_en_dashes_in_text():
    # Construct sentinels by codepoint so the source file itself stays clean.
    bad = (chr(0x2014), chr(0x2013))
    for k, h in REGISTRY.items():
        for field in (h.title, h.h0, h.h1, h.effect_of_interest,
                       h.domain_question, h.causal_caveat):
            for ch in bad:
                assert ch not in field, f"{k}: forbidden dash in field"


def test_directions_are_valid():
    valid = {"two-sided", "greater", "less"}
    for h in REGISTRY.values():
        assert h.direction in valid
