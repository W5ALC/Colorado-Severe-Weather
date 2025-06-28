#!/usr/bin/python3
import sys
import webbrowser
import json
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QMessageBox, QTextEdit, QFileDialog, QLineEdit, QMenu, QMenuBar, 
    QInputDialog, QComboBox, QDialog, QSpinBox, QSizePolicy, QScrollArea, QFrame, QSplitter,
    QTabWidget, QProgressBar, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QSettings, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QAction, QIcon, QPixmap, QPalette, QColor, QPainter, QLinearGradient, QBrush
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
APP_VERSION = "2.1 Enhanced"

DEFAULT_CONFIG = {
    "theme": "dark",
    "font_size": 12,
    "auto_refresh_mins": 5,
    "window_geometry": "1400x1000+50+50",
    "default_section": "",
    "compact_mode": False,
    "show_tooltips": True,
}

# Enhanced themes with better color schemes and gradients
themes = {
    "dark": {
        "bg": "#1a1a1a",
        "bg_secondary": "#2d2d2d",
        "fg": "#ffffff",
        "fg_secondary": "#b0b0b0",
        "accent": "#00d4ff",
        "accent_hover": "#00b8e6",
        "button_bg": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a3a3a, stop:1 #2a2a2a)",
        "button_hover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a4a4a, stop:1 #3a3a3a)",
        "button_pressed": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a2a2a, stop:1 #1a1a1a)",
        "button_fg": "#ffffff",
        "group_bg": "#252525",
        "group_border": "#404040",
        "entry_bg": "#2a2a2a",
        "entry_fg": "#ffffff",
        "entry_border": "#404040",
        "entry_focus": "#00d4ff",
        "section_fg": "#00d4ff",
        "status_bg": "#1f1f1f",
        "status_fg": "#ffffff",
        "warning": "#ff4757",
        "watch": "#ffa726",
        "advisory": "#ffeb3b",
        "success": "#4caf50",
        "info": "#2196f3",
        "shadow": "rgba(0, 0, 0, 0.3)",
    },
    "light": {
        "bg": "#f8f9fa",
        "bg_secondary": "#ffffff",
        "fg": "#212529",
        "fg_secondary": "#6c757d",
        "accent": "#007bff",
        "accent_hover": "#0056b3",
        "button_bg": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa)",
        "button_hover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef)",
        "button_pressed": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e9ecef, stop:1 #dee2e6)",
        "button_fg": "#212529",
        "group_bg": "#ffffff",
        "group_border": "#dee2e6",
        "entry_bg": "#ffffff",
        "entry_fg": "#212529",
        "entry_border": "#ced4da",
        "entry_focus": "#007bff",
        "section_fg": "#007bff",
        "status_bg": "#f8f9fa",
        "status_fg": "#212529",
        "warning": "#dc3545",
        "watch": "#fd7e14",
        "advisory": "#ffc107",
        "success": "#28a745",
        "info": "#17a2b8",
        "shadow": "rgba(0, 0, 0, 0.1)",
    },
    "blue": {
        "bg": "#0d1421",
        "bg_secondary": "#1e2a3a",
        "fg": "#ffffff",
        "fg_secondary": "#a0b0c0",
        "accent": "#4fc3f7",
        "accent_hover": "#29b6f6",
        "button_bg": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a3f5f, stop:1 #1e2a3a)",
        "button_hover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a4f70, stop:1 #2a3f5f)",
        "button_pressed": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e2a3a, stop:1 #0d1421)",
        "button_fg": "#ffffff",
        "group_bg": "#1a2533",
        "group_border": "#2a3f5f",
        "entry_bg": "#1e2a3a",
        "entry_fg": "#ffffff",
        "entry_border": "#2a3f5f",
        "entry_focus": "#4fc3f7",
        "section_fg": "#4fc3f7",
        "status_bg": "#0d1421",
        "status_fg": "#ffffff",
        "warning": "#f44336",
        "watch": "#ff9800",
        "advisory": "#ffeb3b",
        "success": "#4caf50",
        "info": "#2196f3",
        "shadow": "rgba(0, 0, 0, 0.4)",
    }
}

