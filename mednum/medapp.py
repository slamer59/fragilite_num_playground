#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import geopandas as gpd
import geoviews as gv
import pandas as pd
import panel as pn
import param
import pygal
from holoviews import opts
from holoviews.element.tiles import StamenTerrain
from pygal.style import Style

from mednum import *

# from mednum.loadapp import get_dept_df, iris_df
gv.extension("bokeh")

opts.defaults(
    opts.Polygons(
        width=800,
        height=600,
        toolbar="above",
        colorbar=True,
        tools=["hover", "tap"],
        aspect="equal",
    )
)


class MedNumApp(param.Parameterized):
    localisation = param.String(
        default="Toulouse", label=""
    )  # default=["Toulouse"], objects=list(ifrag_cont_df_merged.nom_com.unique()), label='', doc="A string")
    score = param.Range(default=(0, 250), bounds=(0, 250), label="")
    interfaces_num = param.ListSelector(label="")
    infos_num = param.ListSelector(label="")

    comp_admin = param.ListSelector(label="")
    comp_usage_num = param.ListSelector(label="")

    point_ref = param.Selector(
        objects=["Pays", "Région", "Département", "Intercommune", "Commune"],
        label="Point de référence",
    )

    donnees_infra = param.Action(
        lambda x: x, doc="""Données Infra-Communales""", precedence=0.7
    )
    export_data = param.Action(
        lambda x: x.timestamps.append(dt.datetime.utcnow()),
        doc="""Exporter les résultats""",
        precedence=0.7,
    )
    edit_report = param.Action(
        lambda x: x.timestamps.append(dt.datetime.utcnow()),
        doc="""Editer un rapport""",
        precedence=0.7,
    )
    tiles = StamenTerrain()

    def __init__(self, **params):
        super(MedNumApp, self).__init__(**params)

        self.param.interfaces_num.objects = OPTIONS_INT_NUM
        self.param.infos_num.objects = OPTIONS_X_INFOS

        self.param.comp_admin.objects = OPTIONS_X_COMP_ADMIN
        self.param.comp_usage_num.objects = OPTIONS_X_COMP_USAGE

        self.gauge_ind1 = PyGauge(value=80, max_value=100, name="Gauge1")
        self.gauge_ind2 = PyGauge(value=158, max_value=200, name="Gauge2")

    def lat_widgets(self):
        score_panel = pn.Column("# Score", self.param.score)
        point_ref_panel = pn.Column(
            "# Point de reference",
            pn.Param(
                self.param.point_ref,
                widgets={
                    "point_ref": pn.widgets.RadioBoxGroup,
                },
            ),
        )
        export_panel = pn.Column(
            "# Aller plus loin", self.param.export_data, self.param.edit_report
        )

        localisation_panel = pn.Column("# Localisation", self.param.localisation)
        spec_interfaces = {
            "interfaces_num": pn.widgets.TreeViewCheckBox,
            "infos_num": pn.widgets.TreeViewCheckBox,
            "comp_admin": pn.widgets.TreeViewCheckBox,
            "comp_usage_num": pn.widgets.TreeViewCheckBox,
        }

        g_params = [
            pn.Param(self.param[p], widgets={p: w}) for p, w in spec_interfaces.items()
        ]
        pn.Column(*g_params)
        indicateurs = pn.Column("# Indicateurs", *g_params)

        ordered_panel = pn.Column(
            localisation_panel,
            score_panel,
            indicateurs,
            point_ref_panel,
            export_panel,
            width=400,
        )

        return ordered_panel

    def top_panel(self):
        return pn.Row(self.gauge_ind1.view, self.gauge_ind2.view)

    @param.depends("localisation")  # , interfaces_num)
    def plot(self):

        commune_plot = gv.Polygons(
            ifrag_cont_df_merged[ifrag_cont_df_merged.nom_com == self.localisation],
            vdims=vdims,
        )
        return self.tiles * commune_plot.opts(
            color=indice, width=600, height=600, fill_alpha=0.5
        )

    def view(self):
        return pn.Row(self.lat_widgets(), pn.Column(self.top_panel, self.plot))

    def panel(self):
        # return pn.Row(global_param.lat_widgets(), global_param.plot)
        return self.lat_widgets()

cwd = Path(os.getcwd())
exec_path = cwd.parent
# css_files = [
#     "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css"
# ]
data_path = Path("../data")

if data_path.exists():
    medcss_file = data_path.parent / "mednum" / "css" / "medapp.css"
else:
    data_path = Path("./data")
    medcss_file = data_path.parent / "mednum" / "css" / "medapp.css"

css_files = [medcss_file]
external_data = data_path / "external/"
processed_data = data_path / "processed/"
raw_data = data_path / "raw/"
interim_data = data_path / "interim/"

cont_iris = external_data / "geojson" / "contours-iris.geojson"
hard_reset = False
cache_dir = interim_data

france_geo_path = external_data / "france-geojson-master"
geojson_path = {geo.stem: geo for geo in france_geo_path.rglob("*.parquet")}
indice_frag_reformated = interim_data / "Tableau_data.parquet"

