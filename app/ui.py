# ---- path shim first (must be before any local imports) ----
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # ...\ifcrecolorrgb
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ------------------------------------------------------------

import json
import streamlit as st
from core.io_ifc import open_ifc_from_bytes, save_ifc_to_bytes
from core.colorize import recolor_with_rules
from core.psets import build_pset_index, discover_entity_types
from app.components.rule_editor import rules_editor

st.set_page_config(page_title="IFC Recolor", layout="wide")

def _strip_internal(obj):
    if isinstance(obj, dict):
        return {k: _strip_internal(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_internal(x) for x in obj]
    return obj

def load_ifc(upload):
    if not upload:
        return None, None
    data = upload.read()
    model = open_ifc_from_bytes(data)
    return data, model

def main():
    st.title("IFC Recolor")

    # Upload IFC
    up = st.file_uploader("Upload IFC", type=["ifc"])
    if up:
        data, model = load_ifc(up)
        st.session_state["ifc_bytes"] = data
        st.session_state["ifc_model"] = model
        # clear caches bound to previous file
        st.session_state.pop("entity_types", None)
        st.session_state.pop("pset_index", None)
        st.success("IFC loaded.")

    model = st.session_state.get("ifc_model")
    if not model:
        return

    # Quick counts (safe)
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

    # Discover entity types present (e.g., IfcStair, IfcWall, …)
    if "entity_types" not in st.session_state:
        with st.spinner("Discovering entity types…"):
            st.session_state["entity_types"] = discover_entity_types(model)
    entity_types = st.session_state["entity_types"]

    # Build (or re-use) pset index for sensitive dropdowns using discovered entities
    if "pset_index" not in st.session_state:
        with st.spinner("Indexing property sets…"):
            st.session_state["pset_index"] = build_pset_index(
                model,
                entity_types=entity_types,   # <-- ensures IfcStair, etc., are included
                max_elements=30000,
                limit_values=1000,
            )
    pset_index = st.session_state["pset_index"]

    # Horizontal tabs
    tab_rules, tab_apply = st.tabs(["🧩 Rules", "🎨 Apply & Export"])

    # ---- Rules tab ----
    with tab_rules:
        rules = st.session_state.get("rules", [])

        # Entity dropdown options: All + discovered types
        entity_options = ["All (*)"] + entity_types

        rules = rules_editor(rules, entity_options=entity_options, pset_index=pset_index)
        st.session_state["rules"] = rules

        # Export / Import
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
            up_rules = st.file_uploader("Import rules.json", type=["json"], key="rules_import_inline")
            if up_rules:
                try:
                    imported = json.loads(up_rules.read().decode("utf-8"))
                    st.session_state["rules"] = imported
                    st.success("Rules imported.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

    # ---- Apply & Export tab ----
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
                        f"Changed {stats['changed_styles']} styles on {stats['touched_elements']} elements."
                    )

if __name__ == "__main__":
    main()
