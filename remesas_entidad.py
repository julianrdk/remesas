"""

Fuente:
https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=1&accion=consultarCuadro&idCuadro=CE100&locale=es

"""

import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from plotly.subplots import make_subplots


# Definimos los colores que usaremos para el mapa y tablas.
PLOT_COLOR = "#18122B"
PAPER_COLOR = "#393053"
HEADER_COLOR = "#e65100"

# Mes y año en que se recopilaron los datos.
FECHA_FUENTE = "febrero 2024"

# Periodo de tiempo del análisis.
PERIODO_TIEMPO = "enero-diciembre de 2023"


def plot_mapa(año):
    """
    Esta función crea un mapa y unas tablas con la información de remesas per cápita.

    Parameters
    ----------
    año : int
        El año que nos interesa graficar.

    """

    # Cargamos el dataset de población total por entidad.
    pop = pd.read_csv("./assets/poblacion_anual.csv", index_col=0)

    # Seleccionamos la población del año que nos interesa.
    pop = pop[str(año)]

    # Renombramos algunos estados a sus nombres más comunes.
    pop = pop.rename(
        {
            "Coahuila de Zaragoza": "Coahuila",
            "México": "Estado de México",
            "Michoacán de Ocampo": "Michoacán",
            "Veracruz de Ignacio de la Llave": "Veracruz",
        }
    )

    # Cargamos el dataset de remesas por entidad.
    df = pd.read_csv("./data/remesas_entidad.csv", index_col=0)

    # Seleccionamos las columnas del año que nos interesa.
    cols = [col for col in df.columns if str(año) in col]

    # Filtramos el DataFrama con las columnas que nos interesan.
    df = df[cols]

    # Quitamos los decimales de las cifras.
    df["total"] = df.sum(axis=1) * 1000000

    # Calculamos las remesas per cápita para toda la polación.
    subtitulo = f"Nacional: {df['total'].sum() / pop.sum():,.2f} dólares per cápita"

    # Asignamos la población a cada entidad.
    df["pop"] = df.index.map(pop)

    # Calculamos el valor per cápita.
    df["capita"] = df["total"] / df["pop"]

    # Ordenamos per cápita de mayor a menor.
    df = df.sort_values("capita", ascending=False)

    # Estas listas nos serviran para alimetnar el mapa.
    ubicaciones = list()
    valores = list()

    # Estos valores serán usados para definir la escala en el mapa.
    min_val = df["capita"].min()
    max_val = df["capita"].max()

    marcas = np.linspace(min_val, max_val, 11)
    etiquetas = list()

    for item in marcas:
        etiquetas.append("{:,.0f}".format(item))

    # Cargamos el archivo GeoJSON de México.
    geojson = json.loads(open("./assets/mexico.json", "r", encoding="utf-8").read())

    # Iteramos sobre cada entidad dentro de nuestro archivo GeoJSON de México.
    for item in geojson["features"]:
        geo = item["properties"]["NOMGEO"]

        # Alimentamos las listas creadas anteriormente con la ubicación y su valor per capita.
        ubicaciones.append(geo)
        valores.append(df.loc[geo, "capita"])

    fig = go.Figure()

    # Vamos a crear un mapa Choropleth con todas las variables anteriormente definidas.
    fig.add_traces(
        go.Choropleth(
            geojson=geojson,
            locations=ubicaciones,
            z=valores,
            featureidkey="properties.NOMGEO",
            colorscale="oranges",
            reversescale=True,
            marker_line_color="#FFFFFF",
            marker_line_width=1.0,
            zmin=min_val,
            zmax=max_val,
            colorbar=dict(
                x=0.03,
                y=0.5,
                ypad=50,
                ticks="outside",
                outlinewidth=1.5,
                outlinecolor="#FFFFFF",
                tickvals=marcas,
                ticktext=etiquetas,
                tickwidth=2,
                tickcolor="#FFFFFF",
                ticklen=10,
                tickfont_size=20,
            ),
        )
    )

    # Personalizamos la apariencia del mapa.
    fig.update_geos(
        fitbounds="locations",
        showocean=True,
        oceancolor=PLOT_COLOR,
        showcountries=False,
        framecolor="#FFFFFF",
        framewidth=2,
        showlakes=False,
        coastlinewidth=0,
        landcolor="#1C0A00",
    )

    fig.update_layout(
        legend_x=0.01,
        legend_y=0.07,
        legend_bgcolor="#111111",
        legend_font_size=20,
        legend_bordercolor="#FFFFFF",
        legend_borderwidth=2,
        font_family="Lato",
        font_color="#FFFFFF",
        margin={"r": 40, "t": 50, "l": 40, "b": 30},
        width=1280,
        height=720,
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.5,
                y=1.01,
                xanchor="center",
                yanchor="top",
                text=f"Ingresos por remesas hacia México por entidad durante {PERIODO_TIEMPO}",
                font_size=28,
            ),
            dict(
                x=0.57,
                y=-0.04,
                xanchor="center",
                yanchor="top",
                text=subtitulo,
                font_size=26,
            ),
            dict(
                x=0.0275,
                y=0.45,
                textangle=-90,
                xanchor="center",
                yanchor="middle",
                text="Dólares per cápita",
                font_size=18,
            ),
            dict(
                x=0.01,
                y=-0.04,
                xanchor="left",
                yanchor="top",
                text=f"Fuente: Banxico ({FECHA_FUENTE})",
                font_size=24,
            ),
            dict(
                x=1.01,
                y=-0.04,
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
                font_size=24,
            ),
        ],
    )

    fig.write_image("./0.png")

    # Vamos a crear dos tablas, cada una con la información de 16 entidades.
    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.03,
        specs=[[{"type": "table"}, {"type": "table"}]],
    )

    fig.add_trace(
        go.Table(
            columnwidth=[145, 100, 100],
            header=dict(
                values=[
                    "<b>Entidad</b>",
                    "<b>Total en dólares</b>",
                    "<b>Per cápita ↓</b>",
                ],
                font_color="#FFFFFF",
                fill_color=HEADER_COLOR,
                align="center",
                height=29,
                line_width=0.8,
            ),
            cells=dict(
                values=[
                    df.index[:16],
                    df["total"][:16],
                    df["capita"][:16],
                ],
                fill_color=PLOT_COLOR,
                height=29,
                prefix=["", "$", "$"],
                format=["", ",.0f", ",.2f"],
                line_width=0.8,
                align=["left", "left", "center"],
            ),
        ),
        col=1,
        row=1,
    )

    fig.add_trace(
        go.Table(
            columnwidth=[145, 100, 100],
            header=dict(
                values=[
                    "<b>Entidad</b>",
                    "<b>Total en dólares</b>",
                    "<b>Per cápita ↓</b>",
                ],
                font_color="#FFFFFF",
                fill_color=HEADER_COLOR,
                align="center",
                height=29,
                line_width=0.8,
            ),
            cells=dict(
                values=[
                    df.index[16:],
                    df["total"][16:],
                    df["capita"][16:],
                ],
                fill_color=PLOT_COLOR,
                height=29,
                prefix=["", "$", "$"],
                format=["", ",.0f", ",.2f"],
                line_width=0.8,
                align=["left", "left", "center"],
            ),
        ),
        col=2,
        row=1,
    )

    fig.update_layout(
        showlegend=False,
        legend_borderwidth=1.5,
        xaxis_rangeslider_visible=False,
        width=1280,
        height=560,
        font_family="Lato",
        font_color="#FFFFFF",
        font_size=18,
        title="",
        title_x=0.5,
        title_y=0.95,
        margin_t=20,
        margin_l=40,
        margin_r=40,
        margin_b=0,
        title_font_size=26,
        paper_bgcolor=PAPER_COLOR,
    )

    fig.write_image("./1.png")

    # Unimos el mapa y las tablas en una sola imagen.
    image1 = Image.open("./0.png")
    image2 = Image.open("./1.png")

    result_width = 1280
    result_height = image1.height + image2.height

    result = Image.new("RGB", (result_width, result_height))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(0, image1.height))

    result.save("./mapa_mexico.png")

    # Borramos las imágenes originales.
    os.remove("./0.png")
    os.remove("./1.png")


