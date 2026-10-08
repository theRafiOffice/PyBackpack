<div align="center">

# 🎒 PyBackpack

### **The Modern Python Package Backup & Offline Restore Utility**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](#-prerequisites)

*Effortlessly freeze, archive, sync, and re-install Python dependencies across air-gapped environments, virtual machines, or isolated servers—with zero GUI hanging.*

---

</div>

## 📌 Overview

**PyBackpack** is a desktop application that solves a common pain point for developers: moving Python environments to computers without internet access or creating reliable offline snapshots of installed dependencies.

Unlike standard terminal scripts, PyBackpack runs background `pip` tasks inside isolated execution threads (`QThread`), streaming real-time console output into a sleek dark-mode user interface.

---

## ✨ Features

- 🔍 **Environment Auto-Detection:** Automatically identifies active global, `venv`, or `conda` runtimes and resolves exact executable binaries.
- 📦 **Flexible Backups:** Save your entire environment or specify individual packages on the fly.
- 🔌 **True Offline Restoration:** Re-install packages using `--no-index` flags paired with local wheels (`.whl`) and source archives (`.tar.gz`).
- ⚡ **Incremental Smart Sync:** Scans existing backup archives against your active environment, identifying newly added or upgraded libraries and fetching only the changes.
- ⏱️ **Non-Blocking Execution:** Asynchronous thread workers prevent UI lockup during lengthy downloads or installations.
- 📜 **Persistent Activity Logs:** Records all backup and restoration tasks locally in a structured JSON ledger (`~/.pybackpack_history.json`).
- 🎨 **Modern Dark Interface:** Clean visual hierarchy built on a custom PyQt6 dark theme.

---

## 🖥️ Application Layout

The app is divided into 5 focused modules:

| Tab | Purpose |
| :--- | :--- |
| **`Dashboard`** | Inspect installed environment libraries, versions, and filter packages. |
| **`Backup Packages`** | Export full environments or individual libraries to a designated directory. |
| **`Restore Packages`** | Perform local offline installations from an existing backup folder. |
| **`Smart Sync`** | Compare target folders against active environments to archive updates. |
| **`Action History`** | Review timestamped records of past backup and restore operations. |

---

## 🛠️ Prerequisites

* **Python:** `3.10` or higher
* **Package Manager:** `pip` (up to date)
* **Operating Systems:** Windows, macOS, or Linux

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/pybackpack.git](https://github.com/your-username/pybackpack.git)
cd pybackpack
