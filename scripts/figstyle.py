"""Tipografía común de todas las figuras: Myriad Pro.

Myriad Pro NO está instalada como fuente del sistema en esta máquina. Los
únicos ejemplares son los .otf que Acrobat/Reader traen dentro de su paquete,
así que se registran en matplotlib EN TIEMPO DE EJECUCIÓN — no se copia ni se
instala nada. Si una actualización de Adobe mueve esas rutas, el módulo avisa
por stderr y cae a la sans-serif por defecto: una figura sin Myriad es
preferible a un script que aborta.

Uso: importar antes de crear cualquier figura.

    import figstyle; figstyle.use()

Si algún día se instala Myriad Pro como fuente del sistema (~/Library/Fonts),
matplotlib la encontrará sola y este módulo no hará falta más que para fijar
los tamaños; USER_FONT_DIR se busca primero, así que esa copia gana.

GLIFOS QUE ESTA MYRIAD NO TRAE. El corte que distribuye Acrobat carece de la
FLECHA "→" (U+2192) y de los PRIMOS "′ ″" (U+2032/33); matplotlib los dibuja
como un rectángulo vacío. Todo lo demás que usan estas figuras sí está:
á é í ó ú ñ Ñ ¿ ¡ ° × · – — − ≥ ≤ ±. En vez de flecha, escribir "a" o una raya
(Ñuble a Los Lagos, 31-jul – 1-ago); en vez de primos, decimales de grado.
`check()` lista los caracteres de un texto que la fuente no tiene, y el aviso
de matplotlib por glifo ausente se deja ACTIVO a propósito: es la única señal
de que una figura salió con rectángulos.
"""
import glob
import os
import sys

import matplotlib
from matplotlib import font_manager as fm
from matplotlib.ft2font import FT2Font

FAMILY = "Myriad Pro"
USER_FONT_DIR = os.path.expanduser("~/Library/Fonts")
ADOBE_GLOBS = [
    os.path.join(USER_FONT_DIR, "MyriadPro*.otf"),
    os.path.join(USER_FONT_DIR, "Myriad Pro*.otf"),
    "/Library/Application Support/Adobe/Acrobat/DC/WebResources/Resource1/OWP/default/fonts/MyriadPro*.otf",
    "/Library/Application Support/Adobe/Acrobat/DC/WebResources/Resource1/app1/fonts/MyriadPro*.otf",
    "/Library/Application Support/Adobe/Reader/DC/WebResources/Resource0/OWP/default/fonts/MyriadPro*.otf",
    "/Library/Application Support/Adobe/Reader/DC/WebResources/Resource0/app1/fonts/MyriadPro*.otf",
]
FALLBACKS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]

_done = False


def register():
    """Registra los .otf de Myriad Pro. Devuelve la lista de archivos usados."""
    files = []
    for pat in ADOBE_GLOBS:
        files.extend(sorted(glob.glob(pat)))
    seen, keep = set(), []
    for f in files:                       # de-duplica por nombre de archivo
        b = os.path.basename(f)
        if b not in seen:
            seen.add(b); keep.append(f)
    for f in keep:
        try:
            fm.fontManager.addfont(f)
        except Exception as e:            # un .otf ilegible no debe voltear todo
            print(f"figstyle: no se pudo registrar {f}: {e}", file=sys.stderr)
    return keep


def available():
    return FAMILY in {f.name for f in fm.fontManager.ttflist}


def use(base=10.0):
    """Fija Myriad Pro y los tamaños base. Idempotente."""
    global _done
    if not _done:
        register()
        _done = True
    fams = ([FAMILY] if available() else []) + FALLBACKS
    if not available():
        print(f"figstyle: AVISO — no se encontró '{FAMILY}'; se usa "
              f"{FALLBACKS[0]}. Revisar las rutas en ADOBE_GLOBS.", file=sys.stderr)
    matplotlib.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": fams,
        "mathtext.fontset": "dejavusans",   # Myriad no trae glifos matemáticos
        "mathtext.default": "regular",
        "font.size": base,
        "axes.titlesize": base * 1.0,
        "axes.labelsize": base * 0.95,
        "xtick.labelsize": base * 0.85,
        "ytick.labelsize": base * 0.85,
        "legend.fontsize": base * 0.85,
        "figure.titlesize": base * 1.3,
        # texto vectorial y editable en PDF/SVG (para llevarlo a Illustrator)
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })
    return available()


MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_formatter(patron="{d} {mes}"):
    """Formateador de eje temporal en español.

    `DateFormatter("%d %b")` toma el mes del locale del proceso, que aquí es
    inglés y no hay garantía de que es_ES esté generado en el sistema. Se
    formatea a mano. Campos: {d} día, {mes} mes abreviado, {H} hora, {a} año.
    """
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter

    def _f(x, pos=None):
        t = mdates.num2date(x)
        return patron.format(d=t.day, mes=MESES[t.month - 1],
                             H=f"{t.hour:02d}", a=t.year)
    return FuncFormatter(_f)


def check(*texts):
    """Caracteres de `texts` que la Myriad registrada NO tiene. Vacío = todo bien."""
    if not _done:
        use()
    if not available():
        return []
    p = fm.findfont(fm.FontProperties(family=FAMILY))
    cmap = FT2Font(p).get_charmap()
    bad = {c for t in texts for c in str(t)
           if not c.isspace() and ord(c) not in cmap}
    return sorted(bad)


if __name__ == "__main__":
    files = register()
    print(f"{len(files)} archivo(s) Myriad Pro registrados:")
    for f in files:
        print("   ", f)
    ok = use()
    print(f"'{FAMILY}' disponible en matplotlib: {ok}")
    fams = sorted({f.name for f in fm.fontManager.ttflist if "yriad" in f.name})
    print("familias con 'yriad':", fams)
    print("faltantes en 'a→b 41°28′S áéíóúñ ≥ ± ×':",
          check("a→b 41°28′S áéíóúñ ≥ ± ×"))
