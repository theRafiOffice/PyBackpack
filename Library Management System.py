import sys
import os
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QListWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog, QMessageBox, 
    QPlainTextEdit, QRadioButton, QButtonGroup, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# --- THREADING CLASSES --- #

class PipWorker(QThread):
    """
    Background thread to run pip commands safely without freezing the GUI.
    """
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd

    def run(self):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.cwd,
                creationflags=creationflags
            )

            for line in process.stdout:
                self.log_signal.emit(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                self.finished_signal.emit(True, "Operation completed successfully.")
            else:
                self.finished_signal.emit(False, f"Process exited with code {process.returncode}")

        except Exception as e:
            self.finished_signal.emit(False, str(e))


# --- MAIN GUI CLASS --- #

class PyBackpackApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBackpack - Advanced Python Backup Utility")
        self.resize(1100, 700)
        
        # Core data
        self.python_exe = sys.executable
        self.python_version = sys.version.split(' ')[0]
        self.is_venv = sys.prefix != sys.base_prefix
        self.env_packages = [] # Stores current env state
        self.sync_tasks = [] # Stores packages needing sync
        
        # History setup
        self.history_file = os.path.join(os.path.expanduser("~"), ".pybackpack_history.json")
        self.history_data = self.load_history_data()

        self.init_ui()
        self.apply_dark_theme()
        self.load_packages()
        self.refresh_history_table()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems([
            "Dashboard", "Backup Packages", "Restore Packages", 
            "Smart Sync (Update)", "Action History"
        ])
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.switch_tab)
        main_layout.addWidget(self.sidebar)

        # 2. Main Content Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Build Tabs
        self.stack.addWidget(self.build_dashboard_tab())
        self.stack.addWidget(self.build_backup_tab())
        self.stack.addWidget(self.build_restore_tab())
        self.stack.addWidget(self.build_sync_tab())
        self.stack.addWidget(self.build_history_tab())

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QWidget { color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px;}
            
            QListWidget { 
                background-color: #1e1e1e; border: none; border-right: 1px solid #333; 
                outline: none; font-size: 15px; font-weight: bold;
            }
            QListWidget::item { padding: 20px 15px; border-bottom: 1px solid #2a2a2a; }
            QListWidget::item:selected { background-color: #0d47a1; color: white; border-left: 4px solid #64b5f6;}
            QListWidget::item:hover:!selected { background-color: #2a2a2a; }
            
            QLabel#TitleLabel { font-size: 22px; font-weight: bold; color: #ffffff; padding-bottom: 10px; }
            QLabel#InfoLabel { font-size: 13px; color: #aaaaaa; }
            
            QPushButton { 
                background-color: #1976d2; color: white; border-radius: 5px; 
                padding: 10px 15px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
            QPushButton:disabled { background-color: #424242; color: #757575; }
            QPushButton#PathButton { background-color: #424242; }
            QPushButton#PathButton:hover { background-color: #616161; }
            QPushButton#AnalyzeButton { background-color: #2e7d32; }
            QPushButton#AnalyzeButton:hover { background-color: #1b5e20; }
            
            QTableWidget { 
                background-color: #1e1e1e; alternate-background-color: #252525; 
                border: 1px solid #333; border-radius: 5px; gridline-color: #333;
            }
            QHeaderView::section { background-color: #2a2a2a; color: white; padding: 5px; border: 1px solid #333; font-weight: bold; }
            
            QLineEdit { background-color: #1e1e1e; border: 1px solid #444; padding: 8px; border-radius: 5px; color: white; }
            QLineEdit:focus { border: 1px solid #1976d2; }
            QLineEdit:disabled { background-color: #2c2c2c; color: #777; }
            
            QPlainTextEdit { 
                background-color: #000000; color: #00ff00; 
                font-family: 'Consolas', monospace; font-size: 13px;
                border: 1px solid #333; border-radius: 5px; padding: 10px;
            }
            
            QRadioButton { spacing: 8px; font-weight: bold; }
            QRadioButton::indicator { width: 16px; height: 16px; }
        """)

    # --- TAB BUILDERS --- #

    def build_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Environment Dashboard")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        env_type = "Virtual Environment (venv/conda)" if self.is_venv else "Global Environment"
        info = QLabel(f"Python Version: {self.python_version}  |  Type: {env_type}\nExecutable: {self.python_exe}")
        info.setObjectName("InfoLabel")
        layout.addWidget(info)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search installed packages...")
        self.search_input.textChanged.connect(self.filter_dashboard_packages)
        layout.addWidget(self.search_input)

        self.dash_table = QTableWidget(0, 2)
        self.dash_table.setHorizontalHeaderLabels(["Package Name", "Version"])
        self.dash_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.dash_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.dash_table.setAlternatingRowColors(True)
        self.dash_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.dash_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.dash_table)

        return widget

    def build_backup_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Backup Packages")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        # Mode Selection
        mode_layout = QHBoxLayout()
        self.bkp_radio_full = QRadioButton("Full Environment")
        self.bkp_radio_custom = QRadioButton("Custom Package(s)")
        self.bkp_radio_full.setChecked(True)
        mode_layout.addWidget(self.bkp_radio_full)
        mode_layout.addWidget(self.bkp_radio_custom)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self.bkp_custom_input = QLineEdit()
        self.bkp_custom_input.setPlaceholderText("e.g. requests pandas==2.0.3 (Space separated)")
        self.bkp_custom_input.setEnabled(False)
        layout.addWidget(self.bkp_custom_input)

        self.bkp_radio_full.toggled.connect(lambda: self.bkp_custom_input.setEnabled(not self.bkp_radio_full.isChecked()))

        # Path Selection
        path_layout = QHBoxLayout()
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setReadOnly(True)
        self.backup_path_input.setPlaceholderText("Select Destination Folder...")
        btn_browse = QPushButton("Browse")
        btn_browse.setObjectName("PathButton")
        btn_browse.clicked.connect(lambda: self.browse_folder(self.backup_path_input))
        path_layout.addWidget(self.backup_path_input)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        self.btn_start_backup = QPushButton("Start Backup Process")
        self.btn_start_backup.clicked.connect(self.start_backup)
        layout.addWidget(self.btn_start_backup)

        self.backup_log = QPlainTextEdit()
        self.backup_log.setReadOnly(True)
        layout.addWidget(self.backup_log)

        return widget

    def build_restore_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Restore Packages (Offline)")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        # Mode Selection
        mode_layout = QHBoxLayout()
        self.rst_radio_full = QRadioButton("Full Restore (from requirements.txt)")
        self.rst_radio_custom = QRadioButton("Custom Package(s)")
        self.rst_radio_full.setChecked(True)
        mode_layout.addWidget(self.rst_radio_full)
        mode_layout.addWidget(self.rst_radio_custom)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self.rst_custom_input = QLineEdit()
        self.rst_custom_input.setPlaceholderText("e.g. requests numpy (Space separated)")
        self.rst_custom_input.setEnabled(False)
        layout.addWidget(self.rst_custom_input)

        self.rst_radio_full.toggled.connect(lambda: self.rst_custom_input.setEnabled(not self.rst_radio_full.isChecked()))

        # Path Selection
        path_layout = QHBoxLayout()
        self.restore_path_input = QLineEdit()
        self.restore_path_input.setReadOnly(True)
        self.restore_path_input.setPlaceholderText("Select Backup Folder...")
        btn_browse = QPushButton("Browse")
        btn_browse.setObjectName("PathButton")
        btn_browse.clicked.connect(lambda: self.browse_folder(self.restore_path_input))
        path_layout.addWidget(self.restore_path_input)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        self.btn_start_restore = QPushButton("Start Restore Process")
        self.btn_start_restore.clicked.connect(self.start_restore)
        layout.addWidget(self.btn_start_restore)

        self.restore_log = QPlainTextEdit()
        self.restore_log.setReadOnly(True)
        layout.addWidget(self.restore_log)

        return widget

    def build_sync_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Smart Sync (Incremental Backup)")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        
        layout.addWidget(QLabel("Scan your current environment against a backup folder to detect new or updated packages."))

        path_layout = QHBoxLayout()
        self.sync_path_input = QLineEdit()
        self.sync_path_input.setReadOnly(True)
        self.sync_path_input.setPlaceholderText("Select Backup Folder to Analyze...")
        btn_browse = QPushButton("Browse")
        btn_browse.setObjectName("PathButton")
        btn_browse.clicked.connect(lambda: self.browse_folder(self.sync_path_input))
        
        btn_analyze = QPushButton("Analyze")
        btn_analyze.setObjectName("AnalyzeButton")
        btn_analyze.clicked.connect(self.analyze_sync)

        path_layout.addWidget(self.sync_path_input)
        path_layout.addWidget(btn_browse)
        path_layout.addWidget(btn_analyze)
        layout.addLayout(path_layout)

        self.sync_table = QTableWidget(0, 4) # Check, Name, Status, Version
        self.sync_table.setHorizontalHeaderLabels(["Sync", "Package Name", "Current Version", "Status"])
        self.sync_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.sync_table.setAlternatingRowColors(True)
        self.sync_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.sync_table)

        self.btn_start_sync = QPushButton("Sync Selected Packages")
        self.btn_start_sync.clicked.connect(self.start_sync)
        self.btn_start_sync.setEnabled(False)
        layout.addWidget(self.btn_start_sync)

        self.sync_log = QPlainTextEdit()
        self.sync_log.setReadOnly(True)
        self.sync_log.setMaximumHeight(150)
        layout.addWidget(self.sync_log)

        return widget

    def build_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Action History")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Date/Time", "Action", "Status", "Path/Target"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.history_table)

        btn_clear = QPushButton("Clear History")
        btn_clear.setObjectName("PathButton") # Reusing darker style
        btn_clear.clicked.connect(self.clear_history)
        layout.addWidget(btn_clear)

        return widget

    # --- DATA & LOGIC HUB --- #

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def write_terminal(self, log_widget, text):
        log_widget.appendPlainText(text)
        scrollbar = log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # --- ENVIRONMENT PARSING --- #

    def load_packages(self):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, creationflags=creationflags
            )
            self.env_packages = json.loads(result.stdout)
            
            self.dash_table.setRowCount(len(self.env_packages))
            for row, pkg in enumerate(self.env_packages):
                self.dash_table.setItem(row, 0, QTableWidgetItem(pkg.get("name", "")))
                self.dash_table.setItem(row, 1, QTableWidgetItem(pkg.get("version", "")))
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Packages", f"Could not list packages: {e}")

    def filter_dashboard_packages(self, text):
        for row in range(self.dash_table.rowCount()):
            item = self.dash_table.item(row, 0)
            self.dash_table.setRowHidden(row, text.lower() not in item.text().lower())

    # --- BACKUP WORKFLOW --- #

    def start_backup(self):
        target_dir = self.backup_path_input.text().strip()
        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.warning(self, "Validation Error", "Please select a valid destination folder.")
            return

        is_full = self.bkp_radio_full.isChecked()
        custom_pkgs = self.bkp_custom_input.text().strip()
        
        if not is_full and not custom_pkgs:
            QMessageBox.warning(self, "Validation Error", "Please enter at least one package name.")
            return

        self.btn_start_backup.setEnabled(False)
        self.backup_log.clear()
        self.write_terminal(self.backup_log, f"[*] Starting backup to: {target_dir}")

        self._pending_action = "Full Backup" if is_full else f"Backup: {custom_pkgs}"
        self._pending_path = target_dir

        if is_full:
            # Generate requirements.txt first
            req_path = os.path.join(target_dir, "requirements.txt")
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                freeze_res = subprocess.run([self.python_exe, '-m', 'pip', 'freeze'], capture_output=True, text=True, creationflags=creationflags)
                with open(req_path, "w", encoding="utf-8") as f:
                    f.write(freeze_res.stdout)
                self.write_terminal(self.backup_log, "[+] requirements.txt created/updated.")
            except Exception as e:
                self.write_terminal(self.backup_log, f"[-] Failed to generate requirements.txt: {e}")
                self.btn_start_backup.setEnabled(True)
                return

            command = [self.python_exe, '-m', 'pip', 'download', '-r', req_path, '-d', target_dir]
        else:
            # Custom package(s)
            pkg_list = custom_pkgs.split()
            command = [self.python_exe, '-m', 'pip', 'download', '-d', target_dir] + pkg_list

        self.backup_worker = PipWorker(command, cwd=target_dir)
        self.backup_worker.log_signal.connect(lambda txt: self.write_terminal(self.backup_log, txt))
        self.backup_worker.finished_signal.connect(self.backup_finished)
        self.backup_worker.start()

    def backup_finished(self, success, message):
        self.btn_start_backup.setEnabled(True)
        status = "Success" if success else "Failed"
        self.log_history(self._pending_action, self._pending_path, status)

        if success:
            self.write_terminal(self.backup_log, "\n[+] Backup completed successfully!")
            QMessageBox.information(self, "Success", "Backup completed successfully!")
        else:
            self.write_terminal(self.backup_log, f"\n[-] Backup failed: {message}")

    # --- RESTORE WORKFLOW --- #

    def start_restore(self):
        source_dir = self.restore_path_input.text().strip()
        if not source_dir or not os.path.isdir(source_dir):
            QMessageBox.warning(self, "Validation Error", "Please select a valid backup folder.")
            return

        is_full = self.rst_radio_full.isChecked()
        custom_pkgs = self.rst_custom_input.text().strip()

        if not is_full and not custom_pkgs:
            QMessageBox.warning(self, "Validation Error", "Please enter at least one package name.")
            return

        self.btn_start_restore.setEnabled(False)
        self.restore_log.clear()
        
        self._pending_action = "Full Restore" if is_full else f"Restore: {custom_pkgs}"
        self._pending_path = source_dir

        command = [self.python_exe, '-m', 'pip', 'install', '--no-index', '--find-links', source_dir]

        if is_full:
            req_path = os.path.join(source_dir, "requirements.txt")
            if not os.path.exists(req_path):
                QMessageBox.warning(self, "Invalid Backup", "The folder does not contain 'requirements.txt'.")
                self.btn_start_restore.setEnabled(True)
                return
            command.extend(['-r', req_path])
        else:
            command.extend(custom_pkgs.split())

        self.write_terminal(self.restore_log, f"[*] Starting offline install from: {source_dir}\n")
        
        self.restore_worker = PipWorker(command, cwd=source_dir)
        self.restore_worker.log_signal.connect(lambda txt: self.write_terminal(self.restore_log, txt))
        self.restore_worker.finished_signal.connect(self.restore_finished)
        self.restore_worker.start()

    def restore_finished(self, success, message):
        self.btn_start_restore.setEnabled(True)
        status = "Success" if success else "Failed"
        self.log_history(self._pending_action, self._pending_path, status)

        if success:
            self.write_terminal(self.restore_log, "\n[+] Restore completed successfully!")
            self.load_packages() # Refresh table
        else:
            self.write_terminal(self.restore_log, f"\n[-] Restore failed: {message}")

    # --- SMART SYNC WORKFLOW --- #

    def analyze_sync(self):
        backup_dir = self.sync_path_input.text().strip()
        if not backup_dir or not os.path.isdir(backup_dir):
            QMessageBox.warning(self, "Validation Error", "Please select a valid backup folder.")
            return

        self.sync_log.clear()
        self.write_terminal(self.sync_log, "[*] Analyzing environment vs backup folder...")

        # Parse requirements.txt from backup
        req_path = os.path.join(backup_dir, "requirements.txt")
        backup_dict = {}
        if os.path.exists(req_path):
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '==' in line:
                        parts = line.strip().split('==', 1)
                        backup_dict[parts[0].lower()] = parts[1]

        # Compare
        self.sync_tasks.clear()
        for pkg in self.env_packages:
            name = pkg['name']
            lower_name = name.lower()
            current_ver = pkg['version']

            if lower_name not in backup_dict:
                self.sync_tasks.append((name, current_ver, "New Package (Not in backup)"))
            elif backup_dict[lower_name] != current_ver:
                self.sync_tasks.append((name, current_ver, f"Update Available (Backup has {backup_dict[lower_name]})"))

        self.populate_sync_table()

        if self.sync_tasks:
            self.write_terminal(self.sync_log, f"[+] Found {len(self.sync_tasks)} packages to sync.")
            self.btn_start_sync.setEnabled(True)
        else:
            self.write_terminal(self.sync_log, "[+] Your backup is completely up to date with this environment.")
            self.btn_start_sync.setEnabled(False)

    def populate_sync_table(self):
        self.sync_table.setRowCount(len(self.sync_tasks))
        for row, (name, ver, status) in enumerate(self.sync_tasks):
            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0,0,0,0)
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            chk_layout.addWidget(checkbox)
            
            self.sync_table.setCellWidget(row, 0, chk_widget)
            self.sync_table.setItem(row, 1, QTableWidgetItem(name))
            self.sync_table.setItem(row, 2, QTableWidgetItem(ver))
            self.sync_table.setItem(row, 3, QTableWidgetItem(status))

    def start_sync(self):
        target_dir = self.sync_path_input.text().strip()
        packages_to_sync = []
        
        # Gather checked items
        for row in range(self.sync_table.rowCount()):
            chk_widget = self.sync_table.cellWidget(row, 0)
            checkbox = chk_widget.findChild(QCheckBox)
            if checkbox.isChecked():
                name = self.sync_table.item(row, 1).text()
                ver = self.sync_table.item(row, 2).text()
                packages_to_sync.append(f"{name}=={ver}")

        if not packages_to_sync:
            QMessageBox.information(self, "No Selection", "No packages selected for syncing.")
            return

        self.btn_start_sync.setEnabled(False)
        self.sync_log.clear()
        self.write_terminal(self.sync_log, f"[*] Syncing {len(packages_to_sync)} packages...")

        self._pending_action = f"Smart Sync ({len(packages_to_sync)} pkgs)"
        self._pending_path = target_dir

        command = [self.python_exe, '-m', 'pip', 'download', '-d', target_dir] + packages_to_sync

        self.sync_worker = PipWorker(command, cwd=target_dir)
        self.sync_worker.log_signal.connect(lambda txt: self.write_terminal(self.sync_log, txt))
        self.sync_worker.finished_signal.connect(self.sync_finished)
        self.sync_worker.start()

    def sync_finished(self, success, message):
        status = "Success" if success else "Failed"
        self.log_history(self._pending_action, self._pending_path, status)

        if success:
            # Update requirements.txt in the backup folder to reflect the new state
            target_dir = self.sync_path_input.text().strip()
            req_path = os.path.join(target_dir, "requirements.txt")
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                freeze_res = subprocess.run([self.python_exe, '-m', 'pip', 'freeze'], capture_output=True, text=True, creationflags=creationflags)
                with open(req_path, "w", encoding="utf-8") as f:
                    f.write(freeze_res.stdout)
                self.write_terminal(self.sync_log, "[*] Updated requirements.txt in backup folder.")
            except Exception as e:
                self.write_terminal(self.sync_log, f"[-] Could not update requirements.txt: {e}")

            self.write_terminal(self.sync_log, "\n[+] Sync completed successfully!")
            self.sync_table.setRowCount(0) # clear table
            self.btn_start_sync.setEnabled(False)
        else:
            self.write_terminal(self.sync_log, f"\n[-] Sync failed: {message}")
            self.btn_start_sync.setEnabled(True)

    # --- HISTORY MANAGEMENT --- #

    def load_history_data(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history_data(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=4)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def log_history(self, action, path, status):
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "status": status,
            "path": path
        }
        self.history_data.insert(0, record) # Insert at top
        self.save_history_data()
        self.refresh_history_table()

    def refresh_history_table(self):
        self.history_table.setRowCount(len(self.history_data))
        for row, rec in enumerate(self.history_data):
            self.history_table.setItem(row, 0, QTableWidgetItem(rec.get("timestamp", "")))
            self.history_table.setItem(row, 1, QTableWidgetItem(rec.get("action", "")))
            self.history_table.setItem(row, 2, QTableWidgetItem(rec.get("status", "")))
            self.history_table.setItem(row, 3, QTableWidgetItem(rec.get("path", "")))

    def clear_history(self):
        reply = QMessageBox.question(self, "Clear History", "Are you sure you want to clear all history records?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.history_data = []
            self.save_history_data()
            self.refresh_history_table()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = PyBackpackApp()
    window.show()
    sys.exit(app.exec())