# Importación de las bibliotecas necesarias para la aplicación
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc  # Importa Dash Bootstrap Components
from dash import Dash, html, Output, Input, State, no_update
import dash_leaflet as dl
import rasterio
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from rasterio.warp import transform_bounds
import os
import re

# Abre el archivo TIFF y extrae información geoespacial
with rasterio.open('./assets/2015/Agencias de cobranza y comunicaciones.tiff') as src:
    bounds = src.bounds  # Obtiene los límites originales del TIFF
    src_crs = src.crs  # Obtiene el Sistema de Referencia de Coordenadas (CRS) original
    # Transforma los límites a EPSG:4326 (WGS84) para usarlos en mapas web
    wgs84_bounds = transform_bounds(src_crs, "EPSG:4326", 
                                    bounds.left, bounds.bottom, 
                                    bounds.right, bounds.top)

# Lista todas las carpetas de actividades en el directorio './assets/activities/'
actividades = [f for f in os.listdir('./assets/activities/') if os.path.isdir(os.path.join('./assets/activities/', f))]

# Lista todos los archivos .png dentro de la carpeta específica de "Agencias de cobranza y comunicaciones"
folder_files = [f for f in os.listdir('./assets/activities/Agencias de cobranza y comunicaciones/') if f.endswith('.png')]

# Elimina la extensión '.png' de los nombres de archivo
anios = [re.sub(r"\.png", "", anio) for anio in folder_files]

# Remueve la parte fija del nombre, dejando sólo el indicador del año o periodo
anios = [re.sub(r"Agencias de cobranza y comunicaciones_", "", anio) for anio in anios]

# Define un diccionario que mapea valores numéricos a periodos o años específicos
diccionario = {
    0: '2015', 2: '2016A', 4: '2016B', 6: '2017A', 8: '2017B', 
    10: '2018A', 12: '2018B', 14: '2019A', 16: '2019B', 18: '2020A', 
    20: '2020B', 22: '2021A', 24: '2021B', 26: '2022A', 28: '2022B', 
    30: '2023B', 32: '2024A', 34: '2024B'
}

foto = "./assets/sigeh3.png"

import geopandas as gpd
map = gpd.read_file("assets/municipiosjair/municipiosjair.shp")

geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    **feature["properties"],
                    #"tooltip": f"Municipio: {feature['properties'].get('NOM_MUN','N/A')} "

                }
            }
            for idx, feature in enumerate(map.__geo_interface__["features"])
        ]
    }

# Imprime los límites transformados en la consola para verificar la conversión
print(wgs84_bounds)

# Instancia la aplicación Dash usando un tema de Bootstrap
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP])

play_pause_icon = html.I(id = "play_pause", className= "")

