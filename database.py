import datetime
import operator
import json
import csv
import time
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class File:
    """Class that holds file data."""

    def __init__(self, path: str, bytes: int, size: str):
        self.path = path
        self.bytes = bytes
        self.size = size


    def as_csv_row(self) -> list:
        """Returns the data as a csv row [path, bytes] (intended for csv.writer.writerow())"""
        return [self.path, self.bytes]


class Database:
    """Class that contains data and all related methods. Parsing, updating, sorting and more."""
    encoding = "utf-8"
    date_format = "%d-%b-%Y"  # Date displayed on screen
    session_data_path = os.path.join("Data", "session_data.json")
    data_path = os.path.join("Data", "data.csv")


    def __init__(self, *, output, search_output):
        """Getting output screens and initializing variables."""
        self.output = output
        self.search_info = search_output
        self.matches_size = 0
        self.location = ""
        self.date = ""
        self.total_files = 0
        self.total_bytes = 0
        self.total_size = ""
        self.data = []
        self.matches = []
        self.time = 0
        self.sorted = None


    def save_data_as_csv(self) -> None:
        """Dumps data to a .csv as: path,bytes
        Encoding: "utf-8" by default."""
        
        with open(self.data_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                for file in self.data:
                    csv_writer.writerow(file.as_csv_row())


    def load_data_from_csv(self) -> None:
        """Parses data from csv format.
        Handles errors by creating a sample file, and calling the method again."""

        try:
            error_occured = False

            with open(self.data_path, "r", encoding=self.encoding) as fp:
                csv_reader = csv.reader(fp)
                self.data.clear()
                for row in csv_reader:
                    bytesize = int(row[1])
                    self.data.append(File(row[0], bytesize, self.format_bytes(bytesize)))
        
        except FileNotFoundError:
            error_occured = True
        except ValueError:  # Not enough values to unpack
            error_occured = True
        except IndexError:
            error_occured = True

        if error_occured:
            with open(self.data_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                csv_writer.writerow(["No directory selected", 0])
            self.load_data_from_csv()


    def save_session_data_as_json(self) -> None:
        """Dumps session data to a .json. These are the attributes:
        location, date, total_files, total_bytes, time"""

        with open(self.session_data_path, "w", encoding=self.encoding) as fp:
            json.dump({"location": self.location,
                       "date": self.date,
                       "file_count": len(self.data),
                       "total_bytes": self.total_bytes,
                       "time": self.time}, fp)


    def load_session_data_from_json(self) -> None:
        """Parses session data from json format.
        Handles errors by creating a sample file, and calling the method again."""

        try:
            error_occured = False

            with open(self.session_data_path, "r", encoding=self.encoding) as fp:
                session_data = json.load(fp)
                
                self.location = session_data["location"]
                self.date = session_data["date"]
                self.total_files = session_data["file_count"]
                self.total_bytes = session_data["total_bytes"]
                self.total_size = self.format_bytes(self.total_bytes)
                self.time = session_data["time"]
        except FileNotFoundError:
            error_occured = True
        except ValueError:  # Not enough values to unpack
            error_occured = True
        except IndexError:
            error_occured = True

        if error_occured:
            with open(self.session_data_path, "w", encoding="utf-8")as fp:
                json.dump({"location": "None",
                            "date": "dd-mmm-yyyy",
                            "file_count": 0,
                            "total_bytes": 0,
                            "time": 0.00}, fp)
            self.load_session_data_from_json()


    def gather_data(self, dirpath: str) -> None:
        """Walks the path given to the end, gathers and loads self.data with new data.
        Ignores FileNotFoundError and PermissionError.
        Data:
        [ File(), File(), ... ]"""
        self.data.clear()
        self.total_bytes = 0
        for path, dirs, files in os.walk(dirpath):
            for file in files:
                try:
                    filepath = os.path.join(path, file)

                    # if a comma is found in a pathname, it will mess up the csv delimiter. ignore these paths
                    if "," in filepath:
                        continue

                    bytesize = os.path.getsize(filepath)
                    self.total_bytes += bytesize
                    self.data.append(File(filepath, int(bytesize), self.format_bytes(int(bytesize))))
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue
        self.total_size = self.format_bytes(self.total_bytes)
        self.sorted = None


    def load_data(self, dirpath: str=None):
        """Load data method, either gathers new data from dirpath and saves them,
        or loads previous data from their respective files."""
        if dirpath:
            ti = time.perf_counter()
            self.gather_data(dirpath)
            # Matches are the active data that is processed, helps sort while searching
            self.matches = self.data.copy()
            self.time = round(time.perf_counter() - ti, 2)
            self.date = datetime.datetime.now().strftime(self.date_format)
            self.total_files = len(self.data)
            self.location = dirpath
            self.save_session_data_as_json()
            self.save_data_as_csv()
        else:
            self.load_session_data_from_json()
            self.load_data_from_csv()
            self.matches = self.data.copy()
        self.sorted = None


    @staticmethod
    def format_bytes(bytes: int) -> str:
        """Converts bytes to a readable string format."""
        TB = 1_099_511_627_776  # 1 << 40 or 2 ** 40
        GB = 1_073_741_824  # 1 << 30 or 2 ** 30
        MB = 1_048_576  # 1 << 20 or 2 ** 20
        KB = 1_024  # 1 << 10 or 2 ** 10
        if bytes / TB >= 1:
            return f"{round(bytes / TB, 3)} TB"
        elif bytes / GB >= 1:
            return f"{round(bytes / GB, 3)} GB"
        elif bytes / MB >= 1:
            return f"{round(bytes / MB, 3)} MB"
        elif bytes / KB >= 1:
            return f"{round(bytes / KB, 3)} KB"
        return f"{round(bytes, 3)} Bytes"


    @staticmethod
    def parse_bytes(text: str) -> int:
        """Parses and converts bytes strings into bytes. Returns bytes as integers."""
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
        """Performs linear search, updates self.matches, their size and calls prints the results."""
        self.sorted = None
        if not key:
            self.matches = self.data.copy()
            self.print()
            return
        # Clear the screen, to fill with matches
        self.output.clear()

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
        elif key.startswith("$"):
            key = key[1:]
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
                            if key in self.data[i].path
                            or key in self.data[i].size]

        # Key #2 search:
        if key2:
            n = len(self.matches)
            prev_matches = list(self.matches.copy())
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
            elif key2.startswith("$"):
                key2 = key2[1:]
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
                                if key2 in prev_matches[i].path
                                or key2 in prev_matches[i].size]

        # Calculate the size of matches in bytes
        self.matches_size = 0
        for match in self.matches:
            self.matches_size += match.bytes

        self.print()


    def print(self) -> None:
        """Print all the matches to GUI screen. If search is not active, then print all the data.
        In case of search, print total matches and their size in search_info label.
        Takes care of displaying data on screen."""
        
        self.output.clear()
        if self.matches:
            result = ""
            for file in self.matches:
                result += f"{file.size:>12}        {file.path}\n"
            self.output.write(result)
            # Updating search_info. If the whole database is displayed, then don't display match count
            if len(self.matches) == self.total_files:
                self.search_info.config(text="")
            else:
                self.search_info.config(
                    text=f"{len(self.matches):,} files ({self.format_bytes(self.matches_size)})")
        else:
            self.output.write("No files found.")
            self.search_info.config(text="0 files")


    def export_as(self, kind: str) -> None:
        """Exports the data as <kind>.
        @kind values: csv text excel"""

        # extensionless name
        export_path = os.path.join(os.getcwd(), "Exports",
            f"Export {self.location.replace(os.path.sep, '_')}_{datetime.datetime.now().strftime('%d-%b-%Y')}")
        
        if kind == "text":
            export_path += ".txt"
            with open(export_path, "w", encoding=self.encoding) as txt_file:
                txt_file.write(f"{self.date}\nTotal files: {self.total_files}\nTotal size: {self.total_size}\n\n")
                for file in self.data:
                    txt_file.write(f"{file.size}     {file.path}")

        elif kind == "csv":
            export_path += ".csv"
            with open(export_path, "w", encoding=self.encoding) as fp:
                csv_writer = csv.writer(fp)
                for file in self.data:
                    csv_writer.writerow(file.as_csv_row())

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
            df.set_index("Path", inplace=True)
            df.to_excel(export_path)
        
        elif kind == "json":
            export_path += ".json"
            # dictionary with a single key named data
            json_data_dict = {"data": []}
            for file in self.data:
                json_data_dict["data"].append([file.path, file.bytes, file.size])
            with open(export_path, "w", encoding=self.encoding) as fp:
                json.dump(json_data_dict, fp, indent=4)


    def import_data(self, filepath: str) -> bool:
        """Import data saved in .csv format."""
        try:

            with open(filepath, "r", encoding=self.encoding) as fp:
                csv_reader = csv.reader(fp)
                self.data.clear()
                for row in csv_reader:
                    bytesize = int(row[1])
                    self.data.append(File(row[0], bytesize, self.format_bytes(bytesize)))
            self.matches = self.data.copy()

            self.location = "Imported data"
            self.date = "unknown"
            self.total_files = len(self.data)
            self.total_bytes = 0
            self.time = 0
            self.sorted = None
            return True
        except FileNotFoundError:
            return False
        except ValueError:
            return False


    def sort_by_name(self, ascending=True) -> None:
        """Sorts matches by name. Ascending by default.
            If the data is already sorted, then it reverses it."""

        if ascending:
            if self.sorted == "name/desc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("path", "bytes"))
            self.sorted = "name/asc"
        else:
            if self.sorted == "name/asc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("path", "bytes"), reverse=True)
            self.sorted = "name/desc"


    def sort_by_size(self, ascending=True) -> None:
        """Sorts matches by size. Ascending by default.
            If the data is already sorted, then it reverses it."""
        if ascending:
            if self.sorted == "size/desc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("bytes", "path"))
            self.sorted = "size/asc"
        else:
            if self.sorted == "size/asc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("bytes", "path"), reverse=True)
            self.sorted = "size/desc"


    def plot_data(self):
        """Scatter plots bytes of each file in self.matches. Logarithmic y-scale."""
        if len(self.matches) < 2: # Plotting just one value is obsolete and raises a DivisionByZeroError
            return
        
        x_axis = np.arange(len(self.matches))
        y_axis = [np.float32(file.bytes) for file in self.matches]
        
        plt.style.use("ggplot")
        
        plt.scatter(x_axis, y_axis, s=2, color="royalblue",edgecolor="black")
        y_mean = np.mean(y_axis)
        y_median = np.median(y_axis)
        plt.plot(x_axis, np.full_like(x_axis, y_mean), color="red",
                label=f"Mean = {self.format_bytes(y_mean)}", linewidth=1)
        plt.plot(x_axis, np.full_like(x_axis, y_median), color="green",
                label=f"Median = {self.format_bytes(y_median)}", linewidth=1)
        plt.yscale("log")
        plt.title("Search Results")
        plt.xlabel("File")
        plt.ylabel("Bytes")
        plt.legend()
        plt.tight_layout()
        plt.show()
