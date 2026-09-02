# ==============================================================================
# ==================== COLUMNAS DISPONIBLES PARA APLICATIVO ====================
# ==============================================================================

# ==============================================================================
# ============== PASO 1: VERIFICAR PERIODOS DE TIEMPO DISPONIBLES ==============
# ==============================================================================

# Verificar los periodos de tiempo disponibles en la tabla: TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P
# Páginas en las que se usa:
                            # Segmentación
                            # Empresas
# Formato del corrido: ("Enero YYYY", "Enero - Febrero YYYY", "Enero - Marzo YYYY", ...
#                       "Enero - Octubre YYYY", "Enero - Noviembre YYYY", "Enero - Diciembre YYYY")
# Cuando el año esté cerrado, reemplazar el corrido por el año completo: (2021, 2026)
exportaciones_anios_disponibles = (2021, "Enero a Mayo 2026")
servicios_anios_disponibles = (2023, "Enero a Junio 2026")
negocios_anios_disponibles = (2023, "Enero a Junio 2026")
oportunidades_anios_disponibles = (2023, "Enero a Junio 2026")

# Verificar los periodos de tiempo disponibles en las tablas: BIENES_Y_SERVICIOS_P y BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P
# Páginas en las que se usa:
                            # Segmentación (BIENES_Y_SERVICIOS_P)
                            # Destinos (BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P)
                            # Valor Agregado (BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P)
                            # Departamentos (BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P)
exportaciones_bienes_servicios_anios_disponibles = (2021, "Enero a Mayo 2026")

# =================================================================================================
# ============== PASO 2: ACTUALIZAR COLUMNAS DE VALORES SEGÚN INFORMACIÓN DISPONIBLE ==============
# =================================================================================================

#################################################################################
# La tabla TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P la usan las siguientes páginas:
                #   - Segmentación
                #   - Empresas
#################################################################################

# Para facilitar la gestión de cambios futuros, las columnas de valores se centralizan aquí.

# ---- PÁGINA: SEGMENTACIÓN ----
# Formato alias corridos: 'Exportaciones Enero YYYY (FOB USD)'
#                         'Exportaciones Enero - Febrero YYYY (FOB USD)'
#                         'Exportaciones Enero - Marzo YYYY (FOB USD)', ...
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada del corrido anterior por la nueva.
# Ejemplo: reemplazar 'EXPO_ENE_2026': 'Exportaciones Enero 2026 (FOB USD)'
#               por   'EXPO_ENE_FEB_2026': 'Exportaciones Enero - Febrero 2026 (FOB USD)'
# Cuando el año cierre: ELIMINAR la entrada del corrido y agregar el año cerrado.
# Ejemplo: eliminar 'EXPO_ENE_DIC_2026': '...'
#          y agregar 'EXPO_2026': 'Exportaciones 2026 (FOB USD)'
COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES = {
    'EXPO_2021': 'Exportaciones totales de la empresa 2021 (FOB USD)',
    'EXPO_2022': 'Exportaciones totales de la empresa 2022 (FOB USD)',
    'EXPO_2023': 'Exportaciones totales de la empresa 2023 (FOB USD)',
    'EXPO_2024': 'Exportaciones totales de la empresa 2024 (FOB USD)',
    'EXPO_2025': 'Exportaciones totales de la empresa 2025 (FOB USD)',
    'EXPO_ENE_MAY_2025': 'Exportaciones totales de la empresa Enero - Mayo 2025 (FOB USD)',
    'EXPO_ENE_MAY_2026': 'Exportaciones totales de la empresa Enero - Mayo 2026 (FOB USD)'   # <-- REEMPLAZAR cuando haya nuevo mes
}

# Deben ser iguales a los elementos del AS en el diccionario anterior
COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES_USUARIO = list(COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES.values())

