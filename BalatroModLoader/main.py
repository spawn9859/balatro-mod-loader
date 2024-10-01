import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QFileDialog, QMessageBox, QListWidgetItem, QCheckBox, QLabel, QDialog, QFormLayout, QLineEdit, QToolButton, QTextEdit
)
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QPalette, QColor, QIcon, QPixmap
import json
import logging
import subprocess

class ModLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.load_config()
        self.setWindowTitle("Balatro Mod Loader")
        self.setGeometry(100, 100, 600, 400)
        self.setup_ui()
        self.import_existing_mods()  # Import existing mods upon initialization
        self.load_mods()

    def setup_logging(self):
        logging.basicConfig(
            filename='modloader.log',
            level=logging.INFO,
            format='%(asctime)s:%(levelname)s:%(message)s'
        )
        logging.info("Mod Loader started.")

    def load_config(self):
        config_path = os.path.join(os.getcwd(), 'config', 'config.json')
        if not os.path.exists(config_path):
            self.create_default_config(config_path)
        try:
            with open(config_path, 'r') as config_file:
                self.config = json.load(config_file)
                logging.info("Configuration loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            QMessageBox.critical(self, "Error", "Failed to load configuration.")
            self.config = self.create_default_config(config_path)

    def create_default_config(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        default_config = {
            "game_mods_folder": os.path.join(os.getenv('APPDATA'), "Balatro", "Mods"),  # Uses APPDATA environment variable
            "mod_loader_folder": os.path.join(os.getcwd(), "mods")
        }
        try:
            with open(path, 'w') as config_file:
                json.dump(default_config, config_file, indent=4)
                logging.info("Default configuration created.")
        except Exception as e:
            logging.error(f"Failed to create default configuration: {e}")
            QMessageBox.critical(self, "Error", "Failed to create default configuration.")
        return default_config

    def setup_ui(self):
        layout = QVBoxLayout()

        # Added Banner
        self.banner_label = QLabel()
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        banner_pixmap = QPixmap("icons/balbanner.png")
        self.banner_label.setPixmap(banner_pixmap.scaledToWidth(600, Qt.SmoothTransformation))
        layout.addWidget(self.banner_label)

        # Mod List with increased spacing
        self.mod_list = QListWidget()
        self.mod_list.setSpacing(10)  # Increased spacing between items
        self.mod_list.itemChanged.connect(self.handle_item_changed)
        layout.addWidget(self.mod_list)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Enable All Button without Icon
        enable_all_btn = QPushButton("Enable All")
        enable_all_btn.clicked.connect(self.enable_all_mods)
        button_layout.addWidget(enable_all_btn)

        # Disable All Button without Icon
        disable_all_btn = QPushButton("Disable All")
        disable_all_btn.clicked.connect(self.disable_all_mods)
        button_layout.addWidget(disable_all_btn)

        # Add Mod Button without Icon
        add_mod_btn = QPushButton("Add Mod")
        add_mod_btn.clicked.connect(self.add_mod)
        button_layout.addWidget(add_mod_btn)

        # Settings Button without Icon
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.apply_dark_mode()

    def apply_dark_mode(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

    def load_mods(self):
        self.mod_list.clear()
        mods_path = self.get_mods_directory()
        if not os.path.exists(mods_path):
            os.makedirs(mods_path)
            logging.info(f"Mods directory created at {mods_path}.")

        # Load and sort mods alphabetically
        mods = sorted(os.listdir(mods_path), key=lambda x: x.lower())
        for mod in mods:
            item = QListWidgetItem(mod)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # Check if mod is enabled
            game_mods_path = self.get_game_mods_folder()
            mod_path_in_game = os.path.join(game_mods_path, mod)
            if os.path.exists(mod_path_in_game):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.mod_list.addItem(item)
            logging.info(f"Loaded mod: {mod}")

    def handle_item_changed(self, item):
        mod_name = item.text()
        if item.checkState() == Qt.Checked:
            self.enable_mod(mod_name)
        else:
            self.disable_mod(mod_name)

    def enable_mod(self, mod_name):
        mod_path = os.path.join(self.get_mods_folder(), mod_name)
        game_mods_path = self.get_game_mods_folder()
        try:
            if os.path.isdir(mod_path):
                shutil.copytree(mod_path, os.path.join(game_mods_path, mod_name))
                logging.info(f"Enabled folder mod '{mod_name}'.")
            elif os.path.isfile(mod_path):
                shutil.copy(mod_path, game_mods_path)
                logging.info(f"Enabled file mod '{mod_name}'.")
            # QMessageBox.information(self, "Enabled", f"Mod '{mod_name}' enabled.")  # Removed
        except Exception as e:
            logging.error(f"Failed to enable mod '{mod_name}': {e}")
            QMessageBox.warning(self, "Error", f"Failed to enable mod '{mod_name}'.\n{str(e)}")

    def disable_mod(self, mod_name):
        game_mod_path = os.path.join(self.get_game_mods_folder(), mod_name)
        try:
            if os.path.isdir(game_mod_path):
                shutil.rmtree(game_mod_path)
                logging.info(f"Disabled folder mod '{mod_name}'.")
            elif os.path.isfile(game_mod_path):
                os.remove(game_mod_path)
                logging.info(f"Disabled file mod '{mod_name}'.")
            # QMessageBox.information(self, "Disabled", f"Mod '{mod_name}' disabled.")  # Removed
        except Exception as e:
            logging.error(f"Failed to disable mod '{mod_name}': {e}")
            QMessageBox.warning(self, "Error", f"Failed to disable mod '{mod_name}'.\n{str(e)}")

    def add_mod(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog  # Allows for selecting both files and folders

        dialog = QFileDialog(self, "Select Mod Files or Folders")
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.ExistingFiles)  # Start with file selection mode
        dialog.setNameFilter("Lua Files (*.lua);;ZIP Files (*.zip);;All Files (*)")

        # Add a button to toggle between file and folder selection
        toggle_btn = QPushButton(QIcon("icons/toggle.png"), "Toggle File/Folder Selection")
        dialog.layout().addWidget(toggle_btn)

        file_mode = True  # Start with file selection mode

        def toggle_selection_mode():
            nonlocal file_mode
            file_mode = not file_mode
            if file_mode:
                dialog.setFileMode(QFileDialog.ExistingFiles)
                dialog.setNameFilter("Lua Files (*.lua);;ZIP Files (*.zip);;All Files (*)")
            else:
                dialog.setFileMode(QFileDialog.Directory)
                dialog.setNameFilter("")

        toggle_btn.clicked.connect(toggle_selection_mode)

        # Replace exec_() with exec() to fix DeprecationWarning
        if dialog.exec() == QFileDialog.Accepted:
            selected_paths = dialog.selectedFiles()
            mods_folder = self.get_mods_folder()

            for path in selected_paths:
                try:
                    if os.path.isdir(path):
                        destination = os.path.join(mods_folder, os.path.basename(path))
                        shutil.copytree(path, destination)
                        logging.info(f"Copied folder mod to {destination}.")
                    elif path.endswith('.zip'):
                        destination = os.path.join(mods_folder, os.path.splitext(os.path.basename(path))[0])
                        shutil.unpack_archive(path, destination)
                        logging.info(f"Unpacked ZIP mod to {destination}.")
                    else:
                        shutil.copy(path, mods_folder)
                        logging.info(f"Copied file mod to {mods_folder}.")
                    QMessageBox.information(self, "Success", f"Mod '{os.path.basename(path)}' added successfully.")
                except Exception as e:
                    logging.error(f"Failed to add mod '{os.path.basename(path)}': {e}")
                    QMessageBox.warning(self, "Error", f"Failed to add mod '{os.path.basename(path)}'.\n{str(e)}")
            
            # Added option to set a banner during mod addition
            banner_option = QMessageBox.question(self, "Add Banner", "Would you like to add a banner image?", QMessageBox.Yes | QMessageBox.No)
            if banner_option == QMessageBox.Yes:
                banner_path, _ = QFileDialog.getOpenFileName(self, "Select Banner Image", "", "Images (*.png *.xpm *.jpg)")
                if banner_path:
                    self.set_banner(banner_path)

            self.mod_list.clear()
            self.load_mods()

    def get_mods_directory(self):
        # Directory to store all mods within the Mod Loader
        return self.config.get("mod_loader_folder", os.path.join(os.getcwd(), "mods"))

    def get_mods_folder(self):
        # Folder where enabled mods are copied
        return self.get_mods_directory()

    def get_game_mods_folder(self):
        # Path to the game's Mods directory
        return self.config.get("game_mods_folder", os.path.join(os.getenv('APPDATA'), "Balatro", "Mods"))

    def integrate_injectors(self):
        try:
            # Example: Call an external injector executable
            subprocess.run(["path_to_injector", "arguments"], check=True)
            logging.info("Injector integrated successfully.")
        except Exception as e:
            logging.error(f"Injector integration failed: {e}")
            QMessageBox.warning(self, "Injector Error", f"Failed to integrate injector.\n{str(e)}")

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_config()
            self.load_mods()

    def import_existing_mods(self):
        """Import existing mods from the game's Mods folder into the mod loader's mods directory."""
        game_mods_path = self.get_game_mods_folder()
        mod_loader_mods_path = self.get_mods_folder()
        
        if not os.path.exists(game_mods_path):
            logging.warning(f"Game mods folder does not exist at {game_mods_path}.")
            return
        
        for mod in os.listdir(game_mods_path):
            mod_loader_path = os.path.join(mod_loader_mods_path, mod)
            if not os.path.exists(mod_loader_path):
                source_path = os.path.join(game_mods_path, mod)
                try:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, mod_loader_path)
                        logging.info(f"Imported existing mod '{mod}' from game mods to mod loader.")
                    elif os.path.isfile(source_path):
                        shutil.copy(source_path, mod_loader_mods_path)
                        logging.info(f"Imported existing mod '{mod}' from game mods to mod loader.")
                except Exception as e:
                    logging.error(f"Failed to import existing mod '{mod}': {e}")
                    QMessageBox.warning(self, "Error", f"Failed to import existing mod '{mod}'.\n{str(e)}")

    def get_mod_description(self, mod_path):
        """Extract the first couple of sentences from the README file for the mod."""
        readme_files = ['README.md', 'README.txt', 'README']
        for readme in readme_files:
            readme_path = os.path.join(mod_path, readme)
            if os.path.isfile(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        # Extract first two non-empty lines as description
                        description = ""
                        for line in lines:
                            stripped = line.strip()
                            if stripped:
                                description += stripped + " "
                                if len(description.split('.')) >= 2:
                                    break
                        return description.strip()
                except Exception as e:
                    logging.error(f"Error reading README for mod at {mod_path}: {e}")
                    return ""
        return ""

    def enable_all_mods(self):
        for index in range(self.mod_list.count()):
            item = self.mod_list.item(index)
            if item.checkState() != Qt.Checked:
                item.setCheckState(Qt.Checked)

    def disable_all_mods(self):
        for index in range(self.mod_list.count()):
            item = self.mod_list.item(index)
            if item.checkState() != Qt.Unchecked:
                item.setCheckState(Qt.Unchecked)

    def set_banner(self, image_path):
        """Sets the banner image at the top of the UI."""
        try:
            pixmap = QPixmap(image_path)
            self.banner_label.setPixmap(pixmap.scaled(self.banner_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logging.info(f"Banner set to {image_path}.")
        except Exception as e:
            logging.error(f"Failed to set banner: {e}")
            QMessageBox.warning(self, "Error", f"Failed to set banner.\n{str(e)}")

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QFormLayout()
        
        self.game_mods_input = QLineEdit(self)
        self.game_mods_input.setText(config.get("game_mods_folder", ""))
        self.layout.addRow("Game Mods Folder:", self.game_mods_input)
        
        self.mod_loader_input = QLineEdit(self)
        self.mod_loader_input.setText(config.get("mod_loader_folder", ""))
        self.layout.addRow("Mod Loader Folder:", self.mod_loader_input)
        
        self.save_btn = QPushButton(QIcon("icons/save.png"), "Save", self)
        self.save_btn.clicked.connect(self.save_settings)
        self.layout.addRow(self.save_btn)
        
        self.setLayout(self.layout)
        self.config = config

    def save_settings(self):
        self.config["game_mods_folder"] = self.game_mods_input.text()
        self.config["mod_loader_folder"] = self.mod_loader_input.text()
        with open(os.path.join(os.getcwd(), 'config', 'config.json'), 'w') as config_file:
            json.dump(self.config, config_file, indent=4)
        QMessageBox.information(self, "Settings", "Configuration saved successfully.")
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loader = ModLoader()
    loader.show()
    sys.exit(app.exec())