# Define el layout de la aplicación con dos columnas: una principal (90%) y una secundaria (10%)
app.layout = html.Div([
    # Primer bloque: 10% de alto y 100% de ancho dividido en 3 columnas
    dbc.Row([
        dbc.Col(
            html.H4("Actividades Económicas", style={'textAlign': 'center', 'color': 'white'}),
            style = {
                'display': 'inline-block',
                'backgroundColor': '#9C2448',  # Color de fondo
            },
            width = 3,
            xxl= 3, xl= 3, lg = 3, md = 3, sm=12,  xs = 12   
        ),
        dbc.Col(
            html.H5("Selecciona una actividad: ", style={'textAlign': 'center', 'color': 'black', 'fontSize': 'large'}),
            style = {
                'display': 'inline-block'
            },
            width = 3,
            xxl= 3, xl= 3, lg = 3, md = 3, sm=3, xs = 3   
        ),
        dbc.Col(
            dcc.Dropdown(
                id='actividades-dropdown',
                options=[{'label': act, 'value': act} for act in actividades],
                value='Agencias de cobranza y comunicaciones',
                style={'margin': 'auto', 
                       'display': 'table',  # Mantiene su tamaño original sin encogerse
                       'width': '90%'}
            ),
            style={ 'backgroundColor': '#9C2448', 'display': 'flex', 'verticalAlign': 'middle'},
            width= 6,
            xxl= 6, xl= 6, lg = 6, md = 6, sm = 9, xs = 9   
        )
    ], style={'width': '100%', 'height': 'auto','margin': '0'}
    ),
    
    # Segundo bloque: 10% de alto y 100% de ancho dividido en 3 columnas
    dbc.Row([ 
        dbc.Col( 
    dbc.Button(["Histórico", play_pause_icon], id="start_button", color="primary", n_clicks=0, size="sm", className="custom-button", style={'80%': 'auto','height': '4vh', 'margin': '3vh 10% 3vh 10%'},
               ),
    width=1,
    style={'backgroundColor': 'white', 'padding': '0'},
    xxl= 1, xl= 1, lg = 1, md = 1, xs = 2),
    dbc.Col(
        dcc.Slider(
            id="slider_periodo",
            step=None,
            marks=diccionario,
            value=0,
            className="custom-slider",   # Aplica la clase CSS personalizada  
        ),
        width = 9,
        style={'backgroundColor': 'white', 'padding': '0',},
        xxl= 9, xl= 9, lg = 9, md = 9, xs = 10
    ),
    dbc.Col( 
        html.Div([html.P("Periodo Observado", style = {'marginBottom': '0'}), html.P(id="periodo_observado", style={'fontWeight': 'bold', 'marginBottom': '0'})], style={'backgroundColor': '#BC955B', 'color': 'white','padding': '0', 'width': '100%', 'height': '10vh', 
                                                                                                         'display':'block',
                                                                                                         'textAlign': 'center',
                                                                                                         }),
        width=2,
        style={'backgroundColor': 'white', 'padding': '0'},
        xxl= 2, xl= 2, lg = 2, md = 2, xs = 12
    ) 
    ],style={'width': '100%', 'height': 'auto','margin': '0'}),
    # Tercer bloque: 80% de alto y 100% de ancho para el mapa
html.Div([
    dl.Map([
        dl.TileLayer(),
        dl.FullScreenControl(position="topleft"),  # Pantalla Completa
        dl.ImageOverlay(
            id='GEOTIFF_ID',
            interactive=True,
            url="",
            bounds=[[wgs84_bounds[1], wgs84_bounds[0]], [wgs84_bounds[3], wgs84_bounds[2]]],
            opacity=0.7
        ),
        dl.GeoJSON(data=geojson_data,
                   id='geojson',
                   options={'style': {
                       'color': 'black',
                       'weight': 0.7,
                       'opacity': 0.5,
                       'fillOpacity': 0.0005
                       }
                   }),
    ], center=[(wgs84_bounds[1] + wgs84_bounds[3]) / 2, (wgs84_bounds[0] + wgs84_bounds[2]) / 2], zoom=8,
        style={'width': '100%', 'height': '100%'}),
    
    # Foto fija
    # html.Div(
    #     children=[
    #         html.Img(
    #             src="./assets/logo_lab.png",  
    #             style={
    #                 "width": "10wh",   # Tamaño del ícono
    #                 "height": "10vh",  # Tamaño del ícono
    #             }
    #         )
    #     ],
    #     style={ # Estilos CSS aplicados al Div
    #         "position": "absolute", # El elemento no ocupa espacio en el diseño habitual. Esto significa que otros elementos actúan como si el elemento "absoluto" no existiera.
    #         "bottom": "2vh",   # Posicionamiento desde el borde inferior
    #         "left": "15wh",     # Posicionamiento desde el borde izquierdo
    #         "z-index": "1000"   # Asegura que esté sobre otros elementos
    #     }
    # )
], style={'width': '100%', 'height': '100%'}),
    
    # Componente Interval (se mantiene fuera de los bloques anteriores)
    dcc.Interval(
        id="intervalo",
        interval=500,  # 100 ms
        n_intervals=0,
        disabled=True
    )
], style={'display': 'flex', 'flexDirection': 'column', 'width': '100vw', 'height': '100vh'})


# Callback para actualizar la imagen, el slider y el texto del periodo
@app.callback(
    [Output("GEOTIFF_ID", "url"),                       # Actualizar la URL de la imagen geoespacial
     Output("slider_periodo", "value"),                 # Actualizar el valor del slider
     Output("periodo_observado", "children")],          # Actualizar el texto del periodo observado
    [Input("actividades-dropdown", "value"),            # Input para la actividad seleccionada
     Input("intervalo", "n_intervals"),                 # Input para el intervalo de tiempo
     Input("slider_periodo", "value")]                  # Input para el valor del slider
)

