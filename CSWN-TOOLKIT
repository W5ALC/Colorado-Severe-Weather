#!/usr/bin/python3
import sys
import webbrowser
import json
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QMessageBox, QTextEdit, QFileDialog, QLineEdit, QMenu, QMenuBar, QInputDialog, QComboBox, QDialog, QSpinBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QSettings
from PyQt6.QtGui import QFont, QAction, QIcon, QPixmap
from io import BytesIO

try:
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET
    from PIL import Image, ImageQt
except Exception as e:
    print(f"Import error: {e.__class__.__name__}: {e}")
    sys.exit(1)

CONFIG_FILE = os.path.expanduser("~/.weather_toolkit_config.json")
ERROR_LOG = os.path.expanduser("~/.weather_toolkit_error.log")

APP_TITLE = "Colorado Severe Weather Network Toolkit"
APP_AUTHOR = "W5ALC"
AUTHOR_EMAIL = "Jon.W5ALC@gmail.com"
APP_VERSION = "2.0"

DEFAULT_CONFIG = {
    "theme": "dark",
    "font_size": 12,
    "auto_refresh_mins": 5,
    "window_geometry": "1200x900+50+50",
    "default_section": "",
}

themes = {
    "dark": {
        "bg": "#181818",
        "fg": "white",
        "accent": "cyan",
        "button_bg": "#222",
        "button_fg": "white",
        "button_active_bg": "gray30",
        "button_active_fg": "cyan",
        "label_fg": "white",
        "label_bg": "#181818",
        "entry_bg": "#222",
        "entry_fg": "white",
        "entry_insert": "white",
        "section_fg": "cyan",
        "status_bg": "#222",
        "status_fg": "white",
        "warning": "red",
        "watch": "orange",
        "advisory": "#ffd700",
        "county": "cyan",
        "help_fg": "white",
    },
    "light": {
        "bg": "#f0f0f0",
        "fg": "#232323",
        "accent": "#0a62b1",
        "button_bg": "#ffffff",
        "button_fg": "#232323",
        "button_active_bg": "#e0e0e0",
        "button_active_fg": "#0a62b1",
        "label_fg": "#232323",
        "label_bg": "#f0f0f0",
        "entry_bg": "#ffffff",
        "entry_fg": "#232323",
        "entry_insert": "#232323",
        "section_fg": "#0a62b1",
        "status_bg": "#e0e0e0",
        "status_fg": "#232323",
        "warning": "#b20000",
        "watch": "#e67e00",
        "advisory": "#b1a000",
        "county": "#0a62b1",
        "help_fg": "#232323",
    }
}

