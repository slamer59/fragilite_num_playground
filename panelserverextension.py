from subprocess import Popen
import os
def load_jupyter_server_extension(nbapp):
    """serve the gapminder.ipynb directory with bokeh server"""
    os.chdir("./notebooks")
    Popen(["panel", "serve", "ind_frag_num_communes-mybinder.ipynb", "--allow-websocket-origin=*"])
