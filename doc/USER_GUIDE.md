# Text Analysis Manager — User Guide

This guide is for **people who use** Text Analysis Manager. It explains what the program does, how to do everyday tasks, and what you see on each screen. No technical or programming knowledge is required.

---

## What Is Text Analysis Manager?

Text Analysis Manager helps you **organize and analyze research information** in one place. You can:

- **Save your sources** — Who or what provided the information (people, organizations, websites, etc.).
- **Save your content** — Articles, notes, or summaries, and link each one to a source.
- **Add analysis** — For each piece of content: classification, names of people and places, locations on a map, sides involved, and dates.
- **See everything together** — One combined list (All Data) and a Timeline showing when things happened.
- **Create reports** — Run ready-made or custom reports, add charts, and save or print as PDF, Excel, or CSV.

All your data is stored **on your own computer**. You do not need the internet to use the program, except when you choose “View on Map” (which opens a map in your browser).

---

## Getting Started

### Starting the Program

- **If the program is installed on your computer:**  
  Open it from the **Start menu** or from the **desktop shortcut** (e.g. “Text Analysis Manager”).
- **First time you run it:**  
  The program will create a place to store your data automatically. If something goes wrong, a message will tell you where it tried to save and what to check (e.g. permissions, disk space, antivirus).

### Where Is My Data Stored?

- **When you run the installed program:**  
  Your data is stored in a folder on your computer, for example:  
  **This PC → Your user folder → AppData → Roaming → TextAnalysisManager**  
  (The exact path may differ slightly by Windows version.)
- That folder contains your **main data file**, **settings**, **backups**, and **logs**. You can copy this folder to back up your data manually.

---

## The Main Screen

When you open the program you see:

- **Top:** The **menu bar** (File, View, Tools, Help) and the **window title** (e.g. “Text Analysis Manager”).
- **Middle:** **Six tabs** — Sources, Contents, Analysis, All Data, Timeline, Reports. Click a tab to switch to that section.
- **Bottom:** A **status bar** that shows short messages (e.g. “Ready” or a success message after you do something).

### Menus (Quick Reference)

- **File** — Exit the program (or press **Ctrl+Q**).
- **View** — Jump to a tab: Sources (Ctrl+1), Contents (Ctrl+2), Analysis (Ctrl+3), All Data (Ctrl+4), Timeline (Ctrl+5), Reports (Ctrl+6).
- **Tools** — Settings, Backup & Restore, Reset, Print Settings, Manage Attachments, Import Data (**Ctrl+I**), Performance Monitor.
- **Help** — Help (**F1**), Keyboard Shortcuts, About (program name and version).

---

## Recommended Way to Work

A typical way to use the program:

1. **Sources** — Add your information sources first (name, type, link, importance, country, city, description, etc.).
2. **Contents** — Add your content (title, text, attachments, importance, date) and **choose which source** it belongs to.
3. **Analysis** — For important content, add analysis: classification, people, places, map coordinates, sides, date.
4. **All Data** — When you want an overview, open this tab to see sources, contents, and analysis in one list. You can filter by type, search, and use dates.
5. **Timeline** — Open this tab to see your content and events in **time order**. Click an event to see its details.
6. **Reports** — When you need a report, open the Reports tab. You can use **ready-made report templates** or build a **custom report**, add a chart, then **print or export** (PDF, Excel, CSV).

You can switch between tabs anytime by clicking the tab name or using the View menu (or Ctrl+1 to Ctrl+6).

---

## Section 1 — Sources

**What it’s for:** Managing your **information sources** (who or what gave you the information).

### What You See

- **Toolbar at the top** with buttons.
- A **list (table)** of all your sources. Each row is one source. You can sort by any column by clicking the column header. The first column shows the row number.
- **At the bottom:** Page number and how many items you have (pagination). You can change the page or how many rows appear per page.

### Buttons and What They Do

