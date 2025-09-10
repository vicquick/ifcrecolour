# core/psets.py
from utils.ifc_helpers import unwrap

def iter_pset_values(element, pset_name_contains, key_name):
    """Yield string values for a given (pset contains, key equals) on one element."""
    for rel in getattr(element, "IsDefinedBy", []) or []:
        pdef = getattr(rel, "RelatingPropertyDefinition", None)
        if not pdef or not pdef.is_a("IfcPropertySet"):
            continue
        pname = (pdef.Name or "")
        if pset_name_contains.lower() not in pname.lower():
            continue
        for prop in pdef.HasProperties or []:
            if prop.is_a("IfcPropertySingleValue") and prop.Name == key_name:
                yield str(unwrap(getattr(prop, "NominalValue", None)) or "")

def survey_psets(model, entity_types=("IfcGeographicElement",), limit_values=100, max_elements=20000):
    """Return a flat list of {pset,key,values,count_values} for quick inspection."""
    index = {}
    total = 0
    for et in entity_types:
        try:
            elems = model.by_type(et) or []
        except Exception:
            elems = []
        for e in elems:
            total += 1
            if total > max_elements:
                break
            for rel in getattr(e, "IsDefinedBy", []) or []:
                pdef = getattr(rel, "RelatingPropertyDefinition", None)
                if not pdef or not pdef.is_a("IfcPropertySet"):
                    continue
                pset_name = pdef.Name or ""
                for prop in pdef.HasProperties or []:
                    if prop.is_a("IfcPropertySingleValue"):
                        key = prop.Name or ""
                        val = str(unwrap(getattr(prop, "NominalValue", None)) or "")
                        index.setdefault((pset_name, key), set()).add(val)
        if total > max_elements:
            break

    rows = []
    for (ps, k), vals in index.items():
        rows.append({"pset": ps, "key": k, "values": sorted(list(vals)), "count_values": len(vals)})
    return rows

def get_pset_names(model, entity_types=("IfcGeographicElement","IfcProduct"), max_elements=20000, max_psets=400):
    """Collect unique Pset names (for suggestions)."""
    names = set()
    total = 0
    for et in entity_types:
        try:
            elems = model.by_type(et) or []
        except Exception:
            elems = []
        for e in elems:
            total += 1
            if total > max_elements:
                break
            for rel in getattr(e, "IsDefinedBy", []) or []:
                pdef = getattr(rel, "RelatingPropertyDefinition", None)
                if pdef and pdef.is_a("IfcPropertySet") and pdef.Name:
                    names.add(pdef.Name)
                    if len(names) >= max_psets:
                        return sorted(names)
        if total > max_elements:
            break
    return sorted(names)

def build_pset_index(model, entity_types=None, max_elements=30000, limit_values=1000):
    """
    Build a nested index (for 'sensitive' dropdowns in the rule editor):
      { entity: { pset: { key: [values...] } } }
    """
    default_entities = [
        "IfcGeographicElement","IfcProduct","IfcBuildingElementProxy",
        "IfcSite","IfcBuilding","IfcBuildingStorey","IfcSpace",
        "IfcWall","IfcSlab","IfcRoof","IfcColumn","IfcBeam","IfcMember",
        "IfcCovering","IfcFurnishingElement","IfcDistributionElement",
        "IfcProxy","IfcAnnotation"
    ]
    if entity_types is None:
        entity_types = default_entities

    idx = {}
    for et in entity_types:
        try:
            elems = model.by_type(et) or []
        except Exception:
            elems = []
        count = 0
        for e in elems:
            count += 1
            if count > max_elements:
                break
            for rel in getattr(e, "IsDefinedBy", []) or []:
                pdef = getattr(rel, "RelatingPropertyDefinition", None)
                if not pdef or not pdef.is_a("IfcPropertySet"):
                    continue
                pset = pdef.Name or ""
                if not pset:
                    continue
                et_map = idx.setdefault(et, {})
                key_map = et_map.setdefault(pset, {})
                for prop in pdef.HasProperties or []:
                    if prop.is_a("IfcPropertySingleValue"):
                        key = prop.Name or ""
                        if not key:
                            continue
                        val = str(unwrap(getattr(prop, "NominalValue", None)) or "")
                        s = key_map.setdefault(key, set())
                        if len(s) < limit_values:
                            s.add(val)

    # Convert sets to sorted lists
    for et in idx:
        for ps in idx[et]:
            for k in idx[et][ps]:
                idx[et][ps][k] = sorted(idx[et][ps][k])

    return idx

def discover_entity_types(model, base_types=("IfcProduct",), max_elements=200000):
    """
    Return a sorted list of concrete entity type names present in the model,
    e.g. ["IfcBeam","IfcWall","IfcStair", ...].
    """
    seen = set()
    for base in base_types:
        try:
            elems = model.by_type(base) or []
        except Exception:
            elems = []
        for i, e in enumerate(elems):
            if i >= max_elements:
                break
            t = e.is_a()
            if t:
                seen.add(t)
    return sorted(seen)