# ---- PÁGINA: SEGMENTACIÓN (columnas ProColombia) ----
# Columnas acumuladas (NEGOCIOS, SERVICIOS, OPORTUNIDADES): se actualizan automáticamente
# con los valores de las tuplas definidas al inicio (negocios_anios_disponibles, etc.).
# Columnas anuales por tipo: Formato clave 'NUMERO_NEGOCIOS_YYYY', alias 'Negocios YYYY'.
# Columnas corridas por tipo: Formato clave 'NUMERO_NEGOCIOS_ENE_FEB_YYYY',
#                             alias 'Negocios Enero - Febrero YYYY'.
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada corrida anterior por la nueva.
# Ejemplo: reemplazar 'NUMERO_NEGOCIOS_ENE_FEB_2026': 'Negocios Enero - Febrero 2026'
#               por   'NUMERO_NEGOCIOS_ENE_MAR_2026': 'Negocios Enero - Marzo 2026'
# Aplicar el mismo reemplazo para SERVICIOS y OPORTUNIDADES.
# Cuando el año cierre: ELIMINAR la entrada corrida y agregar el año cerrado.
# Ejemplo: eliminar 'NUMERO_NEGOCIOS_ENE_DIC_2026': '...'
#          y agregar 'NUMERO_NEGOCIOS_2026': 'Negocios 2026'
COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_PC = {
    'ATENDIDA_PC' : f'Empresa atendida por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
    'SERVICIOS': f'Servicios prestados por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
    'OPORTUNIDADES': f'Oportunidades {oportunidades_anios_disponibles[0]} - {oportunidades_anios_disponibles[1]}',
    'NEGOCIOS': f'Negocios facilitados por ProColombia {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}',
    'NUMERO_NEGOCIOS_2023': 'Negocios 2023',
    'NUMERO_NEGOCIOS_2024': 'Negocios 2024',
    'NUMERO_NEGOCIOS_2025': 'Negocios 2025',
    'NUMERO_NEGOCIOS_ENE_JUN_2026' : 'Negocios Enero - Junio 2026',   # <-- REEMPLAZAR cuando haya nuevo mes
    'NUMERO_SERVICIOS_2023': 'Servicios 2023',
    'NUMERO_SERVICIOS_2024': 'Servicios 2024',
    'NUMERO_SERVICIOS_2025': 'Servicios 2025',
    'NUMERO_SERVICIOS_ENE_JUN_2026' : 'Servicios Enero - Junio 2026',  # <-- REEMPLAZAR cuando haya nuevo mes
    'NUMERO_OPORTUNIDADES_2023': 'Oportunidades 2023',
    'NUMERO_OPORTUNIDADES_2024': 'Oportunidades 2024',
    'NUMERO_OPORTUNIDADES_2025': 'Oportunidades 2025',
    'NUMERO_OPORTUNIDADES_ENE_JUN_2026' : 'Oportunidades Enero - Junio 2026'  # <-- REEMPLAZAR cuando haya nuevo mes

}

# ---- PÁGINA: EMPRESAS ----
# Formato alias corridos: 'Valor FOB USD Enero YYYY'
#                         'Valor FOB USD Enero - Febrero YYYY'
#                         'Valor FOB USD Enero - Marzo YYYY', ...
# CRÍTICO: el alias debe comenzar exactamente con 'Valor FOB USD ' (con espacio al final)
# para que las funciones de empresas_utils.py lo detecten correctamente.
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada del corrido anterior por la nueva.
# Ejemplo: reemplazar 'EXPO_ENE_2026': 'Valor FOB USD Enero 2026'
#               por   'EXPO_ENE_FEB_2026': 'Valor FOB USD Enero - Febrero 2026'
# Cuando el año cierre: ELIMINAR la entrada del corrido y agregar el año cerrado.
# Ejemplo: eliminar 'EXPO_ENE_DIC_2026': '...'
#          y agregar 'EXPO_2026': 'Valor FOB USD 2026'
# Recordar hacer el mismo cambio en COLS_VARIABLES_USUARIO_... justo abajo.
COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS = {
    'EXPO_2021': 'Valor FOB USD 2021',
    'EXPO_2022': 'Valor FOB USD 2022',
    'EXPO_2023': 'Valor FOB USD 2023',
    'EXPO_2024': 'Valor FOB USD 2024',
    'EXPO_2025': 'Valor FOB USD 2025',
    'EXPO_ENE_MAY_2025': 'Valor FOB USD Enero - Mayo 2025',
    'EXPO_ENE_MAY_2026': 'Valor FOB USD Enero - Mayo 2026',            # <-- REEMPLAZAR cuando haya nuevo mes
    'NEGOCIOS': f'Negocios facilitados por ProColombia {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}',
    'SERVICIOS': f'Servicios prestados por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
    'OPORTUNIDADES': f'Oportunidades {oportunidades_anios_disponibles[0]} - {oportunidades_anios_disponibles[1]}'
}

# Deben ser iguales a los elementos del AS en el diccionario anterior
# Actualizar en paralelo con COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS
COLS_VARIABLES_USUARIO_COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS = [
    'Valor FOB USD 2021',
    'Valor FOB USD 2022',
    'Valor FOB USD 2023',
    'Valor FOB USD 2024',
    'Valor FOB USD 2025',
    'Valor FOB USD Enero - Mayo 2025',
    'Valor FOB USD Enero - Mayo 2026',                             # <-- REEMPLAZAR cuando haya nuevo mes
    f'Negocios facilitados por ProColombia {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}',
    f'Servicios prestados por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
    f'Oportunidades {oportunidades_anios_disponibles[0]} - {oportunidades_anios_disponibles[1]}']

