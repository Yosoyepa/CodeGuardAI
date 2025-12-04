"""Combined test file with security AND style violations."""

import hashlib
import json  # STYLE020_UNUSED_IMPORT: never used
import os  # STYLE021_DUP_IMPORT: duplicate
import pickle

PASSWORD = "MySuperSecretPassword123"  # SEC003_PASSWORD: hardcoded
api_key = "sk_live_abcdefghij1234567890"  # SEC003_API_KEY + STYLE033: camelCase var


def badlyNamedFunction(userInput):  # STYLE030_FUNC_NAMING: not snake_case, no docstring
    result = eval(userInput)  # SEC001_EVAL: arbitrary code execution
    exec(userInput)  # SEC001_EXEC: arbitrary code execution
    return result


class lowercase_class:  # STYLE031_CLASS_NAMING: not PascalCase, no docstring
    def CamelCaseMethod(self, data):  # STYLE030: method not snake_case, no docstring
        return pickle.loads(data)  # SEC001_PICKLE: unsafe deserialization


def sql_query(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id  # SEC002_SQL_INJECTION
    cursor.execute(f"DELETE FROM logs WHERE user = {user_id}")  # SEC002_SQL_INJECTION
    return query


def weak_hash(data):
    md5_hash = hashlib.md5(data.encode()).hexdigest()  # SEC004_MD5: weak crypto
    sha1_hash = hashlib.sha1(data.encode()).hexdigest()  # SEC004_SHA1: weak crypto
    return md5_hash, sha1_hash


def line_too_long():
    very_long_variable_name_that_exceeds_the_pep8_limit = "This is a string that combined with the variable name makes this line exceed 88 characters"  # STYLE001
    return very_long_variable_name_that_exceeds_the_pep8_limit


def trailing_ws():
    x = 1
    y = 2
    unusedVar = x + y  # STYLE033: camelCase + F841: unused
    return x
