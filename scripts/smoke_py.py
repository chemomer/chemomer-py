"""The chemomer-py smoke test: a V2000 molfile in, the water identity
out — run against the built extension module (maturin develop, or a
wheel installed from dist/). Also gates the version scheme: the PyPI
version is {engine-semver}.{runtime-increment} (the engine is 1.0.0;
the 4th segment counts this package's runtime-only revisions, reset
at the engine's 1.0.0 major)."""

import re
import sys
from importlib.metadata import version

import chemomer

ENGINE_SEMVER = r"1\.1\.6"

WATER = "\n".join(
    [
        "water",
        "  AsciiChem",
        "",
        "  1  0  0  0  0  0  0  0  0  0999 V2000",
        "   12.0000   12.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0",
        "M  END",
        "",
    ]
)

inchi, key = chemomer.from_molfile(WATER)
aux = chemomer.aux_from_molfile(WATER)

failures = []
if inchi != "InChI=1S/H2O/h1H2":
    failures.append(f"identifier: got {inchi!r}")
if aux != "AuxInfo=1/0/N:1/rA:1nO/rB:/rC:12,12,0;":
    failures.append(f"aux: got {aux!r}")
if key != "XLYOFNOQVPJJNP-UHFFFAOYSA-N":
    failures.append(f"key: got {key!r}")

# The ABI-v2 surface (chemomer 1.1.3+): the record with the
# force-equilibrium option, and the SMILES reader.
WATER_RXN = "\n".join(
    [
        "$RXN",
        "water-is-water",
        "  chemomer",
        "",
        "  1  1",
        "$MOL",
        "",
        "  AsciiChem",
        "",
        "  1  0  0  0  0  0  0  0  0  0999 V2000",
        "   12.0000   12.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0  0",
        "M  END",
        "$MOL",
        "",
        "  AsciiChem",
        "",
        "  1  0  0  0  0  0  0  0  0  0999 V2000",
        "   12.0000   12.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0  0",
        "M  END",
        "",
    ]
)
record = chemomer.rinchi_record_from_rxn(WATER_RXN)
if record["rinchi"] != "RInChI=1.00.1S/H2O/h1H2<>H2O/h1H2/d+":
    failures.append(f"record rinchi: got {record['rinchi']!r}")
equil = chemomer.rinchi_record_from_rxn(WATER_RXN, force_equilibrium=True)
if equil["rinchi"] != "RInChI=1.00.1S/H2O/h1H2<>H2O/h1H2/d=":
    failures.append(f"equilibrium rinchi: got {equil['rinchi']!r}")
if equil["rinchikey"] != (
    "Short-RInChIKey=SA-EUHFF-XLYOFNOQVP-XLYOFNOQVP-UHFFFADPSC-NUHFF-NUHFF-NUHFF-ZZZ"
):
    failures.append(f"equilibrium rinchikey: got {equil['rinchikey']!r}")

smiles_inchi, smiles_key = chemomer.from_smiles("c1ccccc1")
if smiles_inchi != "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H":
    failures.append(f"smiles identifier: got {smiles_inchi!r}")

scheme = re.compile(rf"\A{ENGINE_SEMVER}\.\d+\Z")
if not scheme.match(version("chemomer")):
    failures.append(
        f"version scheme: {version('chemomer')!r} does not match "
        f"{{engine-semver}}.{{runtime-increment}} ({scheme.pattern})"
    )
if failures:
    print("chemomer-py smoke test FAILED:", file=sys.stderr)
    for failure in failures:
        print(f"  {failure}", file=sys.stderr)
    sys.exit(1)

print(f"identifier  {inchi}")
print(f"aux         {aux}")
print(f"key         {key}")
print("chemomer-py smoke test passed")