####################################################################################
# La tabla BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P la usan las siguientes páginas:
                #   - Destinos
                #   - Valor Agregado
#####################################################################################

# Para facilitar la gestión de cambios futuros, las columnas de valores se centralizan aquí.

# ---- PÁGINAS: DESTINOS y VALOR AGREGADO ----
# Formato alias corridos: 'Valor FOB USD Enero YYYY'
#                         'Valor FOB USD Enero - Febrero YYYY'
#                         'Valor FOB USD Enero - Marzo YYYY', ...
# CRÍTICO: el alias debe comenzar exactamente con 'Valor FOB USD ' (con espacio al final)
# para que las funciones de destinos_utils.py lo detecten correctamente.
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada del corrido anterior por la nueva.
# Ejemplo: reemplazar 'VALOR_FOB_USD_ENE_2026_BIENES': 'Valor FOB USD Enero 2026'
#               por   'VALOR_FOB_USD_ENE_FEB_2026_BIENES': 'Valor FOB USD Enero - Febrero 2026'
# Cuando el año cierre: ELIMINAR la entrada del corrido y agregar el año cerrado.
# Ejemplo: eliminar 'VALOR_FOB_USD_ENE_DIC_2026_BIENES': '...'
#          y agregar 'VALOR_FOB_USD_2026_BIENES': 'Valor FOB USD 2026'
# Recordar hacer el mismo cambio en COLS_VARIABLES_USUARIOS_... justo abajo,
# y en periodos_corridos en el PASO 3.
COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA = {
    'VALOR_FOB_USD_2021_BIENES': 'Valor FOB USD 2021',
    'VALOR_FOB_USD_2022_BIENES': 'Valor FOB USD 2022',
    'VALOR_FOB_USD_2023_BIENES': 'Valor FOB USD 2023',
    'VALOR_FOB_USD_2024_BIENES': 'Valor FOB USD 2024',
    'VALOR_FOB_USD_2025_BIENES': 'Valor FOB USD 2025',
    'VALOR_FOB_USD_ENE_MAY_2025_BIENES' : 'Valor FOB USD Enero - Mayo 2025',
    'VALOR_FOB_USD_ENE_MAY_2026_BIENES' : 'Valor FOB USD Enero - Mayo 2026'  # <-- REEMPLAZAR cuando haya nuevo mes
}

# Deben ser iguales a los elementos del AS en el diccionario anterior
# Actualizar en paralelo con COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA
COLS_VARIABLES_USUARIOS_COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA = [
    'Valor FOB USD 2021',
    'Valor FOB USD 2022',
    'Valor FOB USD 2023',
    'Valor FOB USD 2024',
    'Valor FOB USD 2025',
    'Valor FOB USD Enero - Mayo 2025',
    'Valor FOB USD Enero - Mayo 2026'                              # <-- REEMPLAZAR cuando haya nuevo mes
]

# La tabla DEPARTAMENTOS_SERVICIOS la usan las siguientes páginas:
                #   - Territorios - Sección Servicios por departamento ofrecido por ProColombia
                #   - No necesita parámetros adicionales.

# La tabla DEPARTAMENTOS_EXPORTACIONES la usan las siguientes páginas:
                #   - Territorios - Sección Exportaciones por departamento de origen

# ---- PÁGINA: TERRITORIOS - Exportaciones por departamento ----
# Formato clave:  'VALOR_FOB_USD_YYYY_BIENES'        → alias 'VALOR_FOB_USD_YYYY'
# Formato corrido: 'VALOR_FOB_USD_ENE_YYYY_BIENES'   → alias 'VALOR_FOB_USD_ENE_YYYY'
#                  'VALOR_FOB_USD_ENE_FEB_YYYY_BIENES'→ alias 'VALOR_FOB_USD_ENE_FEB_YYYY'
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada corrida anterior por la nueva.
# Ejemplo: reemplazar 'VALOR_FOB_USD_ENE_2026_BIENES': 'VALOR_FOB_USD_ENE_2026'
#               por   'VALOR_FOB_USD_ENE_FEB_2026_BIENES': 'VALOR_FOB_USD_ENE_FEB_2026'
# Cuando el año cierre: ELIMINAR la entrada corrida y agregar el año cerrado.
COLS_VARIABLES_DEPARTAMENTOS_EXPORTACIONES = {
    'VALOR_FOB_USD_2021_BIENES':'VALOR_FOB_USD_2021',
    'VALOR_FOB_USD_2022_BIENES':'VALOR_FOB_USD_2022',
    'VALOR_FOB_USD_2023_BIENES':'VALOR_FOB_USD_2023',
    'VALOR_FOB_USD_2024_BIENES':'VALOR_FOB_USD_2024',
    'VALOR_FOB_USD_2025_BIENES':'VALOR_FOB_USD_2025',
    'VALOR_FOB_USD_ENE_MAY_2025_BIENES' : 'VALOR_FOB_USD_ENE_MAY_2025',
    'VALOR_FOB_USD_ENE_MAY_2026_BIENES' : 'VALOR_FOB_USD_ENE_MAY_2026'  # <-- REEMPLAZAR cuando haya nuevo mes
}

