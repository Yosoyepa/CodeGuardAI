"""Tests para EventBus."""

import pytest

from src.core.events.event_bus import EventBus
from src.core.events.observers import EventObserver


class MockObserver(EventObserver):
    """Observer mock para testing."""

    def __init__(self):
        self.received_events = []

    def on_event(self, event_type: str, data: dict) -> None:
        self.received_events.append((event_type, data))


class TestEventBus:
    """Tests para EventBus."""

    @pytest.fixture
    def event_bus(self):
        """Crea instancia de EventBus y limpia estado."""
        bus = EventBus()
        bus.clear()
        return bus

    def test_subscribe_and_publish(self, event_bus):
        """Verifica que los observers reciben eventos."""
        observer = MockObserver()

        event_bus.subscribe(observer)
        event_bus.publish("analysis_started", {"id": "123"})

        assert len(observer.received_events) == 1
        assert observer.received_events[0][0] == "analysis_started"
        assert observer.received_events[0][1]["id"] == "123"

    def test_multiple_subscribers(self, event_bus):
        """Verifica que múltiples observers reciben el mismo evento."""
        observer1 = MockObserver()
        observer2 = MockObserver()

        event_bus.subscribe(observer1)
        event_bus.subscribe(observer2)
        event_bus.publish("analysis_started", {"test": True})

        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 1

    def test_unsubscribe(self, event_bus):
        """Verifica que unsubscribe funciona."""
        observer = MockObserver()

        event_bus.subscribe(observer)
        event_bus.unsubscribe(observer)
        event_bus.publish("analysis_started", {"id": "456"})

        assert len(observer.received_events) == 0

    def test_publish_without_subscribers(self, event_bus):
        """Publicar sin suscriptores no debe fallar."""
        # No debe lanzar excepción
        event_bus.publish("analysis_completed", {"id": "789"})

    def test_clear_all_subscribers(self, event_bus):
        """Verifica que clear elimina todos los suscriptores."""
        observer = MockObserver()

        event_bus.subscribe(observer)
        event_bus.clear()

        event_bus.publish("analysis_started", {})
        event_bus.publish("analysis_completed", {})

        assert len(observer.received_events) == 0

    def test_handler_exception_does_not_break_others(self, event_bus):
        """Un observer que falla no debe afectar a otros."""

        class FailingObserver(EventObserver):
            def on_event(self, event_type: str, data: dict) -> None:
                raise ValueError("Observer error")

        failing_observer = FailingObserver()
        working_observer = MockObserver()

        event_bus.subscribe(failing_observer)
        event_bus.subscribe(working_observer)

        # No debe lanzar excepción
        event_bus.publish("analysis_started", {"id": "test"})

        assert len(working_observer.received_events) == 1
