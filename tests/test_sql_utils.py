import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.sql_utils import generar_insert


def test_fecha_datetime():
    fila = {"fecha": datetime.datetime(2025, 4, 29, 0, 15, 31)}
    sql = generar_insert("mi_tabla", fila)
    assert "TO_DATE('29-04-2025 00:15:31', 'DD-MM-YYYY HH24:MI:SS')" in sql


def test_none_value():
    fila = {"valor": None}
    sql = generar_insert("mi_tabla", fila)
    assert "NULL" in sql


def test_numeric_values():
    fila = {"id": 123, "monto": 45.67}
    sql = generar_insert("mi_tabla", fila)
    assert "123" in sql and "45.67" in sql


def test_text_with_quotes():
    fila = {"nombre": "O'Hara"}
    sql = generar_insert("mi_tabla", fila)
    assert "'O''Hara'" in sql


def test_multiline_text():
    fila = {"xml": "<Request>\n<accion>Test</accion>\n</Request>"}
    sql = generar_insert("mi_tabla", fila)
    assert "\n" not in sql
    assert "<Request>" in sql and "</Request>" in sql


def test_string_date():
    fila = {"fecha": "2025-04-29 10:27:18"}
    sql = generar_insert("mi_tabla", fila)
    assert "TO_DATE('29-04-2025 10:27:18', 'DD-MM-YYYY HH24:MI:SS')" in sql