| Button / control | What it does |
|------------------|--------------|
| **Add** | Opens a form to add a new source. Fill in the fields (name, type, link, importance, country, city, description, etc.) and save. The new source appears in the list. |
| **Edit** | Opens the same form with the **selected** source’s data so you can change it. You must click one row first to select it. |
| **Delete** | Deletes the **selected** source. The program will ask you to confirm. |
| **Refresh** | Reloads the list from your saved data (useful if you think something changed). |
| **Export** | Opens a window where you choose **which columns** to export and **in what format** (e.g. PDF, Excel, Word, CSV). Then you choose where to save the file. |
| **Print** | Lets you choose which columns to include, then opens the normal print window so you can print the list. |
| **Search** | A text box: type a word or phrase and the list shows only rows that contain that text in any column. |
| **Date filter** | “From” and “To” date boxes. Set a date range to see only sources within that range. |
| **Import Sources** | Lets you import many sources at once from a **CSV file** (e.g. from Excel saved as CSV). The program will try to match columns (name, type, link, importance, country, city, etc.) and show how many were imported and any errors. |
| **Duplicate** | Copies the **selected** source into a new one (the name will have “(Copy)” added). A form opens so you can adjust and save it as a new source. |
| **Statistics** | Shows a summary: total number of sources, how many by type, how many by country, and average importance. |

### Table Columns (Sources)

The list shows things like: **ID**, **Name**, **Type**, **Link**, **Importance**, **Country**, **City**, **Description**, **Accounts**, **Note**, **Ownership**, **Date Entry**, **Date Creation**, **Date Modified**. You can resize columns by dragging the border between column headers.

---

## Section 2 — Contents

**What it’s for:** Managing your **content** (articles, notes, summaries) and linking each one to a **source**.

### What You See

- Same kind of **toolbar** and **list** as in Sources, but the columns are for content (title, text, source, importance, attachments, dates, etc.).
- **Pagination** at the bottom.

### Buttons and What They Do

| Button / control | What it does |
|------------------|--------------|
| **Add** | Opens a form to add new content. You **choose which source** it belongs to, then enter title, text, attachments, note, importance, and dates. |
| **Edit** | Lets you change the **selected** content. Click a row first. |
| **Delete** | Deletes the **selected** content (with confirmation). |
| **Refresh** | Reloads the content list. |
| **Export** | Same as in Sources: choose columns and format, then save to a file. |
| **Print** | Choose columns and print the list. |
| **Search** | Type text to filter the list. |
| **Date filter** | Filter by date range. |
| **Import Contents** | Import many contents from a CSV file. You need a column that links to the source (e.g. source ID or name). |
| **Duplicate** | Creates a copy of the **selected** content (title gets “(Copy)”). You can then change and save it as new. |
| **View Attachments** | For the **selected** content, opens a viewer for the attached files (if any). |
| **Link to Analysis** | Opens the form to add a **new analysis** that is already linked to the **selected** content. Useful when you want to analyze this content right away. |
| **Preview Content** | Opens a window with the **full** content: title, source, date, full text, and note. Good for reading without editing. |

### Table Columns (Contents)

You’ll see: **ID**, **Source ID**, **Source Name**, **Title**, **Content Data** (the main text), **Importance**, **Attachments**, **Note**, **Date Content**, **Date Creation**, **Date Modified**.

---

## Section 3 — Analysis

**What it’s for:** Managing **analysis** of your content — classification, people, places, map coordinates, sides, and dates. Each analysis is linked to one piece of content.

### What You See

- **Toolbar** and **list** of analyses. Each row is one analysis linked to a content item.
- **Pagination** at the bottom.

### Buttons and What They Do

| Button / control | What it does |
|------------------|--------------|
| **Add** | Opens a form to add analysis. You **choose which content** it refers to, then enter classification, people, places, coordinates, sides, and date. |
| **Edit** | Edit the **selected** analysis. |
| **Delete** | Delete the **selected** analysis (with confirmation). |
| **Refresh** | Reload the list. |
| **Export** / **Print** / **Search** / **Date filter** | Same idea as in Sources and Contents. |
| **Import Analysis** | Import analyses from a CSV file (with a column that links to content). |
| **Duplicate** | Copy the **selected** analysis so you can save it as a new one (e.g. for another content). |
| **View Map** | For the **selected** analysis, if it has **coordinates** (latitude, longitude), opens your default browser and shows that location on a map. |
| **Compare** | Shows the **current list** (or filtered list) in a comparison view — up to 10 analyses side by side (e.g. classification, people, places, coordinates, sides). |
| **Summary** | Shows a short summary: total number of analyses, breakdown by classification, how many unique people and places, and how many have coordinates. |

