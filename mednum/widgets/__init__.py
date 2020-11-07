import param
import panel as pn
import uuid
from param import Path

import pygal
from tempfile import NamedTemporaryFile
from pygal.style import Style
import os


def css2dict(css_str):
    css_style = {}
    for style in css_str.replace(";", "").split("\n"):
        if style:
            try:
                k, v = style.split(":")
                css_style[k.strip()] = v.strip()
            except Exception as e:
                print(e)
                print(style)
                pass
    return css_style


class TreeViewCheckBox(param.Parameterized):
    # tree_categories = param.Parameter()
    # all_checkbox = param.Boolean()
    box_size = param.Number()

    def __init__(self, tree_categories, **params):
        self.tree_categories = tree_categories
        # .get("tree_categories",

        try:
            all_checkbox_label = self.tree_categories["select_all"]
        except NameError as n:
            raise NameError("Define a dict containing the name of **select_all**")
        except:
            raise Exception

        try:
            self.options = self.tree_categories["select_options"]
        except NameError as n:
            raise NameError(
                "Define a dict containing a list of options in **select_options**"
            )
        except:
            raise Exception

        TreeViewCheckBox.box_size = (
            max(
                [len(word) for word in self.options]
                + [len(all_checkbox_label), TreeViewCheckBox.box_size]
            )
            * 10
        )

        self.all_checkbox = pn.widgets.Checkbox(name=all_checkbox_label)
        self.select_string = pn.widgets.CheckBoxGroup(
            name="Checkbox Group",
            value=[],
            options=self.options,
        )
        self.all_drop = pn.widgets.Checkbox(css_classes=["chck-custom"])

        self.init_tree_panel()
        super().__init__(**params)

    def checked_values(self):
        return [self.all_checkbox.name] + self.select_string.values
        # max([len(word) for word in self.options]+ [len(all_checkbox_label), TreeViewCheckBox.box_size]) * 10

    @param.depends("box_size", watch=True)
    def init_tree_panel(self):
        self._initial_tree = pn.Row(
            pn.Row(self.all_checkbox, max_width=self.box_size), self.all_drop
        )

    @pn.depends("all_checkbox.value", watch=True)
    def _update_all(self):
        if self.all_checkbox.value:
            self.select_string.value = self.select_string.options
        else:
            if len(self.options[:-1]) != len(self.select_string.value):
                self.select_string.value = []

    @pn.depends("select_string.value", watch=True)
    def _update_select_string(self):
        if len(self.options) == len(self.select_string.value):
            self.all_checkbox.value = True
        else:
            self.all_checkbox.value = False

    @pn.depends("all_drop.value")
    def panel(self):
        self._initial_tree = pn.Row(
            pn.Row(self.all_checkbox, max_width=self.box_size), self.all_drop
        )
        if self.all_drop.value:
            return pn.Column(self._initial_tree, self.select_string)

        else:
            return pn.Column(self._initial_tree)


class Export(param.Parameterized):
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


class Score(param.Parameterized):
    score = param.Range(default=(0, 250), bounds=(0, 250))


class Localisation(param.Parameterized):
    localisation = param.String(default="Marseille", label="", doc="A string")


class Reference(param.Parameterized):
    point_ref = param.ListSelector(
        objects=["Pays", "Région", "Département", "Intercommune", "Commune"],
        label="Point de référence",
    )

    donnees_infra = param.Action(
        lambda x: x, doc="""Données Infra-Communales""", precedence=0.7
    )


class TreeViewCheckBoxCompo(param.Parameterized):
    OPTIONS_INT_NUM = [
        "Taux de pauvreté",
        "Equipement des ménages",
        "Couverture mobile",
        "Taux de couverture HD / THD",
    ]
    CATEGORIES_INT_NUM = {
        "select_all": "Accès aux interfaces numériques",
        "select_options": OPTIONS_INT_NUM,
    }

    OPTIONS_X_INFOS = ["Oui", "Non"]
    CATEGORIES_X_INFOS = {
        "select_all": "Accès à l'info",
        "select_options": OPTIONS_X_INFOS,
    }

    OPTIONS_X_COMP_ADMIN = ["Oui", "Non"]
    CATEGORIES_X_COMP_ADMIN = {
        "select_all": "Compétences adminitratives",
        "select_options": OPTIONS_X_COMP_ADMIN,
    }

    OPTIONS_X_COMP_USAGE = ["Oui", "Non"]
    CATEGORIES_X_COMP_USAGE = {
        "select_all": "Compétences usages numériques",
        "select_options": OPTIONS_X_COMP_USAGE,
    }

    ind_x_interfaces_num = TreeViewCheckBox(tree_categories=CATEGORIES_INT_NUM)
    ind_x_infos_num = TreeViewCheckBox(tree_categories=CATEGORIES_X_INFOS)
    ind_x_comp_admi = TreeViewCheckBox(tree_categories=CATEGORIES_X_COMP_ADMIN)
    ind_x_comp_uasge_num = TreeViewCheckBox(tree_categories=CATEGORIES_X_COMP_USAGE)

    indicateurs = pn.Column(
        pn.pane.Markdown("\n**Indicateurs**"),
        ind_x_interfaces_num.panel,
        ind_x_infos_num.panel,
        ind_x_comp_admi.panel,
        ind_x_comp_uasge_num.panel,
    )

    def __init__(self, **params):
        print(self.ind_x_interfaces_num.param)

    def panel(self):
        return self.indicateurs