# ---- Período de filtro para mapa "Tamaño de empresas por departamento" (Territorios) ----
# Usar siempre el último CORRIDO disponible para mostrar el año en curso.
# CRÍTICO: debe coincidir exactamente con uno de los alias (valores) del diccionario anterior.
# Cuando llegue un nuevo mes: REEMPLAZAR por el alias del nuevo corrido.
# Ejemplo: reemplazar 'VALOR_FOB_USD_ENE_2026'
#               por   'VALOR_FOB_USD_ENE_FEB_2026'
# Cuando el año cierre: REEMPLAZAR por el alias del año cerrado.
# Ejemplo: reemplazar 'VALOR_FOB_USD_ENE_DIC_2026' por 'VALOR_FOB_USD_2026'
col_conteo_tamanos_departamentos = 'VALOR_FOB_USD_ENE_MAY_2026'  # <-- REEMPLAZAR cuando haya nuevo mes

# ---- Período de filtro para mapa "Tamaño de empresas por municipio" (Territorios) ----
# Misma lógica que col_conteo_tamanos_departamentos (ver arriba).
# CRÍTICO: debe coincidir exactamente con uno de los alias (valores) de
# COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES definido abajo.
# Cuando llegue un nuevo mes: REEMPLAZAR por el alias del nuevo corrido.
# Ejemplo: reemplazar 'VALOR_FOB_USD_ENE_2026'
#               por   'VALOR_FOB_USD_ENE_FEB_2026'
# Cuando el año cierre: REEMPLAZAR por el alias del año cerrado.
col_conteo_tamanos_municipios = 'VALOR_FOB_USD_ENE_MAY_2026'  # <-- REEMPLAZAR cuando haya nuevo mes

# La tabla MUNICIPIOS_EXPORTACIONES la usan las siguientes páginas:
                #   - Territorios - Sección Exportaciones por municipio

# ---- PÁGINA: TERRITORIOS - Exportaciones por municipio (mapa de sectores) ----
# Formato: 'FOB USD YYYY' para años cerrados, 'FOB USD Enero YYYY' para corridos.
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada corrida anterior por la nueva.
# Ejemplo: reemplazar 'FOB USD Enero 2026'
#               por   'FOB USD Enero - Febrero 2026'
# Recordar hacer el mismo cambio en COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES justo abajo.
ls_columnas_fob_sectores = ['FOB USD 2021', 'FOB USD 2022', 'FOB USD 2023', 'FOB USD 2024', 'FOB USD 2025', 'FOB USD Enero - Mayo 2025', 'FOB USD Enero - Mayo 2026']  # <-- REEMPLAZAR cuando haya nuevo mes

# ---- PÁGINA: TERRITORIOS - Exportaciones por municipio ----
# Formato clave:   'EXPO_YYYY'      → alias 'VALOR_FOB_USD_YYYY'
# Formato corrido: 'EXPO_ENE_YYYY'  → alias 'VALOR_FOB_USD_ENE_YYYY'
#                  'EXPO_ENE_FEB_YYYY' → alias 'VALOR_FOB_USD_ENE_FEB_YYYY'
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada corrida anterior por la nueva.
# Ejemplo: reemplazar 'EXPO_ENE_2026': 'VALOR_FOB_USD_ENE_2026'
#               por   'EXPO_ENE_FEB_2026': 'VALOR_FOB_USD_ENE_FEB_2026'
# Recordar hacer el mismo cambio en ls_columnas_fob_sectores justo arriba.
COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES = {
	'EXPO_2021' : 'VALOR_FOB_USD_2021',
	'EXPO_2022' : 'VALOR_FOB_USD_2022',
    'EXPO_2023' : 'VALOR_FOB_USD_2023',
    'EXPO_2024' : 'VALOR_FOB_USD_2024',
    'EXPO_2025' : 'VALOR_FOB_USD_2025',
    'EXPO_ENE_MAY_2025' : 'VALOR_FOB_USD_ENE_MAY_2025',
    'EXPO_ENE_MAY_2026' : 'VALOR_FOB_USD_ENE_MAY_2026',  # <-- REEMPLAZAR cuando haya nuevo mes
}

