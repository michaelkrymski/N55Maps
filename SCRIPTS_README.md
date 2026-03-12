# N55Maps Tuning Scripts & Workflow

This guide explains how to use the automated scripts for managing your BMW N55 tuning map repository.

## 📋 Quick Start

### macOS
```bash
# First time: organize existing maps into subfolders
./organize_maps.sh

# After tuning: save new revision and update GitHub
./save_map.sh ~/path/to/your/new_tune.bin "Description of changes"

# Manage symlinks to latest versions
./refresh_shortcuts.sh
```

### Windows
```cmd
REM First time: organize existing maps
organize_maps.sh

REM After tuning: save new revision
save_map.bat "C:\Path\To\Your\Tune.bin" "Description of changes"

REM Manage shortcuts to latest versions
refresh_shortcuts.bat
```

---

## 🔧 Scripts Overview

### 1. **organize_maps.sh** (One-time setup)
Moves scattered map files from the root folder into their proper fuel-type subfolders.

**What it does:**
- Moves `93map*.bin/.log` → `93/` folder
- Moves `E30map*.bin/.log` → `E30/` folder
- Moves `E85map*.bin/.log` → `E85/` folder
- Moves `MKMM*.bin/.log` → `Flex/` folder
- Moves `Modified*.bin/.log` → `93/` folder

**Usage:**
```bash
./organize_maps.sh
```

**Notes:**
- Skips files that already exist in the destination folder (no overwrite)
- Non-matching files (Stock.bin, etc.) stay in root
- Safe to run multiple times

---

### 2. **save_map.sh** / **save_map.bat** (After each tuning session)
Saves a new tuning revision with automatic version numbering and GitHub integration.

**What it does:**
1. Detects fuel type from filename (93, E30, E85, Flex, or Modified)
2. Auto-detects next revision number
3. Copies file to proper subfolder with new revision number
4. Creates `_LATEST` symlink (macOS) or copy (Windows)
5. Removes old `_LATEST` tags
6. Optionally commits and pushes to GitHub
7. Updates root symlinks/shortcuts

**Usage:**

macOS:
```bash
./save_map.sh ~/TunerPro/93mapMK30.bin "Improved mid-range boost response"
```

Windows:
```cmd
save_map.bat "C:\TunerPro\93mapMK30.bin" "Improved mid-range boost response"
```

**Filename Requirements:**
- `93mapMK{N}.bin` → 93 octane (N = revision number)
- `E30mapMK{N}.bin` → E30 ethanol
- `E85mapMK{N}.bin` → E85 ethanol
- `MKMM{variant}.bin` → Flex (variant = 0.1, 0.2, 93E40, etc.)
- `Modifiedrev{N}.bin` → Modified 93 revisions (in 93/ folder)

**Optional parameters:**
- If no commit message provided, defaults to "Auto-saved new map revision"
- Prompts for GitHub commit/push (can skip if not ready)

**Example workflow:**
```bash
# Tune in TunerPro, save as 93mapMK30.bin
./save_map.sh ~/Downloads/93mapMK30.bin "MK30: Further AFR optimization"
# → Copies to: 93/93mapMK30(PD).bin
# → Creates: 93/93mapMK30(PD)_LATEST.bin
# → Updates: 93_LATEST symlink → points to latest file
```

---

### 3. **refresh_shortcuts.sh** / **refresh_shortcuts.bat** (Manage root symlinks)
Interactive menu to create/update symlinks to latest revisions in each fuel category.

**macOS version features:**
- Arrow keys (↑↓) to navigate
- Space to toggle selection
- `A` = select all, `N` = select none
- `G` = git pull from GitHub
- Enter = confirm and create symlinks
- Remembers your selections in `.shortcuts_config.json`

