import os
import datetime
import operator
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from tkinter.messagebox import showinfo


class File:
    """Class that holds file data."""

    def __init__(self, path: str, bytes: np.uint64):
        # Unsigned 64-bit integer. Can save an unreasonably large number, in just 8 bytes
        # Selected because an unsigned 32-bit can save up to 4gb. And there might be a problem
        self.path = path
        self.bytes = np.uint64(bytes)
        self.size = self.format_bytes(self.bytes)

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


class Database:
    """Class that contains data and all related methods. Parsing, updating, sorting and more."""
    encoding = "utf-8"
    date_format = "%d-%b-%Y"  # Date displayed on screen
    delimiter = ": | :"  # A wierd delimiter so that no random match occurs
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

    def dump_data(self) -> None:
        """
        Dumps session data to a .json. These are the attributes:
            location, date, total_files, total_bytes, time
        Dumps data to a .csv as follows:
            bytes{delimiter}path
            ...
        Encoding: "utf-8" by default."""

        with open(self.session_data_path, "w", encoding=self.encoding) as csv_file:
            csv_file.write(
                f"{self.location}{self.delimiter}{self.date}{self.delimiter}{len(self.data)}{self.delimiter}{self.total_bytes}{self.delimiter}{self.time}")

        with open(self.session_data_path, "w", encoding=self.encoding) as fp:
            json.dump({"location": self.location,
                       "date": self.date,
                       "file_count": len(self.data),
                       "total_bytes": self.total_bytes,
                       "time": self.time}, fp)

        with open(self.data_path, "w", encoding=self.encoding) as csv_file:
            for file in self.data:
                csv_file.write(f"{file.bytes}{self.delimiter}{file.path}\n")

    def parse_data(self) -> None:
        """Parses data and session data from their respective files."""
        try:
            with open(self.session_data_path, "r", encoding=self.encoding) as fp:
                session_data = json.load(fp)
            
            self.location = session_data["location"]
            self.date = session_data["date"]
            self.total_files = session_data["file_count"]
            self.total_bytes = session_data["total_bytes"]
            self.total_size = self.format_bytes(self.total_bytes)
            self.time = session_data["time"]

            # Parsing previous session data
            with open(self.data_path, "r", encoding=self.encoding) as csv_file:
                self.data.clear()
                lines = csv_file.readlines()
                for line in lines:
                    bytesize, path = line.strip("\n").split(self.delimiter)
                    self.data.append(File(path.strip("\n"), np.uint64(bytesize)))
            self.matches = self.data.copy()

        # Errors are handled by creating sample .json and .csv files and calling the method again
        except FileNotFoundError:
            with open(self.session_data_path, "w", encoding="utf-8")as fp:
                json.dump({"location": "/home/user/select/a/directory",
                            "date": "dd-mmm-yyyy",
                            "file_count": 1,
                            "total_bytes": 0,
                            "time": 0.00}, fp)
            with open(self.data_path, "w", encoding=self.encoding) as fp:
                fp.write(f"0{self.delimiter}No directory selected\n")
            self.parse_data()

        except ValueError:  # Not enough values to unpack
            with open(self.session_data_path, "w", encoding="utf-8")as fp:
                json.dump({"location": "/home/user/select/a/directory",
                            "date": "dd-mmm-yyyy",
                            "file_count": 1,
                            "total_bytes": 0,
                            "time": 0.00}, fp)
            with open(self.data_path, "w", encoding=self.encoding) as fp:
                fp.write(f"0{self.delimiter}No directory selected\n")
            self.parse_data()

        except IndexError:
            with open(self.session_data_path, "w", encoding="utf-8")as fp:
                json.dump({"location": "/home/user/select/a/directory",
                            "date": "dd-mmm-yyyy",
                            "file_count": 1,
                            "total_bytes": 0,
                            "time": 0.00}, fp)
            with open(self.data_path, "w", encoding=self.encoding) as fp:
                fp.write(f"0{self.delimiter}No directory selected\n")
            self.parse_data()

    def gather_data(self, dirpath: str) -> None:
        """Walks the path given to the end and returns data.
        Ignores FileNotFoundError.
        Data:
        [ File(), File(), ... ]"""
        self.data.clear()
        self.total_bytes = 0
        for path, dirs, files in os.walk(dirpath):
            for file in files:
                try:
                    filepath = os.path.join(path, file)
                    bytesize = os.path.getsize(filepath)
                    self.total_bytes += bytesize
                    self.data.append(File(filepath, np.uint64(bytesize)))
                except FileNotFoundError:
                    pass
        self.total_size = self.format_bytes(self.total_bytes)
        self.sorted = None

    def load_data(self, dirpath=None):
        if dirpath:
            ti = time.perf_counter()
            self.gather_data(dirpath)
            # Matches are the active data that is processed, helps sort while searching
            self.matches = self.data.copy()
            self.time = round(time.perf_counter() - ti, 2)
            self.date = datetime.datetime.now().strftime(self.date_format)
            self.total_files = len(self.data)
            self.location = dirpath
            self.dump_data()
        else:
            self.parse_data()
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
        if self.matches:
            self.output.clear()
            result = ""
            for file in self.matches:
                result += f"{file.size:>12}        {file.path}\n"
            self.output.write(result)
            # Updating search_info. If the whole database is displayed, then don't display match count
            if len(self.matches) == self.total_files:
                self.search_info.config(text="")
            else:
                self.search_info.config(
                    text=f"{format(len(self.matches), ',')} files ({self.format_bytes(self.matches_size)})")
        else:
            self.output.clear()
            self.output.write("No files found.")
            self.search_info.config(text="0 files")

    def export_txt(self) -> None:
        """Export as .txt"""
        export_path = os.path.join(os.getcwd(), "Exports",
                                   f"Export {self.location.replace(os.path.sep, '_')} {datetime.datetime.now().strftime('%d-%b-%Y')}.txt")
        with open(export_path, "w", encoding=self.encoding) as txt_file:
            txt_file.write(f"{self.date}\nTotal files: {self.total_files}\nTotal size: {self.total_size}\n\n")
            for file in self.data:
                txt_file.write(f"{file.size}     {file.path}")
        showinfo("Export", f"    Exported in Exports as\n{os.path.basename(export_path)}")

    def export_csv(self) -> None:
        """Exports data to a readable .csv file as follows:
            bytes{delimiter}path
            ...
        Encoding: "utf-8" by default."""
        export_path = os.path.join(os.getcwd(), "Exports",
                                   f"Export {self.location.replace(os.path.sep, '_')} {datetime.datetime.now().strftime('%d-%b-%Y')}.csv")
        with open(export_path, "w", encoding=self.encoding) as csv_file:
            for file in self.data:
                csv_file.write(f"{file.bytes}{self.delimiter}{file.path}\n")
        showinfo("Export", f"    Exported in Exports as\n{os.path.basename(export_path)}")

    def load_external_data(self, filepath: str) -> bool:
        """Load data saved in .csv format."""
        try:

            with open(filepath, "r", encoding=self.encoding) as csv_file:
                self.data.clear()
                lines = csv_file.readlines()
                for line in lines:
                    bytesize, path = line.strip("\n").split(self.delimiter)
                    self.data.append(File(path.strip("\n"), np.uint64(bytesize)))
            self.matches = self.data.copy()

            self.location = "Exported data"
            self.date = "d?-mm?-yyy?"
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
                self.matches.sort(key=operator.attrgetter("path"))
            self.sorted = "name/asc"
        else:
            if self.sorted == "name/asc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("path"), reverse=True)
            self.sorted = "name/desc"

    def sort_by_size(self, ascending=True) -> None:
        """Sorts matches by size. Ascending by default.
            If the data is already sorted, then it reverses it."""
        if ascending:
            if self.sorted == "size/desc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("bytes"))
            self.sorted = "size/asc"
        else:
            if self.sorted == "size/asc":
                self.matches.reverse()
            else:
                self.matches.sort(key=operator.attrgetter("bytes"), reverse=True)
            self.sorted = "size/desc"

    def plot_data(self):
        """Plots file size in mb from self.matches."""
        MB = 1 << 20
        y_axis = [np.float32(file.bytes / MB) for file in self.matches]
        plt.plot(y_axis, color="black")
        y_axis_mean = sum(y_axis) / len(y_axis)
        plt.plot([x for x in range(len(y_axis) + 1)], [y_axis_mean for y in range(len(y_axis) + 1)], color="red",
                 label=f"Mean Size: {round(y_axis_mean, 3)} MB")
        plt.title(f"Search Results Size Distribution")
        plt.xlabel("Files")
        plt.ylabel("Mega bytes")
        plt.xlim(0, len(y_axis))
        plt.xticks(np.arange(0, len(y_axis), len(y_axis) // 4))
        plt.ylim(0, max(y_axis) * 1.1)
        plt.yticks(np.arange(min(y_axis), max(y_axis) + 0.1, max(y_axis) / 15))
        plt.legend()
        plt.show()
