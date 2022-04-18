import pymongo
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import threading
import datetime
import time
import os


class Database:
    """Class that behaves like a database.
    Loads the data from MongoDB. Gathers and stores new ones. Sorts them, searches in them, exports them as different
    file types or as a mongodump, import an external mongodump.
    The data is saved as a pandas.DataFrame.
    The data itself doesn't change in the database, a copy is saved in self.matches to be processed.
    Apart from the data, some metadata about the gather session is also saved.
    Default encoding: utf-8"""
    
    encoding = "utf-8"
    date_format = "%d-%b-%Y"
    conn_path = "mongodb://127.0.0.1:27017"


    def __init__(self) -> None:

        # Metadata
        self.metadata = {
            "location": "",
            "date": "",
            "time": "",
            "total_files": 0,
            "total_bytes": 0
        }

        # Data
        self.data = pd.DataFrame({"path": [], "bytes": [], "size": []}) # self.data is stored and only accessed
        self.matches = self.data.copy() # self.matches is the one being processed (sorted, searched)

        # Data related attributes
        self.total_size = ""
        self.matches_bytes = 0
        self.sorted = None


    def store_data(self) -> None:
        """Stores metadata and data to a MongoDB database.
        The full path is saved in the database. And it is shortened when loaded into memory.
        Opens and closes the connection at the end.
        This method is calle in a thread. When it finishes, it prints to stdout to avoid errors."""

        # Data preparation
        data_rows = []
        for i in range(self.metadata["total_files"]):
            data_rows.append({
                "path": self.data.iloc[i]["path"].replace("~", self.metadata["location"]),
                "bytes": int(self.data.iloc[i]["bytes"]) # np.int64 cannot be encoded by mongodb, so cast it to int
                })
        
        # Opening a connection to save the metadata/data
        conn = pymongo.MongoClient(self.conn_path)
        mydb = conn["fsv"]

        metadata_col = mydb["metadata"]
        data_col = mydb["data"]
        
        # Delete old and insert new metadata/data
        # Metadata isn't updated because this way errors can be avoided with future changes
        metadata_col.delete_many({})
        data_col.delete_many({})

        metadata_col.insert_one(self.metadata)
        data_col.insert_many(data_rows)

        conn.close()
        print("Thread closed. Data stored successfully!")


    def load_data(self) -> None:
        """Parses metadata and data from a MongoDB database.
        The path is shortened when parsed. self.metadata["location"] is replaced by "~".
        Opens and closes the connection at the end."""

        # Opening mongodb connection, reading data and closing it
        conn = pymongo.MongoClient(self.conn_path)
        mydb = conn["fsv"]

        metadata_col = mydb["metadata"]
        data_col = mydb["data"]

        metadata = metadata_col.find_one({},{"_id": 0})
        data = data_col.find({},{"_id": 0})
        
        conn.close()

        # Metadata/Data parsing
        try:
            self.metadata["location"] = metadata["location"]
            self.metadata["date"] = metadata["date"]
            self.metadata["time"] = metadata["time"]
            self.metadata["total_files"] = metadata["total_files"]
            self.metadata["total_bytes"] = metadata["total_bytes"]

            _data_dict = {"path": [], "bytes": [], "size": []}

            for row in data:
                filepath = row["path"].replace(self.metadata["location"], "~")
                bytesize = row["bytes"]

                _data_dict["path"].append(filepath)
                _data_dict["bytes"].append(bytesize)
                _data_dict["size"].append(self.format_bytes(bytesize))

            self.matches = pd.DataFrame(_data_dict)
            self.data = self.matches.copy()
        except TypeError:
            # Raised when the database is empty
            return False

        return True


    def gather_data(self, dirpath: str) -> None:
        """Walks the path given to the end, gathers and stores new data in a temporary dictionary.
        When the process ends, converts and saves the data as a DataFrame (Both self.data and self.matches)
        Gathers new metadata and calls self.store_data().
        Ignores FileNotFoundError and PermissionError."""

        def format_process_time(process_time: int) -> str:
            """self.metadata["time"] is formatted and saved as a string."""
            m, s = divmod(process_time, 60)
            s = round(s, 2)
            return f"{s} s" if not m else f"{int(m)}m {s}s"
        
        self.sorted = None
        self.metadata["total_bytes"] = 0

        _data_dict = {"path": [], "bytes": [], "size": []}

        # Gather new data
        ti = time.perf_counter()
        for path, dirs, files in os.walk(dirpath):
            for file in files:
                try:
                    filepath = os.path.join(path, file)
                    bytesize = os.path.getsize(filepath)
                    self.metadata["total_bytes"] += bytesize
                    _data_dict["path"].append(filepath.replace(dirpath, "~"))
                    _data_dict["bytes"].append(bytesize)
                    _data_dict["size"].append(self.format_bytes(bytesize))
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue

        self.matches = pd.DataFrame(_data_dict)
        self.data = self.matches.copy()


        final_time = round(time.perf_counter() - ti, 2)
        
        # Gather metadata
        self.matches_bytes = self.metadata["total_bytes"]
        self.metadata["location"] = dirpath
        self.metadata["date"] = datetime.datetime.now().strftime(self.date_format)
        self.metadata["time"] = format_process_time(final_time)
        self.metadata["total_files"] = self.data.shape[0]
        self.total_size = self.format_bytes(self.metadata["total_bytes"])

        # Saving data to MongoDB is time consuming. So it's done using a thread
        threading.Thread(target=self.store_data).start()
        print("Opening thread. Storing data to MongoDB. Do not interrupt...")


    @staticmethod
    def format_bytes(bytes: int) -> str:
        """Converts bytes to a readable string format."""
        
        TB = 1_099_511_627_776
        GB = 1_073_741_824
        MB = 1_048_576
        KB = 1_024
        
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
        """Parses and converts byte strings into bytes. Returns bytes as integers.
        This function is used to covert human readable bytes from the search bar, into bytes."""
        
        TB = 1_099_511_627_776
        GB = 1_073_741_824
        MB = 1_048_576
        KB = 1_024
        
        text = text.lower().replace(" ", "")
        if text.endswith("kb"):
            return int(float(text[:-2]) * KB)
        elif text.endswith("mb"):
            return int(float(text[:-2]) * MB)
        elif text.endswith("gb"):
            return int(float(text[:-2]) * GB)
        elif text.endswith("tb"):
            return int(float(text[:-2]) * TB)
        elif text.endswith("b") or "byte" in text:
            return int(text.replace("b", "").replace("yte", "").replace("s", ""))


    def search(self, query: str) -> None:
        """Performs linear search, updates self.matches and self.matches_bytes.
        query is broken down to its' keys (if there are multiple)."""
        self.sorted = None
        self.matches = self.data.copy()
        self.matches_bytes = self.metadata["total_bytes"]
        
        if not query:
            return

        queries = query.split(" && ")

        for key in queries:
            
            # Filtered size search
            if key.startswith(">"):
                if key.startswith(">="):
                    size_filter = self.parse_bytes(key[2:])
                    self.matches = self.matches.loc[self.matches["bytes"] >= size_filter]
                else:
                    size_filter = self.parse_bytes(key[1:])
                    self.matches = self.matches.loc[self.matches["bytes"] > size_filter]
            elif key.startswith("<"):
                if key.startswith("<="):
                    size_filter = self.parse_bytes(key[2:])
                    self.matches = self.matches.loc[self.matches["bytes"] <= size_filter]
                else:
                    size_filter = self.parse_bytes(key[1:])
                    self.matches = self.matches.loc[self.matches["bytes"] < size_filter]
            
            # RegEx name search
            elif key.startswith("^"):
                key = key[1:]
                self.matches = self.matches.loc[self.matches["path"].str.startswith(key)]
            elif key.endswith("$"):
                key = key[:-1]
                self.matches = self.matches.loc[self.matches["path"].str.endswith(key)]
            
            # Case insensitive search
            elif key.startswith("%") and key.endswith("%"):
                key = key[1:-2]
                self.matches = self.matches.loc[self.matches["path"].str.contains(key, case=False)]
            
            # Not in name search
            elif key.startswith("!"):
                key = key[1:]
                self.matches = self.matches.loc[~self.matches["path"].str.contains(key)]
                        
            # Full search
            else:
                self.matches = self.matches.loc[self.matches["path"].str.contains(key)]

        # Calculate the size of matches in bytes
        self.matches_bytes = self.matches["bytes"].sum()


    def export_as(self, kind: str) -> None:
        """Exports the data as @kind.
        @kind: database/excel/csv/json/html/text"""

        if not os.path.exists("Exports"):
            os.mkdir("Exports")

        # Extensionless name. The correct extension is added later
        _loc = self.metadata["location"].replace(os.path.sep, "_")
        _date = datetime.datetime.now().strftime(self.date_format)
        export_path = os.path.join("Exports", f"Export {_loc} {_date}")
        
        if kind == "database":
            # Export the whole database
            export_path = os.path.join("Exports", f"MongoDump {_date}")
            subprocess.run(["mongodump", "--db=fsv", f"--out={export_path}"])
        
        elif kind == "excel":
            export_path += ".xlsx"

            df = self.data.copy()
            df.columns = [f"Path (~ = {self.metadata['location']})", "Bytes", "Size"]
            df.to_excel(export_path, 
                        sheet_name=f"{os.path.basename(self.metadata['location'])} - {self.metadata['date']}",
                        index=False)
        
        elif kind == "csv":
            export_path += ".csv"
            
            with open(export_path, "w", encoding=self.encoding, newline="") as fp:
                fp.write(";".join([str(value) for value in self.metadata.values()]) + "\n")
            self.matches.to_csv(export_path, mode="a", sep=";", index=False, header=False)
        
        elif kind == "json":
            export_path += ".json"
            self.matches.to_json(export_path, indent=4)

        elif kind == "html":
            export_path += ".html"
            self.matches.to_html(export_path)

        elif kind == "text":
            export_path += ".txt"
            with open(export_path, "w", encoding=self.encoding) as fp:
                fp.write(f"{self.metadata['date']}\n")
                fp.write(f"~ = {self.metadata['location']}\n")
                fp.write(f"Process time: {self.metadata['time']}\n")
                fp.write(f"Total files: {self.metadata['total_files']}\n")
                fp.write(f"Total size: {self.total_size}\n\n")
                for i in range(self.metadata["total_files"]):
                    fp.write(f"""{self.data.iloc[i]["size"]}{" " * 8}{self.data.iloc[i]["path"]}\n""")


    def import_data(self, dirpath: str) -> bool:
        """Drop the old database and import data/metadata from a mongodump."""

        successful = not bool(subprocess.run(["mongorestore", f"--db=fsv", "--drop", dirpath], capture_output=True).returncode)
        if successful:
            self.load_data()
        return successful


    def sort_by(self, attr: str) -> None:
        """Sorts matches by @attr. If matches aren't sorted, sorts ascending first, otherwise descending."""

        if attr == "size":
            if self.sorted == "size/asc":
                self.matches.sort_values(by=["bytes", "path"], ascending=[False, False], inplace=True)
                self.sorted = "size/desc"
            else:
                self.matches.sort_values(by=["bytes", "path"], ascending=[True, True], inplace=True)
                self.sorted = "size/asc"
        
        elif attr == "name":
            if self.sorted == "name/asc":
                self.matches.sort_values(by=["path", "bytes"], ascending=[False, False], inplace=True)
                self.sorted = "name/desc"
            else:
                self.matches.sort_values(by=["path", "bytes"], ascending=[True, True], inplace=True)
                self.sorted = "name/asc"


    def plot_data(self):
        """Creates a size histogram of self.data.
        The histogram is done manually and plotted as a barchart due to the byte scale difference."""
        
        def insert_labels(bars) -> None:
            """Insert a text label above each bar in the barchart given."""
            for bar in bars:
                height = bar.get_height()
                plt.annotate(f"{height:,}", xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points", ha="center", va="bottom")

        
        x_axis = ["0b - 0.5Kb", "0.5Kb - 1Kb",
                "1Kb - 0.5Mb", "0.5Mb - 1Mb",
                "1Mb - 0.5Gb", "0.5Gb - 1Gb", ">1Gb"]
        y_axis = [0 for _ in range(7)] # Filled later

        # The 6 bytesize filters
        KB = 1024
        MB = 1024 ** 2
        GB = 1024 ** 3
        half_KB = KB // 2
        half_MB = MB // 2
        half_GB = GB // 2

        bytesizes = self.data["bytes"]
        for bytesize in bytesizes:
            if bytesize < half_KB:
                y_axis[0] += 1
            elif bytesize < KB:
                y_axis[1] += 1
            elif bytesize < half_MB:
                y_axis[2] += 1
            elif bytesize < MB:
                y_axis[3] += 1
            elif bytesize < half_GB:
                y_axis[4] += 1
            elif bytesize < GB:
                y_axis[5] += 1
            else:
                y_axis[6] += 1
        
        
        plt.grid(which="major", axis="y", linestyle=":", zorder=0)
        bars = plt.bar(x_axis, y_axis, color="royalblue", edgecolor="black", zorder=3)
        insert_labels(bars)

        plt.title("Size Histogram")
        plt.ylabel("Files")
        plt.tight_layout()
        plt.show()


    def get_data(self) -> tuple:
        """Returns (self.matches, self.matches_size)."""
        return self.matches, self.format_bytes(self.matches_bytes)


    def get_printable_metadata(self) -> tuple:
        """Returns metadata. Except total_bytes, which is returned formatted."""
        printable_metadata = (self.metadata["location"],
                            self.metadata["date"],
                            self.metadata["time"],
                            self.metadata["total_files"],
                            self.format_bytes(self.metadata["total_bytes"]))
        return printable_metadata


    def is_sliced(self) -> bool:
        """Boolean function that compares matches with the data.
        If True, then display search output. If not, then clear.
        If self.matches is slice of self.data, then a search has taken place, so search info must be displayed."""
        return self.matches.shape[0] != self.metadata["total_files"]
