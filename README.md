# File System Viewer

**File System Viewer** is a Windows-friendly Python desktop application for scanning a directory tree, inspecting file sizes and paths, filtering large datasets, analysing storage usage, and saving the latest scan locally.

The application stores the latest scan in a local MongoDB database and automatically reloads it on startup.

## Features

### Directory scanning

- Recursively scans a selected directory and its subdirectories.
- Records each file's path and size.
- Counts both **folders** and **files**.
- Uses `~` as a compact representation of the scanned root directory.
- Runs scans in a background thread so the interface remains responsive.
- Supports **Update Data** to rescan the currently loaded directory.

### Scan timing breakdown

Instead of showing only one scan duration, File System Viewer records:

- **Scan** — filesystem traversal and file-size collection.
- **Process** — DataFrame creation and formatting.
- **DB save** — MongoDB persistence time.
- **Total** — complete operation time.

This makes it easier to identify whether a slow operation is caused by filesystem scanning, data processing, or database persistence.

### Searching and filtering

The application supports both a normal search bar and a **Visual Filter Builder**.

Supported search syntax includes:

| Syntax | Meaning |
|---|---|
| `text` | Path contains text |
| `%text%` | Case-insensitive contains |
| `^text` | Path starts with text |
| `text$` | Path ends with text |
| `!text` | Exclude paths containing text |
| `ext:pdf,xlsx` | Match one or more exact file extensions |
| `>10mb` | Files larger than 10 MB |
| `>=10mb` | Files at least 10 MB |
| `<500kb` | Files smaller than 500 KB |
| `<=500kb` | Files at most 500 KB |
| `condition && condition` | Combine multiple filters |

Examples:

```text
ext:pdf,xlsx && >=1mb
```

```text
%invoice% && ext:pdf && <=20mb
```

```text
>1gb && !backup
```

The **Visual Filter Builder** can create the same queries using controls for:

- text matching mode,
- file extensions,
- minimum size,
- maximum size.

### Sorting and pagination

- Sort current results by **Size** or **Path**.
- Repeated clicks reverse the sort order.
- Results are displayed using pagination.
- Configurable **Rows per Page**:
  - 250
  - 500
  - 1,000
  - 2,000
  - All rows
- Navigation controls:
  - First
  - Previous
  - Next
  - Last

Searches, filters, sorting, rescans, and imports automatically return to page 1.

### File navigation

Double-clicking a row opens the selected file's **parent directory** in the operating system's file manager.

The file itself is not opened.

## Analysis and charts

Charts always use the **current filtered results**. If no filter is active, that means the complete loaded dataset.

### Size Distribution

**File → Plot Size Distribution**

Displays a polished histogram-style chart using practical size buckets such as:

- `< 1 KB`
- `1–100 KB`
- `100 KB–1 MB`
- `1–10 MB`
- `10–100 MB`
- `100 MB–1 GB`
- `≥ 1 GB`

The chart includes file counts, percentages, total size, and adapts to the application's light/dark theme.

### File Types by Total Size

**File → Plot File Types by Size**

Displays the file extensions consuming the most storage space.

The chart shows:

- Top 10 file types by total size.
- Number of files for each type.
- An **Other** category for remaining file types.

This is useful for quickly identifying what kinds of files are responsible for most disk usage.

## Data persistence

File System Viewer stores the latest scan locally in MongoDB:

```text
mongodb://127.0.0.1:27017
```

Database name:

```text
fsv
```

The application uses generation-based snapshots so that a partially failed database write does not replace the previously committed dataset.

## Backup and import

MongoDB Database Tools are **not required**.

File System Viewer uses its own importable CSV snapshot format instead of `mongodump` / `mongorestore`.

### CSV Snapshot Backup

**File → Export As → CSV Snapshot (Backup)**

Creates a complete backup containing:

- scanned root location,
- scan date,
- folder/file metadata,
- total size,
- timing information,
- all file paths,
- all file sizes.

### Import CSV Snapshot

**File → Import CSV Snapshot…**

Loads a snapshot previously created by **CSV Snapshot (Backup)**.

CSV validation and MongoDB persistence are handled separately. If a valid snapshot is loaded successfully but saving it to MongoDB fails, the imported dataset remains available for the current application session and the user receives a specific database warning.

## Export formats

The application supports:

| Format | Behaviour |
|---|---|
| **CSV Snapshot** | Complete importable backup |
| **Excel (.xlsx)** | Full scanned dataset |
| **HTML (.html)** | Current matching results as a styled standalone HTML report |
| **CSV (.csv)** | Current matching results |
| **JSON (.json)** | Current matching results |
| **Text (.txt)** | Human-readable listing of the full dataset |

The HTML report includes:

- scan metadata cards,
- dark/light mode,
- responsive layout,
- sticky table headers,
- built-in search,
- live result counter.

Exports default to an `Exports` directory beside the source application or packaged executable, while the Save dialog allows another destination to be selected.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+G` | Gather data |
| `Ctrl+U` | Update current directory |
| `Ctrl+I` | Import CSV Snapshot |
| `Ctrl+F` | Focus search bar |
| `Esc` | Clear active search/filter |
| `Ctrl+Shift+D` | Toggle Light/Dark mode |
| `Ctrl+Q` | Exit |

Charts intentionally do **not** use keyboard shortcuts so additional analysis views can be added later without consuming shortcut combinations.

## Requirements

### Python packages

- Python 3.13
- PyQt5
- pandas
- matplotlib
- numpy
- pymongo
- openpyxl

Install the Python dependencies with:

```powershell
py -m pip install PyQt5 pandas matplotlib numpy pymongo openpyxl
```

### MongoDB

A local MongoDB server is required for automatic persistence between application sessions.

Default connection:

```text
mongodb://127.0.0.1:27017
```

MongoDB Database Tools (`mongodump`, `mongorestore`) are **not required**.

## Running from source

From the project directory:

```powershell
py main.py
```

## Project structure

```text
file-system-viewer/
│
├── main.py
├── database.py
├── gui.py
│
├── Images/
│   └── database.png
│
├── Manual/
│   └── manual.html
│
└── Exports/
    └── ...
```

`Exports` is created automatically when required.

## Notes

- Inaccessible or vanished filesystem entries are skipped during scanning.
- Symlinked directories are not recursively traversed.
- Very large datasets can be made easier to browse using pagination and filtering.
- Older saved scans may not contain newer metadata such as folder counts or detailed timings. Running **Gather Data** or **Update Data** refreshes them.

## Icon attribution

Database icon:

[Smashicons - Flaticon](https://www.flaticon.com/free-icons/database)

---

Repository: [Nick-Bounatsos/file-system-viewer](https://github.com/Nick-Bounatsos/file-system-viewer)
