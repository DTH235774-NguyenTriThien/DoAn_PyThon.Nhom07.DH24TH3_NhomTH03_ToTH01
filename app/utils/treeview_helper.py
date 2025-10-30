# treeview_helpers.py
import math
import threading
import tkinter as tk
from tkinter import ttk

# fill treeview in batches to keep UI responsive
def fill_treeview_chunked(tree: ttk.Treeview, rows: list, batch: int = 200, on_complete=None):
    """
    Insert rows into a ttk.Treeview in chunks to avoid freezing UI.
    rows: list of tuples/lists representing values for each row
    batch: number of rows per chunk insert
    """
    # clear existing
    tree.delete(*tree.get_children())

    total = len(rows)
    if total == 0:
        if on_complete:
            on_complete()
        return

    def insert_chunk(start=0):
        end = min(start + batch, total)
        for r in rows[start:end]:
            # assume r is (iid, (col1, col2, ...)) or dict-like
            if isinstance(r, dict):
                iid = r.get("id") or r.get("iid") or None
                vals = r.get("values") or r.get("vals") or tuple(r.values())
            elif isinstance(r, (list, tuple)) and len(r) == 2:
                iid, vals = r
            else:
                iid = None
                vals = r
            tree.insert("", "end", iid=iid, values=vals)
        # schedule next chunk
        if end < total:
            tree.after(10, insert_chunk, end)
        else:
            if on_complete:
                on_complete()

    insert_chunk(0)


# Simple pagination controller class
class Paginator:
    def __init__(self, page_size=200):
        self.page_size = page_size
        self.page = 1
        self.total = 0

    def set_total(self, total):
        self.total = total
        self.page = 1

    def pages_count(self):
        if self.total == 0: return 1
        return math.ceil(self.total / self.page_size)

    def offset(self):
        return (self.page - 1) * self.page_size

    def next(self):
        if self.page < self.pages_count():
            self.page += 1

    def prev(self):
        if self.page > 1:
            self.page -= 1
