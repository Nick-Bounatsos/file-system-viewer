import datetime
import html
import json
import os
import sys
import time
import uuid

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymongo
from pymongo.errors import PyMongoError


class Database:
    """Database and data-processing layer for File System Viewer.

    Public API used by the GUI:
    load_data, gather_data, search, sort_by, export_as, import_data,
    plot_data, get_data, get_printable_metadata and is_sliced.
    """

    encoding = "utf-8"
    date_format = "%d-%b-%Y"
    conn_path = "mongodb://127.0.0.1:27017"
    mongo_timeout_ms = 2000
    mongo_batch_size = 10_000

    _KB = 1_024
    _MB = 1_048_576
    _GB = 1_073_741_824
    _TB = 1_099_511_627_776

    def __init__(self) -> None:
        self.metadata = {
            "location": "",
            "date": "",
            "time": "",
            "total_folders": None,
            "total_files": 0,
            "total_bytes": 0,
            "timings": {
                "scan": None,
                "processing": None,
                "database": None,
                "total": None,
            },
        }

        self.data = self._empty_dataframe()
        self.matches = self.data.copy()

        self.total_size = ""
        self.matches_bytes = 0
        self.sorted = None

    @staticmethod
    def _format_duration(seconds) -> str:
        """Format an elapsed duration for the interface and exports."""
        if seconds is None:
            return "—"

        try:
            value = max(0.0, float(seconds))
        except (TypeError, ValueError):
            return "—"

        if value < 60:
            return f"{value:.2f} s"

        minutes, remaining = divmod(value, 60)
        return f"{int(minutes)}m {remaining:.2f}s"

    @staticmethod
    def _empty_dataframe() -> pd.DataFrame:
        """Return an empty DataFrame with stable column types."""
        return pd.DataFrame(
            {
                "path": pd.Series(dtype="object"),
                "bytes": pd.Series(dtype="int64"),
                "size": pd.Series(dtype="object"),
            }
        )

    def _get_mongo_client(self) -> pymongo.MongoClient:
        """Create a MongoDB client with a short connection timeout."""
        return pymongo.MongoClient(
            self.conn_path,
            serverSelectionTimeoutMS=self.mongo_timeout_ms,
        )

    @classmethod
    def _format_byte_sizes(cls, byte_sizes) -> list[str]:
        """Format many byte counts efficiently."""
        formatted = []
        append = formatted.append

        KB = cls._KB
        MB = cls._MB
        GB = cls._GB
        TB = cls._TB

        for value in byte_sizes:
            size = int(value)

            if size >= TB:
                append(f"{size / TB:.3f} TB")
            elif size >= GB:
                append(f"{size / GB:.3f} GB")
            elif size >= MB:
                append(f"{size / MB:.3f} MB")
            elif size >= KB:
                append(f"{size / KB:.3f} KB")
            else:
                append(f"{size} Bytes")

        return formatted

    @classmethod
    def _build_dataframe(
        cls,
        paths: list[str],
        byte_sizes: list[int],
    ) -> pd.DataFrame:
        """Build the application's standard DataFrame from raw scan data."""
        if not paths:
            return cls._empty_dataframe()

        return pd.DataFrame(
            {
                "path": paths,
                "bytes": byte_sizes,
                "size": cls._format_byte_sizes(byte_sizes),
            }
        )

    @staticmethod
    def _shorten_path(
        filepath: str,
        root: str,
        root_length: int,
    ) -> str:
        """Replace the scanned root prefix with '~'."""
        if filepath.startswith(root):
            return "~" + filepath[root_length:]

        return filepath.replace(root, "~", 1)

    def _store_data_snapshot(
        self,
        metadata: dict,
        paths: list[str],
        byte_sizes: list[int],
    ) -> bool:
        """Store a complete scan snapshot safely in MongoDB.

        A new generation is written first. Metadata is updated only after all
        file rows are inserted successfully, so an interrupted write does not
        destroy the previously committed snapshot.
        """
        location = metadata["location"]
        generation = uuid.uuid4().hex

        try:
            with self._get_mongo_client() as conn:
                conn.admin.command("ping")

                mydb = conn["fsv"]
                metadata_col = mydb["metadata"]
                data_col = mydb["data"]

                # Used by load_data() and cleanup to identify the active scan.
                data_col.create_index("_generation")

                if paths:
                    batch = []
                    append = batch.append

                    for path, size in zip(paths, byte_sizes):
                        append(
                            {
                                "_generation": generation,
                                "path": path.replace(
                                    "~",
                                    location,
                                    1,
                                ),
                                "bytes": int(size),
                            }
                        )

                        if len(batch) >= self.mongo_batch_size:
                            data_col.insert_many(
                                batch,
                                ordered=False,
                            )

                            batch = []
                            append = batch.append

                    if batch:
                        data_col.insert_many(
                            batch,
                            ordered=False,
                        )

                # This metadata document is the commit marker for the snapshot.
                committed_metadata = metadata.copy()
                committed_metadata["_generation"] = generation

                metadata_col.replace_one(
                    {"_id": "current"},
                    {
                        "_id": "current",
                        **committed_metadata,
                    },
                    upsert=True,
                )

                # Cleanup only after the new generation is committed.
                try:
                    data_col.delete_many(
                        {
                            "_generation": {
                                "$ne": generation,
                            }
                        }
                    )

                    metadata_col.delete_many(
                        {
                            "_id": {
                                "$ne": "current",
                            }
                        }
                    )

                except PyMongoError as exc:
                    # Non-fatal. load_data() still reads only the active
                    # generation, so leftover rows do not affect correctness.
                    print(
                        f"MongoDB cleanup warning: {exc}"
                    )

        except PyMongoError as exc:
            print(
                f"MongoDB store error: {exc}"
            )

            # Best-effort cleanup of an uncommitted partial generation.
            try:
                with self._get_mongo_client() as conn:
                    conn["fsv"]["data"].delete_many(
                        {
                            "_generation": generation,
                        }
                    )

            except PyMongoError:
                pass

            return False

        print(
            "Data stored successfully!"
        )

        return True

    def store_data(self) -> bool:
        """Store the current in-memory dataset in MongoDB."""
        paths = self.data["path"].tolist()
        byte_sizes = self.data["bytes"].tolist()

        return self._store_data_snapshot(
            self.metadata.copy(),
            paths,
            byte_sizes,
        )

    def load_data(self) -> bool:
        """Load the currently committed snapshot from MongoDB."""
        paths = []
        byte_sizes = []

        append_path = paths.append
        append_size = byte_sizes.append

        try:
            with self._get_mongo_client() as conn:
                conn.admin.command("ping")

                mydb = conn["fsv"]
                metadata_col = mydb["metadata"]
                data_col = mydb["data"]

                # Prefer the new fixed-ID metadata document. Fall back to the
                # legacy format so older databases remain readable.
                metadata = metadata_col.find_one(
                    {"_id": "current"},
                    {"_id": 0},
                )

                if metadata is None:
                    metadata = metadata_col.find_one(
                        {},
                        {"_id": 0},
                    )

                if metadata is None:
                    return False

                try:
                    location = str(
                        metadata["location"]
                    )

                    date = metadata["date"]
                    process_time = metadata.get("time", "")
                    total_folders = metadata.get("total_folders")
                    timings = metadata.get("timings")

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as exc:
                    print(
                        f"Invalid MongoDB metadata: {exc}"
                    )

                    return False

                generation = metadata.get(
                    "_generation"
                )

                if generation:
                    data_filter = {
                        "_generation": generation,
                    }

                else:
                    # Legacy rows do not contain a generation field.
                    data_filter = {
                        "_generation": {
                            "$exists": False,
                        }
                    }

                cursor = data_col.find(
                    data_filter,
                    {
                        "_id": 0,
                        "path": 1,
                        "bytes": 1,
                    },
                ).batch_size(
                    self.mongo_batch_size
                )

                for row in cursor:
                    try:
                        filepath = str(
                            row["path"]
                        ).replace(
                            location,
                            "~",
                            1,
                        )

                        byte_size = int(
                            row["bytes"]
                        )

                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                    ):
                        continue

                    append_path(filepath)
                    append_size(byte_size)

        except PyMongoError as exc:
            print(
                f"MongoDB load error: {exc}"
            )

            return False

        total_bytes = sum(
            byte_sizes
        )

        total_files = len(
            paths
        )

        if not isinstance(timings, dict):
            timings = {
                "scan": None,
                "processing": None,
                "database": None,
                "total": None,
            }

        self.metadata.update(
            {
                "location": location,
                "date": date,
                "time": process_time,
                "total_folders": (
                    int(total_folders)
                    if total_folders is not None
                    else None
                ),
                "total_files": total_files,
                "total_bytes": total_bytes,
                "timings": {
                    "scan": timings.get("scan"),
                    "processing": timings.get("processing"),
                    "database": timings.get("database"),
                    "total": timings.get("total"),
                },
            }
        )

        self.data = self._build_dataframe(
            paths,
            byte_sizes,
        )

        self.matches = self.data.copy()
        self.matches_bytes = total_bytes

        self.total_size = self.format_bytes(
            total_bytes
        )

        self.sorted = None

        return True

    def _scan_directory(
        self,
        dirpath: str,
    ) -> tuple[
        list[str],
        list[int],
        int,
        int,
    ]:
        """Scan a directory tree and count successfully visited folders."""
        paths = []
        byte_sizes = []

        append_path = paths.append
        append_size = byte_sizes.append

        total_bytes = 0
        total_folders = 0

        root = os.path.normpath(
            dirpath
        )

        root_length = len(
            root
        )

        stack = [
            root
        ]

        while stack:
            current_dir = stack.pop()
            subdirectories = []

            try:
                with os.scandir(
                    current_dir
                ) as entries:
                    # Count only folders that were actually opened and scanned.
                    # The selected root directory is included in this count.
                    total_folders += 1

                    for entry in entries:
                        try:
                            if entry.is_dir(
                                follow_symlinks=False
                            ):
                                subdirectories.append(
                                    entry.path
                                )

                                continue

                            # Do not recursively traverse symlinked directories.
                            if (
                                entry.is_symlink()
                                and entry.is_dir(
                                    follow_symlinks=True
                                )
                            ):
                                continue

                            byte_size = entry.stat(
                                follow_symlinks=True
                            ).st_size

                        except (
                            FileNotFoundError,
                            PermissionError,
                            OSError,
                        ):
                            continue

                        total_bytes += byte_size

                        append_path(
                            self._shorten_path(
                                entry.path,
                                root,
                                root_length,
                            )
                        )

                        append_size(
                            byte_size
                        )

            except (
                FileNotFoundError,
                PermissionError,
                OSError,
            ):
                continue

            # Reverse preserves intuitive traversal order while using a stack.
            stack.extend(
                reversed(
                    subdirectories
                )
            )

        return (
            paths,
            byte_sizes,
            total_bytes,
            total_folders,
        )

    def _persist_timing_metadata(self) -> None:
        """Best-effort update of timing details on the committed snapshot."""
        try:
            with self._get_mongo_client() as conn:
                conn.admin.command("ping")
                conn["fsv"]["metadata"].update_one(
                    {"_id": "current"},
                    {
                        "$set": {
                            "time": self.metadata.get("time", ""),
                            "timings": self.metadata.get("timings", {}),
                        }
                    },
                )
        except PyMongoError as exc:
            print(f"MongoDB timing metadata warning: {exc}")

    def gather_data(
        self,
        dirpath: str,
    ) -> None:
        """Scan a directory, build the dataset and persist it with timings."""
        self.sorted = None
        total_started = time.perf_counter()

        scan_started = time.perf_counter()
        (
            paths,
            byte_sizes,
            total_bytes,
            total_folders,
        ) = self._scan_directory(
            dirpath
        )
        scan_elapsed = time.perf_counter() - scan_started

        processing_started = time.perf_counter()
        self.data = self._build_dataframe(
            paths,
            byte_sizes,
        )
        self.matches = self.data.copy()
        self.matches_bytes = total_bytes
        self.total_size = self.format_bytes(
            total_bytes
        )
        processing_elapsed = time.perf_counter() - processing_started

        total_files = len(paths)
        self.metadata.update(
            {
                "location": dirpath,
                "date": datetime.datetime.now().strftime(
                    self.date_format
                ),
                "time": "",
                "total_folders": total_folders,
                "total_files": total_files,
                "total_bytes": total_bytes,
                "timings": {
                    "scan": scan_elapsed,
                    "processing": processing_elapsed,
                    "database": None,
                    "total": None,
                },
            }
        )

        database_started = time.perf_counter()
        stored = self._store_data_snapshot(
            self.metadata.copy(),
            paths,
            byte_sizes,
        )
        database_elapsed = time.perf_counter() - database_started
        total_elapsed = time.perf_counter() - total_started

        self.metadata["timings"] = {
            "scan": scan_elapsed,
            "processing": processing_elapsed,
            "database": database_elapsed,
            "total": total_elapsed,
        }
        self.metadata["time"] = self._format_duration(
            total_elapsed
        )

        if stored:
            self._persist_timing_metadata()

    @classmethod
    def format_bytes(
        cls,
        bytes: int,
    ) -> str:
        """Convert bytes to a human-readable string."""
        size = int(
            bytes
        )

        if size >= cls._TB:
            return (
                f"{size / cls._TB:.3f} TB"
            )

        if size >= cls._GB:
            return (
                f"{size / cls._GB:.3f} GB"
            )

        if size >= cls._MB:
            return (
                f"{size / cls._MB:.3f} MB"
            )

        if size >= cls._KB:
            return (
                f"{size / cls._KB:.3f} KB"
            )

        return f"{size} Bytes"

    @classmethod
    def parse_bytes(
        cls,
        text: str,
    ):
        """Parse sizes such as 500b, 1.5kb, 20mb, 2gb or 1tb."""
        if not isinstance(
            text,
            str,
        ):
            return None

        units = {
            "tb": cls._TB,
            "gb": cls._GB,
            "mb": cls._MB,
            "kb": cls._KB,
            "b": 1,
        }

        value = (
            text
            .lower()
            .strip()
            .replace(
                " ",
                "",
            )
        )

        value = (
            value
            .replace(
                "bytes",
                "b",
            )
            .replace(
                "byte",
                "b",
            )
        )

        try:
            for (
                suffix,
                multiplier,
            ) in units.items():

                if value.endswith(
                    suffix
                ):
                    numeric_value = value[
                        :-len(
                            suffix
                        )
                    ]

                    return int(
                        float(
                            numeric_value
                        )
                        * multiplier
                    )

            # Plain numbers are interpreted as bytes.
            return int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    def search(
        self,
        query: str,
    ) -> None:
        """Search/filter self.data and store the result in self.matches."""
        self.sorted = None

        self.matches_bytes = self.metadata[
            "total_bytes"
        ]

        if not query:
            self.matches = self.data.copy()
            return

        matches = self.data
        filtered = False

        for key in query.split(
            " && "
        ):
            if not key:
                continue

            if key.startswith(">"):
                if key.startswith(">="):
                    size_filter = self.parse_bytes(
                        key[2:]
                    )

                    if size_filter is None:
                        continue

                    matches = matches.loc[
                        matches["bytes"]
                        >= size_filter
                    ]

                else:
                    size_filter = self.parse_bytes(
                        key[1:]
                    )

                    if size_filter is None:
                        continue

                    matches = matches.loc[
                        matches["bytes"]
                        > size_filter
                    ]

                filtered = True

            elif key.startswith("<"):
                if key.startswith("<="):
                    size_filter = self.parse_bytes(
                        key[2:]
                    )

                    if size_filter is None:
                        continue

                    matches = matches.loc[
                        matches["bytes"]
                        <= size_filter
                    ]

                else:
                    size_filter = self.parse_bytes(
                        key[1:]
                    )

                    if size_filter is None:
                        continue

                    matches = matches.loc[
                        matches["bytes"]
                        < size_filter
                    ]

                filtered = True

            elif key.lower().startswith("ext:"):
                extensions = [
                    extension.strip().lower().lstrip(".")
                    for extension in key[4:].split(",")
                    if extension.strip()
                ]

                if not extensions:
                    continue

                suffixes = tuple(
                    f".{extension}"
                    for extension in extensions
                )

                matches = matches.loc[
                    matches["path"].str.lower().str.endswith(
                        suffixes,
                        na=False,
                    )
                ]

                filtered = True

            elif key.startswith("^"):
                key = key[1:]

                matches = matches.loc[
                    matches["path"].str.startswith(
                        key,
                        na=False,
                    )
                ]

                filtered = True

            elif key.endswith("$"):
                key = key[:-1]

                matches = matches.loc[
                    matches["path"].str.endswith(
                        key,
                        na=False,
                    )
                ]

                filtered = True

            elif (
                key.startswith("%")
                and key.endswith("%")
            ):
                key = key[1:-1]

                matches = matches.loc[
                    matches["path"].str.contains(
                        key,
                        case=False,
                        regex=False,
                        na=False,
                    )
                ]

                filtered = True

            elif key.startswith("!"):
                key = key[1:]

                matches = matches.loc[
                    ~matches["path"].str.contains(
                        key,
                        regex=False,
                        na=False,
                    )
                ]

                filtered = True

            else:
                matches = matches.loc[
                    matches["path"].str.contains(
                        key,
                        regex=False,
                        na=False,
                    )
                ]

                filtered = True

        self.matches = (
            matches
            if filtered
            else self.data.copy()
        )

        self.matches_bytes = int(
            self.matches[
                "bytes"
            ].sum()
        )

    @staticmethod
    def _safe_filename_part(value: str) -> str:
        """Return a Windows-safe filename fragment."""
        invalid = '<>:"/\\|?*'
        translation = str.maketrans({char: "_" for char in invalid})
        cleaned = str(value).translate(translation).strip().rstrip(".")
        return cleaned or "Export"

    @staticmethod
    def _safe_excel_sheet_name(value: str) -> str:
        """Return a valid Excel worksheet name (maximum 31 characters)."""
        invalid = set('[]:*?/\\')
        cleaned = "".join("_" if char in invalid else char for char in str(value))
        cleaned = cleaned.strip().strip("'")
        return (cleaned or "Files")[:31]

    @staticmethod
    def _ensure_export_extension(path: str, extension: str) -> str:
        """Append the expected extension when the user omitted it."""
        if path.lower().endswith(extension.lower()):
            return path
        return path + extension

    @staticmethod
    def _application_directory() -> str:
        """Return the source folder or packaged executable folder."""
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))

        return os.path.dirname(os.path.abspath(__file__))

    def get_exports_directory(self) -> str:
        """Return the default Exports directory beside the application."""
        return os.path.join(
            self._application_directory(),
            "Exports",
        )

    def get_default_export_path(self, kind: str) -> str:
        """Return a unique default path for an export operation."""
        extensions = {
            "snapshot": ".csv",
            "excel": ".xlsx",
            "csv": ".csv",
            "json": ".json",
            "html": ".html",
            "text": ".txt",
        }

        timestamp = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        location = self.metadata.get("location", "")
        location_name = os.path.basename(
            os.path.normpath(location)
        ) if location else "Files"

        location_name = self._safe_filename_part(location_name)
        exports_directory = self.get_exports_directory()

        extension = extensions.get(kind)
        if extension is None:
            raise ValueError(f"Unknown export type: {kind}")

        if kind == "snapshot":
            filename = (
                f"File System Viewer Snapshot - {location_name} - "
                f"{timestamp}{extension}"
            )
        else:
            filename = (
                f"File System Viewer - {location_name} - "
                f"{timestamp}{extension}"
            )

        return os.path.join(
            exports_directory,
            filename,
        )

    def _export_snapshot_csv(
        self,
        export_path: str,
    ) -> None:
        """Export a complete, importable File System Viewer CSV snapshot."""
        snapshot_metadata = {
            "format": "File System Viewer Snapshot",
            "version": 1,
            "location": self.metadata.get("location", ""),
            "date": self.metadata.get("date", ""),
            "time": self.metadata.get("time", ""),
            "total_folders": self.metadata.get("total_folders"),
            "total_files": int(self.data.shape[0]),
            "total_bytes": int(self.data["bytes"].sum())
            if not self.data.empty
            else 0,
            "timings": self.metadata.get("timings", {}),
        }

        with open(
            export_path,
            "w",
            encoding=self.encoding,
            newline="",
        ) as fp:
            fp.write("# File System Viewer Snapshot v1\n")
            fp.write(
                "# META "
                + json.dumps(
                    snapshot_metadata,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )

            self.data[["path", "bytes"]].to_csv(
                fp,
                sep=";",
                index=False,
            )

    def _load_snapshot_csv(
        self,
        filepath: str,
    ) -> tuple[dict, list[str], list[int]]:
        """Parse and validate an importable File System Viewer CSV snapshot."""
        with open(
            filepath,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as fp:
            signature = fp.readline().strip().lstrip("\ufeff")
            metadata_line = fp.readline().strip()

        if signature != "# File System Viewer Snapshot v1":
            raise ValueError(
                "This CSV is not a File System Viewer snapshot."
            )

        if not metadata_line.startswith("# META "):
            raise ValueError(
                "Snapshot metadata is missing or invalid."
            )

        try:
            snapshot_metadata = json.loads(
                metadata_line[7:]
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Snapshot metadata could not be read."
            ) from exc

        if snapshot_metadata.get("version") != 1:
            raise ValueError(
                "Unsupported File System Viewer snapshot version."
            )

        frame = pd.read_csv(
            filepath,
            sep=";",
            skiprows=2,
            usecols=["path", "bytes"],
            keep_default_na=False,
            encoding="utf-8-sig",
        )

        if frame.empty:
            paths = []
            byte_sizes = []
        else:
            frame["bytes"] = pd.to_numeric(
                frame["bytes"],
                errors="raise",
            )

            if (frame["bytes"] < 0).any():
                raise ValueError(
                    "Snapshot contains an invalid negative file size."
                )

            frame["bytes"] = frame["bytes"].astype(
                "int64"
            )

            paths = frame["path"].astype(str).tolist()
            byte_sizes = frame["bytes"].tolist()

        imported_timings = snapshot_metadata.get("timings")
        if not isinstance(imported_timings, dict):
            imported_timings = {}

        metadata = {
            "location": str(
                snapshot_metadata.get("location", "")
            ),
            "date": str(
                snapshot_metadata.get("date", "")
            ),
            "time": str(
                snapshot_metadata.get("time", "")
            ),
            "total_folders": (
                int(snapshot_metadata["total_folders"])
                if snapshot_metadata.get("total_folders") is not None
                else None
            ),
            "total_files": len(paths),
            "total_bytes": int(sum(byte_sizes)),
            "timings": {
                "scan": imported_timings.get("scan"),
                "processing": imported_timings.get("processing"),
                "database": imported_timings.get("database"),
                "total": imported_timings.get("total"),
            },
        }

        return metadata, paths, byte_sizes

    def _export_html_report(self, export_path: str) -> None:
        """Export the current matches as a polished standalone HTML report."""
        exported_rows = int(self.matches.shape[0])
        exported_bytes = int(self.matches["bytes"].sum()) if exported_rows else 0
        export_scope = "Filtered results" if self.is_sliced() else "Full dataset"

        table_html = self.matches.to_html(
            index=False,
            border=0,
            classes=["file-table"],
            escape=True,
        )

        location = html.escape(str(self.metadata.get("location", "")))
        scan_date = html.escape(str(self.metadata.get("date", "")))
        scan_time = html.escape(str(self.metadata.get("time", "")))
        exported_size = html.escape(self.format_bytes(exported_bytes))
        scope = html.escape(export_scope)

        document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>File System Viewer Export</title>
<style>
:root {{
    color-scheme: dark;
    --bg: #0f172a;
    --panel: #111827;
    --panel-2: #182130;
    --border: #2b3545;
    --text: #e5e7eb;
    --muted: #94a3b8;
    --heading: #f8fafc;
    --accent: #3b82f6;
    --accent-soft: rgba(59, 130, 246, 0.14);
    --row-alt: #151f2f;
    --row-hover: #1d2b40;
    --shadow: 0 20px 55px rgba(0, 0, 0, 0.28);
}}

:root[data-theme="light"] {{
    color-scheme: light;
    --bg: #f4f6f8;
    --panel: #ffffff;
    --panel-2: #f8fafc;
    --border: #dfe3e8;
    --text: #20242a;
    --muted: #667085;
    --heading: #16191d;
    --accent: #3478f6;
    --accent-soft: rgba(52, 120, 246, 0.11);
    --row-alt: #fafbfc;
    --row-hover: #eef4ff;
    --shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
}}

* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    background:
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 32rem),
        var(--bg);
    color: var(--text);
    font-family: "Segoe UI", Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}}

