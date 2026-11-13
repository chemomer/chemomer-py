"""The PyO3 transport, gated by the inchi-tests oracle corpus.

Every identity fixture's molfile goes through the built chemomer
module; the returned identifier / AuxInfo / InChIKey byte-compare
against the recorded oracle. A failure names the case id — the corpus
is never edited to make a binding pass (the engine's CI owns the same
gate; this one exists because the transport across the Python boundary
is where drift would appear, and smoke tests don't cover it).

Usage: python scripts/oracle_gate.py [INCHI_TESTS_DIR]
Default dir: ../inchi-tests (the CI clone layout).
"""

import json
import os
import sys
from pathlib import Path

import chemomer

CORPUS = Path(
    sys.argv[1] if len(sys.argv) > 1
    else os.environ.get("INCHI_TESTS", "../inchi-tests")
)
FIXTURES = CORPUS / "corpus" / "fixtures"

if not FIXTURES.is_dir():
    print(f"oracle gate: corpus not found at {FIXTURES}", file=sys.stderr)
    sys.exit(2)

failures = []
ran = 0
for fixture_path in sorted(FIXTURES.glob("identity-*.json")):
    cases = json.loads(fixture_path.read_text())
    for case in cases:
        case_id = f"{fixture_path.stem}/{case.get('id', '?')}"
        molfile = case["molfile"]
        try:
            inchi, key = chemomer.from_molfile(molfile)
            aux = chemomer.aux_from_molfile(molfile)
        except Exception as exc:  # noqa: BLE001 - the gate reports, not guesses
            failures.append(f"{case_id}: raised {exc}")
            continue
        ran += 1
        # Compare only fields the fixture records (identity-metal2
        # carries no aux layer) — a missing oracle field is not a gate.
        if "inchi" in case and inchi != case["inchi"]:
            failures.append(f"{case_id}: inchi {inchi!r} != {case['inchi']!r}")
        if "aux" in case and aux != case["aux"]:
            failures.append(f"{case_id}: aux {aux!r} != {case['aux']!r}")
        if "inchikey" in case and key != case["inchikey"]:
            failures.append(f"{case_id}: key {key!r} != {case['inchikey']!r}")

print(f"oracle gate: {ran} cases byte-compared, {len(failures)} failures")
if failures:
    for failure in failures[:20]:
        print(f"  {failure}", file=sys.stderr)
    sys.exit(1)
