"""
OS Privacidad — Generador del Informe Oficial de Vulneración de Seguridad (Art. 26 RGLOPDP)
============================================================================================
Compila el informe técnico-jurídico exigido por la Superintendencia de Protección
de Datos Personales (SPDP) y la ARCOTEL bajo los 7 requisitos mínimos del Art. 26 del Reglamento.
"""

from __future__ import annotations

import datetime
from typing import Any

from models.brecha_seguridad import BrechaSeguridad


def generar_informe_oficial_spdp(
    brecha: BrechaSeguridad,
    organizacion_nombre: str = "Responsable del Tratamiento",
    organizacion_ruc: str = "N/A",
) -> dict[str, Any]:
    """
    Genera el contenido estructurado y la plantilla en Markdown del informe oficial
    para presentación formal ante la SPDP y ARCOTEL.
    """
    ahora = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    colectivos_str = (
        ", ".join(brecha.colectivos_afectados)
        if isinstance(brecha.colectivos_afectados, list)
        else str(brecha.colectivos_afectados or "No especificado")
    )
    categorias_str = (
        ", ".join(brecha.categorias_datos_expuestas)
        if isinstance(brecha.categorias_datos_expuestas, list)
        else str(brecha.categorias_datos_expuestas or "No especificado")
    )

    # Diagnóstico de plazo
    es_tardia = (
        brecha.fecha_notificacion_spdp and brecha.fecha_notificacion_spdp > brecha.fecha_limite_spdp
    )
    estado_plazo = (
        "NOTIFICACIÓN EXTEMPORÁNEA CON JUSTIFICACIÓN DE DILACIÓN"
        if es_tardia
        else "NOTIFICACIÓN DENTRO DEL TÉRMINO LEGAL (5 DÍAS)"
    )

    markdown_reporte = f"""# INFORME OFICIAL DE NOTIFICACIÓN DE VULNERACIÓN DE SEGURIDAD
## Conforme al Art. 43 LOPDP y Art. 26 del Reglamento General

---

### DATOS DEL RESPONSABLE DEL TRATAMIENTO
* **Organización:** {organizacion_nombre}
* **RUC / Identificación:** {organizacion_ruc}
* **Código de Expediente Interno:** `{brecha.codigo}`
* **Fecha y Hora de Generación:** {ahora}
* **Estado de Cumplimiento:** **{estado_plazo}**

---

### 1. NATURALEZA Y TIPO DE LA VULNERACIÓN (Art. 26 Num. 1)
* **Tipología de Seguridad:** Vulneración de **{brecha.tipo_vulneracion.value.upper()}**
* **Severidad Calificada:** **{brecha.severidad.value.upper()}**
* **Título del Incidente:** {brecha.titulo}
* **Descripción Detallada:**
{brecha.descripcion}

---

### 2. IDENTIFICACIÓN DE LOS TITULARES AFECTADOS (Art. 26 Num. 2)
* **Colectivos de Interesados Comprometidos:** {colectivos_str}
* **Volumen Estimado de Personas Afectadas:** {brecha.volumen_titulares_estimado:,} titulares

---

### 3. DETALLE DE LOS SISTEMAS VULNERADOS (Art. 26 Num. 3)
{brecha.sistemas_afectados}

---

### 4. CAUSA PRESUNTA DE LA VULNERACIÓN (Art. 26 Num. 4)
{brecha.causa_presunta}

---

### 5. VOLUMEN Y TIPOLOGÍA DE DATOS EXPUESTOS (Art. 26 Num. 5)
* **Categorías de Datos Personales:** {categorias_str}
* **Sensibilidad:** {"Incluye datos sensibles / salud / biométricos" if "salud" in categorias_str.lower() or "biom" in categorias_str.lower() else "Datos personales generales / financieros"}

---

### 6. MEDIDAS ADOPTADAS Y PREVISTAS PARA MITIGAR (Art. 26 Num. 6)
#### A. Medidas Inmediatas de Contención:
{brecha.medidas_contencion_inmediatas}

#### B. Medidas Posteriores de Remediación y Erradicación:
{brecha.medidas_remediacion_previstas}

---

### 7. EVALUACIÓN DE IMPACTO Y RIESGO PARA LOS TITULARES (Art. 26 Num. 7)
* **Dictamen del Delegado de Protección de Datos (DPD):**
{brecha.dictamen_dpd or "En proceso de emisión final"}

* **Evaluación de Riesgo a Derechos y Libertades:**
{brecha.evaluacion_riesgo_titulares or "Evaluación técnica conforme a la Guía SPDP 2026"}

* **Notificación al Titular (Art. 46 LOPDP):** {"Requerida y Ejecutada" if brecha.notificada_a_titulares else ("No requerida por excepción legal: " + str(brecha.excepcion_titulares_aplicada) if brecha.excepcion_titulares_aplicada else "Bajo evaluación")}
"""

    return {
        "codigo": brecha.codigo,
        "titulo": brecha.titulo,
        "tipo_vulneracion": brecha.tipo_vulneracion.value,
        "severidad": brecha.severidad.value,
        "volumen_titulares": brecha.volumen_titulares_estimado,
        "fecha_deteccion": brecha.fecha_deteccion.isoformat(),
        "fecha_limite_spdp": brecha.fecha_limite_spdp.isoformat(),
        "notificada_a_spdp": brecha.notificada_a_spdp,
        "informe_markdown": markdown_reporte,
        "generado_en": ahora,
    }