def plot_tendencias():
    """
    Esta función crea una cuadrícula de sparklines con los
     estados que han crecido más en ingresos por remesas.
    """

    # Cargamos el dataset de remesas por entidad.
    df = pd.read_csv("./data/remesas_entidad.csv", index_col=0)

    # Vamos a sumar los totales de remesas por año.
    # Para esto crearemos un ciclo del 2013 al 2023.
    for year in range(2014, 2024):
        cols = [col for col in df.columns if str(year) in col]
        df[str(year)] = df[cols].sum(axis=1)

    # Solo vamos a escoger las últimas 10 columnas que creamos.
    df = df.iloc[:, -10:]

    primer_año = df.columns[0]
    ultimo_año = df.columns[-1]

    # Vamos a calcular el cambio porcentual entre el primer y último año.
    df["change"] = (df[ultimo_año] - df[primer_año]) / df[primer_año] * 100

    # Quitamos los municipsios con valores infinitos.
    df = df[df["change"] != np.inf]

    # Ordenamos los valores usando el cambio porcentual de mayor a menor.
    df.sort_values("change", ascending=False, inplace=True)

    # Esta lista contendrá los textos de cada anotación.
    texto_anotaciones = list()

    # Fromateamos los subtítulos para cada cuadro en nuestra cuadrícula.
    titles = [f"<b>{item}</b>" for item in df.index.tolist()]

    # Vamos a crear una cuadrícula de 3 columnas por 5 filas (15 cuadros).
    fig = make_subplots(
        rows=5,
        cols=3,
        horizontal_spacing=0.09,
        vertical_spacing=0.07,
        subplot_titles=titles,
    )

    # Esta variable la usaremos para saber de que fila extraer la información.
    index = 0

    # Con ciclos anidados es como creamos la cuadrícula.
    for row in range(5):
        for column in range(3):
            # Seleccionamos la fila correspondiente a la variable index pero omitimos la última columna.
            # la cual contiene el cambio porcentual.
            temp_df = df.iloc[index, :-1]

            # Al íncide (que son los años) lq quitamos los primeros 2 dígitos y le agregamos un apóstrofe.
            # Esto es para reducir el tamaño de la etiqueta de cada año.
            temp_df.index = temp_df.index.map(lambda x: f"'{x[-2:]}")

            # Para nuestra gráfica de línea solo vamos a necesitar que el primer y último registro tengan un punto.
            sizes = [0 for _ in range(len(temp_df))]
            sizes[0] = 20
            sizes[-1] = 20

            # Vamos a extraer algunos valores para calcular el cambio porcentual.
            primer_valor = temp_df.iloc[0]
            ultimo_valor = temp_df.iloc[-1]

            # Solo el primer y último registro llevarán un texto con sus valores.
            textos = ["" for _ in range(len(temp_df))]

            if primer_valor >= 1000:
                textos[0] = f"<b>{primer_valor:,.0f}</b>"
            else:
                textos[0] = f"<b>{primer_valor:,.1f}</b>"

            if ultimo_valor >= 1000:
                textos[-1] = f"<b>{ultimo_valor:,.0f}</b>"
            else:
                textos[-1] = f"<b>{ultimo_valor:,.1f}</b>"

            # Posicionamos los dos textos.
            text_pos = ["middle center" for _ in range(len(temp_df))]
            text_pos[0] = "top center"
            text_pos[-1] = "bottom center"

            # Calculamos el cambio porcentual y creamos el texto que irá en la anotación de cada cuadro.
            change = (ultimo_valor - primer_valor) / primer_valor * 100
            diff = ultimo_valor - primer_valor

            if diff >= 1000:
                texto_anotaciones.append(f"<b>+{diff:,.0f}</b><br>+{change:,.0f}%")
            else:
                texto_anotaciones.append(f"<b>+{diff:,.1f}</b><br>+{change:,.0f}%")

            fig.add_trace(
                go.Scatter(
                    x=temp_df.index,
                    y=temp_df.values,
                    text=textos,
                    mode="markers+lines+text",
                    textposition=text_pos,
                    textfont_size=18,
                    marker_color="#64ffda",
                    marker_opacity=1.0,
                    marker_size=sizes,
                    marker_line_width=0,
                    line_width=4,
                    line_shape="spline",
                    line_smoothing=1.0,
                ),
                row=row + 1,
                col=column + 1,
            )

            # Sumamos 1 a esta variable para que el siguiente cuadro extraíga la siguiente fila.
            index += 1

    fig.update_xaxes(
        tickfont_size=14,
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=1.5,
        showline=True,
        gridwidth=0.35,
        mirror=True,
        nticks=15,
    )

    fig.update_yaxes(
        title_text="Millones de dólares",
        separatethousands=True,
        tickfont_size=14,
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=1.5,
        showline=True,
        showgrid=True,
        gridwidth=0.35,
        mirror=True,
        nticks=8,
    )

    fig.update_layout(
        font_family="Lato",
        showlegend=False,
        width=1280,
        height=1600,
        font_color="#FFFFFF",
        font_size=14,
        margin_t=120,
        margin_l=110,
        margin_r=40,
        margin_b=100,
        title_text=f"Las 15 entidades de México con mayor crecimiento en ingresos por remesas ({primer_año} vs. {ultimo_año})",
        title_x=0.5,
        title_y=0.985,
        title_font_size=26,
        plot_bgcolor="#171010",
        paper_bgcolor="#2B2B2B",
    )

    # Vamos a crear una anotación en cada cuadro con textos mostrando el total y el cambio porcentual.
    # Lo que vamos a hacer a continuación se puede considerar como un 'hack'.
    annotations_x = list()
    annotations_y = list()

    # Iteramos sobre todos los subtítulos de cada cuadro, los cuales son considerados como anotaciones.
    for annotation in fig["layout"]["annotations"]:
        # A cada subtítulo lo vamos a ajustar ligeramente.
        annotation["y"] += 0.005
        annotation["font"]["size"] = 20

        # Vamos a extraer las coordenadas X y Y de cada subtítulo para usarlas de referencia
        # para nuestras nuevas anotaciones.
        annotations_x.append(annotation["x"])
        annotations_y.append(annotation["y"])

    # Es momento de crear nuestras nuevas anotaciones.
    # Usando la función zip() podemos iterar sobre nuestras listas de valores al mismo tiempo.
    for (
        x,
        y,
        t,
    ) in zip(annotations_x, annotations_y, texto_anotaciones):
        # Vamos a ajustar las nuevas anotaciones basandonos en las coornedas de los subtítulos.
        x -= 0.12
        y -= 0.035

        fig.add_annotation(
            x=x,
            xanchor="left",
            xref="paper",
            y=y,
            yanchor="top",
            yref="paper",
            text=t,
            font_color="#64ffda",
            font_size=18,
            bordercolor="#64ffda",
            borderpad=5,
            borderwidth=1.5,
            bgcolor="#171010",
        )

    fig.add_annotation(
        x=0.01,
        xanchor="left",
        xref="paper",
        y=-0.085,
        yanchor="bottom",
        yref="paper",
        text=f"Fuente: Banxico ({FECHA_FUENTE})",
    )

    fig.add_annotation(
        x=0.5,
        xanchor="center",
        xref="paper",
        y=-0.085,
        yanchor="bottom",
        yref="paper",
        text=f"El crecimiento nacional por ingresos de remesas del {primer_año} al {ultimo_año} es de <b>162.34%</b>",
    )

    fig.add_annotation(
        x=1.01,
        xanchor="right",
        xref="paper",
        y=-0.085,
        yanchor="bottom",
        yref="paper",
        text="🧁 @lapanquecita",
    )

    fig.write_image("./estados_tendencia.png")


if __name__ == "__main__":
    plot_mapa(2023)
    plot_tendencias()