.shell {{
    width: min(1500px, calc(100% - 40px));
    margin: 0 auto;
    padding: 36px 0 48px;
}}

.hero {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
    margin-bottom: 18px;
}}

.eyebrow {{
    margin: 0 0 7px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 750;
    letter-spacing: .12em;
    text-transform: uppercase;
}}

h1 {{
    margin: 0;
    color: var(--heading);
    font-size: clamp(28px, 4vw, 42px);
    line-height: 1.05;
    letter-spacing: -.03em;
}}

.subtitle {{
    margin: 10px 0 0;
    color: var(--muted);
    font-size: 14px;
}}

.location {{
    margin-top: 14px;
    display: inline-block;
    max-width: 100%;
    padding: 8px 11px;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--panel-2);
    color: var(--text);
    font-family: Consolas, "SFMono-Regular", monospace;
    font-size: 13px;
    overflow-wrap: anywhere;
}}

.theme-button {{
    flex: 0 0 auto;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--panel);
    color: var(--text);
    padding: 9px 13px;
    cursor: pointer;
    font: inherit;
    font-weight: 650;
    box-shadow: var(--shadow);
}}

.theme-button:hover {{ border-color: var(--accent); }}

.cards {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 20px 0;
}}

.card {{
    border: 1px solid var(--border);
    border-radius: 13px;
    background: linear-gradient(180deg, var(--panel-2), var(--panel));
    padding: 15px 16px;
    box-shadow: var(--shadow);
}}