### Table Columns (Analysis)

**ID**, **Content ID**, **Source Name**, **Classification**, **People**, **Places**, **Coordinates**, **Sides**, **Date Analysis**, **Date Creation**, **Date Modified**.

---

## Section 4 — All Data

**What it’s for:** Seeing **all** your sources, contents, and analyses in **one list**. This view is **read-only** — you cannot add, edit, or delete here; use the Sources, Contents, or Analysis tabs for that.

### What You See

- A label that says **“All Data”** and a **“Read-only”** badge.
- **Toolbar** with: Refresh, Export, Print, Search, Date filter, and Header settings (for how printed/exported pages look).
- A **filter area** with:
  - A **dropdown** to show **All types**, or only **Sources**, or only **Contents**, or only **Analysis**. Rows are color-coded by type (e.g. green for sources, orange for content, purple for analysis).
  - **Quick View** — Opens a window with **all** details of the **selected** row.
  - **Generate Report** — Takes you to the Reports tab so you can create a report from the current data.
- **Main area:**  
  - **Top part:** A **table** with columns like Record Type, Source Name, Title, Content Data, Classification, Importance, Date Content, Date Creation. Click a row to select it.  
  - **Bottom part:** A **preview panel** that shows the **details of the selected row** (you cannot edit here).
- **Bottom:** Page information (e.g. “Showing 1–20 of 45 records”) and pagination.

### What You Can Do

- **Filter** by type (dropdown), **search** by text, and **set a date range** to narrow the list.
- **Click a row** to see its full details in the preview panel.
- **Double-click** a row (or use **Quick View**) to open the full-detail window.
- **Export** or **Print** the current list (with column choice). What you export is what you see after filters and pagination.
- Use **Generate Report** to jump to Reports and build a report from this data.

---

## Section 5 — Timeline

**What it’s for:** Seeing your content and events in **time order** — what happened when.

### What You See

- A **title** “Timeline.”
- **Left (or top)** area: A **timeline** of events. Events are grouped by time (e.g. by day or month). Each event is shown as a **card** with date, title, a short summary, and source. You can **click** a card to select it.
- **Right (or bottom)** area: A **preview panel** that shows the **full details** of the **selected** event.
- A **status line** at the bottom (e.g. “No events” or “Loaded 25 events”).

### What You Can Do

- **Scroll** through the timeline to see older or newer events.
- **Click** an event to read its details in the preview panel.
- In **Settings** (Tools → Settings) you can change **Timeline density** (Compact, Comfortable, or Expansive) to make the cards smaller or larger and more spaced out.

---

### Timeline in detail: data, filters, charts, and benefits

This section explains the Timeline from a **data analysis** point of view: what you see, why it helps, and how to use it without any technical knowledge.

**Why the Timeline is useful**

- **See when things happened** — All your sources, content, and analyses that have a date are shown in **time order**. You can spot busy periods, gaps, or trends at a glance.
- **One place for different kinds of records** — Sources (e.g. when you added a source), content (e.g. publication or event date), and analyses (e.g. when you analysed a piece of content) are combined into a single chronological list. Each “event” is one of these.
- **Explore by time, then drill down** — You filter and sort by date or by category, then click an event to read the full details in the preview panel. That supports quick scanning and deeper reading.

**What data is shown**

- **Events** are built from three types of data: **sources**, **contents**, and **analyses**. Only items that have at least one date (e.g. source entry date, content date, or analysis date) appear on the Timeline. The program picks the best date for each record (e.g. content date or analysis date when available).
- **Each event card** shows:
  - **Date and time** (and day of week when available).
  - **Title** — Usually the content title, or a short label for the record.
  - **Summary** — A short extract or description of the content.
  - **Source** — Which source the content or analysis comes from (e.g. newspaper, person, organisation).
  - **Badges** — People, places, and classification (if you have added analysis). These help you see at a glance who and what the event is about.

**Statistics at the top**

- Four summary numbers appear above the timeline:
  - **Total** — How many events exist in your data (all sources, contents, and analyses with dates).
  - **Filtered** — How many events remain after you apply date range, search, and filters (People, Places, Classification). This tells you how much you are currently looking at.
  - **Sources** — How many events come from “source” records (e.g. when you added or registered a source).
  - **Analyses** — How many events come from “analysis” records. The rest are from “content” records.

