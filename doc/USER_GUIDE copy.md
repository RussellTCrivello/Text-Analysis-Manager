# Text Analysis Manager — Complete User Guide

This guide explains how to use the project, how it works, how you interact with it, what benefits you get, and a detailed breakdown of every interface.

---

## 1. What Is This Project?

**Text Analysis Manager** is a desktop application for organizing, analyzing, and reporting research data. You can:

- **Store** information sources (people, organizations, websites, etc.)
- **Attach** content (articles, notes, summaries) to those sources
- **Analyze** content (classify, list people/places, add coordinates, sides)
- **View** everything in one place (All Data) and on a **Timeline**
- **Build reports** with SQL or a visual query builder, add charts, and export to PDF, Excel, CSV, or print

The app uses a **local SQLite database** (no server). Data is stored under `%APPDATA%\TextAnalysisManager\` on Windows when you run the packaged app, or next to the project when you run from source.

---

## 2. How to Use the Project

### 2.1 Running the Application

- **From source (development):**  
  `python mainwindow.py` (or run `mainwindow.py` from your IDE).  
  The database file `research_db.sqlite` is created in the project folder (or in your home directory if the project folder is not writable).

- **As installed/packaged app:**  
  Launch “Text Analysis Manager” from the Start Menu or desktop shortcut.  
  The database and config live in `%APPDATA%\TextAnalysisManager\`.

On first run, the app creates the database and tables automatically. If creation fails, you’ll see an error with the database path and suggestions (permissions, disk space, antivirus).

### 2.2 Typical Workflow

1. **Sources** — Add your information sources (name, type, link, importance, country, city, description, etc.).
2. **Contents** — Add content (title, text, attachments, importance, date) and link each item to a source.
3. **Analysis** — For each content item you can add analysis: classification, people, places, coordinates, sides, date.
4. **All Data** — Browse the combined view, filter by type (source/content/analysis), search, use date filters, and use Quick View or Generate Report.
5. **Timeline** — See events/content chronologically; click an event to see details in the preview panel.
6. **Reports** — Run SQL or use the visual query builder, view results, add charts, customize the report preview, and export (PDF, Excel, CSV, print).

You can jump between tabs via the tab bar or **View** menu (Ctrl+1 … Ctrl+6).

---

## 3. How It Works (High Level)

- **UI:** PyQt5. One main window with a tab widget; each tab is a dedicated module (Sources, Contents, Analysis, All Data, Timeline, Reports).
- **Data:** SQLite database with three main tables: `sources`, `contents`, `content_analysis`. Contents reference sources; analysis references contents. The app uses a single connection (and closes it on exit).
- **Logic:**  
  - **DatabaseManager** (in `db/db_manager.py`) performs all reads/writes.  
  - Tabs load data when they become visible (lazy loading).  
  - Toolbars are built from config (CRUD, export, search, date filter, page-specific buttons).  
  - Export uses shared utilities (print, PDF, Excel, Word, CSV, JSON, XML).
- **Settings:** Language (e.g. English, Arabic, Turkish), theme (light/dark), font size, timeline density, and accessibility options are stored via **ConfigManager** and applied globally (including RTL for Arabic).
- **Backup/Restore:** Tools → Backup & Restore uses the same data directory; you can backup/restore the database and related files.

---

## 4. User Interaction Summary

| Action | Where | What happens |
|--------|--------|--------------|
| Add/Edit/Delete records | Sources, Contents, Analysis tabs | Dialogs open; data is validated and saved to DB; table refreshes. |
| Search | Toolbar on data tabs | Filters table rows by text across columns. |
| Date filter | Toolbar (From/To) | Filters by date (creation/content/analysis depending on tab). |
| Pagination | Bottom of table tabs | Change page or page size; table shows the current page. |
| Export | Toolbar “Export” or per-format buttons | Unified export dialog (choose columns + format) or direct PDF/CSV/Excel/Word. |
| Print | Toolbar | Column selection dialog → print dialog. |
| Duplicate / Statistics / Map / Compare / etc. | Tab-specific toolbar buttons | Each button runs one feature (e.g. duplicate record, show stats, open map, compare analyses). |
| Quick View / Preview | All Data, Timeline, Contents | Shows full record or event in a dialog or side panel. |
| Reports | Reports tab | Write SQL or use visual builder → Execute → see Results; add chart; set report title and options → Preview → Print/Export. |
| Settings | Tools → Settings | Change language, theme, font size, timeline density, accessibility; OK applies and refreshes UI. |
| Backup / Restore / Reset | Tools menu | Backup/Restore dialog or Reset (with confirmation); then data is reloaded. |
| Help / Shortcuts / About | Help menu | Help window, keyboard shortcuts dialog, About. |

---

## 5. Benefits You Get

- **Single place** for sources, content, and analysis instead of scattered files.
- **Structured data** (sources → contents → analysis) with links and dates.
- **Search and filters** (text + date) and **pagination** on large sets.
- **Unified export** with column choice and multiple formats (PDF, Excel, Word, CSV, JSON, XML).
- **Timeline** to see when things happened.
- **Reports** with custom SQL or visual queries, charts, and print/export.
- **Multilingual UI** (e.g. English, Arabic, Turkish) with **RTL** for Arabic.
- **Themes** (light/dark) and **accessibility** options.
- **Backup & Restore** to protect your data.
- **Audit trail** for create/update/delete on main tables (for accountability).
- **No internet required** for core use; only “View on Map” opens a browser.

---

## 6. Detailed Explanation of Each Interface

### 6.1 Main Window

- **Title bar:** Application title (translated). Icon if available.
- **Menu bar:**
  - **File:** Exit (Ctrl+Q).
  - **View:** Switch to tab (Ctrl+1 = Sources … Ctrl+6 = Reports).
  - **Tools:** Settings, Backup & Restore, Reset, Print Settings, Manage Attachments, Import Data (Ctrl+I), Performance Monitor.
  - **Help:** Help (F1), Keyboard Shortcuts, About.
- **Central area:** A single **tab widget** with six tabs. Tabs can expand and show scroll buttons if needed.
- **Status bar:** Short messages (e.g. “Ready”, or feedback after actions).

When you switch tabs, the newly selected tab loads its data if it hasn’t yet (lazy load). After changing language in Settings, the whole UI (menus, tab labels, toolbars, dialogs) is refreshed and direction (RTL/LTR) is applied.

---

### 6.2 Sources Tab (Interface Detail)

**Purpose:** Manage *information sources* (who/what you get information from).

**Layout:**

- **Toolbar (top):**
  - **Add** — Opens “Add Source” dialog; on Save, inserts into `sources` and refreshes the table.
  - **Edit** — Opens “Edit Source” for the selected row; on Save, updates and refreshes.
  - **Delete** — Deletes selected source (with confirmation). Contents linked to it can be cascade-deleted depending on DB design.
  - **Refresh** — Reloads the table from the database.
  - **Export** — Opens the **unified export** dialog (choose columns, format, file path); then export runs.
  - **Print** — Column selection → print dialog.
  - **Search** — Text box: filters rows by any column containing the typed text.
  - **Date filter** — “From” and “To” date pickers; filters by source date (e.g. date_creation/date_entry).
  - **Import Sources** — Opens file picker for CSV; maps columns (name, type, link_sources, importance, country, city, description, accounts, note, ownership) and inserts rows; shows count and errors.
  - **Duplicate** — Copies selected source (name gets a “(Copy)” suffix), opens Add dialog with prefilled data; Save creates a new record.
  - **Statistics** — Shows a summary: total count, count by type, by country, average importance (as %).

- **Table:** Columns include ID, Name, Type, Link, Importance, Country, City, Description, Accounts, Note, Ownership, Date Entry, Date Creation, Date Modified. Row numbers in the first column. Sorting by column header is enabled. Selection: one row.

- **Pagination (bottom):** Page number, page size, total items; change page or size to update the visible set.

**User flow:** Add or import sources → optionally edit → use Search/Date filter to narrow → Export or Print when needed. Duplicate and Statistics support quick reuse and overview.

---

### 6.3 Contents Tab (Interface Detail)

**Purpose:** Manage *content* (articles, notes, summaries) and link each to a **source**.

**Layout:**

- **Toolbar:**
  - CRUD: **Add, Edit, Delete, Refresh.**
  - **Export** (unified), **Print.**
  - **Search**, **Date filter.**
  - **Import Contents** — CSV import for contents (title, content_data, attachments, note, importance, dates, sources_id, etc.).
  - **Duplicate** — Copy selected content (title + “(Copy)”), open Add dialog; save as new.
  - **View Attachments** — For selected row, reads the `attachments` field (e.g. semicolon-separated paths), opens attachment preview dialog (first file).
  - **Link to Analysis** — Opens “Add Content Analysis” dialog with `content_id` preset to the selected content; after Save, a new analysis record is created.
  - **Preview Content** — Dialog with title, source, date, full content text, and note.

- **Table:** ID, Source ID, Source Name, Title, Content Data, Importance, Attachments, Note, Date Content, Date Creation, Date Modified.

- **Pagination:** Same idea as Sources.

**User flow:** Add content and set its source → optionally add attachments and notes → use “Link to Analysis” to create analysis from this tab → use Preview to read full text.

---

### 6.4 Analysis Tab (Interface Detail)

**Purpose:** Manage *content analysis* records (classification, people, places, coordinates, sides, dates) linked to **contents**.

**Layout:**

- **Toolbar:**
  - CRUD: **Add, Edit, Delete, Refresh.**
  - **Export** (unified), **Print.**
  - **Search**, **Date filter.**
  - **Import Analysis** — CSV import for analysis (content_id, list_names_people, list_names_places, coordinates, classification, list_sides, date_analysis, etc.).
  - **Duplicate** — New analysis with same data (except id/dates); dialog to confirm/link to same or other content.
  - **View Map** — For selected row, takes first coordinate from `coordinates` (e.g. "lat,lon"), opens Google Maps in the default browser.
  - **Compare** — Uses current filtered data; opens a comparison table (up to 10 rows) with ID, classification, people, places, coordinates, sides.
  - **Summary** — Stats: total records, by classification, unique people/places, count with coordinates; shown in a message box.

- **Table:** ID, Content ID, Source Name, Classification, People, Places, Coordinates, Sides, Date Analysis, Date Creation, Date Modified.

- **Pagination:** Same pattern.

**User flow:** Add analysis (choose content) → fill classification, people, places, coordinates, sides → use View Map for geography, Compare for multiple rows, Summary for overview.

---

### 6.5 All Data Tab (Interface Detail)

**Purpose:** **Read-only** unified view of sources, contents, and analysis in one table, with filtering and preview.

**Layout:**

- **Header:** Title “All Data” and a **Read-only** badge.
- **Toolbar:** No Add/Edit/Delete. **Refresh**, **Export** (unified), **Print**, **Search**, **Date filter**, **Header settings** (global header for print/export).
- **Type filter (group):**
  - Dropdown: **All types**, **Sources**, **Contents**, **Analysis.**  
  - Colors: sources (green), content (orange), analysis (purple). Rows are tinted by type.
  - **Quick View** — Opens a dialog with the selected row’s type badge and all fields.
  - **Generate Report** — Switches to the Reports tab (and can pass context); or informs that you can generate a report from current data.
- **Splitter:**
  - **Top:** Table — columns: Record Type, Source Name, Title, Content Data, Classification, Importance, Date Content, Date Creation. Row numbers; sortable; one selection.
  - **Bottom:** **Text preview panel** — Shows details of the selected row (no editing).
- **Pagination** and **status line** at bottom (e.g. “Showing 1–20 of 45 records”).

**Behavior:** Data comes from `DatabaseManager.get_all_data_unified()` (combined/joined data). Filters: type (dropdown) + search text + date range. Pagination applies to the filtered set. Double-clicking a row typically opens Quick View. Export uses the current filtered set and column selection in the export dialog.

---

### 6.6 Timeline Tab (Interface Detail)

**Purpose:** Show **chronological** events (from contents and possibly analysis) so you can see *when* things happened.

**Layout:**

- **Title:** “Timeline.”
- **Splitter:**
  - **Timeline widget (main area):** Events grouped by time (e.g. by day/month/year). Each event is a card with date, title, summary, source, type. Density (compact/comfortable/expansive) is configurable in Settings. Clicking an event selects it.
  - **Preview panel:** Shows the selected event’s full details (same data as in the card, possibly more fields).
- **Status:** Message such as “No events” or “Loaded N events.”

**Data:** `DatabaseManager.get_timeline_events()` returns events (from contents and related data). The timeline widget draws sections and cards; selection is connected to the preview panel.

**User flow:** Open Timeline → see events in order → click one → read details in the panel. Change density in Settings if you want more/less spacing.

---

### 6.7 Reports Tab (Interface Detail)

**Purpose:** Build and run **custom reports**: run SQL or use a visual query builder, see results, add charts, and export or print.

**Layout (two main panels):**

**Left panel (tabs):**

1. **Query Builder**
   - **Sub-tabs: SQL Mode / Visual Mode.**
   - **SQL Mode:**
     - **SQL editor** with syntax highlighting (keywords, strings, numbers, comments, table names). Placeholder shows example queries.
     - **Query templates:** Buttons that insert predefined SQL (e.g. all sources, all contents, sources by type/country, content count per source, time-based, stats, geographic, content with/without analysis, etc.).
     - **Database structure:** Tree of tables (`sources`, `contents`, `content_analysis`) and columns with types — for reference while writing SQL.
     - **Clear** and **Execute** — Execute runs the SQL against the app’s SQLite DB; results go to the right panel.
   - **Visual Mode:**
     - **Select tables:** Checkboxes for sources, contents, content_analysis.
     - **Select fields:** Multi-select list of columns (from selected tables).
     - **Filters / options:** Build WHERE/ORDER BY/LIMIT visually (exact widgets depend on implementation).
     - Running the visual query generates SQL and executes it; results appear on the right.

2. **Chart Designer**
   - Configure a chart from current **report results** (or from scratch): chart type (bar, line, pie, etc.), which columns for X/series, colors, title, legend. The chart can be embedded in the report preview.

**Right panel (tabs):**

1. **Results**
   - **Results table:** Columns and rows from the last executed query. Scrollable.
   - **Stats:** Total rows, number of columns.
   - **Create chart from data** — Opens chart designer (or similar) so the current results can be turned into a chart for the report.

2. **Report Preview**
   - **Report title** (editable).
   - **Include chart** checkbox.
   - **Refresh** — Regenerates the preview (table + optional chart).
   - **Preview area** — Read-only HTML/text view of the report (table + chart image if enabled). This is what gets printed or exported.

**Top toolbar (Reports):**

- **New** — Clear query and results; start a new report.
- **Save** — Save current report (query + options) to a file in the reports directory (name + description).
- **Load** — List saved reports; select one to load (query and settings restored).
- **Print** — Print the report preview (current title and layout).
- **Print preview** — Preview before printing.
- **Export PDF / Excel / CSV** — Export the report (data and/or chart) to file.
- **Orientation** and **Page size** — Portrait/Landscape; A4, Letter, A3, Legal.

**User flow:** New report → write SQL or use Visual mode → Execute → see Results → optionally “Create chart from data” and add it in Chart Designer → set report title and “Include chart” → Refresh preview → Print or Export PDF/Excel/CSV. Save/Load lets you reuse report definitions.

---

### 6.8 Settings Dialog (Tools → Settings)

**Purpose:** Configure language, theme, font size, timeline density, and accessibility.

**Tabs (typical):**

- **General:**  
  Language (e.g. English, Arabic, Turkish), Theme (Light/Dark), Font size (e.g. 8–16 pt), Timeline density (Compact / Comfortable / Expansive).  
  Changing language applies RTL for Arabic and refreshes all labels and menus.

- **Accessibility:**  
  Options such as high contrast, larger click targets, keyboard navigation, screen reader hints (depending on implementation).  
  Keyboard shortcuts are also listed under Help → Keyboard Shortcuts.

**Behavior:** Values are read from/saved to ConfigManager. On OK, the main window calls `refresh_ui()` so that theme, language, direction, and font size are applied everywhere.

---

### 6.9 Other Dialogs and Tools

- **Backup & Restore (Tools → Backup & Restore):** Choose backup folder, create backup (e.g. DB + config) or restore from a backup; then all tabs reload data.
- **Reset (Tools → Reset):** Confirmation dialog; resets DB or selected data; then reloads tabs.
- **Print Settings (Tools → Print Settings):** Global header/footer and layout options for printing (used by Print across tabs).
- **Manage Attachments (Tools → Manage Attachments):** Manage attachment files linked to content (list, add, remove, open).
- **Import Data (Tools → Import Data, Ctrl+I):** Choose target table (sources / contents / content_analysis), then run the import preview dialog (e.g. CSV) and complete import; status bar shows result.
- **Performance Monitor (Tools → Performance Monitor):** Diagnostic view (e.g. DB size, slow queries, memory) for troubleshooting.
- **Help (F1):** Opens the help system (content depends on implementation).
- **Keyboard Shortcuts:** Dialog listing Ctrl+1–6, Ctrl+Q, Ctrl+I, F1, etc.
- **About:** App name and version.

---

## 7. Data Model (Short Reference)

- **sources:** id, name, type, link_sources, importance (0–1), country, city, description, accounts, note, ownership, date_entry, date_creation, date_modified.
- **contents:** id, title, content_data, attachments, note, importance (0–1), date_content, date_creation, date_modified, **sources_id** (FK).
- **content_analysis:** id, **content_id** (FK), list_names_people, list_names_places, list_coordinates (or coordinates), classification, list_sides, date_analysis, date_creation, date_modified.

Unified “All Data” and timeline events are built by joining these tables and normalizing column names for display.

---

## 8. Keyboard Shortcuts (Summary)

| Shortcut | Action |
|----------|--------|
| Ctrl+1 … Ctrl+6 | Switch to Sources … Reports tab |
| Ctrl+Q | Exit |
| Ctrl+I | Import Data |
| F1 | Help |

---

## 9. File and Data Locations

- **When running from source:** Database: project folder (or user home) as `research_db.sqlite`.
- **When running installed app:** Data directory: `%APPDATA%\TextAnalysisManager\` (database, config, backups, logs).
- **Reports (saved):** Stored in the reports subfolder under the same data directory (or as configured).

---

This guide covers how to use the project, how it works, how you interact with it, what benefits you get, and a detailed explanation of each interface (main window, all six tabs, Settings, and related dialogs). For step-by-step tutorials or CSV column names for import, refer to the in-app Help and the README.txt in the project root.