regions = geojson_path["regions"]
dept = geojson_path["departements"]
cont_iris = external_data / "geojson" / "contours-iris.geojson"
cont_iris_reformated = interim_data / "contours-iris.parquet"
indice_frag = france_geo_path = external_data / "extract_tableau" / "Tableau_data.csv"

cont_iris_df = iris_df(cont_iris)
dept_df = get_dept_df(regions.with_suffix(".parquet"))
reg_df = get_regions_df(dept.with_suffix(".parquet"))

# Cartes
reg_map = gv.Polygons(reg_df, vdims=["nom"])
dept_map = gv.Polygons(dept_df, vdims=["nom", "code"])
com_map = gv.Polygons(reg_df, vdims=["nom", "code"])

# Extraction de tableau (Indices)
ifrag_df = get_indice_frag(indice_frag.with_suffix(".parquet"))
ifrag_df_pivot = get_indice_frag_pivot(ifrag_df)

# Merged
ifrag_cont_df_merged = get_merged_iris_data(cont_iris_df, ifrag_df_pivot)
indices_list = list(ifrag_df["Noms de mesures"].unique())
vdims = ["code_iris", "nom_com", "nom_iris"] + indices_list

# Lecture des données
# class PathSelector(param.Parameterized):
#     paths = param.Dict(
#         {
#             "external": Path("./data/external/"),
#             "processed": Path("./data/processed/"),
#             "raw": Path("./data/raw/"),
#             "interim": Path("./data/interim/"),
#         }
#     )

#     @pn.depends("paths", watch=True)
#     def setup_path(self):
#         self.paths = {
#             k: Path(v) if isinstance(v, str) else v for k, v in self.paths.items()
#         }

#     def __init__(self, **params) -> None:
#         super(PathSelector, self).__init__(**params)
#         cont_iris = self.paths['external'] / "geojson" / "contours-iris.geojson"
#         hard_reset = False
#         cache_dir = self.interim_data

#     def load_dataset(self):
#         france_geo_path = self.paths['external'] / "france-geojson-master"
#         geojson_path = {geo.stem: geo for geo in france_geo_path.rglob("*.parquet")}
#         indice_frag_reformated = self.paths['interim_data'] / "Tableau_data.parquet"

#         regions = geojson_path["regions"]
#         dept = geojson_path["departements"]
#         cont_iris = self.external_data / "geojson" / "contours-iris.geojson"
#         cont_iris_reformated = self.interim_data / "contours-iris.parquet"
#         indice_frag = france_geo_path = (
#             self.external_data / "extract_tableau" / "Tableau_data.csv"
#         )

#         # Load dataset
#         cont_iris_df = iris_df(cont_iris)
#         dept_df = get_dept_df(regions)
#         reg_df = get_regions_df(dept)

#         # Cartes
#         reg_map = gv.Polygons(reg_df, vdims=["nom"])
#         dept_map = gv.Polygons(dept_df, vdims=["nom", "code"])
#         com_map = gv.Polygons(reg_df, vdims=["nom", "code"])

#         # Extraction de tableau (Indices)
#         ifrag_df = get_indice_frag(indice_frag)
#         ifrag_df_pivot = get_indice_frag_pivot(ifrag_df)

#         # Merged
#         ifrag_cont_df_merged = get_merged_iris_data(cont_iris_df, ifrag_df_pivot)

#         indices_list = list(ifrag_df["Noms de mesures"].unique())
#         vdims = ["code_iris", "nom_com", "nom_iris"] + indices_list

# # Correspondances

map_idx_to_data_idx = {
    # "":'GLOBAL COMPETENCES'
    #: 'GLOBAL ACCES',
    "Compétences usages numériques": "COMPÉTENCES NUMÉRIQUES / SCOLAIRES",
    "Compétences adminitratives": "COMPETENCES ADMINISTATIVES",
    "Accès à l'info": "ACCES A L'INFORMATION",
    "Accès aux interfaces numériques": "ACCÈS AUX INTERFACES NUMERIQUES",
    "Score": "SCORE GLOBAL ",
    "Population": "Population",
    "Taux de pauvreté": None,
    "Epuipement des ménages": None,
    "Couverture mobile": None,
    "Taux de couverture HD / THD": None,
}

selected_idx = ["Compétences usages numériques", "Accès à l'info"]
selected_data_idx = [
    dind for mind, dind in map_idx_to_data_idx.items() if mind in selected_idx
]

vdims = ["code_iris", "nom_com", "nom_iris"] + selected_data_idx
selected_data_idx += ["geometry"]
nom_com = "Toulouse"

# # Widget gauche

OPTIONS_INT_NUM = [
    "Accès aux interfaces numériques",
    "Taux de pauvreté",
    "Epuipement des ménages",
    "Couverture mobile",
    "Taux de couverture HD / THD",
]
OPTIONS_X_INFOS = ["Accès à l'info", "Oui", "Non"]
OPTIONS_X_COMP_ADMIN = ["Compétences adminitratives", "Oui", "Non"]
OPTIONS_X_COMP_USAGE = ["Compétences usages numériques", "Oui", "Non"]

