# chemomer-py

The **Python binding for the [chemomer](https://github.com/chemomer/chemomer)
engine** — a native extension module built with
[PyO3](https://github.com/PyO3/pyo3) + [maturin](https://github.com/PyO3/maturin).

```python
import chemomer

inchi, inchikey = chemomer.from_molfile(molfile_text)
aux = chemomer.aux_from_molfile(molfile_text)
```

A thin wrapper by design: the engine (the byte-exact InChI port, gated
by the shared oracle corpus) lives in the chemomer repo and lands here
as a Cargo git dependency; this repo owns only the pyo3 surface and
the packaging.

## Build and test

```bash
pip install maturin
maturin develop --release
python scripts/smoke_py.py
```

## Publishing

`pypi.yml` is dispatch-only and doubly gated (`publish` input + the
PyPI trusted-publisher registration for project `chemomer` with
repository `chemomer/chemomer-py`, workflow `pypi.yml`, no
environment) — the publish credential is the job's OIDC token; no
stored secrets.

## License

MIT, same as the engine.
