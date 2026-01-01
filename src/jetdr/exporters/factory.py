"""
factory - Exporter factory for creating editor-specific exporters

Provides a centralized way to instantiate the appropriate exporter
based on target editor name.
"""

from __future__ import annotations

from jetdr.exporters.base import BaseTimelineExporter


class ExporterRegistry:
    """Registry of available timeline exporters."""

    _exporters: dict[str, type[BaseTimelineExporter]] = {}

    @classmethod
    def register(cls, name: str, exporter_class: type[BaseTimelineExporter]) -> None:
        """
        Register an exporter class.

        Args:
            name: Identifier for the exporter (e.g., 'davinci', 'fcp')
            exporter_class: The exporter class to register
        """
        cls._exporters[name.lower()] = exporter_class

    @classmethod
    def get(cls, name: str) -> type[BaseTimelineExporter]:
        """
        Get an exporter class by name.

        Args:
            name: Identifier for the exporter

        Returns:
            The exporter class

        Raises:
            KeyError: If exporter not found
        """
        key = name.lower()
        if key not in cls._exporters:
            available = ", ".join(cls._exporters.keys())
            raise KeyError(f"Unknown exporter: {name}. Available: {available}")
        return cls._exporters[key]

    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered exporter names."""
        return list(cls._exporters.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an exporter is registered."""
        return name.lower() in cls._exporters


def create_exporter(name: str, **kwargs: object) -> BaseTimelineExporter:
    """
    Factory function to create an exporter instance.

    Args:
        name: Exporter identifier ('davinci', 'fcp', etc.)
        **kwargs: Arguments passed to exporter constructor

    Returns:
        Configured exporter instance
    """
    exporter_class = ExporterRegistry.get(name)
    return exporter_class(**kwargs)
