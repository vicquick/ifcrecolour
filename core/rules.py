# core/rules.py
import re
from core.psets import iter_pset_values  # <-- fixed import

def _cmp(a, op, b, case):
    if a is None: a = ""
    if b is None: b = ""
    if case == "insensitive":
        a, b = str(a).casefold(), str(b).casefold()
    if op == "equals":   return a == b
    if op == "contains": return b in a
    if op == "regex":    return re.search(b, a) is not None
    return False

def matches(element, rule):
    ent = (rule.get("entity") or "").strip()
    # "*" / "All" / "Any" means no entity restriction
    if ent and ent not in ("*", "All", "Any") and not element.is_a(ent):
        return False
    for cond in rule.get("conditions", []):
        hit = False
        for val in iter_pset_values(element, cond["pset"], cond["key"]):
            if _cmp(val, cond["op"], cond["value"], cond.get("case","insensitive")):
                hit = True
                break
        if not hit:
            return False
    return True
