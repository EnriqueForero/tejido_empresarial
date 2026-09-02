# Librerías
import streamlit as st
from streamlit.errors import StreamlitAPIException

class DynamicFilters:
    """
    Clase para crear filtros dinámicos de selección múltiple en Streamlit.

    ...

    Atributos
    ---------
    df : DataFrame
        El DataFrame sobre el que se aplican los filtros.
    filters : dict
        Diccionario con los nombres de filtros como claves y sus valores seleccionados.
    display_names : dict
        Diccionario que mapea el nombre de cada filtro a un nombre a mostrar en el multiselect.
        Se utilizará para mostrar el nombre en negrilla.

    Métodos
    --------
    check_state():
        Inicializa el estado de la sesión con los filtros si aún no están definidos.
    filter_df(except_filter=None):
        Retorna el DataFrame filtrado basado en el estado de la sesión, excluyendo el filtro especificado.
    display_filters(...):
        Muestra los filtros dinámicos para que el usuario realice sus selecciones.
    display_df(...):
        Muestra el DataFrame filtrado en Streamlit.
    """

    def __init__(self, df, filters, filters_name="filters", display_names=None):
        """
        Construye todos los atributos necesarios para el objeto DynamicFilters.

        Parámetros
        ----------
        df : DataFrame
            El DataFrame sobre el que se aplican los filtros.
        filters : list
            Lista de nombres de columnas en df para los cuales se crearán filtros.
        filters_name : str, opcional
            Nombre del objeto de filtros en el estado de la sesión.
        display_names : dict, opcional
            Diccionario que mapea el nombre del filtro (llave) a un nombre a mostrar.
            Este nombre se mostrará en negrilla en el multiselect.
        """
        self.df = df
        self.filters_name = filters_name
        self.filters = {filter_name: [] for filter_name in filters}
        # Si no se proporciona el diccionario, se utiliza un diccionario vacío.
        self.display_names = display_names if display_names is not None else {}
        self.check_state()

    def check_state(self):
        """
        Inicializa el estado de la sesión con los filtros si aún no están definidos.
        """
        if self.filters_name not in st.session_state:
            st.session_state[self.filters_name] = self.filters

    def reset_filters(self):
        """
        Reinicia/elimina los filtros actuales y limpia los widgets asociados.

        Puede ser llamado usando un botón, por ejemplo:

            st.button("Reset Filters", on_click=dynamic_filters.reset_filters)
        """
        # 1. Reinicializar el diccionario de filtros con listas vacías
        st.session_state[self.filters_name] = {filter_name: [] for filter_name in self.filters.keys()}
        
        # 2. Eliminar las keys de los widgets multiselect
        # Las keys son: filters_name + filter_name (ej: "generalesDEPARTAMENTO")
        for filter_name in self.filters.keys():
            widget_key = self.filters_name + filter_name
            st.session_state.pop(widget_key, None)

    def filter_df(self, except_filter=None):
        """
        Filtra el DataFrame basado en los valores del estado de la sesión,
        exceptuando el filtro especificado.

        Parámetros
        ----------
        except_filter : str, opcional
            El nombre del filtro que debe ser excluido de la operación de filtrado actual.

        Retorna
        -------
        DataFrame
            El DataFrame filtrado.
        """
        filtered_df = self.df
        for key, values in st.session_state[self.filters_name].items():
            if key != except_filter and values:
                filtered_df = filtered_df[filtered_df[key].isin(values)]
        return filtered_df
    
    def display_filters(self, location=None, num_columns=0, gap="small"):
        """
        Muestra filtros dinámicos de selección múltiple para que el usuario realice sus selecciones.

        Parámetros:
        -----------
        location : str, opcional
            El lugar donde se mostrarán los filtros. Los valores aceptados son:
            - 'sidebar': Muestra los filtros en el panel lateral de la aplicación.
            - 'columns': Muestra los filtros en formato de columnas en el área principal de la aplicación.
            - None: Se muestra en el área principal de la aplicación sin columnas.
            Por defecto es None.

        num_columns : int, opcional
            El número de columnas en las que se mostrarán los filtros cuando location esté establecido en 'columns'.
            Restricciones:
            - Debe ser un entero.
            - Debe ser menor o igual a 8.
            - Debe ser menor o igual al número de filtros + 1.
            Si location es 'columns', este valor debe ser mayor que 0.
            Por defecto es 0.

        gap : str, opcional
            Especifica el espacio entre columnas cuando location esté establecido en 'columns'. Los valores aceptados son:
            - 'small': Espacio mínimo entre columnas.
            - 'medium': Espacio moderado entre columnas.
            - 'large': Espacio máximo entre columnas.
            Por defecto es 'small'.

        Comportamiento:
        --------------
        - La función itera sobre los filtros almacenados en el estado de la sesión.
        - Para cada filtro, la función:
            1. Genera las opciones disponibles basadas en el conjunto de datos actual.
            2. Muestra una caja de selección múltiple para que el usuario realice sus selecciones.
               El título del multiselect utiliza el nombre del filtro. Si se proporcionó el diccionario
               display_names y existe la llave correspondiente, se mostrará el valor asociado en negrilla.
            3. Actualiza el estado de la sesión con la selección del usuario.
        - Si algún valor de filtro cambia, la aplicación se actualiza para ajustar las demás opciones basándose en la selección actual.
        - Si la selección previa del usuario ya no es válida de acuerdo al conjunto de datos, se elimina.
        - Si se actualiza algún filtro, la aplicación se reinicia para que los cambios surtan efecto.

        Excepciones:
        ------------
        Lanza StreamlitAPIException si los argumentos proporcionados no cumplen con las restricciones requeridas.

        Notas:
        ------
        La función utiliza el estado de la sesión de Streamlit para mantener las selecciones del usuario a lo largo de los reinicios.
        """
        # manejo de errores
        if location not in ["sidebar", "columns", None]:
            raise StreamlitAPIException(
                "location must be either 'sidebar' or 'columns'"
            )
        if not isinstance(num_columns, int):
            raise StreamlitAPIException("num_columns must be an integer")
        if num_columns > 8:
            raise StreamlitAPIException("num_columns must be less than or equal to 8")
        if num_columns > len(st.session_state[self.filters_name]) + 1:
            raise StreamlitAPIException(
                "num_columns must be less than or equal to the number of filters"
            )
        if location == "columns" and num_columns == 0:
            raise StreamlitAPIException(
                "num_columns must be greater than 0 when location is 'columns'"
            )
        if gap not in ["small", "medium", "large"]:
            raise StreamlitAPIException(
                "gap must be either 'small', 'medium' or 'large'"
            )


        # Inicializar contador y valor máximo para columnas
        if location == "columns" and num_columns > 0:
            counter = 1
            max_value = num_columns
            col_list = st.columns(num_columns, gap=gap)

        for filter_name in st.session_state[self.filters_name].keys():
            # AGREGAR ESTAS 3 LÍNEAS:
            if st.session_state.get('_filters_resetting', False):
                st.session_state[self.filters_name][filter_name] = []
                continue
            
            filtered_df = self.filter_df(filter_name)
            options = filtered_df[filter_name].unique()  # Mantener como numpy array
            # Remover valores seleccionados que ya no están disponibles en las opciones
            options_set = set(options)
            valid_selections = [
                v for v in st.session_state[self.filters_name][filter_name] if v in options_set
            ]
            if valid_selections != st.session_state[self.filters_name][filter_name]:
                st.session_state[self.filters_name][filter_name] = valid_selections

            # Determinar el texto a mostrar en el multiselect utilizando el diccionario display_names si está disponible
            if self.display_names and filter_name in self.display_names:
                label = f"**{self.display_names[filter_name]}**"
            else:
                label = f"**{filter_name}**"

            if location == "sidebar":
                with st.sidebar:
                    selected = st.multiselect(
                        label,
                        sorted(options),
                        default=st.session_state[self.filters_name][filter_name],
                        key=self.filters_name + filter_name,
                    )
            elif location == "columns" and num_columns > 0:
                with col_list[counter - 1]:
                    selected = st.multiselect(
                        label,
                        sorted(options),
                        default=st.session_state[self.filters_name][filter_name],
                        key=self.filters_name + filter_name,
                    )
                counter += 1
                counter = counter % (max_value + 1)
                if counter == 0:
                    counter = 1
            else:
                selected = st.multiselect(
                    label,
                    sorted(options),
                    default=st.session_state[self.filters_name][filter_name],
                    key=self.filters_name + filter_name,
                )

            if selected != st.session_state[self.filters_name][filter_name]:
                st.session_state[self.filters_name][filter_name] = selected

    def display_df(self, **kwargs):
        """
        Muestra el DataFrame filtrado en el área principal.

        Parámetros:
        -----------
        **kwargs : dict
            Argumentos adicionales que se pasan a st.dataframe.
        """
        st.dataframe(self.filter_df(), **kwargs)