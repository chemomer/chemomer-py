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


# -- the reaction-identity transport (the corpus's RInChI tranche) ------
# Graceful absence: a chemomer module built from an engine that
# predates the rinchi surface skips the tranche with a report — the
# gate lights up when the build picks up an engine that ships it. The
# equilibrium family is recorded under the oracle's /force-equilibrium
# flag, which the Python surface carries no entry for; its four cases
# gate through the DECODE direction (the recorded string decodes to
# equilibrium) and are reported as derive-skips. The RDfile edge
# exports the identifier line only — the other four lines ride the RXN
# exports' assembly, and the engine's CI owns the full per-line gate.

try:
    chemomer.rinchi_decode("RInChI=1.00.1S/H2O/h1H2<>H2O/h1H2/d+", "")
except AttributeError:
    print("rinchi gate: skipped — the chemomer module predates the rinchi surface")
    sys.exit(0)

rinchi_path = FIXTURES / "rinchi-reactions.json"
if not rinchi_path.is_file():
    print("rinchi gate: skipped — the corpus pin predates the rinchi tranche")
    sys.exit(0)
rinchi_cases = json.loads(rinchi_path.read_text())


def triples(components):
    """The order-free identity-triple comparison: roles resolve from the
    direction flag; within a role the wire order is the assembly's
    sorted order."""
    return sorted(
        (component["inchi"], component["aux"], component["inchikey"])
        for component in components
    )


rinchi_ran = 0
rinchi_failures = []
derive_skips = []
for case in rinchi_cases:
    case_id = f"rinchi-reactions/{case['id']}"

    # The decode direction: the recorded identifier (plus its RAuxInfo
    # companion) reads back into the recorded per-component identity
    # triples.
    try:
        decoded = chemomer.rinchi_decode(case["rinchi"], case.get("rauxinfo", ""))
    except Exception as exc:  # noqa: BLE001 - the gate reports, not guesses
        rinchi_failures.append(f"{case_id}: decode raised {exc}")
        continue
    rinchi_ran += 1
    decoded_components = [
        *decoded["reactants"], *decoded["products"], *decoded["agents"]
    ]
    if triples(decoded_components) != triples(case["components"]):
        rinchi_failures.append(f"{case_id}: decoded components differ from the oracle")
    expected_directionality = "equilibrium" if case.get("forceEquilibrium") else "directional"
    if decoded["directionality"] != expected_directionality:
        rinchi_failures.append(
            f"{case_id}: directionality {decoded['directionality']!r} != {expected_directionality!r}"
        )

    # The derive direction (keys compared headerless — the corpus
    # records them without their headers).
    try:
        if case.get("forceEquilibrium"):
            derive_skips.append(case_id)
        elif "rxnfile" in case:
            outputs = {
                "rinchi": chemomer.rinchi_from_rxn(case["rxnfile"]),
                "rauxinfo": chemomer.rinchi_aux_from_rxn(case["rxnfile"]),
                "rinchikey": chemomer.rinchi_short_key_from_rxn(case["rxnfile"]).removeprefix("Short-RInChIKey="),
                "longKey": chemomer.rinchi_long_key_from_rxn(case["rxnfile"]).removeprefix("Long-RInChIKey="),
                "webKey": chemomer.rinchi_web_key_from_rxn(case["rxnfile"]).removeprefix("Web-RInChIKey="),
            }
            rinchi_ran += 1
            for field, actual in outputs.items():
                if field in case and actual != case[field]:
                    rinchi_failures.append(f"{case_id}: {field} {actual!r} != {case[field]!r}")
        elif "rdfile" in case:
            rinchi = chemomer.rinchi_from_rd(case["rdfile"])
            rinchi_ran += 1
            if rinchi != case["rinchi"]:
                rinchi_failures.append(f"{case_id}: rinchi {rinchi!r} != {case['rinchi']!r}")
    except Exception as exc:  # noqa: BLE001 - the gate reports, not guesses
        rinchi_failures.append(f"{case_id}: raised {exc}")

print(
    f"rinchi gate: {rinchi_ran} comparisons, {len(rinchi_failures)} failures, "
    f"{len(derive_skips)} derive-skips (force-equilibrium: {', '.join(derive_skips)})"
)
if rinchi_failures:
    for failure in rinchi_failures[:20]:
        print(f"  {failure}", file=sys.stderr)
    sys.exit(1)