resources = {
    "⚠️ Hazardous Weather Outlooks": {
        "Grand Junction HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=GJT&product=HWO",
        "Boulder HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=BOU&product=HWO",
        "Goodland HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=GLD&product=HWO",
        "Pueblo HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=PUB&product=HWO",
        "Cheyenne HWO": "https://forecast.weather.gov/product.php?site=NWS&issuedby=CYS&product=HWO",
    },
    "📊 Area Forecast Discussions": {
        "Grand Junction AFD": "https://forecast.weather.gov/product.php?site=GJT&product=AFD&issuedby=GJT",
        "Boulder AFD": "https://forecast.weather.gov/product.php?site=BOU&product=AFD&issuedby=BOU",
        "Goodland AFD": "https://forecast.weather.gov/product.php?site=GLD&product=AFD&issuedby=GLD",
        "Pueblo AFD": "https://forecast.weather.gov/product.php?site=PUB&product=AFD&issuedby=PUB",
        "Cheyenne AFD": "https://forecast.weather.gov/product.php?site=CYS&product=AFD&issuedby=CYS",
    },
    "🏠 NWS Office Homepages": {
        "Grand Junction NWS": "https://www.weather.gov/gjt/",
        "Boulder NWS": "https://www.weather.gov/bou/",
        "Goodland NWS": "https://www.weather.gov/gld/",
        "Pueblo NWS": "https://www.weather.gov/pub/",
        "Cheyenne NWS": "https://www.weather.gov/cys/",
    },
    "🚨 Active Alerts and Reports": {
        "NWS Colorado Warnings Map": "https://www.weather.gov/alerts/co",
        "Colorado Active NWS Alerts": "https://alerts.weather.gov/cap/co.php?x=0",
        "NWS Storm Reports": "https://mesonet.agron.iastate.edu/lsr/#CO",
        "NWS Snow & Ice Reports": "https://www.weather.gov/crh/snowreports?sid=pub",
        "mPING Reports": "https://mping.ou.edu/display/",
        "CoCoRaHS Rain/Snow Map": "https://www.cocorahs.org/Maps/ViewMap.aspx?state=CO",
        "NWS EDD Digital Display": "https://digital.weather.gov/",
    },
    "📡 Radar and Satellite": {
        "NWS Enhanced Radar": "https://radar.weather.gov/",
        "COD NEXRAD Viewer SW": "https://weather.cod.edu/satrad/?parms=regional-southwest-comp_radar-24-0-100-1&checked=map",
        "Ventusky Radar": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=radar",
        "Ventusky Satellite": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=satellite",
        "GOES Geocolor": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/GEOCOLOR/latest.jpg",
        "GOES Sandwich RGB": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/Sandwich/2500x1500.jpg",
        "GOES SLIDER": "https://rammb-slider.cira.colostate.edu/?sat=goes-16&sec=Colorado",
        "Zoom Earth": "https://zoom.earth/",
    },
    "🌐 Model and Forecast Tools": {
        "National Forecast": "https://www.wpc.ncep.noaa.gov/national_forecast/natfcst.php",
        "WPC Excessive Rainfall Outlook": "https://www.wpc.ncep.noaa.gov/qpf/excessive_rainfall_outlook_ero.php",
        "NDFD Graphical Forecast": "https://digital.weather.gov/?zoom=6&lat=38.9972&lon=-105.5478&layers=F00BTTTFFTT&region=0&element=4",
        "WPC Homepage": "https://www.wpc.ncep.noaa.gov/",
        "HRRR Model Viewer": "https://rapidrefresh.noaa.gov/hrrr/HRRR/",
        "NAM NEST Model": "https://mag.ncep.noaa.gov/model-guidance-model-area.php?group=Model%20Guidance&model=NAM%20NEST",
        "Pivotal Weather Models": "https://www.pivotalweather.com/model.php?m=nam",
        "NBM Graphical Forecasts": "https://digital.weather.gov/",
    },
    "⛈️ SPC and Severe Weather": {
        "SPC Thunderstorm Outlook": "https://www.spc.noaa.gov/products/exper/enhtstm/",
        "SPC Mesoscale Discussions": "https://www.spc.noaa.gov/products/md/",
        "SPC Mesoanalysis": "https://www.spc.noaa.gov/exper/mesoanalysis/",
        "SPC Convective Outlooks": "https://www.spc.noaa.gov/products/outlook/",
        "SPC Watches": "https://www.spc.noaa.gov/products/watch/",
        "SPC Storm Reports": "https://www.spc.noaa.gov/climo/reports/",
        "SPC GIS Data": "https://www.spc.noaa.gov/gis/svrgis/",
    },
    "📻 Skywarn and Amateur Radio": {
        "Skywarn Spotter's Field Guide": "https://www.weather.gov/spotterguide/",
        "Skywarn Spotter Checklist": "https://www.weather.gov/gjt/spotterchecklist",
        "Skywarn National Page": "https://www.weather.gov/skywarn/",
        "Skywarn Online Training": "https://learn.meted.ucar.edu/#/curricula/0302af65-dcad-4841-87a8-77014473fe29",
        "Colorado ARES": "https://www.coloradoares.org/",
        "SkyHubLink Website": "https://skyhublink.com/",
        "SkyHubLink Live Audio": "https://hose.brandmeister.network/?subscribe=310847",
        "Colorado Severe WX Hoseline": "https://hose.brandmeister.network/?subscribe=31083",
    },
    "🔥 Fire, Flood, and Avalanche": {
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
            json.dump(cfg, f, indent=2)
    except Exception as e:
        log_error(f"Error saving config: {e}")

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def apply_style(self, theme):
        self.setStyleSheet(f"""
            QPushButton {{
                background: {theme['button_bg']};
                color: {theme['button_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {theme['button_hover']};
                border-color: {theme['accent']};
                color: {theme['accent']};
            }}
            QPushButton:pressed {{
                background: {theme['button_pressed']};
                border-color: {theme['accent_hover']};
            }}
        """)

class ModernGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        
    def apply_style(self, theme):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 14px;
                color: {theme['section_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 10px;
                background: {theme['group_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background: {theme['group_bg']};
                border-radius: 4px;
            }}
        """)

class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        self.result = None
        self.config = config
        theme = themes[config["theme"]]
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {theme['bg']};
                color: {theme['fg']};
            }}
            QLabel {{
                color: {theme['fg']};
                font-weight: 500;
                margin: 5px 0;
            }}
            QComboBox, QSpinBox, QLineEdit {{
                background: {theme['entry_bg']};
                color: {theme['entry_fg']};
                border: 2px solid {theme['entry_border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border-color: {theme['entry_focus']};
            }}
            QPushButton {{
                background: {theme['button_bg']};
                color: {theme['button_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {theme['button_hover']};
                border-color: {theme['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Theme selection
        theme_label = QLabel("🎨 Theme:")
        self.theme_box = QComboBox()
        self.theme_box.addItems(["dark", "light", "blue"])
        self.theme_box.setCurrentText(config["theme"])
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_box)
        
        # Font size
        font_label = QLabel("🔤 Font Size:")
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 28)
        self.font_spin.setValue(config["font_size"])
        layout.addWidget(font_label)
        layout.addWidget(self.font_spin)
        
        # Auto refresh
        refresh_label = QLabel("🔄 Auto-refresh Alerts (minutes):")
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(2, 60)
        self.refresh_spin.setValue(config.get("auto_refresh_mins", 5))
        layout.addWidget(refresh_label)
        layout.addWidget(self.refresh_spin)
        
        # Default section
        section_label = QLabel("📂 Default Section:")
        self.section_edit = QLineEdit()
        self.section_edit.setText(config.get("default_section", ""))
        self.section_edit.setPlaceholderText("Leave empty for no default")
        layout.addWidget(section_label)
        layout.addWidget(self.section_edit)
        
        # Compact mode
        compact_label = QLabel("📱 Compact Mode:")
        self.compact_check = QComboBox()
        self.compact_check.addItems(["No", "Yes"])
        self.compact_check.setCurrentText("Yes" if config.get("compact_mode", False) else "No")
        layout.addWidget(compact_label)
        layout.addWidget(self.compact_check)
        
        # Tooltips
        tooltip_label = QLabel("💡 Show Tooltips:")
        self.tooltip_check = QComboBox()
        self.tooltip_check.addItems(["Yes", "No"])
        self.tooltip_check.setCurrentText("Yes" if config.get("show_tooltips", True) else "No")
        layout.addWidget(tooltip_label)
        layout.addWidget(self.tooltip_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Save Settings")
        btn_save.clicked.connect(self.save)
        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save(self):
        self.result = {
            "theme": self.theme_box.currentText(),
            "font_size": self.font_spin.value(),
            "auto_refresh_mins": self.refresh_spin.value(),
            "default_section": self.section_edit.text(),
            "compact_mode": self.compact_check.currentText() == "Yes",
            "show_tooltips": self.tooltip_check.currentText() == "Yes",
        }
        self.accept()

class TextPopup(QDialog):
    def __init__(self, parent, url, title, typ, theme, font_size, parse_pre=False):
        super().__init__(parent)
        self.setWindowTitle(f"{typ} Viewer - {title}")
        self.setMinimumSize(1000, 700)
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {theme['bg']};
                color: {theme['fg']};
            }}
            QTextEdit {{
                background: {theme['entry_bg']};
                color: {theme['entry_fg']};
                border: 2px solid {theme['entry_border']};
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }}
            QPushButton {{
                background: {theme['button_bg']};
                color: {theme['button_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                margin: 2px;
            }}
            QPushButton:hover {{
                background: {theme['button_hover']};
                border-color: {theme['accent']};
            }}
            QLabel {{
                color: {theme['accent']};
                font-weight: 600;
                padding: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Status bar
        self.status = QLabel(f"Loading {typ}...")
        layout.addWidget(self.status)
        
        # Text area
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Consolas", font_size))
        layout.addWidget(self.text)
        
        # Controls
        ctrl = QHBoxLayout()
        btn_copy = QPushButton("📋 Copy All")
        btn_copy.clicked.connect(self.copy_all)
        btn_save = QPushButton("💾 Save As...")
        btn_save.clicked.connect(self.save_as)
        btn_close = QPushButton("❌ Close")
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
        self.status.setText(f"✅ {typ} loaded successfully")

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
        self.setWindowTitle("🛰️ GOES Satellite Snapshot")
        self.setMinimumSize(1200, 800)
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {theme['bg']};
                color: {theme['fg']};
            }}
            QLabel {{
                color: {theme['accent']};
                font-weight: 600;
                padding: 10px;
            }}
            QPushButton {{
                background: {theme['button_bg']};
                color: {theme['button_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                margin: 5px;
            }}
            QPushButton:hover {{
                background: {theme['button_hover']};
                border-color: {theme['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        
        self.status = QLabel("🔄 Loading satellite image...")
        layout.addWidget(self.status)
        
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"border: 2px solid {theme['group_border']}; border-radius: 8px;")
        layout.addWidget(self.img_label, 1)
        
        btn_close = QPushButton("❌ Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        QTimer.singleShot(100, lambda: self.load_image(url))

    def load_image(self, url):
        try:
            resp = requests.get(url, timeout=15)
            img = Image.open(BytesIO(resp.content))
            qt_img = ImageQt.ImageQt(img)
            pix = QPixmap.fromImage(qt_img)
            self.img_label.setPixmap(pix.scaled(1100, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.status.setText("✅ Satellite image loaded successfully")
        except Exception as e:
            log_error(f"Image load error: {e}")
            self.status.setText("❌ Failed to load satellite image")

class AlertFetcher(QThread):
    alerts_loaded = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self, url, parse_atom=True, parent=None):
        super().__init__(parent)
        self.url = url
        self.parse_atom = parse_atom

    def run(self):
        text = ""
        try:
            self.progress_updated.emit(25)
            resp = requests.get(self.url, timeout=12)
            self.progress_updated.emit(50)
            
            if self.parse_atom:
                rootx = ET.fromstring(resp.content)
                entries = rootx.findall("{http://www.w3.org/2005/Atom}entry")
                self.progress_updated.emit(75)
                
                for entry in entries:
                    title = entry.find("{http://www.w3.org/2005/Atom}title")
                    summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                    link = entry.find("{http://www.w3.org/2005/Atom}link")
                    area = entry.find("{urn:oasis:names:tc:emergency:cap:1.1}areaDesc")
                    counties = area.text if area is not None and area.text else ""
                    text += f"🚨 {title.text}\n📝 {summary.text}\n🗺️ {counties}\n🔗 {link.attrib.get('href') if link is not None else ''}\n\n"
            else:
                text = resp.text
                
            self.progress_updated.emit(100)
        except Exception as e:
            text = f"❌ Failed to fetch alerts:\n{e}"
            log_error(f"Alert fetch error: {e}")
        
        self.alerts_loaded.emit(text)

class WeatherToolkit(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.refresh_alerts)
        self.current_theme = themes[self.config["theme"]]
        
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        
        # Apply window geometry
        geom = self.config.get("window_geometry", "1400x1000+50+50")
        try:
            w, h, x, y = geom.replace('+', 'x').replace('-', 'x').split('x')
            self.setGeometry(int(x), int(y), int(w), int(h))
        except:
            self.setGeometry(50, 50, 1400, 1000)
        
        self.setup_ui()
        self.apply_theme()
        
        # Auto-refresh setup
        if self.config.get("auto_refresh_mins", 5) > 0:
            self.alert_timer.start(self.config["auto_refresh_mins"] * 60000)
        
        # Load default section if specified
        default_section = self.config.get("default_section", "")
        if default_section and default_section in resources:
            self.load_section(default_section)

    def setup_ui(self):
        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        refresh_action = QAction("Refresh Alerts", self)
        refresh_action.triggered.connect(self.refresh_alerts)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # Resources menu with submenus
        resources_menu = menubar.addMenu("Resources")

        for section_name, links in resources.items():
            section_menu = resources_menu.addMenu(section_name)
            for link_name, url in links.items():
                action = QAction(link_name, self)
                action.triggered.connect(lambda checked, u=url: webbrowser.open(u))
                section_menu.addAction(action)

        # Quick access menu
        quick_menu = menubar.addMenu("Quick Access")
        alerts_action = QAction("🚨 Colorado Active Alerts", self)
        alerts_action.triggered.connect(self.show_alerts)
        quick_menu.addAction(alerts_action)

        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        quick_menu.addAction(settings_action)
        # File menu

        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        
        # Header
        header = QLabel(f"🌪️ {APP_TITLE}")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        main_layout.addWidget(header)
        header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        
        # Progress bar for alerts
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - sections
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        sections_label = QLabel("📂 Weather Resources")
        sections_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(sections_label)
        
        # Create section buttons
        self.section_buttons = {}
        for section_name in resources.keys():
            btn = ModernButton(section_name)
            btn.clicked.connect(lambda checked, name=section_name: self.load_section(name))
            self.section_buttons[section_name] = btn
            left_layout.addWidget(btn)
        
        # Quick alerts button
        alerts_btn = ModernButton("🚨 Colorado Active Alerts")
        alerts_btn.clicked.connect(self.show_alerts)
        left_layout.addWidget(alerts_btn)
        
        left_layout.addStretch()
        left_panel.setMaximumWidth(350)
        
        # Right panel - links
        self.right_panel = QScrollArea()
        self.right_panel.setWidgetResizable(True)
        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_panel.setWidget(self.right_content)
        
        # Welcome message
        welcome = QLabel("👈 Select a weather resource category from the left panel to begin")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("font-size: 18px; padding: 50px; color: #888;")
        self.right_layout.addWidget(welcome)
        self.right_layout.addStretch()
        
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(self.right_panel)
        content_splitter.setSizes([350, 1050])
        
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.statusBar().showMessage(f"Ready - {APP_AUTHOR} ({AUTHOR_EMAIL})")

    def load_section(self, section_name):
        # Clear right panel
        for i in reversed(range(self.right_layout.count())):
            child = self.right_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if section_name not in resources:
            return
        
        # Section header
        header = QLabel(f"{section_name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        self.right_layout.addWidget(header)
        
        # Create link buttons
        links = resources[section_name]
        for link_name, url in links.items():
            link_group = ModernGroupBox(link_name)
            link_layout = QVBoxLayout()
            
            # Button layout
            btn_layout = QHBoxLayout()
            

            # Special handling for different content types
            if any(x in url for x in ["HWO", "AFD", "product.php"]):
                view_btn = ModernButton("📄 View Text")
                view_btn.clicked.connect(lambda checked, u=url, n=link_name: self.show_text_popup(u, n, "NWS Text Product", True))
                btn_layout.addWidget(view_btn)
            elif "GOES" in url and url.endswith(".jpg"):
                view_btn = ModernButton("🛰️ View Image")
                view_btn.clicked.connect(lambda checked, u=url: self.show_image_popup(u))
                btn_layout.addWidget(view_btn)
            
            # Open in browser button
            open_btn = ModernButton("🌐 Open in Browser")
            open_btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            btn_layout.addWidget(open_btn)

            link_layout.addLayout(btn_layout)
            
            # URL display
            url_label = QLabel(f"🔗 {url}")
            url_label.setStyleSheet("font-size: 11px; padding: 5px; font-family: monospace;")
            url_label.setWordWrap(True)
            link_layout.addWidget(url_label)
            
            link_group.setLayout(link_layout)
            self.right_layout.addWidget(link_group)
        
        self.right_layout.addStretch()
        
        # Apply theme to new widgets
        self.apply_theme_to_section()

    def apply_theme_to_section(self):
        theme = self.current_theme
        for i in range(self.right_layout.count()):
            item = self.right_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ModernGroupBox):
                    widget.apply_style(theme)
                    # Apply theme to buttons inside
                    for j in range(widget.layout().count()):
                        sub_item = widget.layout().itemAt(j)
                        if sub_item and hasattr(sub_item, 'count'):
                            for k in range(sub_item.count()):
                                btn_item = sub_item.itemAt(k)
                                if btn_item and isinstance(btn_item.widget(), ModernButton):
                                    btn_item.widget().apply_style(theme)

    def show_text_popup(self, url, title, typ, parse_pre=False):
        popup = TextPopup(self, url, title, typ, self.current_theme, self.config["font_size"], parse_pre)
        popup.exec()

    def show_image_popup(self, url):
        popup = ImagePopup(self, url, self.current_theme, self.config["font_size"])
        popup.exec()

    def show_alerts(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.fetcher = AlertFetcher("https://alerts.weather.gov/cap/co.php?x=0")
        self.fetcher.alerts_loaded.connect(self.display_alerts)
        self.fetcher.progress_updated.connect(self.progress_bar.setValue)
        self.fetcher.start()

    def display_alerts(self, alert_text):
        self.progress_bar.setVisible(False)
        popup = QDialog(self)
        popup.setWindowTitle("🚨 Colorado Active Weather Alerts")
        popup.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout()
        
        text_area = QTextEdit()
        text_area.setPlainText(alert_text)
        text_area.setReadOnly(True)
        text_area.setFont(QFont("Consolas", self.config["font_size"]))
        layout.addWidget(text_area)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(popup.close)
        layout.addWidget(close_btn)
        
        popup.setLayout(layout)
        popup.setStyleSheet(self.get_dialog_style())
        popup.exec()

    def refresh_alerts(self):
        self.statusBar().showMessage("🔄 Refreshing alerts...")
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("✅ Alerts refreshed"))

    def show_settings(self):
        dialog = SettingsDialog(self, self.config)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result:
            # Update config
            for k, v in dialog.result.items():
                self.config[k] = v
            
            # Save config
            save_config(self.config)
            
            # Apply changes
            self.current_theme = themes[self.config["theme"]]
            self.apply_theme()
            
            # Restart timer if needed
            self.alert_timer.stop()
            if self.config["auto_refresh_mins"] > 0:
                self.alert_timer.start(self.config["auto_refresh_mins"] * 60000)

    def show_about(self):
        QMessageBox.about(self, "About", 
            f"""<h2>{APP_TITLE}</h2>
            <p><b>Version:</b> {APP_VERSION}</p>
            <p><b>Author:</b> {APP_AUTHOR}</p>
            <p><b>Email:</b> {AUTHOR_EMAIL}</p>
            <p>A comprehensive toolkit for Colorado severe weather monitoring and amateur radio operators.</p>
            <p>Provides quick access to NWS products, radar, satellite imagery, and Skywarn resources.</p>""")

    def apply_theme(self):
        theme = self.current_theme
        font_size = self.config["font_size"]
        
        # Main window style
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {theme['bg']};
                color: {theme['fg']};
                font-size: {font_size}px;
            }}
            QMenuBar {{
                background: {theme['bg_secondary']};
                color: {theme['fg']};
                border-bottom: 2px solid {theme['group_border']};
                padding: 4px;
            }}
            QMenuBar::item {{
                padding: 8px 12px;
                background: transparent;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background: {theme['accent']};
                color: {theme['bg']};
            }}
            QMenu {{
                background: {theme['bg_secondary']};
                color: {theme['fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 8px 20px;
            }}
            QMenu::item:selected {{
                background: {theme['accent']};
                color: {theme['bg']};
            }}
            QStatusBar {{
                background: {theme['status_bg']};
                color: {theme['status_fg']};
                border-top: 1px solid {theme['group_border']};
                padding: 4px;
            }}
            QLabel {{
                color: {theme['fg']};
            }}
            QScrollArea {{
                background: {theme['bg']};
                border: none;
            }}
            QProgressBar {{
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                text-align: center;
                background: {theme['entry_bg']};
                color: {theme['fg']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {theme['accent']};
                border-radius: 6px;
            }}
        """)
        
        # Apply theme to section buttons
        for btn in self.section_buttons.values():
            btn.apply_style(theme)
        
        # Apply theme to current section content
        self.apply_theme_to_section()

    def get_dialog_style(self):
        theme = self.current_theme
        return f"""
            QDialog {{
                background: {theme['bg']};
                color: {theme['fg']};
            }}
            QTextEdit {{
                background: {theme['entry_bg']};
                color: {theme['entry_fg']};
                border: 2px solid {theme['entry_border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton {{
                background: {theme['button_bg']};
                color: {theme['button_fg']};
                border: 2px solid {theme['group_border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                margin: 5px;
            }}
            QPushButton:hover {{
                background: {theme['button_hover']};
                border-color: {theme['accent']};
            }}
        """

    def closeEvent(self, event):
        # Save window geometry
        geom = self.geometry()
        self.config["window_geometry"] = f"{geom.width()}x{geom.height()}+{geom.x()}+{geom.y()}"
        save_config(self.config)
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_AUTHOR)
    
    # Set application icon if available
    try:
        app.setWindowIcon(QIcon("weather_icon.png"))
    except:
        pass
    
    # Create and show main window
    window = WeatherToolkit()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