class PyGauge(param.Parameterized):
    value = param.Integer(85, bounds=(0, 1000))
    max_value = param.Integer(150)

    custom_style = param.Dict(
        default=dict(
            background="transparent",
            plot_background="transparent",
            foreground="#53E89B",
            foreground_strong="#53A0E8",
            foreground_subtle="transparent",
            opacity=".2",
            opacity_hover=".9",
            transition="400ms ease-in",
            colors=("#0000ff", "#ff0000"),
        )
    )
    css_info_h2 = """
    margin: auto;"""
    size_w = param.Integer(100)
    value_font_size = param.Integer()

    def __init__(self, **params):
        super(PyGauge, self).__init__(**params)
        self.set_max()
        self.value_font_size = len(str(self.value)) * self.size_w
        self.w_name = self.name

    @pn.depends("value_font_size", "custom_style", watch=True)
    def set_style(self):
        self.custom_style["value_font_size"] = self.value_font_size
        self.param["custom_style"].default = self.custom_style

    @pn.depends("max_value", watch=True)
    def set_max(self):
        self.param.value.bounds = (0, self.max_value)
        self.value = self.max_value if self.value > self.max_value else self.value

    @pn.depends("value", "custom_style", watch=True)
    def create_gauge(self):
        gauge = pygal.SolidGauge(
            inner_radius=0.70,
            show_legend=False,
            style=Style(**self.custom_style),
        )
        percent_formatter = lambda x: "{:.10g}".format(x)
        gauge.value_formatter = percent_formatter
        vals = {"value": self.value, "max_value": self.max_value}
        gauge.add("", [vals])
        self.file_name = gauge.render_data_uri()
        self.HTML_GAUGE = """
        <h2 style="{css_info_h2}">{name}</h2>
        <img src="{filepath}" width="{width}px" />
        
        """.format(
            filepath=self.file_name,
            name=self.w_name,
            width=self.size_w,
            css_info_h2=self.css_info_h2,
        )

    # @pn.depends('value','max_value',watch=True)
    def view(self):
        self.create_gauge()
        return pn.pane.HTML(self.HTML_GAUGE)


class IndicatorsWithGauge(PyGauge):  # param.Parameterized):
    indicators = param.List(
        [
            dict(name="indic2", main=True, value=50, max_value=100),
            dict(name="indic2", value=150),
        ]
    )
    show_gauge = False
    other_indic = []
    css_info_td = """
        font-family: Source Sans Pro;
        font-style: normal;
        font-weight: normal;
        font-size: 18px;
        align-items: center;
        text-transform: capitalize;
        color: #989898;
        border-left: 1px solid #E5E5E5;
        padding: 10px;
    """
    css_info_h3 = """
    margin: auto;
    """

    def __init__(self, **params) -> None:
        super(IndicatorsWithGauge, self).__init__(**params)
        self.set_indicators()

    @pn.depends("indicators", watch=True)
    def set_indicators(self):
        for ind in self.indicators:
            if "main" in ind:
                self.show_gauge = True
                self.max_value = ind["max_value"]
                self.value = ind["value"]
                self.main_indicators_name = ind["name"]

        self.other_indic = []
        for ind in self.indicators:
            if ind["name"] != self.main_indicators_name:
                self.other_indic.append(ind)
        try:
            c2d= css2dict(self.css_info_td )
            font_h = int(c2d['font-size'].replace('px',''))
            pad = int(c2d['padding'].replace('px',''))
        except:
            font_h = 18
            pad = 10
            pass
        self.size_w = ((font_h*2)+(pad*2))*len(self.indicators)

    def view(self):
        self.w_name = self.main_indicators_name
        self.create_gauge()
        rowspan = len(self.indicators)
        HTML = """
        <table class="gauge-cls" style="border-spacing: 1em; width:100%">
            <tr class="gauge-tr">
                <td class="gauge-td" rowspan={rowspan} style="{style}">{gauge}</td>
        """.format(
            rowspan=rowspan, gauge=self.HTML_GAUGE, style=self.css_info_td
        )

        HTML_ROWS = [
            """
            <td class="gauge-td" style="{style}">
            <h3 style="{style_h3}">{title}</h3>
                {value}
            </td>
        """.format(
                title=row["name"],
                value=row["value"],
                style=self.css_info_td,
                style_h3=self.css_info_h3,
            )
            for row in self.other_indic
        ]

        HTML = HTML + "</tr>\n<tr>\n".join(HTML_ROWS) + "\n<tr>\n</table>"

        return pn.pane.HTML(
            HTML, css_classes=["indicators"]
        )


# from panel.template.theme import Theme

# class TopPanel(Theme):
#     css = param.Filename('./css/medapp.css')
#     _template = pn.template.Template

# class TopPanel(param.Parameterized):
