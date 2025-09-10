# ifcrecolour 🎨

_Recolor IFC models based on name → RGB mappings (e.g., plant species)._  
Built in Python; designed for fast, repeatable post-export styling for landscape / BIM workflows.

---

## Features

- **Name → Color mapping**: recolor elements by (case-sensitive) name keys.
- **Deterministic outputs**: same mappings → same colors every time.
- **Green fallback**: unmapped items get a pleasant default green.
- **Extensible core**: clean separation between app, core logic, and utilities.
- **Windows-friendly**: examples and paths target PowerShell on Windows.

---

## Quick start (Windows / PowerShell)

```powershell
# 1) Clone and enter
git clone https://github.com/vicquick/ifcrecolour.git
cd ifcrecolour

# 2) (Recommended) Create & activate a venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Run the recolor tool (example)
python -m app --input "C:\path\to\input.ifc" --output "C:\path\to\output_recolored.ifc"
```

> If the `-m app` entry point doesn’t exist on your branch, use the main script inside `app/` (e.g. `python app\main.py ...`).

---

## Usage

```
python -m app --input INPUT_IFC --output OUTPUT_IFC [options]
```

**Options (typical):**

- `--map FILE` – external mapping file (JSON or CSV) with name → RGB.  
- `--fallback R G B` – override default fallback color (floats 0–1).  
- `--dry-run` – parse & report what would be recolored, but don’t write.  
- `--verbose` – more logs (useful for debugging names that don’t match).

> Tip: Many IFC authoring tools export with localized names. Ensure your mapping keys match the **exact** `Name` / `ObjectType` / property value your script uses for lookup.

---

## Mapping your colors

You can either hard-code the dictionary in code or load from an external file.

### 1) Inline (Python dict)

```python
NAME_TO_RGB = {
  "Raublattaster":        (0.333, 0.337, 0.200),  # #55592C
  "Sonnenhut":            (0.612, 0.549, 0.161),  # #9C8C29
  "Goldmelisse":          (0.223, 0.310, 0.133),  # #394F22
  "Purpur Sonnenhut":     (0.431, 0.306, 0.176),  # #6E4E2D
  "Blaue Flachslilie":    (0.431, 0.306, 0.176),  # example reuse
}
FALLBACK_RGB = (0.22, 0.45, 0.26)  # pleasant green
```

> RGB values are floats 0–1. If you start from hex, divide the 0–255 channels by 255.

### 2) External JSON

```json
{
  "Raublattaster": [0.333, 0.337, 0.200],
  "Sonnenhut":     [0.612, 0.549, 0.161]
}
```

Run with:

```powershell
python -m app --input input.ifc --output output.ifc --map .\mappings\plants.json
```

---

## Repository structure

```
ifcrecolour/
├─ app/          # CLI / entrypoints (argument parsing, I/O, logging)
├─ core/         # core business logic (IFC read/write, color application)
├─ utils/        # helpers: mapping loaders, name normalizers, color utils
├─ requirements.txt
└─ .gitignore
```

- **app/**  
  - Provides the command-line interface and orchestration.  
  - Validates input/output paths, loads mapping files, calls `core`.

- **core/**  
  - Reads IFC, finds target elements by name, applies surface colors.  
  - Encapsulates IfcOpenShell usage and write-out.

- **utils/**  
  - JSON/CSV mapping loaders, hex↔RGB converters, safe logging, etc.

---

## License

MIT License – feel free to use and adapt.