.card-label {{
    color: var(--muted);
    font-size: 11px;
    font-weight: 750;
    letter-spacing: .08em;
    text-transform: uppercase;
}}

.card-value {{
    margin-top: 7px;
    color: var(--heading);
    font-size: 20px;
    font-weight: 750;
    overflow-wrap: anywhere;
}}

.panel {{
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--panel);
    box-shadow: var(--shadow);
}}

.toolbar {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 13px;
    border-bottom: 1px solid var(--border);
    background: var(--panel-2);
}}

.search {{
    width: min(520px, 100%);
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--panel);
    color: var(--text);
    padding: 10px 12px;
    outline: none;
    font: inherit;
}}

.search:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
}}

.row-count {{
    margin-left: auto;
    white-space: nowrap;
    color: var(--muted);
    font-size: 13px;
}}

.table-wrap {{
    max-height: calc(100vh - 330px);
    min-height: 320px;
    overflow: auto;
}}

.file-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
}}

.file-table thead th {{
    position: sticky;
    top: 0;
    z-index: 2;
    padding: 11px 13px;
    border-bottom: 1px solid var(--border);
    background: var(--panel-2);
    color: var(--muted);
    text-align: left;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .06em;
    text-transform: uppercase;
}}

.file-table tbody td {{
    padding: 10px 13px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}}

