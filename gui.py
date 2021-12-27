import os
import sys
import webbrowser
import tkinter as tk
from tkinter.messagebox import showinfo


def display_icon(parent, icon) -> None:
    """Displays icon, os independently."""
    if sys.platform.startswith("win"):
        parent.iconbitmap(icon)
    elif sys.platform.startswith("linux"):
        parent.call("wm", "iconphoto", parent._w, tk.PhotoImage(file=icon))


class CustomLabel(tk.Label):
    """Child of tkinter.Label, with a custom constructor."""
    INKWELL = "#363945"
    DARK_INKWELL = "#252525"
    SAND_DOLLAR = "#dfcfbe"
    FONT = "Consolas 10"

    def __init__(self, parent, **options):
        tk.Label.__init__(self, parent)
        self.parent = parent
        self.label = tk.Label(parent, font=self.FONT, bg=self.DARK_INKWELL, fg=self.SAND_DOLLAR, **options)

    def pack(self, **options) -> None:
        self.label.pack(**options)

    def config(self, **options) -> None:
        self.label.config(**options)


class CustomEntry(tk.Entry):
    """Child of tkinter.Entry, with a custom constructor."""
    RED = "#bc243c"
    FONT = "Constantia 10"
    SEARCH_WIDTH = 40
    BORDERWIDTH = 3

    def __init__(self, parent, **options):
        tk.Entry.__init__(self, parent)
        self.parent = parent
        self.entry = tk.Entry(self.parent, borderwidth=self.BORDERWIDTH, font=self.FONT,
                              width=self.SEARCH_WIDTH, selectbackground=self.RED, **options)

    def config(self, **options) -> None:
        self.entry.config(**options)

    def get(self) -> str:
        return str(self.entry.get())

    def pack(self, **options) -> None:
        self.entry.pack(**options)


class CustomButton(tk.Button):
    """Child of tkinter.Button, with a custom constructor."""
    INKWELL = "#363945"
    DARK_INKWELL = "#252525"
    SAND_DOLLAR = "#dfcfbe"
    RED = "#bc243c"
    FONT = "Cambria 10"
    BORDERWIDTH = 0

    def __init__(self, parent, **options):
        tk.Button.__init__(self, parent)
        self.parent = parent
        self.button = tk.Button(parent, borderwidth=self.BORDERWIDTH,
                                bg=self.DARK_INKWELL, activebackground=self.INKWELL, font=self.FONT,
                                fg=self.SAND_DOLLAR, activeforeground=self.SAND_DOLLAR,
                                **options)

    def config(self, **options) -> None:
        self.button.config(**options)

    def pack(self, **options) -> None:
        self.button.pack(**options)


class TextField(tk.Text):
    """Child of tkinter.Text, with a custom constructor and custom methods.
    Also creates and packs scrollbars."""
    INKWELL = "#363945"
    DARK_INKWELL = "#252525"
    SAND_DOLLAR = "#dfcfbe"
    RED = "#bc243c"
    FONT = "Consolas 10"
    WRAP = tk.NONE
    CURSOR = "arrow"
    SPACING = 4  # Spacing between lines
    SCROLLBAR_WIDTH = 14

    def __init__(self, parent, **options):
        tk.Text.__init__(self, parent, **options)
        self.parent = parent
        self.scrollbarY = tk.Scrollbar(self.parent, troughcolor=self.SAND_DOLLAR,
                                       width=self.SCROLLBAR_WIDTH, bg=self.DARK_INKWELL, activebackground=self.DARK_INKWELL)
        self.scrollbarX = tk.Scrollbar(self.parent, orient="horizontal", troughcolor=self.SAND_DOLLAR,
                                       width=self.SCROLLBAR_WIDTH, bg=self.DARK_INKWELL, activebackground=self.DARK_INKWELL)
        self.text = tk.Text(self.parent, bg=self.INKWELL, fg=self.SAND_DOLLAR,
                            spacing1=self.SPACING, selectbackground=self.RED,
                            font=self.FONT, wrap=self.WRAP, cursor=self.CURSOR,
                            yscrollcommand=self.scrollbarY.set, xscrollcommand=self.scrollbarX.set)
        self.scrollbarY.config(command=self.text.yview)
        self.scrollbarX.config(command=self.text.xview)

    def display(self) -> None:
        self.scrollbarY.pack(side="right", fill="y")
        self.scrollbarX.pack(side="bottom", fill="x")
        self.text.pack(side="bottom", fill="both", expand=True)

    def config(self, **options) -> None:
        self.text.config(**options)

    def write(self, chars, *args):
        """Enable text editing, write data at the end and then disable it."""
        self.enable()
        self.text.insert("end", chars, *args)
        self.disable()

    def clear(self) -> None:
        """Enables text editing ,clears the whole text and then disables it."""
        self.enable()
        self.text.delete("1.0", "end")
        self.disable()

    def enable(self) -> None:
        """Enable text field editing."""
        self.text.config(state="normal")

    def disable(self) -> None:
        """Disable text field editing."""
        self.text.config(state="disabled")


