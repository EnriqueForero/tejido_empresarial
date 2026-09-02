"""La lectura de resultados no puede depender de una dependencia opcional.

En el despliegue de Railway la imagen se construyó sin `pyarrow`, así que
`Session.sql(...).to_pandas()` fallaba y todas las consultas que devuelven tabla
respondían 502 aunque la conexión con Snowflake estuviera bien. Estas pruebas
fijan el comportamiento en los dos escenarios.
"""
from decimal import Decimal

import pandas as pd
import pytest

from backend import database


class _Fila:
    """Imita snowflake.snowpark.Row en lo que usa el aplicativo."""

    def __init__(self, datos: dict):
        self._datos = datos

    def as_dict(self) -> dict:
        return dict(self._datos)


class _Campo:
    def __init__(self, nombre: str):
        self.name = nombre


class _Esquema:
    def __init__(self, nombres: list[str]):
        self.fields = [_Campo(nombre) for nombre in nombres]


class _Consulta:
    """Resultado de Snowpark; `to_pandas` falla como sin pyarrow."""

    def __init__(self, filas: list[dict], columnas: list[str], arrow: bool):
        self._filas = filas
        self._columnas = columnas
        self._arrow = arrow

    def to_pandas(self) -> pd.DataFrame:
        if not self._arrow:
            raise RuntimeError("Optional dependency: 'pandas' is not installed")
        # Arrow entrega los NUMBER de Snowflake ya convertidos a float/int.
        convertidas = [
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in fila.items()}
            for fila in self._filas
        ]
        return pd.DataFrame(convertidas, columns=self._columnas)

    def collect(self) -> list[_Fila]:
        return [_Fila(fila) for fila in self._filas]

    @property
    def schema(self) -> _Esquema:
        return _Esquema(self._columnas)


FILAS = [
    {"NIT": "900123456", "Razón social": "EMPRESA UNO S.A.S.", "Ingresos": Decimal("1500000.50")},
    {"NIT": "800987654", "Razón social": "EMPRESA DOS LTDA", "Ingresos": Decimal("980000")},
]
COLUMNAS = ["NIT", "Razón social", "Ingresos"]


@pytest.mark.parametrize("arrow", [True, False], ids=["con-pyarrow", "sin-pyarrow"])
def test_las_consultas_devuelven_tabla_con_y_sin_pyarrow(monkeypatch, arrow: bool) -> None:
    monkeypatch.setattr(database, "PANDAS_ARROW", arrow)
    servicio = database.SnowflakeService()
    marco = servicio._a_pandas(_Consulta(FILAS, COLUMNAS, arrow))

    assert list(marco.columns) == COLUMNAS
    assert len(marco) == 2
    assert marco.loc[0, "Razón social"] == "EMPRESA UNO S.A.S."
    # Los importes deben quedar numéricos: el Excel les aplica formato de moneda.
    assert pd.api.types.is_numeric_dtype(marco["Ingresos"])
    assert float(marco.loc[0, "Ingresos"]) == pytest.approx(1500000.50)


def test_sin_pyarrow_un_resultado_vacio_conserva_las_columnas(monkeypatch) -> None:
    monkeypatch.setattr(database, "PANDAS_ARROW", False)
    servicio = database.SnowflakeService()
    marco = servicio._a_pandas(_Consulta([], COLUMNAS, arrow=False))
    assert list(marco.columns) == COLUMNAS
    assert marco.empty


def test_un_fallo_de_consulta_queda_registrado_para_el_mensaje_al_usuario(monkeypatch) -> None:
    """La causa real debe quedar guardada, redactada, tras agotar el reintento."""
    servicio = database.SnowflakeService()
    monkeypatch.setattr(servicio, "_reset_session", lambda: None)

    class _Sesion:
        def sql(self, _consulta):
            raise RuntimeError("SQL compilation error: Object 'X' does not exist")

    monkeypatch.setattr(servicio, "session", lambda *args, **kwargs: _Sesion())
    with pytest.raises(RuntimeError):
        servicio.dataframe("SELECT 1")
    assert "does not exist" in (servicio.ultimo_error_consulta or "")


def test_una_consulta_correcta_borra_el_error_anterior(monkeypatch) -> None:
    monkeypatch.setattr(database, "PANDAS_ARROW", True)
    servicio = database.SnowflakeService()
    servicio.ultimo_error_consulta = "fallo anterior"

    class _Sesion:
        def sql(self, _consulta):
            return _Consulta(FILAS, COLUMNAS, arrow=True)

    monkeypatch.setattr(servicio, "session", lambda *args, **kwargs: _Sesion())
    assert len(servicio.dataframe("SELECT 1")) == 2
    assert servicio.ultimo_error_consulta is None