CATEGORIES_INT_NUM = {
    "select_all": "Accès aux interfaces numériques",
    "select_options": OPTIONS_INT_NUM,
}

# # Dashboards
# ## Haut

# In[64]:

localisation = "Métropole d’Aix-Marseille"
score = (17, 175)
population = ""

size_w = 100
size_w_gauge = size_w * 2

custom_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#53E89B",
    foreground_strong="#53A0E8",
    foreground_subtle="transparent",
    opacity=".2",
    opacity_hover=".9",
    transition="400ms ease-in",
    value_font_size=size_w_gauge,
    colors=("#0000ff", "#ff0000"),
)

# gauge = pygal.SolidGauge(inner_radius=0.70, show_legend=False, style=custom_style)
# percent_formatter = lambda x: "{:.10g}".format(x)
# dollar_formatter = lambda x: "{:.10g}$".format(x)
# gauge.value_formatter = percent_formatter
# gauge.add("", [{"value": 85, "max_value": 255}])
# gauge.render_to_file("gauge1.svg")

# gauge2 = pygal.SolidGauge(inner_radius=0.70, show_legend=False, style=custom_style)
# percent_formatter = lambda x: "{:.10g}".format(x)
# dollar_formatter = lambda x: "{:.10g}$".format(x)
# gauge2.value_formatter = percent_formatter
# gauge2.add("", [{"value": 135, "max_value": 255}])
# gauge2.render_to_file("gauge2.svg")

# pn.pane.SVG("gauge1.svg", width=size_w)  # , height=600)

# g1 = pn.pane.SVG("gauge1.svg", width=size_w)  # , height=600)
# g2 = pn.pane.SVG("gauge2.svg", width=size_w)  # , height=600)

# In[175]:

# py_gauge = PyGauge(max_value=100, name="Gauge")
# pn.Row(py_gauge, py_gauge.view)

# In[170]:

# css_top = """position: absolute;
# background: #FFFFFF;
# border: 1px solid #E5E5E5;
# box-sizing: border-box;
# box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.07);
# border-radius: 11px;
# font-family: Source Sans Pro;
# font-style: normal;
# font-weight: 600;
# font-size: 16px;
# line-height: 20px;
# display: flex;
# align-items: center;
# text-transform: capitalize;
# color: #000000;
# """

# def css2dict(css_str):
#     css_style = {}
#     for style in css_str.replace(";", "").split("\n"):
#         if style:
#             try:
#                 k, v = style.split(":")
#                 css_style[k] = v
#             except Exception as e:
#                 print(e)
#                 print(style)
#     return css_style

# css_top_box = css2dict(css_top)

# HTML = """
# <h1>{loc}</h1>
# """.format(
#     loc=localisation
# )

# html_pane = pn.pane.HTML(HTML, style=css_top_box)

# html_pane

# # In[180]:

# html_indic_info1 = """
#        <h3>{title}</h3>
#        {value}
# """.format(
#     title="Information", value=118
# )

# html_indic_info2 = """
#        <h3>{title}</h3>
#        {value}
# """.format(
#     title="Interfaces", value=53
# )

# css_indic = """
# font-style: normal;
# font-weight: normal;
# font-size: 13px;
# line-height: 16px;
# display: flex;
# align-items: center;
# text-align: center;
# text-transform: uppercase;
# color: #989898;
# border-left: 1px solid #E5E5E5;
# padding: 10px;
# """

# css_info = """
# font-family: Source Sans Pro;
# font-style: normal;
# font-weight: normal;
# font-size: 18px;
# line-height: 14px;
# display: flex;
# align-items: center;
# text-transform: capitalize;
# color: #989898;
# border-left: 1px solid #E5E5E5;
# padding: 10px;
# """

# css_indic_dict = css2dict(css_indic)
# css_info_dict = css2dict(css_info)

# py_gauge = PyGauge(max_value=100, name="Gauge")

# html_indic_gauge_pane = (
#     py_gauge.view
# )  # pn.Row(py_gauge, py_gauge.view) # pn.pane.HTML(html_indic_gauge, style=css_indic_dict)
# html_info1_pane = pn.pane.HTML(html_indic_info1)  # , style=css_info_dict)
# html_info2_pane = pn.pane.HTML(html_indic_info2)  # , style=css_info_dict)

# gspec = pn.GridSpec()  # height=200) #sizing_mode='stretch_both') #, max_height=800)

# gspec[:, 0] = html_indic_gauge_pane
# gspec[0, 1] = html_info1_pane
# gspec[1, 1] = html_info2_pane
# gspec

# # Complet

indice = "GLOBAL COMPETENCES"
global_param = MedNumApp(name="Sélection")


pn.extension(css_files=css_files)  # raw_css=[css], css_files=css_files)
pn.Row(global_param.lat_widgets(), global_param.plot).servable()
