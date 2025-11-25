"""Archivo de prueba con vulnerabilidades."""

import os
import pickle


def unsafe_eval(user_input):
    """Uso peligroso de eval."""
    return eval(user_input)


def unsafe_query(user_id):
    """SQL injection vulnerability."""
    query = "SELECT * FROM users WHERE id = " + user_id
    return query


PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"
