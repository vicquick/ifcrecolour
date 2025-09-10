# app/components/rule_editor.py
import streamlit as st
from uuid import uuid4

DEFAULT_RULE = {
    "entity": "IfcGeographicElement",
    "conditions": [
        {"pset": "lilasp", "key": "dt. Bezeichnung", "op": "equals", "value": "Rauhblattaster", "case": "insensitive"}
    ],
    "color": {"hex": "#55592C"}
}

OPS   = ["equals", "contains", "regex"]
CASES = ["insensitive", "sensitive"]

def _ensure_ids(rules: list):
    for r in rules:
        if "_id" not in r:
            r["_id"] = f"r_{uuid4().hex}"
        for c in r.get("conditions", []):
            if "_id" not in c:
                c["_id"] = f"c_{uuid4().hex}"
    return rules

# ---------- helpers for dropdown data ----------
def _scope_entities(pset_index, entity):
    if not pset_index:
        return []
    if entity in (None, "", "*", "All", "Any", "All (*)"):
        return list(pset_index.keys())
    return [entity] if entity in pset_index else []

def _pset_options(pset_index, entity):
    out = set()
    for et in _scope_entities(pset_index, entity):
        out.update(pset_index.get(et, {}).keys())
    return sorted(out)

def _key_options(pset_index, entity, pset):
    out = set()
    for et in _scope_entities(pset_index, entity):
        out.update(pset_index.get(et, {}).get(pset, {}).keys())
    return sorted(out)

def _value_options(pset_index, entity, pset, key):
    out = set()
    for et in _scope_entities(pset_index, entity):
        out.update(pset_index.get(et, {}).get(pset, {}).get(key, []))
    return sorted(out)

# ---------- a single condition row ----------
def _cond_row(rid: str, cond: dict, rule_entity: str, pset_index):
    """If case == sensitive: render dropdowns; else: text inputs."""
    c1, c2, c3, c4, c5, c6 = st.columns([1.4, 1.1, 1.0, 1.6, 1.1, 0.8])

    case_val = cond.get("case", "insensitive")

    if case_val == "sensitive" and pset_index:
        # dropdown mode (no free text)
        p_opts = ["—"] + _pset_options(pset_index, rule_entity)
        psel = c1.selectbox("Pset", p_opts,
                            index=(p_opts.index(cond.get("pset")) if cond.get("pset") in p_opts else 0),
                            key=f"pset_sel_{rid}_{cond['_id']}")
        cond["pset"] = "" if psel == "—" else psel

        k_opts = ["—"] + (_key_options(pset_index, rule_entity, cond["pset"]) if cond.get("pset") else [])
        ksel = c2.selectbox("Key", k_opts,
                            index=(k_opts.index(cond.get("key")) if cond.get("key") in k_opts else 0),
                            key=f"key_sel_{rid}_{cond['_id']}")
        cond["key"] = "" if ksel == "—" else ksel

        cond["op"] = c3.selectbox("Op", OPS, index=OPS.index(cond.get("op","equals")),
                                  key=f"op_{rid}_{cond['_id']}")

        v_opts = ["—"] + (_value_options(pset_index, rule_entity, cond["pset"], cond["key"]) if cond.get("pset") and cond.get("key") else [])
        vsel = c4.selectbox("Value", v_opts,
                            index=(v_opts.index(cond.get("value")) if cond.get("value") in v_opts else 0),
                            key=f"val_sel_{rid}_{cond['_id']}")
        cond["value"] = "" if vsel == "—" else vsel

        cond["case"] = c5.selectbox("Case", CASES, index=CASES.index(case_val),
                                    key=f"case_{rid}_{cond['_id']}")
    else:
        # free-text mode (insensitive)
        cond["pset"] = c1.text_input("Pset", cond.get("pset",""), key=f"pset_{rid}_{cond['_id']}")
        cond["key"]  = c2.text_input("Key",  cond.get("key",""),  key=f"key_{rid}_{cond['_id']}")
        cond["op"]   = c3.selectbox("Op", OPS, index=OPS.index(cond.get("op","equals")),
                                    key=f"op_{rid}_{cond['_id']}")
        cond["value"]= c4.text_input("Value", cond.get("value",""), key=f"val_{rid}_{cond['_id']}")
        cond["case"] = c5.selectbox("Case", CASES, index=CASES.index(case_val),
                                    key=f"case_{rid}_{cond['_id']}")

    remove = c6.button("🗑️", key=f"rmc_{rid}_{cond['_id']}", help="Remove condition")
    return cond, remove

# ---------- main editor ----------
def rules_editor(rules: list, entity_options=None, pset_index=None):
    """Returns rules WITH internal _id keys."""
    st.subheader("Rules")
    rules = _ensure_ids(list(rules or []))

    # entity choices
    if not entity_options:
        entity_options = ["All (*)","IfcGeographicElement","IfcProduct","IfcBuildingElementProxy"]

    # Add rule (top)
    if st.button("➕ Add new rule", key="add_rule_top"):
        nr = dict(DEFAULT_RULE)
        nr["_id"] = f"r_{uuid4().hex}"
        nr["conditions"] = []
        rules.append(nr)
        st.session_state["rules"] = rules
        st.rerun()

    # Render rules
    for i, rule in enumerate(list(rules)):
        rid = rule["_id"]
        with st.expander(f"Rule #{i+1}", expanded=True):
            h1, h2, h3, h4 = st.columns([1.6, 1.1, 0.9, 0.9])
            # entity dropdown with All (*)
            current = rule.get("entity","IfcGeographicElement")
            display_val = "All (*)" if current in ("*", "All", "Any", "") else current
            sel = h1.selectbox("Entity", entity_options,
                               index=entity_options.index(display_val) if display_val in entity_options else 0,
                               key=f"entity_{rid}")
            rule["entity"] = "*" if sel == "All (*)" else sel

            # color
            rule_color_hex = rule.get("color",{}).get("hex", "#6E4E2D")
            rule_color_hex = h2.color_picker("Color", rule_color_hex, key=f"color_{rid}")
            rule["color"] = {"hex": rule_color_hex}

            if h3.button("⧉ Duplicate", key=f"dupr_{rid}"):
                clone = {k:v for k,v in rule.items()}
                clone["_id"] = f"r_{uuid4().hex}"
                clone["conditions"] = []
                for c in rule.get("conditions", []):
                    nc = dict(c); nc["_id"] = f"c_{uuid4().hex}"
                    clone["conditions"].append(nc)
                rules.insert(i+1, clone)
                st.session_state["rules"] = rules
                st.rerun()

            if h4.button("🗑️ Delete", key=f"delr_{rid}"):
                rules.pop(i)
                st.session_state["rules"] = rules
                st.rerun()

            st.markdown("**Conditions**")
            conds = rule.get("conditions", [])
            to_remove = None
            for j, c in enumerate(conds):
                c, remove = _cond_row(rid, c, rule.get("entity"), pset_index)
                conds[j] = c
                if remove:
                    to_remove = j
            if to_remove is not None:
                conds.pop(to_remove)
                rule["conditions"] = conds
                st.session_state["rules"] = rules
                st.rerun()

            if st.button("Add condition", key=f"addc_{rid}"):
                conds.append({"pset":"", "key":"", "op":"equals", "value":"", "case":"sensitive", "_id": f"c_{uuid4().hex}"})
                rule["conditions"] = conds
                st.session_state["rules"] = rules
                st.rerun()

    return rules