class CustomMenuBar(tk.Menu):
    """Child of tk.Menu, with a custom constructor."""
    INKWELL = "#363945"
    DARK_INKWELL = "#252525"
    SAND_DOLLAR = "#dfcfbe"
    RED = "#bc243c"
    FONT = "Constantia 10"

    def __init__(self, parent, functions):
        tk.Menu.__init__(self, parent)
        self.parent = parent
        self.gather_data, self.update_data, self.export_csv, self.export_txt, self.load_external_data, self.plot_data = functions
        self.menubar = tk.Menu(self.parent, bg=self.DARK_INKWELL, fg=self.SAND_DOLLAR, font=self.FONT,
                               activebackground=self.INKWELL, activeforeground=self.SAND_DOLLAR)

        # Data Menu
        self.filemenu = tk.Menu(self.menubar, tearoff=0, bg=self.DARK_INKWELL, fg=self.SAND_DOLLAR,
                                font=self.FONT, activebackground=self.INKWELL, activeforeground=self.SAND_DOLLAR)
        self.filemenu.add_command(label="Gather Data           Ctrl + G", command=self.gather_data)
        self.filemenu.add_command(label="Update Data           Ctrl + U", command=self.update_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Plot Search Results   Ctrl + P", command=self.plot_data)
        self.filemenu.add_separator()
        self.exportmenu = tk.Menu(self.filemenu, tearoff=0, bg=self.DARK_INKWELL, fg=self.SAND_DOLLAR,
                                  font=self.FONT, activebackground=self.INKWELL, activeforeground=self.SAND_DOLLAR)
        self.filemenu.add_cascade(label="Export As...", menu=self.exportmenu)
        self.exportmenu.add_command(label="   .csv", command=self.export_csv)
        self.exportmenu.add_command(label="   .txt", command=self.export_txt)
        self.filemenu.add_command(label="Load...               Ctrl + L", command=self.load_external_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.parent.quit)

        # Help
        self.helpmenu = tk.Menu(self.menubar, tearoff=0, bg=self.DARK_INKWELL, fg=self.SAND_DOLLAR,
                                font=self.FONT, activebackground=self.INKWELL, activeforeground=self.SAND_DOLLAR)
        self.helpmenu.add_command(label="General Manual", command=self.show_general_manual)
        self.helpmenu.add_command(label="Search Manual", command=self.show_search_manual)
        self.helpmenu.add_command(label="Visit GitHub", command=self.visit_github)
        self.helpmenu.add_command(label="About", command=self.show_html)

        # Adding the menus in the menubar
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

    def display(self) -> None:
        """Display the menubar."""
        self.parent.config(menu=self.menubar)

    def show_general_manual(self) -> None:
        """Prints manual."""
        showinfo("General Manual", """
    ▶ Database:
Database gathers file data/metadata from your system and displays them on screen
    ▶ Gather Data <Ctrl + G>:
Gather Data from the directory specified
    ▶ Update Data <Ctrl + U>:
Re-gathers data from the current directory
    ▶ Load Data <Ctrl + L>:
Loads data from the .json file selected
    ▶ Sorting:
Clicking on the respective data button sorts the data displayed
    ▶ Export:
Exports data as .csv/.txt""")

    def show_search_manual(self) -> None:
        """Prints manual."""
        showinfo("Search Manual", """
    ▶ Size search:
       ⬩ > < = {key}
        (eg. kb, bytes, GB etc)
    ▶ RegEx (Name search):
       ⬩ ^{key}  → Starts with key
       ⬩ ${key}  → Ends with key
       ⬩ %{key}% → Caseless
       ⬩ !{key}  → Not in name
       ⬩ basename: {key}
    ▶ Dual search: &&""")

    def show_html(self) -> None:
        """Opens about.html."""
        webbrowser.open("about.html")

    def visit_github(self) -> None:
        """Visits github repository."""
        webbrowser.open("https://github.com/Nick-Bounatsos/Database")
