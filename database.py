import datetime
import time
import operator
import json
import csv
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class File:
    """Class that holds each file data."""

    def __init__(self, path: str, bytes: int, size: str):
        self.path = path
        self.bytes = bytes
        self.size = size


class Database:
    """Class that behaves like a database.
    Holds the data. Saves them, loads them, gathers new ones, sorts them,
    searches in them, plots them, imports external ones.
    The data is saved in a list, as File objects, and when asked, a list of matches is returned.
    The data itself doesn't change in the database, a copy is saved in self.matches.
    This copy is then being sorted or searched within.
    Apart from the data, some metadata is also saved (location, total bytes/size, process time)
    Default encoding: utf-8
    """
    encoding = "utf-8"
    date_format = "%d-%b-%Y"
    data_path = os.path.join("Data", "data.csv")


    def __init__(self) -> None:

        # metadata
        self.location = ""
        self.date = ""
        self.time = ""
        self.total_files = 0
        self.total_bytes = 0

        # data and data related variables
        self.total_size = ""
        self.data = () # data is saved here as a tuple, and never touched again, only accessed
        self.matches = [] # this is a list of the data, and it's the one being processed (sorted, searched)
        self.matches_bytes = 0
        self.sorted = None


    def save_data(self) -> None:
        """Dumps data to a .csv as: path,bytes
        Encoding: "utf-8" by default."""
        
        with open(self.data_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                
                # First row: Metadata
                metadata_row = [self.location, self.date, self.time, self.total_files, self.total_bytes]
                csv_writer.writerow(metadata_row)
                
                # Data
                for file in self.data:
                    data_row = [file.path.replace(self.location, "~"), file.bytes]
                    csv_writer.writerow(data_row)


    def load_data(self) -> None:
        """Parses data and metadata from csv format.
        Handles errors by creating a sample file, and calling the method again."""

        try:
            error_occured = False

            with open(self.data_path, "r", encoding=self.encoding) as fp:
                csv_reader = csv.reader(fp)
                self.matches.clear()
                                
                # Parsing metadata from the first row
                metadata = fp.readline().rstrip("\n").split(",")
                # Note: .readline() counts as a file iteration. no next(csv_reader) is redundant
                self.location = metadata[0]
                self.date = metadata[1]
                self.time = metadata[2]
                self.total_files = int(metadata[3])
                self.total_bytes = int(metadata[4])

                # Parsing data
                for row in csv_reader:
                    # filepath = row[0].replace("~", self.location) # expanding ~
                    filepath = row[0]
                    bytesize = int(row[1])
                    self.matches.append(File(filepath, bytesize, self.format_bytes(bytesize)))
            self.data = tuple(self.matches)

        except FileNotFoundError:
            error_occured = True
        except ValueError: # Not enough values to unpack
            error_occured = True
        except IndexError:
            error_occured = True

        if error_occured:
            with open(self.data_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                csv_writer.writerow([self.location, self.date, self.time, self.total_files, self.total_bytes])
                csv_writer.writerow(["No directory selected", 0])
            self.load_data()

        return bool(self.matches)


    def gather_data(self, dirpath: str) -> None:
        """Walks the path given to the end, gathers and loads self.matches with new data.
        When the process ends, casts the self.matches to tuple (self.data)
        Gathers new metadata and saves all of them.
        Ignores FileNotFoundError and PermissionError.
        Final data saved as:
        ( File(), File(), ... )"""

        def format_process_time(process_time: int) -> str:
            """self.time is formatted and saved as a string."""
            m, s = divmod(process_time, 60)
            s = round(s, 2)
            return f"{s} s" if not m else f"{int(m)}m {s}s"
        
        self.matches.clear()
        self.total_bytes = 0
        self.sorted = None

        # Gather new data
        ti = time.perf_counter()
        for path, dirs, files in os.walk(dirpath):
            for file in files:
                try:
                    filepath = os.path.join(path, file)

                    # TODO: files with, are currently ignored. Include them
                    # if a comma is found in a pathname, it will mess up the csv delimiter. ignore these paths
                    if "," in filepath:
                        continue

                    bytesize = os.path.getsize(filepath)
                    self.total_bytes += bytesize
                    self.matches.append(File(filepath, int(bytesize), self.format_bytes(int(bytesize))))
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue
        self.data = tuple(self.matches)
        final_time = round(time.perf_counter() - ti, 2)
        
        # Gather metadata
        self.matches_bytes = self.total_bytes
        self.location = dirpath
        self.date = datetime.datetime.now().strftime(self.date_format)
        self.time = format_process_time(final_time)
        self.total_files = len(self.data)
        self.total_size = self.format_bytes(self.total_bytes)

        self.save_data()


    @staticmethod
    def format_bytes(bytes: int) -> str:
        """Converts bytes to a readable string format."""
        TB = 1_099_511_627_776  # 1 << 40 or 2 ** 40
        GB = 1_073_741_824  # 1 << 30 or 2 ** 30
        MB = 1_048_576  # 1 << 20 or 2 ** 20
        KB = 1_024  # 1 << 10 or 2 ** 10
        if bytes / TB >= 1:
            return f"{round(bytes / TB, 3):.3f} TB"
        elif bytes / GB >= 1:
            return f"{round(bytes / GB, 3):.3f} GB"
        elif bytes / MB >= 1:
            return f"{round(bytes / MB, 3):.3f} MB"
        elif bytes / KB >= 1:
            return f"{round(bytes / KB, 3):.3f} KB"
        return f"{bytes} Bytes"


    @staticmethod
    def parse_bytes(text: str) -> int:
        """Parses and converts bytes strings into bytes. Returns bytes as integers.
        This function is used to covert human readable bytes from the search bar, into bytes."""
        text = text.lower().replace(" ", "")
        if text.endswith("kb"):
            return int(float(text[:-2]) * 1024)
        elif text.endswith("mb"):
            return int(float(text[:-2]) * (1 << 20))
        elif text.endswith("gb"):
            return int(float(text[:-2]) * (1 << 30))
        elif text.endswith("tb"):
            return int(float(text[:-2]) * (1 << 40))
        elif text.endswith("bytes") or text.endswith("b") or text.endswith("byte"):
            return int(text.replace("b", "").replace("yte", "").replace("s", ""))


    def search(self, key: str) -> None:
        """Performs linear search, updates self.matches and their size."""
        self.sorted = None
        if not key:
            self.matches = list(self.data)
            self.matches_bytes = self.total_bytes
            return

        n = self.total_files - 1
        self.matches.clear()

        try:
            key, key2 = key.split(" && ")
        except ValueError:
            key2 = ""

        # Filtered size search
        if key.startswith(">"):
            if key.startswith(">="):
                size_filter = self.parse_bytes(key.replace(">=", ""))
                self.matches = [self.data[i] for i in range(n) if self.data[i].bytes >= size_filter]
            else:
                size_filter = self.parse_bytes(key.replace(">", ""))
                self.matches = [self.data[i] for i in range(n) if self.data[i].bytes > size_filter]
        elif key.startswith("<"):
            if key.startswith("<="):
                size_filter = self.parse_bytes(key.replace("<=", ""))
                self.matches = [self.data[i] for i in range(n) if self.data[i].bytes <= size_filter]
            else:
                size_filter = self.parse_bytes(key.replace("<", ""))
                self.matches = [self.data[i] for i in range(n) if self.data[i].bytes < size_filter]
        # RegEx name search
        elif key.startswith("^"):
            key = key[1:]
            self.matches = [self.data[i] for i in range(n) if self.data[i].path.startswith(key)]
        elif key.endswith("$"):
            key = key[:-1]
            self.matches = [self.data[i] for i in range(n) if self.data[i].path.endswith(key)]
        # Case insensitive search
        elif key.startswith("%") and key.endswith("%"):
            key = key[1:-2].lower()
            self.matches = [self.data[i] for i in range(n) if key in self.data[i].path.lower()]
        # Not in name search
        elif key.startswith("!"):
            key = key[1:]
            self.matches = [self.data[i] for i in range(n) if key not in self.data[i].path]
        # Basename search
        elif key.startswith("basename: ") or key2.startswith("Basename: "):
            key = key[10:]
            self.matches = [self.data[i] for i in range(n) if key in os.path.basename(self.data[i].path)]
        # Full search
        else:
            self.matches = [self.data[i] for i in range(n)
            if key in self.data[i].path or key in self.data[i].size]

        # Key #2 search:
        if key2:
            n = len(self.matches)
            prev_matches = self.matches.copy()
            self.matches.clear()
            # Filtered size search
            if key2.startswith(">"):
                if key2.startswith(">="):
                    size_filter = self.parse_bytes(key2.replace(">=", ""))
                    self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].bytes >= size_filter]
                else:
                    size_filter = self.parse_bytes(key2.replace(">", ""))
                    self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].bytes > size_filter]
            elif key2.startswith("<"):
                if key2.startswith("<="):
                    size_filter = self.parse_bytes(key2.replace("<=", ""))
                    self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].bytes <= size_filter]
                else:
                    size_filter = self.parse_bytes(key2.replace("<", ""))
                    self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].bytes < size_filter]
            # RegEx name search
            elif key2.startswith("^"):
                key2 = key2[1:]
                self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].path.startswith(key2)]
            elif key2.endswith("$"):
                key2 = key2[:-1]
                self.matches = [prev_matches[i] for i in range(n) if prev_matches[i].path.endswith(key2)]
            # Case insensitive search
            elif key2.startswith("%") and key2.endswith("%"):
                key2 = key2[1:-2].lower()
                self.matches = [prev_matches[i] for i in range(n) if key2 in self.matches[i].path.lower()]
            # Not in name search
            elif key2.startswith("!"):
                key2 = key2[1:]
                self.matches = [prev_matches[i] for i in range(n) if key2 not in self.matches[i].path]
            # Basename search
            elif key2.startswith("basename: ") or key2.startswith("Basename: "):
                key2 = key2[10:]
                self.matches = [prev_matches[i] for i in range(n) if key2 in os.path.basename(self.matches[i].path)]
            # Full search
            else:
                self.matches = [prev_matches[i] for i in range(n)
                if key2 in prev_matches[i].path or key2 in prev_matches[i].size]

        # Calculate the size of matches in bytes
        self.matches_bytes = 0
        for match in self.matches:
            self.matches_bytes += match.bytes


    def export_as(self, kind: str) -> None:
        """Exports the data as <kind>.
        @kind values: csv text excel json"""

        # extensionless name
        export_path = os.path.join(os.getcwd(), "Exports",
            f"Export {self.location.replace(os.path.sep, '_')}_{datetime.datetime.now().strftime(self.date_format)}")
        
        if kind == "text":
            export_path += ".txt"
            with open(export_path, "w", encoding=self.encoding) as txt_file:
                txt_file.write(f"{self.date}\nTotal files: {self.total_files}\nTotal size: {self.total_size}\n\n")
                for file in self.data:
                    txt_file.write(f"{file.size}{' ' * 8}{file.path}\n")

        elif kind == "csv":
            export_path += ".csv"
            with open(export_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                csv_writer.writerow([self.location, self.date, self.time, self.total_files, self.total_bytes])
                for file in self.data:
                    row = [file.path.replace(self.location, "~"), file.bytes]
                    csv_writer.writerow(row)

        elif kind == "excel":
            export_path += ".xlsx"
            # convert the data to a dictionary, and then to a pandas.DataFrame, then export as excel.
            excel_data_dict = {"path": [], "bytes": [], "size": []}
            for file in self.data:
                excel_data_dict["path"].append(file.path)
                excel_data_dict["bytes"].append(file.bytes)
                excel_data_dict["size"].append(file.size)

            df = pd.DataFrame(excel_data_dict)
            df.columns = ["Path", "Bytes", "Size"]
            df.to_excel(export_path, sheet_name=os.path.basename(self.location), index=False)
        
        elif kind == "json":
            export_path += ".json"
            # dictionary with a single key named data
            json_data_dict = {"data": []}
            for file in self.data:
                json_data_dict["data"].append([file.path, file.bytes, file.size])
            with open(export_path, "w", encoding=self.encoding) as fp:
                json.dump(json_data_dict, fp, indent=4)


    def import_data(self, filepath: str) -> bool:
        """Import data/metadata saved in .csv format.
        Returns True/False depending on the success of the process."""
        try:

            with open(filepath, "r", encoding=self.encoding) as fp:
                csv_reader = csv.reader(fp)
                self.matches.clear()
                                
                # Parsing metadata from the first row
                metadata = fp.readline().rstrip("\n").split(",")
                # Note: .readline() counts as a file iteration. no next(csv_reader) is redundant
                self.location = metadata[0]
                self.date = metadata[1]
                self.time = metadata[2]
                self.total_files = int(metadata[3])
                self.total_bytes = int(metadata[4])

                # Parsing data
                for row in csv_reader:
                    # filepath = row[0].replace("~", self.location) # expanding ~
                    filepath = row[0]
                    bytesize = int(row[1])
                    self.matches.append(File(filepath, bytesize, self.format_bytes(bytesize)))
            self.data = tuple(self.matches)
            
            return True
        except FileNotFoundError:
            return False
        except ValueError:
            return False


    def sort_by_size(self) -> None:
        """Sorts matches by size. If matches aren't sorted, sorts ascending first, otherwise descending.
        If the data is already sorted, then it reverses it."""

        if self.sorted == "size/asc":
            self.matches.reverse()
            self.sorted = "size/desc"
        else:
            if self.sorted == "size/desc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("bytes", "path"))
            self.sorted = "size/asc"


    def sort_by_name(self) -> None:
        """Sorts matches by name. If matches aren't sorted, sorts ascending first, otherwise descending.
        If the data is already sorted, then it reverses it."""

        if self.sorted == "name/asc":
            self.matches.reverse()
            self.sorted = "name/desc"
        else:
            if self.sorted == "name/desc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("path", "bytes"))
            self.sorted = "name/asc"


    def plot_data(self):
        """Creates a size histogram of self.data.
        This is done manually and plotted as barchart due to the byte scale difference."""
        if len(self.matches) < 2: # Plotting just one value is obsolete and raises a DivisionByZeroError
            return
        
        def insert_labels(bars) -> None:
            """Insert a text label above each bar in the barchart given."""
            for bar in bars:
                height = bar.get_height()
                plt.annotate(f"{height:,}", xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points", ha="center", va="bottom")

        bytesizes = [file.bytes for file in self.data]
        
        x_axis = ["0b - 0.5Kb", "0.5Kb - 1Kb",
                "1Kb - 0.5Mb", "0.5Mb - 1Mb",
                "1Mb - 0.5Gb", "0.5Gb - 1Gb", ">1Gb"]

        # The 7 groups and their bytesize filters
        g1 = g2 = g3 = g4 = g5 = g6 = g7 = 0
        g2_filter = 1024
        g1_filter = g2_filter // 2

        g4_filter = 1024 ** 2
        g3_filter = g4_filter // 2

        g6_filter = 1024 ** 3
        g5_filter = g6_filter // 2
        
        for bytesize in bytesizes:
            if bytesize < g1_filter:
                g1 += 1
            elif bytesize < g2_filter:
                g2 += 1
            elif bytesize < g3_filter:
                g3 += 1
            elif bytesize < g4_filter:
                g4 += 1
            elif bytesize < g5_filter:
                g5 += 1
            elif bytesize < g6_filter:
                g6 += 1
            else:
                g7 += 1
        
        y_axis = [g1, g2, g3, g4, g5, g6, g7]
        
        plt.grid(which="major", axis="y", linestyle=":", zorder=0)
        bars = plt.bar(x_axis, y_axis, color="royalblue", edgecolor="black", zorder=3)
        insert_labels(bars)

        plt.title("Size Histogram")
        plt.ylabel("Files")
        plt.tight_layout()
        plt.show()


    def get_data(self) -> tuple:
        """Returns (matches, matches_size)."""
        return self.matches, self.format_bytes(self.matches_bytes)


    def get_metadata(self) -> tuple:
        """Returns (location, date, time, total_files, total_size)"""
        self.total_size = self.format_bytes(self.total_bytes)
        return self.location, self.date, self.time, self.total_files, self.total_size


    def is_sliced(self) -> bool:
        """Boolean function that compares matches with the data.
        If True, then display search output. If not, then clear.
        If self.matches is slice of self.data, then a search has taken place, so search info must be displayed."""
        return len(self.matches) != self.total_files