.file-table tbody tr:nth-child(even) {{ background: var(--row-alt); }}
.file-table tbody tr:hover {{ background: var(--row-hover); }}
.file-table tbody tr:last-child td {{ border-bottom: 0; }}

.file-table td:first-child {{
    min-width: 320px;
    font-family: Consolas, "SFMono-Regular", monospace;
    overflow-wrap: anywhere;
}}

.file-table td:nth-child(2) {{
    min-width: 120px;
    text-align: right;
    font-variant-numeric: tabular-nums;
}}

.file-table td:nth-child(3) {{
    min-width: 120px;
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}}

.empty {{
    display: none;
    padding: 34px;
    text-align: center;
    color: var(--muted);
}}

.footer {{
    margin: 14px 2px 0;
    color: var(--muted);
    font-size: 12px;
}}

@media (max-width: 900px) {{
    .shell {{ width: min(100% - 24px, 1500px); padding-top: 24px; }}
    .hero {{ flex-direction: column; }}
    .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .toolbar {{ align-items: stretch; flex-direction: column; }}
    .search {{ width: 100%; }}
    .row-count {{ margin-left: 0; }}
    .table-wrap {{ max-height: none; }}
}}

@media (max-width: 540px) {{
    .cards {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<main class="shell">
    <section class="hero">
        <div>
            <p class="eyebrow">File System Viewer</p>
            <h1>File inventory</h1>
            <p class="subtitle">Standalone export generated from the current application view.</p>
            <div class="location">{location or "No directory loaded"}</div>
        </div>
        <button class="theme-button" id="themeButton" type="button">Light mode</button>
    </section>

    <section class="cards">
        <article class="card">
            <div class="card-label">Exported files</div>
            <div class="card-value">{exported_rows:,}</div>
        </article>
        <article class="card">
            <div class="card-label">Exported size</div>
            <div class="card-value">{exported_size}</div>
        </article>
        <article class="card">
            <div class="card-label">Scan date</div>
            <div class="card-value">{scan_date or "—"}</div>
        </article>
        <article class="card">
            <div class="card-label">Scan time</div>
            <div class="card-value">{scan_time or "—"}</div>
        </article>
    </section>

    <section class="panel">
        <div class="toolbar">
            <input class="search" id="tableSearch" type="search" placeholder="Filter exported rows…" autocomplete="off">
            <div class="row-count" id="rowCount">{exported_rows:,} rows · {scope}</div>
        </div>
        <div class="table-wrap">
            {table_html}
            <div class="empty" id="emptyState">No rows match this filter.</div>
        </div>
    </section>

    <div class="footer">Generated by File System Viewer · {scope}</div>
</main>

<script>
(() => {{
    const root = document.documentElement;
    const themeButton = document.getElementById('themeButton');
    const searchInput = document.getElementById('tableSearch');
    const rowCount = document.getElementById('rowCount');
    const emptyState = document.getElementById('emptyState');
    const rows = Array.from(document.querySelectorAll('.file-table tbody tr'));

    const savedTheme = localStorage.getItem('fsv-export-theme');
    if (savedTheme === 'light') {{
        root.dataset.theme = 'light';
    }}

    const syncThemeButton = () => {{
        const light = root.dataset.theme === 'light';
        themeButton.textContent = light ? 'Dark mode' : 'Light mode';
    }};

    themeButton.addEventListener('click', () => {{
        const light = root.dataset.theme === 'light';
        if (light) {{
            delete root.dataset.theme;
            localStorage.setItem('fsv-export-theme', 'dark');
        }} else {{
            root.dataset.theme = 'light';
            localStorage.setItem('fsv-export-theme', 'light');
        }}
        syncThemeButton();
    }});

    searchInput.addEventListener('input', () => {{
        const needle = searchInput.value.trim().toLocaleLowerCase();
        let visible = 0;

        rows.forEach((row) => {{
            const matches = !needle || row.textContent.toLocaleLowerCase().includes(needle);
            row.hidden = !matches;
            if (matches) visible += 1;
        }});

        rowCount.textContent = `${{visible.toLocaleString()}} of ${{rows.length.toLocaleString()}} rows · {scope}`;
        emptyState.style.display = visible === 0 ? 'block' : 'none';
    }});

    syncThemeButton();
}})();
</script>
</body>
</html>
"""

        with open(
            export_path,
            "w",
            encoding=self.encoding,
        ) as fp:
            fp.write(document)

    def export_as(
        self,
        kind: str,
        export_path: str | None = None,
    ):
        """Export data and return the final destination path on success.

        ``export_path`` may be supplied by the GUI after a Save As / folder
        selection. When omitted, the export is placed in the application's
        default ``Exports`` directory. ``False`` is returned on failure.
        """
        extensions = {
            "snapshot": ".csv",
            "excel": ".xlsx",
            "csv": ".csv",
            "json": ".json",
            "html": ".html",
            "text": ".txt",
        }

        if kind not in extensions:
            print(f"Unknown export type: {kind}")
            return False

        if not export_path:
            export_path = self.get_default_export_path(kind)

        export_path = os.path.abspath(
            os.path.normpath(export_path)
        )

        try:
            extension = extensions[kind]
            export_path = self._ensure_export_extension(
                export_path,
                extension,
            )

            parent_directory = os.path.dirname(export_path)
            if parent_directory:
                os.makedirs(parent_directory, exist_ok=True)

            if kind == "snapshot":
                self._export_snapshot_csv(
                    export_path
                )

            elif kind == "excel":
                df = self.data.rename(
                    columns={
                        "path": (
                            "Path "
                            f"(~ = {self.metadata['location']})"
                        ),
                        "bytes": "Bytes",
                        "size": "Size",
                    }
                )

                location = self.metadata.get("location", "")
                location_name = (
                    os.path.basename(os.path.normpath(location))
                    if location
                    else "Files"
                )

                sheet_name = self._safe_excel_sheet_name(
                    f"{location_name} - {self.metadata['date']}"
                )

                df.to_excel(
                    export_path,
                    sheet_name=sheet_name,
                    index=False,
                )

            elif kind == "csv":
                with open(
                    export_path,
                    "w",
                    encoding=self.encoding,
                    newline="",
                ) as fp:
                    fp.write(
                        ";".join(
                            [
                                str(self.metadata["location"]),
                                str(self.metadata["date"]),
                                str(self.metadata["time"]),
                                str(self.metadata["total_files"]),
                                str(self.metadata["total_bytes"]),
                            ]
                        )
                        + "\n"
                    )

                self.matches.to_csv(
                    export_path,
                    mode="a",
                    sep=";",
                    index=False,
                    header=False,
                )

            elif kind == "json":
                self.matches.to_json(
                    export_path,
                    indent=4,
                    force_ascii=False,
                )

            elif kind == "html":
                self._export_html_report(
                    export_path
                )

            elif kind == "text":
                with open(
                    export_path,
                    "w",
                    encoding=self.encoding,
                ) as fp:
                    fp.write(f"{self.metadata['date']}\n")
                    fp.write(f"~ = {self.metadata['location']}\n")
                    fp.write(
                        f"Process time: {self.metadata['time']}\n"
                    )
                    fp.write(
                        f"Total files: {self.metadata['total_files']}\n"
                    )
                    fp.write(f"Total size: {self.total_size}\n\n")

                    fp.writelines(
                        (
                            f"{size}{' ' * 8}{path}\n"
                            for size, path in self.data[
                                ["size", "path"]
                            ].itertuples(
                                index=False,
                                name=None,
                            )
                        )
                    )

        except (
            OSError,
            ValueError,
            ImportError,
        ) as exc:
            print(f"Export error: {exc}")
            return False

        return export_path

    def import_data(
        self,
        filepath: str,
    ) -> dict:
        """Import a CSV snapshot and report parsing/persistence separately."""
        if not filepath:
            return {
                "success": False,
                "persisted": False,
                "error": "No snapshot file was selected.",
            }

        try:
            (
                metadata,
                paths,
                byte_sizes,
            ) = self._load_snapshot_csv(
                filepath
            )
            imported_data = self._build_dataframe(
                paths,
                byte_sizes,
            )

        except (
            OSError,
            ValueError,
            KeyError,
            UnicodeError,
            pd.errors.ParserError,
        ) as exc:
            message = str(exc)
            print(f"Snapshot import error: {message}")
            return {
                "success": False,
                "persisted": False,
                "error": message,
            }

        # The snapshot itself is valid at this point. Load it into the current
        # session even if MongoDB persistence later fails.
        self.metadata.update(
            metadata
        )
        self.data = imported_data
        self.matches = self.data.copy()
        self.matches_bytes = metadata["total_bytes"]
        self.total_size = self.format_bytes(
            metadata["total_bytes"]
        )
        self.sorted = None

        persisted = self._store_data_snapshot(
            metadata.copy(),
            paths,
            byte_sizes,
        )

        return {
            "success": True,
            "persisted": bool(persisted),
            "error": "" if persisted else (
                "The snapshot was imported, but it could not be saved "
                "to MongoDB. The imported data is available for this "
                "session only."
            ),
        }

    def sort_by(
        self,
        attr: str,
    ) -> None:
        """Sort matches by attr, alternating ascending/descending."""
        if self.matches.empty:
            return

        if attr == "size":
            if self.sorted == "size/asc":
                self.matches = (
                    self.matches
                    .iloc[::-1]
                    .copy()
                )

                self.sorted = "size/desc"

            elif self.sorted == "size/desc":
                self.matches = (
                    self.matches
                    .iloc[::-1]
                    .copy()
                )

                self.sorted = "size/asc"

            else:
                self.matches.sort_values(
                    by=[
                        "bytes",
                        "path",
                    ],
                    ascending=[
                        True,
                        True,
                    ],
                    inplace=True,
                )

                self.sorted = "size/asc"

        elif attr == "name":
            if self.sorted == "name/asc":
                self.matches = (
                    self.matches
                    .iloc[::-1]
                    .copy()
                )

                self.sorted = "name/desc"

            elif self.sorted == "name/desc":
                self.matches = (
                    self.matches
                    .iloc[::-1]
                    .copy()
                )

                self.sorted = "name/asc"

            else:
                self.matches.sort_values(
                    by=[
                        "path",
                        "bytes",
                    ],
                    ascending=[
                        True,
                        True,
                    ],
                    inplace=True,
                )

                self.sorted = "name/asc"

    @staticmethod
    def _apply_plot_theme(fig, ax, dark_mode: bool) -> dict:
        """Apply a restrained theme that mirrors the application's UI."""
        if dark_mode:
            colors = {
                "figure": "#111827",
                "axes": "#161d2a",
                "text": "#e5e7eb",
                "muted": "#9ca3af",
                "grid": "#334155",
                "accent": "#3b82f6",
                "edge": "#60a5fa",
            }
        else:
            colors = {
                "figure": "#f4f6f8",
                "axes": "#ffffff",
                "text": "#20242a",
                "muted": "#667085",
                "grid": "#dfe3e8",
                "accent": "#3478f6",
                "edge": "#2f6fdf",
            }

        fig.patch.set_facecolor(colors["figure"])
        ax.set_facecolor(colors["axes"])
        ax.tick_params(colors=colors["muted"], labelsize=9.5)
        ax.xaxis.label.set_color(colors["muted"])
        ax.yaxis.label.set_color(colors["muted"])
        ax.title.set_color(colors["text"])

        for spine in ax.spines.values():
            spine.set_color(colors["grid"])

        return colors

    def _plot_scope_text(self) -> str:
        """Return a compact description of the currently filtered result set."""
        files = int(self.matches.shape[0])
        size = self.format_bytes(
            int(self.matches["bytes"].sum())
            if files
            else 0
        )
        return f"Current filtered result • {files:,} files • {size}"

    def plot_data(self, dark_mode: bool = True) -> None:
        """Plot a polished file-size distribution for current matches only."""
        byte_values = self.matches["bytes"].to_numpy(
            dtype=float,
            copy=False,
        )

        bins = np.array(
            [
                0,
                self._KB,
                100 * self._KB,
                self._MB,
                10 * self._MB,
                100 * self._MB,
                self._GB,
                np.inf,
            ],
            dtype=float,
        )
        labels = [
            "< 1 KB",
            "1–100 KB",
            "100 KB–1 MB",
            "1–10 MB",
            "10–100 MB",
            "100 MB–1 GB",
            "≥ 1 GB",
        ]
        counts = np.histogram(
            byte_values,
            bins=bins,
        )[0]

        fig, ax = plt.subplots(
            figsize=(11.5, 6.4)
        )
        colors = self._apply_plot_theme(
            fig,
            ax,
            dark_mode,
        )

        bars = ax.bar(
            labels,
            counts,
            color=colors["accent"],
            edgecolor=colors["edge"],
            linewidth=0.8,
            zorder=3,
        )

        total_files = max(1, int(counts.sum()))
        tallest = max(1, int(counts.max(initial=0)))

        for bar, count in zip(bars, counts):
            if count <= 0:
                continue
            percentage = count / total_files * 100
            ax.annotate(
                f"{int(count):,}\n{percentage:.1f}%",
                xy=(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                ),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=colors["text"],
                fontsize=9,
                fontweight="semibold",
            )

        ax.set_title(
            "File Size Distribution",
            loc="left",
            fontsize=17,
            fontweight="bold",
            pad=18,
        )
        ax.text(
            0,
            1.01,
            self._plot_scope_text(),
            transform=ax.transAxes,
            color=colors["muted"],
            fontsize=10,
            va="bottom",
        )
        ax.set_ylabel("Number of files")
        ax.set_xlabel("File size range")
        ax.set_ylim(0, tallest * 1.20)
        ax.grid(
            axis="y",
            linestyle="--",
            linewidth=0.7,
            alpha=0.55,
            color=colors["grid"],
            zorder=0,
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", rotation=18)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(
                lambda value, _position: f"{int(value):,}"
            )
        )

        try:
            fig.canvas.manager.set_window_title(
                "File System Viewer — Size Distribution"
            )
        except AttributeError:
            pass

        fig.tight_layout(pad=2.0)
        plt.show()

    def plot_file_types_by_size(
        self,
        dark_mode: bool = True,
        top_n: int = 10,
    ) -> None:
        """Plot file types ranked by total size for current matches only."""
        frame = self.matches[["path", "bytes"]].copy()

        def file_type(path: str) -> str:
            extension = os.path.splitext(str(path))[1].lower()
            return extension if extension else "[no extension]"

        frame["type"] = frame["path"].map(file_type)
        summary = (
            frame.groupby("type", as_index=False)
            .agg(
                total_bytes=("bytes", "sum"),
                file_count=("bytes", "size"),
            )
            .sort_values(
                "total_bytes",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        top_n = max(1, int(top_n))
        visible = summary.head(top_n).copy()

        if summary.shape[0] > top_n:
            remainder = summary.iloc[top_n:]
            visible.loc[len(visible)] = {
                "type": "Other",
                "total_bytes": int(remainder["total_bytes"].sum()),
                "file_count": int(remainder["file_count"].sum()),
            }

        # Reverse so the largest category appears at the top of a horizontal chart.
        visible = visible.iloc[::-1].reset_index(drop=True)

        fig_height = max(5.8, 0.48 * len(visible) + 2.4)
        fig, ax = plt.subplots(
            figsize=(11.5, fig_height)
        )
        colors = self._apply_plot_theme(
            fig,
            ax,
            dark_mode,
        )

        values = visible["total_bytes"].astype(float).to_numpy()
        labels = visible["type"].tolist()
        counts = visible["file_count"].astype(int).tolist()

        bars = ax.barh(
            labels,
            values,
            color=colors["accent"],
            edgecolor=colors["edge"],
            linewidth=0.8,
            zorder=3,
        )

        maximum = max(1.0, float(values.max(initial=0.0)))
        ax.set_xlim(0, maximum * 1.24)

        for bar, byte_size, count in zip(bars, values, counts):
            ax.text(
                bar.get_width() + maximum * 0.015,
                bar.get_y() + bar.get_height() / 2,
                f"{self.format_bytes(int(byte_size))}  •  {count:,} files",
                va="center",
                ha="left",
                color=colors["text"],
                fontsize=9.2,
            )

        ax.set_title(
            "Top File Types by Total Size",
            loc="left",
            fontsize=17,
            fontweight="bold",
            pad=18,
        )
        ax.text(
            0,
            1.01,
            self._plot_scope_text(),
            transform=ax.transAxes,
            color=colors["muted"],
            fontsize=10,
            va="bottom",
        )
        ax.set_xlabel("Total size")
        ax.set_ylabel("File type")
        ax.grid(
            axis="x",
            linestyle="--",
            linewidth=0.7,
            alpha=0.55,
            color=colors["grid"],
            zorder=0,
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(
                lambda value, _position: self.format_bytes(int(value))
            )
        )

        try:
            fig.canvas.manager.set_window_title(
                "File System Viewer — File Types by Size"
            )
        except AttributeError:
            pass

        fig.tight_layout(pad=2.0)
        plt.show()

    def get_data(
        self,
    ) -> tuple:
        """Return current matches and their formatted total size."""
        return (
            self.matches,
            self.format_bytes(
                self.matches_bytes
            ),
        )

    def get_timing_details(self) -> dict[str, str]:
        """Return formatted scan, processing, database and total timings."""
        timings = self.metadata.get("timings")
        if not isinstance(timings, dict):
            timings = {}

        return {
            "scan": self._format_duration(timings.get("scan")),
            "processing": self._format_duration(timings.get("processing")),
            "database": self._format_duration(timings.get("database")),
            "total": self._format_duration(timings.get("total")),
        }

    def get_printable_metadata(
        self,
    ) -> tuple:
        """Return metadata with total bytes formatted."""
        return (
            self.metadata["location"],
            self.metadata["date"],
            self.metadata["time"],
            self.metadata.get("total_folders"),
            self.metadata["total_files"],
            self.format_bytes(
                self.metadata["total_bytes"]
            ),
        )

    def is_sliced(
        self,
    ) -> bool:
        """Return True if matches are a subset of all loaded data."""
        return (
            self.matches.shape[0]
            != self.metadata["total_files"]
        )
