import database
import gui
import tkinter as tk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import askyesno, showinfo, showwarning

# Constants
ICON = "database.png"
DARK_INKWELL = "#252525"
# Button size constants
SIZE_WIDTH = 16
SEARCH_BUTTON_WIDTH = 6

root = tk.Tk(className="Database")

root.title("Database")
gui.display_icon(root, ICON)
# Open as full-screen
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")


def format_process_time(process_time: int) -> str:
    m, s = divmod(process_time, 60)
    s = round(s, 2)
    return f"{s} s" if not m else f"{int(m)}m {s}s"


def gather_data() -> None:
    """Gathers new data or updates old ones."""
    global data
    dirpath = askdirectory(title="Select a directory")
    if dirpath:
        data.load_data(dirpath=dirpath)
        data.print()
        size_button.config(text=f"Size ({data.total_size})")
        name_button.config(text=f"Path")
        info_label.config(
            text=f" Date: {data.date} | Files: {format(data.total_files, ',')} | Process time: {format_process_time(data.time)}")
    root.title(f"Database - {data.location}")


def update_data() -> None:
    """Asks for confirmation, updates old data and reports changes."""
    global data
    old_file_count = data.total_files
    old_size = data.total_bytes

    if askyesno(title="Confirmation", message="Confirm update?"):
        data.load_data(dirpath=data.location)
        data.print()
        size_button.config(text=f"Size ({data.total_size})")
        name_button.config(text=f"Path")
        info_label.config(
            text=f" Date: {data.date} | Files: {format(data.total_files, ',')} | Process time: {format_process_time(data.time)}")

        # Inform on data difference
        file_dif = data.total_files - old_file_count
        size_dif = data.total_bytes - old_size
        file_report = "⬩ "
        size_report = "⬩ "
        if not file_dif and not size_dif:
            showinfo("Update complete!",
                     f"Completed in {data.time}s.\n"
                     f"⬩ No changes detected")
        else:
            if file_dif > 0:
                file_report += f"{file_dif} new files added"
            elif file_dif < 0:
                file_report += f"{-file_dif} files removed"
            else:
                file_report += "No file count difference"

            if size_dif > 0:
                size_report += f"{data.format_bytes(size_dif)} taken"
            elif size_dif < 0:
                size_report += f"{data.format_bytes(-size_dif)} freed"
            else:
                size_report += "No size difference"

            showinfo("Update complete!",
                     f"Completed in {data.time}s\n"
                     f"{file_report}\n{size_report}")


def load_external_data() -> None:
    """Loads external data saved in .csv format."""
    filepath = askopenfilename(title="Select a CSV file", filetypes=[("CSV Files", "*.csv")])
    if filepath:
        if filepath.endswith(".csv"):
            if data.load_external_data(filepath):
                showinfo("Load", f"Successfully loaded data from {filepath}")
                size_button.config(text=f"Size ({data.total_size})")
                name_button.config(text=f"Path")
                info_label.config(
                    text=f" Date: Unknown | Files: {format(data.total_files, ',')} | Process time: Unknown")
                root.title(f"Database - External Data")
                data.print()
            else:
                showinfo("Load", f"Failed to load data from {filepath}")
        else:
            showwarning("Load", f"File must be .csv")


def search() -> None:
    """Wipes the arrows from size and path buttons and initiates search."""
    name_button.config(text=f"Path")
    size_button.config(text=f"Size ({data.total_size})")
    data.search(search_entry.get())


def sort_by(field: str) -> None:
    """Sorts and prints the data. Altering ascending/descending.
        Calls the database sort method which also reverses when it's possible."""
    if field == "name":
        size_button.config(text=f"Size ({data.total_size})")
        if data.sorted == "name/asc":
            data.sort_by_name(ascending=False)
            name_button.config(text=f"Path ↓")
        else:
            data.sort_by_name()
            name_button.config(text=f"Path ↑")
    elif field == "size":
        name_button.config(text=f"Path")
        if data.sorted == "size/asc":
            data.sort_by_size(ascending=False)
            size_button.config(text=f"Size ({data.total_size}) ↓")
        else:
            data.sort_by_size()
            size_button.config(text=f"Size ({data.total_size}) ↑")
    data.print()


# Widget creation
first_row = tk.Frame(root, bg=DARK_INKWELL)
second_row = tk.Frame(root, bg=DARK_INKWELL)
info_label = gui.CustomLabel(first_row, text=" Date: Null | Files: Null | Process time: Null")
search_entry = gui.CustomEntry(first_row)
search_button = gui.CustomButton(first_row, text="Search", width=SEARCH_BUTTON_WIDTH, command=search)
name_button = gui.CustomButton(second_row, text="Path", command=lambda: sort_by("name"))
size_button = gui.CustomButton(second_row, text="Size", width=SIZE_WIDTH, command=lambda: sort_by("size"))
search_info = gui.CustomLabel(first_row)
text_field = gui.TextField(root)

# Widget packing
first_row.pack(fill="x")
info_label.pack(side="left")
search_button.pack(side="right")
search_entry.pack(side="right")
search_info.pack(side="right")

second_row.pack(fill="x")
size_button.pack(side="left")
name_button.pack(side="left", fill="x", expand=True)
text_field.display()

# Start program
data = database.Database(output=text_field, search_output=search_info)
data.load_data()
data.print()

menubar = gui.CustomMenuBar(root, (gather_data, update_data, data.export_csv, data.export_txt, load_external_data, data.plot_data))
menubar.display()

# Key binds
root.bind("<Return>", lambda search_in_database: search())
root.bind("<Control-g>", lambda gather: gather_data())
root.bind("<Control-u>", lambda update: update_data())
root.bind("<Control-l>", lambda load_external: load_external_data())
root.bind("<Control-p>", lambda plot: data.plot_data())

if data.location:
    root.title(f"Database - {data.location}")

try:
    size_button.config(text=f"Size ({data.total_size})")
    info_label.config(
        text=f" Date: {data.date} | Files: {format(data.total_files, ',')} | Process time: {format_process_time(data.time)}")
    data.print()
finally:
    root.mainloop()
