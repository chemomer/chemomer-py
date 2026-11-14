//! The Python binding for the chemomer engine: the native extension
//! module `chemomer` with `from_molfile(molfile) -> (inchi, inchikey)`,
//! `aux_from_molfile(molfile) -> aux`, and the reaction-identity
//! surface — `rinchi_from_rxn(rxnfile) -> rinchi` and its four
//! companion lines, `rinchi_from_rd(rdfile) -> rinchi`, and
//! `rinchi_decode(rinchi, rauxinfo)` -> the decoded reaction dict.
//!
//! A thin wrapper — the engine lives in chemomer/chemomer (the git
//! dependency, renamed `chemomer_engine` because this crate is the
//! `chemomer` module); this crate owns only the pyo3 surface.

// The `#[pyfunction]` wrapper's return conversion reads as an identity
// `PyErr` conversion to the current clippy (pyo3 0.22 macro output) —
// silenced here: macro-generated code outside this module's control.
#![allow(clippy::useless_conversion)]

use chemomer_engine::Engine;
use chemomer_engine::rinchi::Directionality;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

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

// -- the reaction-identity surface (the RInChI layer) -------------------
// The RXNfile and RDfile input edges derive the oracle lines; the
// decode direction returns the native dict (the engine crate is
// in-process, so no string wire form is needed):
//
//   { "directionality": "directional" | "equilibrium",
//     "reactants" | "products" | "agents":
//         [{"inchi": ..., "aux": ..., "inchikey": ...}, ...] }

/// Derives the RInChI identifier from a V2000 RXNfile.
#[pyfunction]
fn rinchi_from_rxn(rxnfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rxnfile(rxnfile)
        .and_then(|reaction| reaction.rinchi_string())
        .map_err(error_to_value_error)
}

/// Derives the RAuxInfo line from a V2000 RXNfile.
#[pyfunction]
fn rinchi_aux_from_rxn(rxnfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rxnfile(rxnfile)
        .and_then(|reaction| reaction.rinchi_auxinfo())
        .map_err(error_to_value_error)
}

/// Derives the short (hashed) RInChIKey from a V2000 RXNfile.
#[pyfunction]
fn rinchi_short_key_from_rxn(rxnfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rxnfile(rxnfile)
        .and_then(|reaction| reaction.rinchi_short_key())
        .map_err(error_to_value_error)
}

/// Derives the long RInChIKey from a V2000 RXNfile.
#[pyfunction]
fn rinchi_long_key_from_rxn(rxnfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rxnfile(rxnfile)
        .and_then(|reaction| reaction.rinchi_long_key())
        .map_err(error_to_value_error)
}

/// Derives the web RInChIKey from a V2000 RXNfile.
#[pyfunction]
fn rinchi_web_key_from_rxn(rxnfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rxnfile(rxnfile)
        .and_then(|reaction| reaction.rinchi_web_key())
        .map_err(error_to_value_error)
}

/// Derives the RInChI identifier from an MDL RDfile (the `$DATUM
/// $MFMT` agent-scan input edge).
#[pyfunction]
fn rinchi_from_rd(rdfile: &str) -> PyResult<String> {
    chemomer_engine::parse_rdfile(rdfile)
        .and_then(|reaction| reaction.rinchi_string())
        .map_err(error_to_value_error)
}

/// Decodes a RInChI string (with its RAuxInfo companion; pass `""`
/// when unknown) into the decoded reaction dict — no structures are
/// rebuilt, the components carry their identities straight from the
/// string.
#[pyfunction]
fn rinchi_decode<'py>(
    py: Python<'py>,
    rinchi: &str,
    rauxinfo: &str,
) -> PyResult<Bound<'py, PyDict>> {
    let reaction = chemomer_engine::rinchi::reaction_from_rinchi_with_auxinfo(rinchi, rauxinfo)
        .map_err(error_to_value_error)?;

    let decoded = PyDict::new_bound(py);
    decoded.set_item(
        "directionality",
        match reaction.directionality() {
            Directionality::Directional => "directional",
            Directionality::Equilibrium => "equilibrium",
        },
    )?;
    for (role, components) in [
        ("reactants", reaction.reactants()),
        ("products", reaction.products()),
        ("agents", reaction.agents()),
    ] {
        let mut role_list = Vec::with_capacity(components.len());
        for component in components {
            let entry = PyDict::new_bound(py);
            entry.set_item("inchi", component.inchi_string().map_err(error_to_value_error)?)?;
            entry.set_item("aux", component.aux_string().map_err(error_to_value_error)?)?;
            entry.set_item("inchikey", component.inchikey().map_err(error_to_value_error)?)?;
            role_list.push(entry);
        }
        decoded.set_item(role, PyList::new_bound(py, role_list))?;
    }
    Ok(decoded)
}

fn error_to_value_error(error: chemomer_engine::Error) -> PyErr {
    PyValueError::new_err(error.message().to_string())
}

#[pymodule]
fn chemomer(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(from_molfile, module)?)?;
    module.add_function(wrap_pyfunction!(aux_from_molfile, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_from_rxn, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_aux_from_rxn, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_short_key_from_rxn, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_long_key_from_rxn, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_web_key_from_rxn, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_from_rd, module)?)?;
    module.add_function(wrap_pyfunction!(rinchi_decode, module)?)?;
    Ok(())
}
