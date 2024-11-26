import tkinter as tk
from tkinter import ttk

class RoundedFrame(ttk.Frame):
    def __init__(self, parent, radius=20, padding=15, background=None, **kwargs):
        super().__init__(parent, padding=padding, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=background)
        self.canvas.pack(fill='both', expand=True)
        
        def round_rectangle(x1, y1, x2, y2, radius=radius, **kwargs):
            points = [
                x1 + radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1
            ]
            return self.canvas.create_polygon(points, smooth=True, **kwargs)
        
        self.round_rectangle = round_rectangle
        self.bind('<Configure>', self._on_resize)
        
    def _on_resize(self, event):
        self.canvas.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        self.round_rectangle(0, 0, width, height, fill='#262626', outline='#333333')

class CustomProgressBar(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(height=6, bg='#262626', highlightthickness=0)
        self.progress_rect = None
        self.bind('<Configure>', self._on_resize)
        
    def create_progress_bar(self):
        width = self.winfo_width()
        height = self.winfo_height()
        self.create_rounded_rect(0, 0, width, height, 3, fill='#333333')
        self.progress_rect = self.create_rounded_rect(0, 0, 0, height, 3, fill='#0A84FF')
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def set_progress(self, value):
        if not self.progress_rect:
            self.create_progress_bar()
        width = self.winfo_width()
        height = self.winfo_height()
        progress_width = (value / 100) * width
        self.delete(self.progress_rect)
        self.progress_rect = self.create_rounded_rect(0, 0, progress_width, height, 3, fill='#0A84FF')
        
    def _on_resize(self, event):
        self.delete("all")
        self.create_progress_bar()

class CustomEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent,
                        bg='#333333',
                        fg='#FFFFFF',
                        insertbackground='#FFFFFF',
                        relief='flat',
                        highlightthickness=1,
                        highlightbackground='#404040',
                        highlightcolor='#0A84FF',
                        **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_fg = '#888888'
        
        self.insert(0, placeholder)
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
        
        if self.get() == placeholder:
            self.configure(fg=self.placeholder_fg)
    
    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg='#FFFFFF')
    
    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg=self.placeholder_fg)