resources = {
    "Hazardous Weather Outlooks": {
        "Grand Junction HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=GJT&product=HWO",
        "Boulder HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=BOU&product=HWO",
        "Goodland HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=GLD&product=HWO",
        "Pueblo HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=PUB&product=HWO",
        "Cheyenne HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=CYS&product=HWO",
    },
    "Area Forecast Discussions": {
        "Grand Junction AFD": "https://forecast.weather.gov/product.php?site=GJT&product=AFD&issuedby=GJT",
        "Boulder AFD": "https://forecast.weather.gov/product.php?site=BOU&product=AFD&issuedby=BOU",
        "Goodland AFD": "https://forecast.weather.gov/product.php?site=GLD&product=AFD&issuedby=GLD",
        "Pueblo AFD": "https://forecast.weather.gov/product.php?site=PUB&product=AFD&issuedby=PUB",
        "Cheyenne AFD": "https://forecast.weather.gov/product.php?site=CYS&product=AFD&issuedby=CYS",
    },
    "NWS Office Homepages": {
        "Grand Junction NWS": "https://www.weather.gov/gjt/",
        "Boulder NWS": "https://www.weather.gov/bou/",
        "Goodland NWS": "https://www.weather.gov/gld/",
        "Pueblo NWS": "https://www.weather.gov/pub/",
        "Cheyenne NWS": "https://www.weather.gov/cys/",
    },
    "Active Alerts and Reports": {
        "NWS Colorado Warnings Map": "https://www.weather.gov/alerts/co",
        "Colorado Active NWS Alerts": "https://alerts.weather.gov/cap/co.php?x=0",
        "NWS LSRs (Storm Reports)": "https://mesonet.agron.iastate.edu/lsr/#CO",
        "NWS Snow & Ice Reports": "https://www.weather.gov/crh/snowreports?sid=pub",
        "mPING Reports": "https://mping.ou.edu/display/",
        "CoCoRaHS Rain/Snow Map": "https://www.cocorahs.org/Maps/ViewMap.aspx?state=CO",
        "NWS EDD Digital Display": "https://digital.weather.gov/",
    },
    "Radar and Satellite": {
        "NWS Enhanced Radar": "https://radar.weather.gov/",
        "COD NEXRAD Viewer SW": "https://weather.cod.edu/satrad/?parms=regional-southwest-comp_radar-24-0-100-1&checked=map",
        "Ventusky Radar": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=radar",
        "Ventusky Satellite": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=satellite",
        "GOES Geocolor": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/GEOCOLOR/latest.jpg",
        "GOES Sandwich RGB": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/Sandwich/2500x1500.jpg",
        "GOES SLIDER": "https://rammb-slider.cira.colostate.edu/?sat=goes-16&sec=Colorado",
        "Zoom Earth": "https://zoom.earth/",
    },
    "Model and Forecast Tools": {
        "National Forecast": "https://www.wpc.ncep.noaa.gov/national_forecast/natfcst.php",
        "WPC Excessive Rainfall Outlook": "https://www.wpc.ncep.noaa.gov/qpf/excessive_rainfall_outlook_ero.php",
        "NDFD Graphical Forecast": "https://digital.weather.gov/?zoom=6&lat=38.9972&lon=-105.5478&layers=F00BTTTFFTT&region=0&element=4&mxmz=false&barbs=false&subl=TFFFFF&units=english&wunits=nautical&coords=latlon&tunits=localt",
        "WPC Homepage": "https://www.wpc.ncep.noaa.gov/",
        "HRRR Model Viewer": "https://rapidrefresh.noaa.gov/hrrr/HRRR/",
        "NAM NEST Model": "https://mag.ncep.noaa.gov/model-guidance-model-area.php?group=Model Guidance&model=NAM NEST&area=CONUS&sector=conus&element=Precipitation&plot=REFC&timing=Most Recent",
        "Pivotal Weather Models": "https://www.pivotalweather.com/model.php?m=nam",
        "NBM Graphical Forecasts": "https://digital.weather.gov/",
    },
    "SPC and Severe Wx Resources": {
        "SPC Thunderstorm Outlook": "https://www.spc.noaa.gov/products/exper/enhtstm/",
        "SPC Mesoscale Discussions": "https://www.spc.noaa.gov/products/md/",
        "SPC Mesoanalysis": "https://www.spc.noaa.gov/exper/mesoanalysis/",
        "SPC Convective Outlooks": "https://www.spc.noaa.gov/products/outlook/",
        "SPC Watches": "https://www.spc.noaa.gov/products/watch/",
        "SPC Storm Reports": "https://www.spc.noaa.gov/climo/reports/",
        "SPC GIS Data": "https://www.spc.noaa.gov/gis/svrgis/",
    },
    "Skywarn and Amateur Radio": {
        "Skywarn Spotter's Field Guide": "https://www.weather.gov/spotterguide/",
        "Skywarn Spotter Checklist": "https://www.weather.gov/gjt/spotterchecklist",
        "Skywarn National Page": "https://www.weather.gov/skywarn/",
        "Skywarn Online Training (MetEd)": "https://learn.meted.ucar.edu/#/curricula/0302af65-dcad-4841-87a8-77014473fe29",
        "Colorado ARES": "https://www.coloradoares.org/",
        "SkyHubLink Main Website": "https://skyhublink.com/",
        "SkyHubLink Live Audio Feed": "https://hose.brandmeister.network/?subscribe=310847",
        "Colorado Severe WX Hoseline": "https://hose.brandmeister.network/?subscribe=31083",
    },
    "Fire, Flood, and Avalanche": {
        "NWS Fire Weather": "https://www.weather.gov/bou/fire",
        "National Interagency Fire Center": "https://www.nifc.gov/",
        "USGS Colorado Stream Gauges": "https://waterdata.usgs.gov/co/nwis/rt",
        "NWS River Forecasts": "https://water.weather.gov/ahps2/index.php?wfo=pub",
        "Colorado Avalanche Info Center": "https://avalanche.state.co.us/",
    }
}

