"""
OS Privacidad — Exportador de Datos para Portabilidad (Art. 17 LOPDP y Art. 22 RGLOPDP)
========================================================================================
Genera paquetes interoperables, estructurados y de lectura mecánica en formatos
estándar (JSON y CSV) para la entrega directa al titular o transmisión entre responsables.
"""

from __future__ import annotations

import csv
import datetime
import io
import json
from typing import Any

from models.solicitud_derecho import SolicitudDerecho


def generar_paquete_portabilidad(
    solicitud: SolicitudDerecho,
    datos: dict[str, Any] | list[dict[str, Any]],
    formato: str = "json",
) -> tuple[str, bytes, str]:
    """
    Genera el archivo de portabilidad estructurado.
    Retorna: (nombre_archivo, contenido_en_bytes, tipo_mime).
    """
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    formato_clean = formato.lower().strip()

    if formato_clean == "csv":
        filename = f"portabilidad_{solicitud.codigo}_{timestamp}.csv"
        media_type = "text/csv; charset=utf-8"

        output = io.StringIO()
        # Normalizar datos a lista de diccionarios
        records: list[dict[str, Any]]
        if isinstance(datos, list):
            records = [r for r in datos if isinstance(r, dict)]
        elif isinstance(datos, dict):
            # Si es un diccionario con colecciones o plano
            if "registros" in datos and isinstance(datos["registros"], list):
                records = datos["registros"]
            else:
                records = [datos]
        else:
            records = [{"datos": str(datos)}]

        if records:
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for row in records:
                writer.writerow(row)
        else:
            writer = csv.writer(output)
            writer.writerow(["titular", "mensaje"])
            writer.writerow([solicitud.titular_nombre, "Sin datos estructurados adicionales"])

        # UTF-8 con BOM para que Excel en Windows/Mac reconozca acentos y caracteres especiales
        content_bytes = output.getvalue().encode("utf-8-sig")

    else:
        # Formato JSON por defecto (interoperable, legible)
        filename = f"portabilidad_{solicitud.codigo}_{timestamp}.json"
        media_type = "application/json; charset=utf-8"

        payload = {
            "metadata_lopdp": {
                "normativa": "Ley Orgánica de Protección de Datos Personales de Ecuador (Art. 17)",
                "codigo_solicitud": solicitud.codigo,
                "titular": {
                    "nombre": solicitud.titular_nombre,
                    "identificacion": solicitud.titular_identificacion,
                    "email": solicitud.titular_email,
                },
                "fecha_generacion": datetime.datetime.now(datetime.UTC).isoformat(),
                "formato": "JSON Interoperable UTF-8",
            },
            "datos_personales_portables": datos,
        }
        content_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")

    return filename, content_bytes, media_type
