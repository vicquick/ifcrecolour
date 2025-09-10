# utils/ifc_helpers.py

def unwrap(v):
    return getattr(v, "wrappedValue", v)

def _renderings_from_style_container(style_container):
    """Yield IfcSurfaceStyleRendering/Shading from a style container."""
    if not style_container:
        return
    if style_container.is_a("IfcPresentationStyleAssignment"):
        for s in getattr(style_container, "Styles", []) or []:
            if s and s.is_a("IfcSurfaceStyle"):
                for sub in s.Styles or []:
                    if sub and (sub.is_a("IfcSurfaceStyleRendering") or sub.is_a("IfcSurfaceStyleShading")):
                        yield sub
    elif style_container.is_a("IfcSurfaceStyle"):
        for sub in style_container.Styles or []:
            if sub and (sub.is_a("IfcSurfaceStyleRendering") or sub.is_a("IfcSurfaceStyleShading")):
                yield sub

def _styles_for_item(item):
    """Yield style 'rendering/shading' objects attached to a single item."""
    # Case A: item is an IfcStyledItem container
    if item and item.is_a("IfcStyledItem"):
        for sty in getattr(item, "Styles", []) or []:
            yield from _renderings_from_style_container(sty)
        return
    # Case B: inverse StyledByItem from geometry -> style
    if hasattr(item, "StyledByItem") and item.StyledByItem:
        styled = list(item.StyledByItem) if isinstance(item.StyledByItem, tuple) else [item.StyledByItem]
        for si in styled:
            if not si or not getattr(si, "Styles", None):
                continue
            for sty in si.Styles:
                yield from _renderings_from_style_container(sty)

def surface_styles_simple(product):
    """
    Yield surface styles from:
      - the product's own representation items
      - mapped source items (IfcMappedItem → MappingSource)
    (No type/material traversal — intentionally minimal.)
    """
    rep = getattr(product, "Representation", None)
    if not rep:
        return
    for shape in rep.Representations or []:
        for item in getattr(shape, "Items", []) or []:
            # direct styles
            for sty in _styles_for_item(item):
                yield sty
            # mapped source styles
            if item and item.is_a("IfcMappedItem"):
                src = getattr(item, "MappingSource", None)
                if src:
                    mrep = getattr(src, "MappedRepresentation", None)
                    if mrep:
                        for src_item in mrep.Items or []:
                            for sty in _styles_for_item(src_item):
                                yield sty

def has_colour_rgb(style):
    """Return True if style has a SurfaceColour that is an IfcColourRgb."""
    col = getattr(style, "SurfaceColour", None)
    return bool(col and col.is_a("IfcColourRgb"))

# utils/ifc_helpers.py  (additions)

def _iter_material_objects(m):
    """Yield the material object and its common containers -> actual materials."""
    if not m:
        return
    yield m

    # Follow usage wrappers
    for attr in ("ForLayerSet", "ForProfileSet"):
        tgt = getattr(m, attr, None)
        if tgt:
            yield tgt

    # Common containers to actual material leaves
    for attr in ("Materials", "MaterialLayers", "MaterialProfiles", "MaterialConstituents"):
        seq = getattr(m, attr, None)
        if seq:
            for sub in seq:
                mat = getattr(sub, "Material", None)
                if mat:
                    yield from _iter_material_objects(mat)
                else:
                    yield from _iter_material_objects(sub)

def material_styles_for_product(model, product, include_type=True):
    """
    Yield surface styles coming from material styled representations
    associated to the product and (optionally) its type.
    """
    # collect targets: instance and (optionally) its type object(s)
    targets = {product}
    if include_type:
        for reltyp in (getattr(product, "IsTypedBy", []) or []):
            t = getattr(reltyp, "RelatingType", None)
            if t:
                targets.add(t)

    # walk material associations that reference any of those targets
    for rel in model.by_type("IfcRelAssociatesMaterial") or []:
        objs = set(getattr(rel, "RelatedObjects", []) or [])
        if not (objs & targets):
            continue
        mat = getattr(rel, "RelatingMaterial", None)
        for m in _iter_material_objects(mat):
            for mdr in getattr(m, "HasRepresentation", []) or []:
                for sr in getattr(mdr, "Representations", []) or []:
                    for it in getattr(sr, "Items", []) or []:
                        # reuse your existing item -> styles function
                        for sty in _styles_for_item(it):
                            yield sty
