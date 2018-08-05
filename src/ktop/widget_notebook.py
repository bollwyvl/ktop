import json
import traitlets as T
from copy import deepcopy

try:
    import pandas as pd
except ImportError:
    pd = None

from nbformat.v4 import new_notebook, writes, new_code_cell
from nbformat.notebooknode import NotebookNode

import ipywidgets as W

from .widget_kernel import Kernel
from .utils import save_notebook, load_notebook
from .widget_dashboard import DefaultNotebookView
from .widget_nbformat import NBFormat


class Notebook(W.Widget):
    """ An evented notebook, which may have more than one kernel
    """

    # path
    file_name = T.Unicode("Untitled", allow_none=True).tag(sync=True)
    # name
    nbformat = T.Instance(NBFormat).tag(sync=True, **W.widget_serialization)
    kernels = T.Tuple([]).tag(sync=True, **W.widget_serialization)
    kernel_count = T.Integer(0).tag(sync=True)

    _view_klass = DefaultNotebookView

    def __init__(self, *args, **kwargs):
        kwargs["nbformat"] = kwargs.get("nbformat") or NBFormat()
        super(Notebook, self).__init__(*args, **kwargs)

    def view(self, view_klass=None):
        return (view_klass or self._view_klass)(notebook=self)

    def run(self, cells=None, kernels=[], kernel_name=None, shutdown=True,
            append=False, save=True, reuse=True, start=True):

        if reuse:
            kernels = kernels or self.kernels

        kernels = kernels or []

        if cells is None:
            cells = self.nbformat.cells

        if kernel_name is None:
            try:
                kernel_name = self.nbformat.metadata["kernelspec"]["name"]
            except Exception:
                pass

        if not kernels and start:
            kernel = Kernel(
                name=kernel_name or "python3",
                file_name=f"{self.file_name}_{self.kernel_count}"
            )
            kernels = [kernel]
            self.kernels += (kernel,)
            self.kernel_count += 1

        for kernel in kernels:
            yield kernel.run(cells=cells, shutdown=shutdown)

    def save(self):
        if self.file_name is None:
            raise ValueError("needs file_name")
        save_notebook(self.file_name, self.nbformat._to_node())
        return self

    def load(self):
        if self.file_name is None:
            raise ValueError("needs file_name")
        nbf = NBFormat()
        nbf.node = load_notebook(self.file_name)
        self.nbformat = nbf
        return self