These numbers update as you change filters, so you can see the effect of your choices immediately.

**Filters and how they work**

- **Date range (From / To)** — You choose a start and end date. Only events whose date falls in this range are shown. Useful to focus on a specific period (e.g. one year or one month).
- **Search** — A text box that searches across title, content text, classification, people, places, and source name. Only events that match your search term stay in the list. The “Filtered” count updates accordingly.
- **People** — A dropdown/list of people that appear in your analyses. Choosing a person shows only events where that person is mentioned (in the “people” list for that record).
- **Places** — Same idea for places: choose a place to see only events linked to that place (from analysis or from the source’s city/country).
- **Classification** — Filter by analysis classification (e.g. topic or category). Only events with that classification are shown.
- **Clear** — Resets the date range (and other filters if you use the “Clear filters” in the data section). Use it to go back to viewing the full date range or full set.

Filters work together: the Timeline shows only events that match **all** active filters (date range + search + people + places + classification). So you can combine “last year” + “a specific person” + “a specific classification” to narrow down to a very focused set of events.

**Sorting**

- **Sort by** — You can order the list by: **Date**, **People**, **Places**, **Classification**, or **Source**. For example, “Sort by Date” keeps the time order; “Sort by People” groups events by the people mentioned.
- **Order** — **Latest first** (newest at top) or **Chronological** (oldest at top). This applies to whatever you chose in “Sort by.”

**Charts and graphs**

- Above the list of event cards there is a **chart** that summarizes your (filtered) events. You can change the chart type from a dropdown:
  - **Timeline / Event distribution over time** — How many events fall on each date. Helps you see peaks and quiet periods.
  - **Event distribution by type** — How many events are sources, contents, or analyses. Shows the mix of record types.
  - **Activity by day of week** — How many events fall on each weekday. Useful for weekly patterns (e.g. more activity on certain days).
  - **Monthly aggregation** — Events grouped by month. Good for seeing trends over months or years.
  - **Classification distribution** — How many events have each classification. Shows which topics or categories dominate.

The chart always uses the **currently filtered** events, so when you change the date range or other filters, the chart updates to match. That way, the graph and the list always refer to the same subset of data.

**Analysis panel**

- Next to the chart there is a short **Timeline analysis** summary. It shows, for the filtered events:
  - Total number of events.
  - Breakdown by type (source, content, analysis) with counts and percentages.
  - Top classifications (e.g. top five) with counts and percentages.
  - Most active period (e.g. the month with the most events).

This gives you a quick textual summary of the same data that the chart and the list are showing, without having to count or calculate yourself.

**Event cards and preview**

- **Cards** — Each event is shown as a card with date, title, summary, source, and badges (people, places, classification). You can scroll through the list; if there are many events, **pagination** at the bottom lets you move by page and choose how many events per page.
- **Density** — You can switch between **Compact**, **Comfortable**, and **Expansive** to make cards smaller (more on screen) or larger (easier to read). This can also be set in **Tools → Settings** under “Timeline density.”
- **Click a card** — The **preview panel** on the right (or below, depending on layout) shows the **full details** of that event: all fields for that source, content, or analysis. So you browse the timeline and open a single event to read everything.

**Print and export**

- **Print** — Prints the timeline (the list of event cards and layout) so you can have a paper copy or save as PDF from the print dialog.
- **Export** — Opens a dialog where you can export timeline events to **Word**, **Excel**, or **PDF**. You can choose:
  - **Current page** — Only the events on the current page.
  - **All filtered** — All events that pass your current filters (recommended for reports).
  - **All data** — Every timeline event, ignoring filters.

Export is useful for sharing with others, for reports, or for further analysis in a spreadsheet or document.

**Summary of benefits**

- **Chronological view** — See all dated sources, content, and analyses in one time-ordered list.
- **Quick overview** — Statistics and charts show totals, breakdowns by type, and patterns (by day, month, or classification) without leaving the tab.
- **Focused exploration** — Date range, search, and filters (People, Places, Classification) let you narrow down to the subset you care about; the chart and analysis panel update to that subset.
- **Drill-down** — Click any event to read full details in the preview panel.
- **Flexible presentation** — Sort by date, people, places, classification, or source; choose card density; print or export to Word, Excel, or PDF for sharing or archiving.

