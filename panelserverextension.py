from subprocess import Popen

def load_jupyter_server_extension(nbapp):
    """serve the gapminder.ipynb directory with bokeh server"""
    Popen(["panel", "serve", "ind_frag_num_communes-mybinder.ipynb", "--allow-websocket-origin=*"])