def log_error(msg):
    try:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
    except Exception as e:
        log_error(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f)
    except Exception as e:
        log_error(f"Error saving config: {e}")

class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.result = None
        theme = themes[config["theme"]]

        layout = QVBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_box = QComboBox()
        self.theme_box.addItems(themes.keys())
        self.theme_box.setCurrentText(config["theme"])
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_box)
        font_label = QLabel("Font Size:")
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 28)
        self.font_spin.setValue(config["font_size"])
        layout.addWidget(font_label)
        layout.addWidget(self.font_spin)
        refresh_label = QLabel("Auto-refresh Alerts (mins):")
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(2, 60)
        self.refresh_spin.setValue(config.get("auto_refresh_mins", 5))
        layout.addWidget(refresh_label)
        layout.addWidget(self.refresh_spin)
        section_label = QLabel("Default Section:")
        self.section_edit = QLineEdit()
        self.section_edit.setText(config.get("default_section", ""))
        layout.addWidget(section_label)
        layout.addWidget(self.section_edit)
        btn = QPushButton("Save")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)
        self.setLayout(layout)

    def save(self):
        self.result = {
            "theme": self.theme_box.currentText(),
            "font_size": self.font_spin.value(),
            "auto_refresh_mins": self.refresh_spin.value(),
            "default_section": self.section_edit.text(),
        }
        self.accept()