---

## Section 6 — Reports

**What it’s for:** Creating **reports** from your data — lists, summaries, or statistics — and then **printing** them or **exporting** to PDF, Excel, or CSV. You can also add **charts**.

### Layout (Two Main Parts)

- **Left side:** Two sub-tabs — **Query Builder** (to choose or build what data the report shows) and **Chart Designer** (to add or edit a chart).
- **Right side:** Two sub-tabs — **Results** (the data that will go into the report) and **Report Preview** (how the report will look when printed or exported).
- **Top:** Buttons for New, Save, Load, Print, Print preview, Export PDF, Export Excel, Export CSV, and options for **page orientation** (Portrait/Landscape) and **page size** (A4, Letter, A3, Legal).

### Query Builder (Left Side)

This is where you decide **what data** the report shows.

- **SQL Mode**  
  - There is a **text area** where you can write a **query** (advanced).  
  - Below it you’ll see many **buttons** — each is a **ready-made report template** (e.g. “All sources”, “All contents”, “Sources by country”, “Content count per source”, “Recent content”, “Analyses by classification”, etc.). **Clicking a button** puts that query into the text area.  
  - There is also a **list of tables and columns** (sources, contents, content_analysis and their fields) so you can see what you can ask for.  
  - **Clear** erases the text area. **Execute** runs the query and fills the **Results** tab on the right.

- **Visual Mode**  
  - You **select which tables** to use (sources, contents, content_analysis) with checkboxes.  
  - You **select which fields** (columns) to show in the report from a list.  
  - You can set **filters and options** (e.g. date range, limits) using the on-screen controls.  
  - When you run the query, the program builds it for you and shows the result in **Results**.

**In short:** If you prefer not to write a query, use the **template buttons** in SQL Mode or the **Visual Mode** to build the report by clicking and selecting.

### Results (Right Side)

- After you **Execute** a query, the **Results** tab shows a **table** with the rows and columns that the report will use.
- You’ll see **total number of rows** and **number of columns**.
- A button **“Create chart from data”** (or similar) lets you open the **Chart Designer** to turn this data into a chart that can be included in the report.

### Chart Designer (Left Side)

- Here you can **create or edit a chart** (e.g. bar, line, pie).
- You choose **which data** to use (e.g. which column for the horizontal axis, which for the bars or slices), **colors**, **title**, and **legend**.
- The chart can be **included in the Report Preview** when you check “Include chart” there.

### Report Preview (Right Side)

- You can type a **Report title** that will appear at the top of the printed or exported report.
- A checkbox **“Include chart”** lets you include the chart you designed (if any).
- **Refresh** updates the preview so it shows the current data and chart.
- The **preview area** shows how the report will look when you print or export. This is what gets sent to the printer or saved as PDF/Excel/CSV.

### Report Toolbar (Top)

| Button / option | What it does |
|-----------------|--------------|
| **New** | Clears the current query and results so you can start a new report. |
| **Save** | Saves the current report (query and settings) with a name and description so you can **Load** it later. |
| **Load** | Opens a list of **saved reports**. Choose one to load; the query and settings are restored. |
| **Print** | Prints the **Report Preview** (the table and, if enabled, the chart). |
| **Print preview** | Shows how the report will look on paper before you print. |
| **Export PDF** / **Export Excel** / **Export CSV** | Saves the report (and chart if included) to a file in the format you choose. |
| **Orientation** | Switch between Portrait and Landscape. |
| **Page size** | Choose A4, Letter, A3, or Legal. |

### Typical Steps to Create a Report

1. Open the **Reports** tab.
2. In **Query Builder**, either click a **template button** (e.g. “All sources” or “Sources by country”) or use **Visual Mode** to pick tables and fields.
3. Click **Execute**. Check the **Results** tab to see if the data is what you want.
4. (Optional) Click **“Create chart from data”** and design a chart in **Chart Designer**.
5. Go to **Report Preview**. Enter a **title**, check **Include chart** if you want the chart, then click **Refresh**.
6. Use **Print** or **Export PDF/Excel/CSV** to print or save the report.
7. If you want to reuse this report later, click **Save** and give it a name. Next time, use **Load** to open it again.

