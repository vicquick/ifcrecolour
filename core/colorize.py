# core/colorize.py
EPS = 1e-6
from utils.colors import parse_color
from utils.ifc_helpers import surface_styles_simple, has_colour_rgb, material_styles_for_product
from core.rules import matches

def get_or_make_rgb(model, rgb_tuple, name=None):
    r, g, b = rgb_tuple
    for c in model.by_type("IfcColourRgb") or []:
        if abs(c.Red-r) < EPS and abs(c.Green-g) < EPS and abs(c.Blue-b) < EPS:
            return c
    return model.create_entity("IfcColourRgb", Name=name, Red=r, Green=g, Blue=b)

def _gather_targets(model, rules):
    # if any rule is "*" → scan broadly (IfcProduct)
    if any((r.get("entity") in (None, "", "*", "All", "Any")) for r in rules):
        return list(model.by_type("IfcProduct") or [])
    # else union of entities from rules
    seen = set(); targets = []
    for r in rules:
        ent = r.get("entity")
        if not ent:
            continue
        for e in model.by_type(ent) or []:
            gid = getattr(e, "GlobalId", None)
            if gid and gid in seen:
                continue
            targets.append(e)
            if gid:
                seen.add(gid)
    return targets

def recolor_with_rules(model, rules, dry_run=False):
    changed = 0
    touched = set()
    targets = _gather_targets(model, rules)

    for prod in targets:
        # pick the first matching rule's color
        apply_rgb = None
        for rule in rules:
            if matches(prod, rule):
                apply_rgb = parse_color(rule["color"])
                break
        if not apply_rgb:
            continue

        new_rgb = get_or_make_rgb(model, apply_rgb, name="LL-Recolor")
        any_hit = False

        # A) direct + mapped styles (instance & MappingSource)
        for sty in surface_styles_simple(prod):
            if not has_colour_rgb(sty):
                continue
            if not dry_run:
                sty.SurfaceColour = new_rgb
            changed += 1
            any_hit = True

        # B) material styled representations (instance + type)
        for sty in material_styles_for_product(model, prod, include_type=True):
            if not has_colour_rgb(sty):
                continue
            if not dry_run:
                sty.SurfaceColour = new_rgb
            changed += 1
            any_hit = True

        if any_hit:
            gid = getattr(prod, "GlobalId", None)
            if gid:
                touched.add(gid)

    stats = {"changed_styles": changed, "touched_elements": len(touched)}
    return (model, stats) if not dry_run else stats
