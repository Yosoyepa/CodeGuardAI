"""Tests para get_db dependency."""

from unittest.mock import MagicMock, patch

import pytest


class TestGetDb:
    """Tests para get_db dependency."""

    @patch("src.core.dependencies.get_db.SessionLocal")
    def test_get_db_yields_session(self, mock_session_local):
        """get_db yields una sesión de base de datos."""
        from src.core.dependencies.get_db import get_db

        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Act
        generator = get_db()
        session = next(generator)

        # Assert
        assert session == mock_session
        mock_session_local.assert_called_once()

    @patch("src.core.dependencies.get_db.SessionLocal")
    def test_get_db_closes_session_after_use(self, mock_session_local):
        """get_db cierra la sesión después de usarla."""
        from src.core.dependencies.get_db import get_db

        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Act
        generator = get_db()
        session = next(generator)
        
        # Simular fin del request
        try:
            next(generator)
        except StopIteration:
            pass

        # Assert
        mock_session.close.assert_called_once()

    @patch("src.core.dependencies.get_db.SessionLocal")
    def test_get_db_closes_session_on_exception(self, mock_session_local):
        """get_db cierra la sesión incluso si hay excepción."""
        from src.core.dependencies.get_db import get_db

        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Act
        generator = get_db()
        session = next(generator)
        
        # Simular excepción y cierre
        try:
            generator.throw(Exception("Test exception"))
        except Exception:
            pass

        # Assert
        mock_session.close.assert_called_once()

    @patch("src.core.dependencies.get_db.SessionLocal")
    def test_get_db_can_be_used_as_context(self, mock_session_local):
        """get_db funciona correctamente en contexto de FastAPI Depends."""
        from src.core.dependencies.get_db import get_db

        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simular uso típico con Depends
        db_generator = get_db()
        
        # Obtener sesión
        db = next(db_generator)
        assert db is mock_session
        
        # Usar la sesión
        db.query.return_value = "result"
        result = db.query()
        assert result == "result"
        
        # Cerrar (simular fin de request)
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()