class TextPopup(QDialog):
    def __init__(self, parent, url, title, typ, theme, font_size, parse_pre=False):
        super().__init__(parent)
        self.setWindowTitle(f"{typ} Viewer - {title}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        self.status = QLabel(f"Loading {typ}...")
        self.status.setStyleSheet(f"color: {theme['accent']};")
        layout.addWidget(self.status)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Courier", font_size))
        self.text.setStyleSheet(f"background: {theme['bg']}; color: {theme['fg']};")
        layout.addWidget(self.text)
        ctrl = QHBoxLayout()
        btn_copy = QPushButton("Copy All")
        btn_copy.clicked.connect(self.copy_all)
        btn_save = QPushButton("Save As...")
        btn_save.clicked.connect(self.save_as)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        ctrl.addWidget(btn_copy)
        ctrl.addWidget(btn_save)
        ctrl.addStretch()
        ctrl.addWidget(btn_close)
        layout.addLayout(ctrl)
        self.setLayout(layout)
        QTimer.singleShot(100, lambda: self.load_content(url, typ, parse_pre))

    def load_content(self, url, typ, parse_pre):
        try:
            resp = requests.get(url, timeout=10)
            if parse_pre:
                soup = BeautifulSoup(resp.content, "html.parser")
                pre = soup.find("pre")
                text = pre.text if pre else f"{typ} content not found."
            else:
                text = resp.text
        except Exception as e:
            text = f"Failed to retrieve {typ}:\n{e}"
            log_error(text)
        self.text.setPlainText(text)
        self.status.setText(f"{typ} loaded.")

    def copy_all(self):
        QApplication.clipboard().setText(self.text.toPlainText())

    def save_as(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Text", "", "Text Files (*.txt)")
        if fname:
            try:
                with open(fname, "w") as f:
                    f.write(self.text.toPlainText())
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Could not save file: {e}")

class ImagePopup(QDialog):
    def __init__(self, parent, url, theme, font_size):
        super().__init__(parent)
        self.setWindowTitle("GOES Snapshot")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(f"background: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        self.status = QLabel("Loading image...")
        self.status.setStyleSheet(f"color: {theme['accent']};")
        layout.addWidget(self.status)
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_label, 1)
        btn = QPushButton("Close")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)
        self.setLayout(layout)
        QTimer.singleShot(100, lambda: self.load_image(url))

    def load_image(self, url):
        try:
            resp = requests.get(url, timeout=10)
            img = Image.open(BytesIO(resp.content))
            qt_img = ImageQt.ImageQt(img)
            pix = QPixmap.fromImage(qt_img)
            self.img_label.setPixmap(pix.scaled(900, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.status.setText("GOES Snapshot loaded.")
        except Exception as e:
            log_error(f"Image load error: {e}")
            self.status.setText("Image failed to load.")

class AlertFetcher(QThread):
    alerts_loaded = pyqtSignal(str)

    def __init__(self, url, parse_atom=True, parent=None):
        super().__init__(parent)
        self.url = url
        self.parse_atom = parse_atom

    def run(self):
        text = ""
        try:
            resp = requests.get(self.url, timeout=12)
            if self.parse_atom:
                rootx = ET.fromstring(resp.content)
                entries = rootx.findall("{http://www.w3.org/2005/Atom}entry")
                for entry in entries:
                    title = entry.find("{http://www.w3.org/2005/Atom}title")
                    summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                    link = entry.find("{http://www.w3.org/2005/Atom}link")
                    area = entry.find("{urn:oasis:names:tc:emergency:cap:1.1}areaDesc")
                    counties = area.text if area is not None and area.text else ""
                    text += f"{title.text}\n{summary.text}\n{counties}\n{link.attrib.get('href') if link is not None else ''}\n\n"
            else:
                text = resp.text
        except Exception as e:
            text = f"Failed to fetch alerts:\n{e}"
            log_error(text)
        self.alerts_loaded.emit(text)

class AlertPopup(QDialog):
    def __init__(self, parent, url, title, theme, font_size):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(950, 700)
        self.setStyleSheet(f"background: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        self.status = QLabel("Loading alerts...")
        self.status.setStyleSheet(f"color: {theme['accent']};")
        layout.addWidget(self.status)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter alerts...")
        layout.addWidget(self.search_box)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Courier", font_size))
        self.text.setStyleSheet(f"background: {theme['bg']}; color: {theme['fg']};")
        layout.addWidget(self.text)
        ctrl = QHBoxLayout()
        btn_copy = QPushButton("Copy All")
        btn_copy.clicked.connect(self.copy_all)
        btn_save = QPushButton("Save As...")
        btn_save.clicked.connect(self.save_as)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        ctrl.addWidget(btn_copy)
        ctrl.addWidget(btn_save)
        ctrl.addStretch()
        ctrl.addWidget(btn_close)
        layout.addLayout(ctrl)
        self.setLayout(layout)
        self.data = ""
        self.search_box.textChanged.connect(self.apply_filter)
        self.fetcher = AlertFetcher(url, parse_atom=True)
        self.fetcher.alerts_loaded.connect(self.load_alerts)
        self.fetcher.start()

    def load_alerts(self, text):
        self.data = text
        self.text.setPlainText(text)
        self.status.setText("Alerts loaded.")

    def apply_filter(self):
        term = self.search_box.text().lower()
        if not term:
            self.text.setPlainText(self.data)
        else:
            # Simple filter/highlight
            filtered = "\n".join([line for line in self.data.splitlines() if term in line.lower() or line.strip() == ""])
            self.text.setPlainText(filtered)

    def copy_all(self):
        QApplication.clipboard().setText(self.text.toPlainText())

    def save_as(self):
        from PyQt5.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getSaveFileName(self, "Save Alerts", "", "Text Files (*.txt);;All Files (*)")
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(self.text.toPlainText())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.theme = themes[self.config["theme"]]
        self.font_size = self.config["font_size"]
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 900)
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"background: {self.theme['status_bg']}; color: {self.theme['status_fg']};")
        self.status_bar.showMessage("Ready.")
        self.setup_ui()
        self.apply_theme()
        self.restore_geometry()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        # Top Buttons
        top_layout = QHBoxLayout()
        btn_co_alerts = QPushButton("Colorado Alerts (Alt+C)")
        btn_co_alerts.clicked.connect(self.fetch_colorado_alerts)
        top_layout.addWidget(btn_co_alerts)
        btn_us_alerts = QPushButton("US Alerts (Alt+U)")
        btn_us_alerts.clicked.connect(self.fetch_us_alerts)
        top_layout.addWidget(btn_us_alerts)
        btn_goes = QPushButton("GOES Snapshot (Alt+G)")
        btn_goes.clicked.connect(self.show_satellite_image)
        top_layout.addWidget(btn_goes)
        btn_nws = QPushButton("Report Weather to NWS (Alt+A)")
        btn_nws.clicked.connect(lambda: webbrowser.open("https://inws.ncep.noaa.gov/report/"))
        top_layout.addWidget(btn_nws)
        btn_settings = QPushButton("Settings")
        btn_settings.clicked.connect(self.open_settings)
        top_layout.addWidget(btn_settings)
        btn_help = QPushButton("Help (F1)")
        btn_help.clicked.connect(self.show_help)
        top_layout.addWidget(btn_help)
        btn_submit = QPushButton("Submit Resource")
        btn_submit.clicked.connect(self.submit_resource)
        top_layout.addWidget(btn_submit)
        btn_exit = QPushButton("Exit (Alt+Q)")
        btn_exit.clicked.connect(self.close)
        top_layout.addWidget(btn_exit)
        main_layout.addLayout(top_layout)

        # Section Grid (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        grid_widget = QWidget()
        section_grid = QGridLayout()
        grid_widget.setLayout(section_grid)

        row, col = 0, 0
        max_columns = 3
        for i, (section, items) in enumerate(resources.items()):
            group = QGroupBox(section)
            group.setStyleSheet(f"color: {self.theme['section_fg']}; background: {self.theme['bg']};")
            vbox = QVBoxLayout()
            for name, url in items.items():
                btn = QPushButton(name)
                btn.setStyleSheet(f"background: {self.theme['button_bg']}; color: {self.theme['button_fg']};")
                btn.clicked.connect(self.make_resource_command(section, name, url))
                vbox.addWidget(btn)
            group.setLayout(vbox)
            section_grid.addWidget(group, row, col)
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
        scroll_area.setWidget(grid_widget)
        main_layout.addWidget(scroll_area)
        self.central.setLayout(main_layout)

        self.setup_menu()

        # Keyboard shortcuts
        self.shortcut_actions = {
            Qt.Key.Key_F1: self.show_help,
            Qt.Key.Key_F12: self.show_about,
            Qt.Key.Key_G: self.show_satellite_image,
            Qt.Key.Key_C: self.fetch_colorado_alerts,
            Qt.Key.Key_Q: self.close,
            Qt.Key.Key_U: self.fetch_us_alerts,
        }
        self.central.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            key = event.key()
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                if key in self.shortcut_actions:
                    self.shortcut_actions[key]()
                    return True
            if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and key == Qt.Key.Key_S:
                self.open_settings()
                return True
            if key == Qt.Key.Key_F1:
                self.show_help()
                return True
            if key == Qt.Key.Key_F12:
                self.show_about()
                return True
        return super().eventFilter(obj, event)

    # def setup_menu(self):
    #     menubar = self.menuBar()
    #     settings_menu = menubar.addMenu("Settings")
    #     action_settings = QAction("Settings...", self)
    #     action_settings.triggered.connect(self.open_settings)
    #     settings_menu.addAction(action_settings)
    #     help_menu = menubar.addMenu("Help")
    #     action_help = QAction("Help", self)
    #     action_help.triggered.connect(self.show_help)
    #     help_menu.addAction(action_help)
    #     action_about = QAction("About", self)
    #     action_about.triggered.connect(self.show_about)
    #     help_menu.addAction(action_about)

    def setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        action_open = QAction("Open Resource List", self)
        action_open.triggered.connect(self.open_resource_list)
        file_menu.addAction(action_open)
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        action_settings = QAction("Settings...", self)
        action_settings.triggered.connect(self.open_settings)
        settings_menu.addAction(action_settings)

        # Extras menu
        extras_menu = menubar.addMenu("Extras")
        action_feedback = QAction("Send Feedback", self)
        action_feedback.triggered.connect(self.send_feedback)
        extras_menu.addAction(action_feedback)
        action_website = QAction("Visit Website", self)
        action_website.triggered.connect(lambda: webbrowser.open("https://yourwebsite.com"))
        extras_menu.addAction(action_website)

        # Help menu
        help_menu = menubar.addMenu("Help")
        action_help = QAction("Help", self)
        action_help.triggered.connect(self.show_help)
        help_menu.addAction(action_help)
        action_about = QAction("About", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    # Example handler for opening resource list
    def open_resource_list(self):
        QMessageBox.information(self, "Resource List", "Here you could show the full list of resources.")

    # Example handler for feedback
    def send_feedback(self):
        webbrowser.open("mailto:Jon.W5ALC@gmail.com?subject=Feedback%20for%20WeatherToolkit")


    def make_resource_command(self, section, name, url):
        def cmd():
            if section == "Hazardous Weather Outlooks":
                self.show_hwo(url, name)
            elif section == "Area Forecast Discussions":
                self.show_afd(url, name)
            else:
                webbrowser.open(url)
                self.status_bar.showMessage(f"Opened: {url}")
        return cmd

    def fetch_colorado_alerts(self):
        dlg = AlertPopup(self, "https://alerts.weather.gov/cap/co.php?x=0", "Active Colorado Alerts", self.theme, self.font_size)
        dlg.exec()

    def fetch_us_alerts(self):
        dlg = AlertPopup(self, "https://api.weather.gov/alerts/active.atom", "Active US Alerts", self.theme, self.font_size)
        dlg.exec()

    def show_afd(self, url, title):
        dlg = TextPopup(self, url, title, "AFD", self.theme, self.font_size, parse_pre=True)
        dlg.exec()

    def show_hwo(self, url, title):
        dlg = TextPopup(self, url, title, "HWO", self.theme, self.font_size, parse_pre=True)
        dlg.exec()

    def show_satellite_image(self):
        url = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/latest.jpg"
        dlg = ImagePopup(self, url, self.theme, self.font_size)
        dlg.exec()

    def submit_resource(self):
        mailto_link = (
            "mailto:Jon.W5ALC@gmail.com"
            "?subject=Colorado%20SWN%20toolkit%20Resource%20Suggestion"
            "&body=Suggest%20a%20new%20resource%20or%20link%20here:%0A%0A"
            "Name%20of%20Resource:%0AURL:%0ADescription%20(optional):"
        )
        self.launch_item(mailto_link)
        self.status_bar.showMessage("Opened mail client for resource suggestion.")

    def open_settings(self):
        dlg = SettingsDialog(self, self.config)
        if dlg.exec() and dlg.result:
            self.config.update(dlg.result)
            save_config(self.config)
            self.theme = themes[self.config["theme"]]
            self.font_size = self.config["font_size"]
            self.apply_theme()
            self.status_bar.showMessage("Settings updated.")

    def apply_theme(self):
        self.setStyleSheet(f"background: {self.theme['bg']}; color: {self.theme['fg']};")
        self.status_bar.setStyleSheet(f"background: {self.theme['status_bg']}; color: {self.theme['status_fg']};")

    def show_about(self):
        msg = (
            f"{APP_TITLE}\n"
            f"Version: {APP_VERSION}\n"
            f"Author: {APP_AUTHOR}\n"
            f"Contact: {AUTHOR_EMAIL}\n\n"
            "A toolkit for quick access to Colorado and US weather resources, "
            "designed for spotters, emergency managers, and weather enthusiasts.\n\n"
            "Features:\n"
            "  • One-click access to NWS outlooks, discussions, radar, and satellite\n"
            "  • Real-time alert feed for Colorado and US\n"
            "  • Amateur radio and Skywarn resources\n"
            "  • Customizable appearance and refresh settings\n"
            "  • Keyboard shortcuts for rapid workflow\n\n"
            "Keyboard Shortcuts:\n"
            "  Alt+C: Colorado Alerts\n"
            "  Alt+U: US Alerts\n"
            "  Alt+G: GOES Snapshot\n"
            "  Ctrl+S: Settings\n"
            "  F1: Help\n"
            "  Alt+Q: Exit\n\n"
            "Website: https://github.com/W5ALC/\n"
            "License: MIT\n"
            "Credits: Thanks to the National Weather Service and community developers.\n"
            "For bug reports and suggestions, please use the 'Submit Resource' button or email directly."
        )
        QMessageBox.information(self, "About", msg)


    def show_help(self):
        msg = (
            "=== Colorado Severe Weather Network Toolkit Help ===\n\n"
            "Welcome! This toolkit provides fast access to critical weather information for Colorado and the US.\n\n"
            "Main Window:\n"
            "• The main area contains grouped buttons for NWS products, radar, forecasts, radio resources, etc.\n"
            "• Click any button to open the resource. Some items (AFD/HWO) show full text in-app; most open in your browser.\n\n"
            "Top Buttons:\n"
            "• Colorado Alerts: Real-time NWS warnings for Colorado\n"
            "• US Alerts: All current US watches/warnings\n"
            "• GOES Snapshot: Latest geostationary satellite image\n"
            "• Report Weather: Opens NWS spotter report form\n"
            "• Settings: Choose dark/light theme, font size, refresh interval, default section\n"
            "• Help: This help dialog\n"
            "• Submit Resource: Suggest new links/resources for inclusion\n"
            "• Exit: Close the application\n\n"
            "Keyboard Shortcuts:\n"
            "  Alt+C: Colorado Alerts\n"
            "  Alt+U: US Alerts\n"
            "  Alt+G: GOES Snapshot\n"
            "  Ctrl+S: Open Settings\n"
            "  F1: Open Help\n"
            "  Alt+Q: Exit app\n\n"
            "Settings:\n"
            "• Adjust theme and font for accessibility.\n"
            "• Set auto-refresh time for alerts.\n"
            "• Choose a default section to show at startup.\n"
            "• Changes are saved automatically.\n\n"
            "Troubleshooting:\n"
            "• If a resource fails to load, check your internet connection.\n"
            "• Some resources may require a modern web browser.\n"
            "• For persistent issues, check the error log at ~/.weather_toolkit_error.log.\n"
            "• For help, feedback, or to report bugs, use 'Submit Resource' or email the author.\n\n"
            "Further Info:\n"
            "• Application updates may be found at: https://github.com/W5ALC/\n"
            "• Licensed under MIT. Attribution for data: National Weather Service, NOAA, UCAR MetEd, and others.\n"
            "• For amateur radio and Skywarn info, see the dedicated section in the main grid.\n"
            "\nContact: Jon.W5ALC@gmail.com\n"
        )
        QMessageBox.information(self, "Help", msg)


    def closeEvent(self, event):
        self.save_geometry()
        event.accept()

    def save_geometry(self):
        settings = QSettings("W5ALC", "WeatherToolkit")
        settings.setValue("geometry", self.saveGeometry())

    def restore_geometry(self):
        settings = QSettings("W5ALC", "WeatherToolkit")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("W5ALC")
    app.setApplicationName("WeatherToolkit")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