# Se accede a dash.callback_context para identificar qué entrada fue la que disparó el callback. Esto es importante para determinar cómo se debe actualizar el valor del período.
# En la primera carga, cuando ninguna acción del usuario ha activado la función, el valor de triggered_id es None. Verificamos esto y lo usamos para mostrar el mensaje: "Aún no has hecho clic en ningún botón".
# Nota: triggered_id está disponible en Dash 2.4 y versiones posteriores. En versiones anteriores de Dash, puedes obtener el id activado con: dash.callback_context.triggered[0]['prop_id'].split('.')[0]

# Actividad: Nombre de la actividad seleccionada, n_intervals: Número de intervalos, slider_val: Valor del slider
def update_image_and_slider(actividad, n_intervals, slider_val):
    print("Se activa callback por:")
    # Determinar qué input disparó el callback
    ctx = dash.callback_context
    print(ctx.triggered)
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Si el usuario movió el slider, se respeta su valor
    if trigger_id == "slider_periodo":
        periodo_actual = slider_val
        nuevo_valor_del_deslizador = slider_val
    else:
        # Si el intervalo es el disparador, es decir, del dcc Interval se actualiza solo cada 5 intervalos
        if n_intervals % 2 == 0:
            print("n_intervals es congruente modulo 5")
            periodo_actual = n_intervals
            nuevo_valor_del_deslizador = n_intervals
        else:
            print("No se actualiza el slider")
            raise dash.exceptions.PreventUpdate     # se lanza una excepción (PreventUpdate) que evita que se realice cualquier actualización. Esto hace que el callback solo procese los intervalos en los que efectivamente se desea actualizar la vista.
    
    # Evitamos que el valor se salga de las claves definidas en el diccionario
    # Duda con recorsividad
    if periodo_actual not in diccionario:
        # Si el contador excede el último valor, reiniciamos a 0
        periodo_actual = 0
        nuevo_valor_del_deslizador = 0

    # Actualizar el texto del periodo observado
    periodo_texto = diccionario.get(periodo_actual, 'Desconocido')
    
    # Construir la URL de la imagen geoespacial
    url_imagen = f"./assets/activities/{actividad}/{actividad}_{diccionario.get(periodo_actual, 'Desconocido')}.png"
    return url_imagen, nuevo_valor_del_deslizador, periodo_texto

# Callback para reiniciar el contador cuando se cambia la actividad seleccionada
@app.callback(
    Output("intervalo", "n_intervals", allow_duplicate=True),
    [Input("actividades-dropdown", "value")],
    prevent_initial_call=True
)
def update_interval(actividad):
    return 0  # Reinicia el contador a 0

# Callback para reiniciar el contador cuando alcanza un valor específico (por ejemplo, 94)
@app.callback(
    Output("intervalo", "n_intervals"),
    [Input("intervalo", "n_intervals")]
)
def recursividad(n):
    if n >= 35:
        return 0  # Reinicia el contador si llega a 94
    else:
        return no_update
@app.callback(
    Output("intervalo", "n_intervals"),
    [Input("slider_periodo", "value"),State("intervalo", "disabled")],
    prevent_initial_call=True
)
def conservarPosicion(value_slider, disabled):
    print(value_slider)
    if(disabled):
        return value_slider
    else:
        return no_update
# Callback para activar/detener el Interval usando el botón (toggle)
@app.callback(
    [Output("intervalo", "disabled"),
    Output("play_pause", "className")],
    [Input("start_button", "n_clicks")],
    State("intervalo", "disabled")
)
def toggle_interval(n_clicks, disabled):
    # Si no se ha hecho clic, se mantiene deshabilitado
    if not n_clicks:
        return True, "bi bi-play-fill"

    # Si el número de clics es impar, activamos el Interval (disabled=False)
    if n_clicks % 2 == 1:
        return False, "bi bi-pause-fill"
    # Si es par, deshabilitamos el Interval (disabled=True)
    return True, "bi bi-play-fill"

# Inicia el servidor de la aplicación si el script se ejecuta directamente
if __name__ == '__main__':
    app.run()