//! The Python binding for the chemomer engine: the native extension
//! module `chemomer` with `from_molfile(molfile) -> (inchi, inchikey)`
//! and `aux_from_molfile(molfile) -> aux`.
//!
//! A thin wrapper — the engine lives in chemomer/chemomer (the git
//! dependency, renamed `chemomer_engine` because this crate is the
//! `chemomer` module); this crate owns only the pyo3 surface.

// The `#[pyfunction]` wrapper's return conversion reads as an identity
// `PyErr` conversion to the current clippy (pyo3 0.22 macro output) —
// silenced here: macro-generated code outside this module's control.
#![allow(clippy::useless_conversion)]

use chemomer_engine::Engine;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Derives `(inchi, inchikey)` from a V2000 molfile.
#[pyfunction]
fn from_molfile(molfile: &str) -> PyResult<(String, String)> {
    Engine::from_molfile(molfile)
        .and_then(|engine| engine.inchi_string().map(|inchi| (engine, inchi)))
        .and_then(|(engine, inchi)| engine.inchikey().map(|inchikey| (inchi, inchikey)))
        .map_err(|error| PyValueError::new_err(error.message().to_string()))
}

/// Derives the AuxInfo line from a V2000 molfile.
#[pyfunction]
fn aux_from_molfile(molfile: &str) -> PyResult<String> {
    Engine::from_molfile(molfile)
        .and_then(|engine| engine.aux_string())
        .map_err(|error| PyValueError::new_err(error.message().to_string()))
}

#[pymodule]
fn chemomer(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(from_molfile, module)?)?;
    module.add_function(wrap_pyfunction!(aux_from_molfile, module)?)?;
    Ok(())
}