---

## Settings (Tools → Settings)

Here you change how the program looks and behaves.

- **Language** — Choose the interface language (e.g. English, Arabic, Turkish). If you choose Arabic, the layout switches to **right-to-left** and all labels and menus update.
- **Theme** — Light or Dark.
- **Font size** — Make text larger or smaller (e.g. 8–16 pt).
- **Timeline density** — How compact or spacious the Timeline cards are: Compact, Comfortable, or Expansive.

Other tabs (e.g. **Accessibility**) may offer options for contrast, keyboard use, or screen readers. **Help → Keyboard Shortcuts** lists all shortcut keys.

When you click **OK**, your choices are saved and the whole program updates (language, theme, font, timeline spacing).

---

## Other Tools (Tools Menu)

| Tool | What it does |
|------|----------------|
| **Backup & Restore** | Create a **backup** of your data (saved to a folder you choose) or **restore** from a previous backup. After restore, the program reloads all tabs. |
| **Reset** | Resets data or parts of the program. The program will **ask you to confirm**. After reset, it reloads the data. Use with care. |
| **Print Settings** | Set **global** options for headers and layout when printing (used when you click Print in any tab). |
| **Manage Attachments** | Open a window where you can see, add, remove, or open **attachment files** linked to your content. |
| **Import Data** (Ctrl+I) | Import data from a file (e.g. CSV). You first **choose what to import into**: Sources, Contents, or Analysis. Then you pick the file and complete the import. The status bar shows how many items were imported. |
| **Performance Monitor** | Opens a technical view (e.g. data size, speed) for troubleshooting. You can ignore this unless you need to diagnose a problem. |

---

## Backing up, restoring, and moving your data

The program stores all your data in one place on your computer. You can **create a backup** (a single file that contains your sources, contents, and analyses), **restore** from a backup to get your data back, and **move your data to another computer** by creating a backup, copying it to the other device, and restoring it there.

### Creating a backup

1. In the menu, click **Tools** → **Backup & Restore**.
2. In the **Backup** area at the top, read the short description, then click **Create backup** (or the button with the backup icon).
3. When asked to confirm, click **Yes**.
4. Wait until the program says the backup was created successfully. The message will tell you **where the backup file was saved** (for example, a folder named “backups” inside your program data folder, or a path like `…\AppData\Roaming\TextAnalysisManager\backups`).
5. That backup is a **single file** (name like `backup_manual_20250220_143022.sqlite`). You can **copy this file** to a USB drive, cloud folder, or another computer.

**Tip:** Create a backup regularly (e.g. weekly) so you always have a recent copy if something goes wrong.

### Restoring your existing data (on this computer)

If you already have backups **on this computer** (listed in the Backup & Restore window):

1. Open **Tools** → **Backup & Restore**.
2. In the **Restore** area, you will see a **table** of backups (filename, size, date).
3. **Click one row** to select the backup you want.
4. Choose what you want to do:
   - **Restore** — Replaces **all** current data with the data from that backup. Your current data will be overwritten. The program will ask you to confirm and will suggest **restarting the program** after restore.
   - **Merge** — **Adds** the data from the backup to your current data. Nothing is deleted; the backup’s sources, contents, and analyses are added. Use this when you want to combine two sets of data.
5. After you click **Restore** or **Merge**, confirm when asked. Wait until the program says the operation finished successfully. If you chose **Restore**, close and reopen the program so everything is refreshed.

### Restoring from a backup file (e.g. after moving to another computer)

If your backup is **a file** you copied from somewhere else (USB, another PC, Downloads folder, etc.):

1. Open **Tools** → **Backup & Restore**.
2. Click **Restore from file** (or “Restore from file” / “Import backup”).
3. In the file window, go to the folder where you put the backup (e.g. USB drive, Desktop, Documents) and **select the backup file** (e.g. `backup_manual_20250220_143022.sqlite`). Click **Open**.
4. The program will check the file and show a **preview** (e.g. how many sources, contents, and analyses it contains, and the file size).
5. If the file is **not** already in the program’s backup folder, you may see an option **“Copy to backup folder after import”**. If you check it, the program will keep a copy of this file in its own backup list for later.
6. Choose how to use the backup:
   - **Restore** — Replaces **all** current data with the data from this file. Use this when you are **moving to a new computer** or want to go back to this backup completely.
   - **Merge** — **Adds** the backup’s data to your current data without deleting what you have.
