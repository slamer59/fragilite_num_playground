"""Example that demonstrates the use of the Designer"""
import panel as pn
from awesome_panel_extensions.developer_tools.designer import (
    ComponentReloader, Designer)

from medapp import MedNumApp
from pathlib import Path

from widgets import PyGauge

css_file = Path(__file__).parent / "medapp.css"
# css_files = ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css']
pn.extension() #css_files=css_files)


def _designer():
    # Define your components
    medapp_reloader = ComponentReloader(
        component=MedNumApp, 
        parameters={"name": "Sélection"},
        css_path=css_file
    )
    medapp_top_reloader = ComponentReloader(
        component=PyGauge, 
        parameters={"max_value":100, "name": "Gauge"},
        css_path=css_file
    )

    components = [
        medapp_top_reloader,
       medapp_reloader
    ]
    # Configure the Designer with you components
    return Designer(components=components)

_designer().show()