# Backup Import & Merge – Complete Guide

This document explains how backup import works, all supported scenarios, validation, and how to run comprehensive tests.

---

## Import Process Overview

| Action | Description | Use Case |
|--------|-------------|----------|
| **Replace** | Full restore – overwrites current DB with backup | Recover from backup, switch to another DB |
| **Merge** | Adds backup data to current DB, skips duplicates | Combine data from another machine, merge backups |

---

## Supported Scenarios (All Possibilities)

### 1. Merge Scenarios

| Scenario | Result |
|----------|--------|
| Merge into empty DB | All backup data added (full import from another machine) |
| Merge when backup = current | All skipped (no duplicates) |
| Merge when backup ⊂ current | All skipped (backup is subset) |
| Merge when backup ⊃ current | New records from backup added |
| Merge when backup ∩ current | Mixed: duplicates skipped, new records added |
| Full restore | Current DB replaced entirely |

### 2. Backup File Types

| Type | Supported | Notes |
|------|-----------|-------|
| `.sqlite` | ✓ | Standard format |
| `.db` | ✓ | Alternative extension |
| `.enc` | ✓ | Encrypted (requires same encryption key) |
| `.sql` | ✗ | Old format not supported |

### 3. Schema Variants (Backward Compatibility)

The import handles schema variants for compatibility with older backups:

| Table | Variant | Handling |
|-------|---------|----------|
| `content_analysis` | `coordinates` vs `list_coordinates` | Both supported |
| `contents` | With/without `title` column | Both supported |
| `sources` | Stable schema | No variants |

### 4. Edge Cases

| Case | Handling |
|------|----------|
| Empty backup | Merge adds nothing; existing data preserved |
| Corrupted file | Validation rejects before import |
| Missing tables | Validation rejects |
| Schema incompatible | Validation rejects with clear error |
| Orphaned content (content with source not in backup) | Skipped (not imported) |
| Orphaned analysis (analysis with content not in backup) | Skipped |
| Merge failure mid-way | All changes rolled back (transaction) |

---

## Validation (Before Import)

Before any import, the file is validated:

1. **File exists** – Rejected if not found
2. **Format** – Must be `.sqlite` or `.db` (or `.enc` for encrypted)
3. **Required tables** – `sources`, `contents`, `content_analysis`
4. **Required columns** – Must have required columns for merge
5. **Schema compatibility** – `content_analysis` must have `coordinates` or `list_coordinates`

Invalid files return a clear error message.

---

## Merge Process (Technical)

1. **Transaction** – Single transaction; rollback on any failure
2. **Pre-merge backup** – Current DB copied to `.sqlite.bak` before merge
3. **Sources** – Merge by name; duplicate = same name, reuse existing ID
4. **Contents** – Full field comparison (including dates); skip if exact match
5. **Content_analysis** – Full field comparison; skip if exact match
6. **ID mapping** – Backup sources/contents IDs mapped to current DB IDs for foreign keys

### Duplicate Detection

- **Sources**: Match by `name` (UNIQUE constraint)
- **Contents**: All fields compared including `date_creation`, `date_modified`
- **Analysis**: All fields compared including `date_analysis`, `date_creation`, `date_modified`

---

## Comprehensive Test Suite

Run all tests:

```powershell
cd C:\Users\Dev\Desktop\txt_analysis
python test_backup_merge.py
```

### Tests Covered

| # | Test | Verifies |
|---|------|----------|
| 1 | Merge with duplicates | No duplicates created |
| 2 | Merge into empty DB | Full import works |
| 3 | Full restore | Replace works |
| 4 | Validation – valid file | Valid backup accepted |
| 5 | Validation – invalid path | Non-existent rejected |
| 6 | Validation – wrong format | Non-SQLite rejected |
| 7 | Old schema (coordinates) | Backward compatibility |
| 8 | Empty backup merge | Existing data preserved |
| 9 | Mixed merge | Current + backup combined |
| 10 | Foreign key integrity | No orphaned records |

---

## Manual Test Steps

1. **Start app**: `python main.py`
2. **Create data**: Add sources and contents
3. **Create backup**: File → Backup & Restore → Create Backup
4. **Import (merge)**: File → Backup & Restore → Import Backup → select file → Merge
5. **Verify**: No duplicates, all data present

---

## Import UI Flow

1. **Import Backup** – File dialog (defaults to Documents)
2. **Validation** – File validated; invalid shows error
3. **Preview** – Shows sources, contents, analyses count, file size
4. **Options** – Replace | Merge | Copy to backup folder (if file outside backups)
5. **Confirm** – Restore/Merge requires confirmation

---

## Files Involved

| File | Purpose |
|------|---------|
| `utils/backup_restore.py` | Backup, restore, merge, validation, schema compatibility |
| `utils/duplicate_detector.py` | Duplicate detection (all fields including dates) |
| `dialogs/backup_restore_dialog.py` | UI, backup list, import preview |
| `test_backup_merge.py` | Comprehensive automated test |
