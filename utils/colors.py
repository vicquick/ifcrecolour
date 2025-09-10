def hex_to_rgb01(h):
    h = h.strip().lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return (r/255.0, g/255.0, b/255.0)

def parse_color(cobj):
    if "hex" in cobj: return hex_to_rgb01(cobj["hex"])
    if "rgb" in cobj: return tuple(cobj["rgb"])
    raise ValueError("color requires hex or rgb")
