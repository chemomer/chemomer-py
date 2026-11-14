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

ENGINE_SEMVER = r"1\.1\.0"

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