7. Click **Restore** or **Merge**, then confirm. Wait until the program reports success. After a **Restore**, close and reopen the program.

### Transferring your data to another computer (step-by-step)

**On the computer where your data is now:**

1. Open Text Analysis Manager.
2. **Tools** → **Backup & Restore**.
3. Click **Create backup**. Confirm and wait until you see the success message and the **backup location** (folder path).
4. Open that folder (e.g. in File Explorer). You will see a file named like `backup_manual_YYYYMMDD_HHMMSS.sqlite`.
5. **Copy this file** to a USB stick, a cloud folder (OneDrive, Google Drive, etc.), or send it to the other computer by email or another method.

**On the other computer:**

1. Install Text Analysis Manager if it is not already installed.
2. **Copy the backup file** from the USB (or cloud, or wherever you put it) to that computer (e.g. Desktop or Documents so you can find it easily).
3. Open Text Analysis Manager.
4. **Tools** → **Backup & Restore**.
5. Click **Restore from file**.
6. In the file window, go to where you put the backup file, **select it**, and click **Open**.
7. Check the preview (number of sources, contents, analyses). If you want this backup to also appear in the backup list on this computer, check **“Copy to backup folder after import”** (if shown).
8. Click **Restore** (to replace any existing data on this computer with your transferred data). Confirm when asked.
9. When the program says the restore finished successfully, **close the program and open it again** so everything loads correctly.

After that, the other computer will have the same sources, contents, and analyses as in the backup you created.

---

## Help and Shortcuts

- **Help** (F1) — Opens the program’s help.
- **Keyboard Shortcuts** — Opens a list of shortcut keys.
- **About** — Shows the program name and version.

### Useful Shortcuts

| Keys | Action |
|------|--------|
| **Ctrl+1** | Go to Sources tab |
| **Ctrl+2** | Go to Contents tab |
| **Ctrl+3** | Go to Analysis tab |
| **Ctrl+4** | Go to All Data tab |
| **Ctrl+5** | Go to Timeline tab |
| **Ctrl+6** | Go to Reports tab |
| **Ctrl+Q** | Exit the program |
| **Ctrl+I** | Import Data |
| **F1** | Help |

---

## What You Get From Using the Program

- **One place** for all your sources, content, and analysis instead of many separate files.
- **Clear links** between sources → content → analysis, with dates.
- **Search** and **filters** (text and date) and **pagination** so you can work with large amounts of data.
- **Export** to PDF, Excel, Word, CSV (and more), choosing which columns to include.
- **Timeline** to see when things happened.
- **Reports** using ready-made templates or your own choices, with charts and print/export.
- **Multiple languages** (e.g. English, Arabic, Turkish) and **right-to-left** layout for Arabic.
- **Light or dark** theme and **accessibility** options.
- **Backup & Restore** to keep your data safe.
- **No internet needed** for normal use; only “View on Map” opens your web browser.

---

## If Something Goes Wrong

- **The program won’t start or says data could not be created:**  
  Check that you have enough **disk space** and that **antivirus** or **permissions** are not blocking the program from writing to the data folder. The error message usually shows the folder path it tried to use.

- **My data disappeared:**  
  If you did a **Reset** or **Restore** from an old backup, the program shows the data from that moment. Use **Backup & Restore → Restore** only when you are sure you want to go back to that backup.

- **I want to transfer my data to another computer:**  
  Use **Tools → Backup & Restore** to create a backup, copy the backup file to the other device (e.g. USB or cloud), then on the other computer open **Backup & Restore → Restore from file** and choose that file. See the section **“Backing up, restoring, and moving your data”** in this guide for full step-by-step instructions (creating a backup, restoring existing data, and moving to another computer).

- **More help:**  
  Use **Help (F1)** and **Keyboard Shortcuts** from the Help menu. Log files are usually stored in the same data folder (e.g. in a “logs” subfolder) and can be used by support to diagnose issues.

---

This user guide describes the full system for the person **using** the program: what each part of the screen is for and how to complete everyday tasks. For the latest version and support, see the program’s About screen or the README that came with your installation.
