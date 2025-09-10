# core/io_ifc.py
import tempfile, os, ifcopenshell

def open_ifc_from_bytes(b: bytes):
    # Safer for various encodings & big files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
        tmp.write(b)
        tmp_path = tmp.name
    try:
        model = ifcopenshell.open(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    return model

def save_ifc_to_bytes(model):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
        tmp_path = tmp.name
    try:
        model.write(tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
