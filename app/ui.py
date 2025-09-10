# ---- path shim first (must be before any local imports) ----
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import hashlib
import streamlit as st

from core.io_ifc import open_ifc_from_bytes, save_ifc_to_bytes
from core.colorize import recolor_with_rules
from core.psets import build_pset_index, discover_entity_types
from app.components.rule_editor import rules_editor

st.set_page_config(page_title="IFC Recolour", layout="wide")

def _strip_internal(obj):
    if isinstance(obj, dict):
        return {k: _strip_internal(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, list):
        return [_strip_internal(x) for x in obj]
    return obj

def _load_ifc(upload):
    if not upload:
        return None, None
    data = upload.read()
    model = open_ifc_from_bytes(data)
    return data, model

def _ifc_hash(data: bytes | None) -> str:
    if not data:
        return "no-ifc"
    return hashlib.md5(data).hexdigest()

@st.cache_data(show_spinner=False)
def _cached_discover_entity_types(ifc_bytes_hash: str, *, ifc_bytes: bytes):
    model = open_ifc_from_bytes(ifc_bytes)
    return discover_entity_types(model)

@st.cache_data(show_spinner=False)
def _cached_build_pset_index(ifc_bytes_hash: str, entity_types: list[str], *, ifc_bytes: bytes):
    model = open_ifc_from_bytes(ifc_bytes)
    return build_pset_index(model, entity_types=entity_types, max_elements=30000, limit_values=1000)

# ---------- Rules upload handler with versioned key ----------
def _handle_rules_upload(upload_key: str):
    up = st.session_state.get(upload_key)
    if not up:
        return
    try:
        imported = json.loads(up.getvalue().decode("utf-8"))
        st.session_state["rules"] = imported
        st.toast("Rules imported.", icon="✅")
    except Exception as e:
        st.toast(f"Import failed: {e}", icon="❌")
    finally:
        # 🚫 Do NOT assign to the widget's value in session_state.
        # ✅ Instead, bump a version so the widget gets a fresh key.
        st.session_state["rules_upload_key"] = st.session_state.get("rules_upload_key", 0) + 1

def main():
    st.title("IFC Recolor")

    # IFC upload
    up = st.file_uploader("Upload IFC", type=["ifc"], key="ifc_upload")
    if up:
        data, model = _load_ifc(up)
        st.session_state["ifc_bytes"] = data
        st.session_state["ifc_model"] = model
        st.session_state.pop("entity_types", None)
        st.session_state.pop("pset_index", None)
        st.success("IFC loaded.")

    model = st.session_state.get("ifc_model")
    if not model:
        st.info("Upload an IFC file to get started.")
        return

    ifc_bytes = st.session_state.get("ifc_bytes")
    ihash = _ifc_hash(ifc_bytes)

    # Quick counts
    try:
        prod_count = len(model.by_type("IfcProduct"))
    except Exception:
        prod_count = "n/a"
    try:
        geo_count = len(model.by_type("IfcGeographicElement"))
    except Exception:
        geo_count = "n/a"
    st.write(f"IfcProduct count: {prod_count}")
    st.write(f"IfcGeographicElement count: {geo_count}")

    # Discover/build (cached)
    if "entity_types" not in st.session_state:
        with st.spinner("Discovering entity types…"):
            st.session_state["entity_types"] = _cached_discover_entity_types(ihash, ifc_bytes=ifc_bytes)
    entity_types = st.session_state["entity_types"]

    if "pset_index" not in st.session_state:
        with st.spinner("Indexing property sets…"):
            st.session_state["pset_index"] = _cached_build_pset_index(ihash, entity_types, ifc_bytes=ifc_bytes)
    pset_index = st.session_state["pset_index"]

    tab_rules, tab_apply = st.tabs(["🧩 Rules", "🎨 Apply & Export"])

    with tab_rules:
        rules = st.session_state.get("rules", [])
        entity_options = ["All (*)"] + entity_types

        rules = rules_editor(rules, entity_options=entity_options, pset_index=pset_index)
        st.session_state["rules"] = rules

        c1, c2 = st.columns(2)
        with c1:
            safe = _strip_internal(rules)
            st.download_button(
                "Export rules.json",
                data=json.dumps(safe, ensure_ascii=False, indent=2),
                file_name="rules.json",
                mime="application/json",
            )
        with c2:
            # 🔑 Versioned key resets the uploader without writing to its value.
            st.session_state.setdefault("rules_upload_key", 0)
            upload_key = f"rules_upload_{st.session_state['rules_upload_key']}"
            st.file_uploader(
                "Import rules.json",
                type=["json"],
                key=upload_key,
                on_change=_handle_rules_upload,
                args=(upload_key,),
            )

    with tab_apply:
        rules = st.session_state.get("rules", [])
        if not rules:
            st.info("Define at least one rule in the Rules tab.")
        else:
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Dry-run (show matches)"):
                    stats = recolor_with_rules(model, rules, dry_run=True)
                    st.json(stats)
            with cc2:
                if st.button("Apply recolor and prepare download"):
                    changed_model, stats = recolor_with_rules(model, rules, dry_run=False)
                    out_bytes = save_ifc_to_bytes(changed_model)
                    st.download_button(
                        "Download recolored.ifc",
                        data=out_bytes,
                        file_name="recolored.ifc",
                        mime="application/octet-stream",
                    )
                    st.success(
                        f"Changed {stats.get('changed_styles','?')} styles on "
                        f"{stats.get('touched_elements','?')} elements."
                    )

if __name__ == "__main__":
    main()
