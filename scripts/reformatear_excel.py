"""
Reformatea un Excel «plano» (como los que generaba la versión Streamlit) al
formato profesional del aplicativo: hojas Resumen, Ficha_Empresa (si hay una
sola empresa), Vista_Principal, Datos_Completos y Diccionario.

Uso:
    python scripts/reformatear_excel.py ENTRADA.xlsx [SALIDA.xlsx] [--modo filters|business_name|nit|batch_nits] [--criterio TEXTO]

Si no se indica salida, el archivo se guarda junto a la entrada con nombre
descriptivo. Los criterios de segmentación se infieren de las columnas con un
único valor (departamento, tamaño, cadena, trayectoria) cuando aplica.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.exporter import create_export, filename_for  # noqa: E402
from backend.glossary import load_glossary  # noqa: E402
from backend.models import SearchRequest  # noqa: E402

INFERIBLES = {
    "Departamento de la empresa": "DEPARTAMENTO",
    "Municipio de la empresa": "MUNICIPIO",
    "Tamaño de la empresa": "TAMANO",
    "Cadena de segmentación": "CADENA_SEGMENTACION",
    "Trayectoria exportadora": "TRAYECTORIA_EXPORTADORA",
    "Inversión extranjera": "INVERSION_EXTRANJERA",
    "¿La empresa ha exportado?": "HA_EXPORTADO",
}


def inferir_filtros(frame: pd.DataFrame) -> dict[str, list[str]]:
    filtros: dict[str, list[str]] = {}
    if len(frame) < 2:
        return filtros
    for columna, clave in INFERIBLES.items():
        if columna in frame.columns:
            valores = frame[columna].dropna().astype(str).unique().tolist()
            if len(valores) == 1:
                filtros[clave] = valores
    return filtros


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path, nargs="?")
    parser.add_argument("--modo", choices=["filters", "business_name", "nit", "batch_nits"])
    parser.add_argument("--criterio", default="", help="Texto buscado (razón social o NIT) cuando el modo es directo.")
    parser.add_argument("--dir", type=Path, help="Carpeta de salida (el nombre del archivo se genera automáticamente).")
    args = parser.parse_args()

    frame = pd.read_excel(args.entrada, sheet_name=0)
    frame = frame.dropna(axis=1, how="all") if len(frame) else frame
    modo = args.modo
    if not modo:
        nombre = args.entrada.stem.casefold()
        modo = "business_name" if "raz" in nombre else "nit" if "nit" in nombre and len(frame) == 1 else "filters"
    if modo == "business_name":
        criterio = args.criterio or (str(frame["Razón social"].iloc[0]).split()[0] if len(frame) == 1 and "Razón social" in frame.columns else "empresa")
        request = SearchRequest(mode="business_name", term=criterio)
    elif modo == "nit":
        request = SearchRequest(mode="nit", term=args.criterio or str(frame["NIT"].iloc[0]))
    elif modo == "batch_nits":
        request = SearchRequest(mode="batch_nits", nits=[str(n) for n in frame["NIT"].tolist()])
    else:
        request = SearchRequest(mode="filters", filters=inferir_filtros(frame))

    total = len(frame)
    buffer = create_export(frame, request, total, load_glossary()["entries"], generated=datetime.now())
    salida = args.salida or (args.dir or args.entrada.parent) / filename_for(request, total)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(buffer.getvalue())
    print(f"{args.entrada.name} -> {salida.name} ({total} empresa(s), {len(frame.columns)} variables, modo {request.mode}: {request.summary()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
