"""
OS Privacidad — Interfaz Abstracta de IA (AIProvider)
======================================================
Según sección 1.3 del Build Prompt:
"Definir una interfaz única en el backend, no integraciones sueltas por proveedor."

Cada proveedor (OpenAI, Gemini, Claude, GPT-OSS/Copilot) implementa esta interfaz
en apps/api/ai/providers/. La selección de proveedor activo es configuración por
tenant (tenants.ai_provider_default), nunca hardcodeada.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AIProvider(Protocol):
    """
    Protocolo que define las operaciones de IA disponibles en el sistema.

    Implementaciones deben residir en ai/providers/ y registrarse
    en el factory de proveedores.

    Ejemplo de uso:
        provider = get_ai_provider(tenant.ai_provider_default)
        resumen = await provider.summarize(texto, context)
    """

    async def summarize(self, text: str, context: dict) -> str:
        """Genera un resumen ejecutivo del texto proporcionado."""
        ...

    async def extract_timeline(self, documents: list[dict]) -> list[dict]:
        """Extrae una línea de tiempo de eventos a partir de documentos."""
        ...

    async def propose_risks(self, case_context: dict) -> list[dict]:
        """Propone riesgos identificados a partir del contexto del caso."""
        ...

    async def detect_evidence(self, documents: list[dict]) -> list[dict]:
        """Detecta piezas de evidencia en los documentos proporcionados."""
        ...


def get_ai_provider(provider_name: str) -> AIProvider:
    """
    Factory que retorna la implementación del AIProvider según el nombre.

    Args:
        provider_name: Nombre del proveedor ('openai', 'gemini', 'claude', 'gptoss')

    Returns:
        Instancia del proveedor de IA.

    Raises:
        ValueError: Si el proveedor no está registrado o configurado.
    """
    # Registro de proveedores — se llena conforme se implementan (Fase 7)
    _providers: dict[str, type] = {
        # "openai": OpenAIProvider,     # Fase 7
        # "gemini": GeminiProvider,     # Fase 7
        # "claude": ClaudeProvider,     # Fase 7
        # "gptoss": GPTOSSProvider,     # Fase 7
    }

    provider_cls = _providers.get(provider_name)
    if provider_cls is None:
        available = ", ".join(_providers.keys()) or "(ninguno configurado)"
        raise ValueError(
            f"Proveedor de IA '{provider_name}' no registrado. "
            f"Disponibles: {available}"
        )

    return provider_cls()