# =================================================================================================
# ==================== PASO 3: DEFINIR EL PERIODO DE TIEMPO PARA LOS GRÁFICOS =====================
# =================================================================================================

# Páginas en las que se usa:
                            # Destinos
                            # Valor Agregado
                            # Departamentos
# Tabla que define el periodo de tiempo de las siguientes tuplas: BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P

# periodos_cerrados: años completos. Formato: 'USD YYYY'. No cambia salvo que se agregue un año nuevo.
# Ejemplo al cerrar 2026: agregar 'USD 2026' al final de la lista.
periodos_cerrados = ['USD 2021', 'USD 2022', 'USD 2023', 'USD 2024', 'USD 2025']

# periodos_corridos: periodos acumulados del año en curso. Formato: 'USD Enero YYYY', 'USD Enero - Febrero YYYY', ...
# CRÍTICO: estos valores deben coincidir exactamente con los alias de
# COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA después de
# quitarles el prefijo 'Valor FOB ' (es decir, 'Valor FOB USD Enero 2026' → 'USD Enero 2026').
# Cuando llegue un nuevo mes: REEMPLAZAR los valores anteriores.
# Ejemplo: reemplazar ['USD Enero 2025', 'USD Enero 2026']
#               por   ['USD Enero - Febrero 2025', 'USD Enero - Febrero 2026']
periodos_corridos = ['USD Enero - Mayo 2025', 'USD Enero - Mayo 2026']   # <-- REEMPLAZAR cuando haya nuevo mes
# disponibilidad_periodos_corridos_usd: 'Si' cuando hay datos corridos cargados, 'No' si no.
disponibilidad_periodos_corridos_usd = 'Si'

# ==================== PERIODOS PARA CONTEO (VALOR AGREGADO) ===================
# Páginas en las que se usa:
                            # Valor Agregado
# Tabla que define el periodo de tiempo de las siguientes tuplas: BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P
# Formato: igual que periodos_cerrados y periodos_corridos (ver arriba).
# periodos_cerrados_conteo: años completos disponibles para el conteo de Valor Agregado.
# Ejemplo al cerrar 2026: agregar 'USD 2026' al final de la lista.
periodos_cerrados_conteo = ['USD 2025']
# periodos_corridos_conteo: período acumulado del año en curso para Valor Agregado.
# CRÍTICO: el valor debe coincidir con el alias de
# COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA después de
# quitarle el prefijo 'Valor FOB ' (ej. 'Valor FOB USD Enero 2026' → 'USD Enero 2026').
# Cuando llegue un nuevo mes: REEMPLAZAR el valor anterior por el nuevo.
# Ejemplo: reemplazar ['USD Enero 2026']
#               por   ['USD Enero - Febrero 2026']
periodos_corridos_conteo = ['USD Enero - Mayo 2026']   # <-- REEMPLAZAR cuando haya nuevo mes
# disponibilidad_periodos_corridos_conteo: 'Si' cuando hay datos corridos cargados, 'No' si no.
disponibilidad_periodos_corridos_conteo = 'Si'

# ==================== PERIODOS PARA CREAR TABLAS DE SECTORES EN MAPAS DEPARTAMENTOS ===================
# Tabla que define el periodo de tiempo de la siguiente tupla: DEPARTAMENTOS_EXPORTACIONES
# Formato años cerrados: 'FOB USD YYYY'
# Formato corridos:      'FOB USD Enero YYYY', 'FOB USD Enero - Febrero YYYY', ...
# Cuando llegue un nuevo mes: REEMPLAZAR las dos entradas corridas por las nuevas.
# Ejemplo: reemplazar 'FOB USD Enero 2025' y 'FOB USD Enero 2026'
#               por   'FOB USD Enero - Febrero 2025' y 'FOB USD Enero - Febrero 2026'
# Cuando el año cierre: ELIMINAR las entradas corridas y agregar el año cerrado.
# Ejemplo: eliminar 'FOB USD Enero - Diciembre 2026' y agregar 'FOB USD 2026'.
periodos_mapa_sector_departamentos = ['FOB USD 2023', 'FOB USD 2024', 'FOB USD 2025', 'FOB USD Enero - Mayo 2025', 'FOB USD Enero - Mayo 2026']  # <-- REEMPLAZAR corridos cuando haya nuevo mes