**Windows version features:**
- Numbered menu (1-5 to toggle)
- `A` = select all, `N` = select none
- `G` = git pull from GitHub
- `0` = confirm and create shortcuts
- Creates `.txt` pointer files (since batch can't create true symlinks easily)

**Root symlinks created:**
- `93_LATEST` → latest 93 octane map
- `E30_LATEST` → latest E30 ethanol map
- `E85_LATEST` → latest E85 ethanol map
- `Flex_LATEST` → latest Flex/mixed map
- `XDF` → current XDF definition file

**Usage:**
```bash
./refresh_shortcuts.sh
```

**Auto-mode** (silent, uses saved preferences):
```bash
./refresh_shortcuts.sh --auto
```

This is called automatically by `save_map.sh` after saving a new revision.

---

## 📁 Repository Structure

```
N55Maps/
├── 93/                          ← 93 octane revisions (MK1-MK32, MKF)
│   ├── 93mapMK25(PD).bin
│   ├── 93mapMK25(PD)_LATEST.bin  ← Always points to latest
│   ├── 93mapMK26(PD).bin
│   ├── Modifiedrev1-5.bin
│   └── ... (39 maps total)
│
├── E30/                         ← E30 ethanol revisions (MK1-MK25)
│   ├── E30mapMK24(PD).bin
│   ├── E30mapMK24(PD)_LATEST.bin
│   ├── E30mapMK25(PD).bin
│   └── ... (26 maps total)
│
├── E85/                         ← E85 ethanol revisions (MK1-MK21)
│   ├── E85mapMK20(PD3M).bin
│   ├── E85mapMK20(PD3M)_LATEST.bin
│   ├── E85mapMK21(PD3M).bin
│   └── ... (21 maps total)
│
├── Flex/                        ← Flex fuel maps (MKMM variants)
│   ├── MKMM(0.1).bin
│   ├── MKMM(0.2).bin
│   └── MKMM(93E40).bin
│
├── Tools/                       ← XDF files, Python utilities
│   ├── 000021571DAA01.xdf
│   ├── autofill.py
│   ├── baseanti.py
│   └── ...
│
├── 93_LATEST → 93/93mapMK32(PD)_LATEST.bin
├── E30_LATEST → E30/E30mapMK25(PD)_LATEST.bin
├── E85_LATEST → E85/E85mapMK21(PD3M)_LATEST.bin
├── Flex_LATEST → Flex/MKMM(93E40).bin
├── XDF → Tools/000021571DAA01.xdf
│
├── save_map.sh                  ← Save new revision
├── save_map.bat                 ← Windows version
├── refresh_shortcuts.sh         ← Manage symlinks
├── refresh_shortcuts.bat        ← Windows version
├── organize_maps.sh             ← One-time setup
├── .shortcuts_config.json       ← Remembered selections
└── SCRIPTS_README.md            ← This file
```

---

## 🔄 Complete Workflow

### Day-to-day tuning:

1. **Tune in TunerPro** (or your favorite tuning software)
   - Work on your map (e.g., `93mapMK30.bin`)

2. **Save revision to repository**
   ```bash
   ./save_map.sh ~/TunerPro/93mapMK30.bin "MK30: Adjusted boost ramp"
   ```
   - Auto-increments version number
   - Creates `_LATEST` symlink
   - Optionally commits to GitHub

3. **Access latest map from root**
   - Use `93_LATEST` symlink to load into TunerPro
   - Or from the Mac Finder/Windows File Explorer

4. **Occasionally refresh symlinks** (if you skip GitHub updates)
   ```bash
   ./refresh_shortcuts.sh
   ```

### Git integration:
- All scripts support `git add`, `git commit`, `git push`
- Requires git to be installed and repo initialized
- If git fails, scripts continue gracefully
- You can commit later manually if needed

---

## 📝 Naming Convention Details

### 93 Octane
- **Format**: `93mapMK{N}(PD).bin`
- **Examples**:
  - `93mapMK25(PD).bin` - MK25 revision, PD tuning
  - `93mapMK32(PD).bin` - MK32 revision
  - `93mapMKF(PD).bin` - MKF (Final) revision
  - `93mapMK10(PID).bin` - full PID tuning variant

### E30 Ethanol
- **Format**: `E30mapMK{N}(PD).bin`
- **Examples**:
  - `E30mapMK23(PD).bin`
  - `E30mapMK25(PD).bin` - Latest E30
  - `E30mapMK5(PD)[Fueling].bin` - Variant with notes

### E85 Ethanol
- **Format**: `E85mapMK{N}(PD3M).bin`
- **Examples**:
  - `E85mapMK19(PD3M).bin` - PD 3-map variant
  - `E85mapMK21(PD3M).bin` - Latest E85
  - `E85mapMK8(PD).bin` - Regular PD variant

### Flex/Mixed
- **Format**: `MKMM({variant}).bin`
- **Examples**:
  - `MKMM(0.1).bin` - 10% ethanol blend
  - `MKMM(0.2).bin` - 20% ethanol blend
  - `MKMM(93E40).bin` - 93 octane with E40 (40% ethanol)

### Modified (93 folder only)
- **Format**: `Modifiedrev{N}.bin`
- **Examples**:
  - `Modifiedrev1.bin` through `Modifiedrev5.bin`

---

## ⚙️ Configuration

### .shortcuts_config.json
Stores your preferred symlink selections:

```json
{
  "enabled_symlinks": ["93", "E30", "E85", "Flex", "XDF"],
  "last_updated": "2026-03-11T21:00:00Z",
  "notes": "This file remembers which symlinks/shortcuts to create in the root folder"
}
```

- Auto-created by `refresh_shortcuts.sh`
- Add/remove fuel types from `enabled_symlinks` array to customize
- Never commit to git if you want different preferences per machine

---

## 🐛 Troubleshooting

### **save_map.sh says "File not found"**
- Check the path: use full path or navigate to N55Maps folder first
- Example: `./save_map.sh ~/Downloads/93mapMK30.bin` ✓
- Not: `./save_map.sh 93mapMK30.bin` (unless file is in current directory)

### **Symlinks not created**
- Check subfolder exists: `ls -la 93/ E30/ E85/`
- Check map files exist in subfolders: `ls 93/*_LATEST.bin`
- Run manually: `refresh_shortcuts.sh`

### **Git push fails**
- Check git is installed: `git --version`
- Check remote: `git remote -v`
- Verify credentials/SSH keys: `git push`
- Scripts will still save locally even if push fails

### **"Unrecognized filename format"**
- Check your filename matches the expected pattern
- Typos: `93mapMk` (lowercase k) won't match `93mapMK`
- Rename the file before running `save_map.sh`

### **Batch scripts don't run on Windows**
- Right-click Command Prompt → "Run as administrator"
- Or double-click `.bat` file and allow execution
- Ensure `%PATH%` includes Git (if using git features)

---

## 💡 Pro Tips

1. **Backup before major changes**: Git is your friend, but also copy important maps
   ```bash
   cp 93/93mapMK30(PD).bin ~/Backups/93mapMK30_backup.bin
   ```

2. **Use descriptive commit messages**:
   ```bash
   ./save_map.sh myfile.bin "MK31: Fixed lean cruising, improved transient response"
   ```

3. **Track all revisions in git**: Every `save_map.sh` creates a git-friendly commit

4. **Use `_LATEST` symlinks in TunerPro**: Set TunerPro to always open `93_LATEST`, then your workflow is:
   - Tune → save_map.sh → reload `93_LATEST` (already updated)

5. **Check git log for history**:
   ```bash
   git log --oneline | head -20
   ```

---

## 📞 Questions?

Refer to the original repository structure and your workflow notes. These scripts automate the grunt work—let them handle versioning while you focus on tuning!

Happy tuning! 🚗
