#!/usr/bin/env python3
"""
Enhanced Colorado Severe Weather Outlook Net Controller
A comprehensive tool for managing the daily Colorado SWO Net

Features:
- Improved UI/UX with better organization
- Enhanced error handling and validation
- Better weather data integration
- Real-time clock and automatic time zone handling
- Improved script generation and navigation
- Better settings management
- Enhanced export capabilities

pip install PyQt6 PyQt6-WebEngine requests beautifulsoup4 pillow
"""

import sys
import os
import json
import logging
import requests
import time
import webbrowser

from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QSpinBox, QGroupBox, QScrollArea,
    QProgressBar, QListWidget, QSplitter, QCompleter, QFontDialog, QTabWidget,
    QGridLayout, QFrame, QSizePolicy, QToolTip, QCheckBox, QComboBox, QSlider,
    QStatusBar, QMenuBar, QMenu, QToolBar, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QSettings, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve,
    QThread, QObject, QSize, QDateTime, QTimeZone, QUrl
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QAction as QGuiAction,
    QKeySequence, QTextCharFormat, QTextCursor, QAction
)

from io import BytesIO

try:
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET
    from PIL import Image, ImageQt
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    WEBENGINE_AVAILABLE = True
except ImportError as e:
    print(f"WebEngine not available: {e}")
    WEBENGINE_AVAILABLE = False
    try:
        from bs4 import BeautifulSoup
        import xml.etree.ElementTree as ET
        from PIL import Image, ImageQt
    except Exception as e:
        print(f"Import error: {e.__class__.__name__}: {e}")
        sys.exit(1)

# Configuration Constants
class Config:
    APP_NAME = "Colorado Severe Weather Outlook Net Controller"
    ORGANIZATION = "SKYHUBLINK"
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


    # Default values with better environment variable handling
    DEFAULT_CALLSIGN = os.environ.get('NET_CONTROL_CALLSIGN', 'NC2WX')
    DEFAULT_NAME = os.environ.get('NET_CONTROL_NAME', 'Gary')
    DEFAULT_LOCATION = os.environ.get('NET_CONTROL_LOCATION', 'Pueblo West in Southestern Colorado')
    DEFAULT_LOGGER = os.environ.get('LOGGER_CALLSIGN', 'N0CALL')
    DEFAULT_LOGGER_NAME = os.environ.get('LOGGER_NAME', 'LOGGER')

    # Time zones
    MST_OFFSET = -7  # Mountain Standard Time
    MDT_OFFSET = -6  # Mountain Daylight Time

    # Net schedule
    NET_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    NET_TIME = "13:00"  # 1:00 PM

    # File paths
    CONFIG_DIR = Path.home() / '.colorado_swo'
    LOG_FILE = CONFIG_DIR / 'swo_net.log'
    CONFIG_FILE = CONFIG_DIR / 'weather_toolkit_config.json'
    ERROR_LOG = CONFIG_DIR / 'weather_toolkit_error.log'


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
        "Skywarn Spotter Checklist": "https://www.weather.gov/images/gjt/spotter/Reporting_Checklist.png",
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

# NWS Weather Forecast Offices serving Colorado
NWS_OFFICES = {
    "Grand Junction": {
        "code": "GJT",
        "areas": "Western Colorado",
        "url": "https://weather.gov/gjt",
        "phone": "970-243-7007"
    },
    "Denver/Boulder": {
        "code": "BOU",
        "areas": "Eastern Colorado, Metro Denver",
        "url": "https://weather.gov/bou",
        "phone": "303-494-4221"
    },
    "Goodland": {
        "code": "GLD",
        "areas": "Eastern Colorado",
        "url": "https://weather.gov/gld",
        "phone": "307-857-3964"
    },
    "Pueblo": {
        "code": "PUB",
        "areas": "Southern Colorado",
        "url": "https://weather.gov/pub",
        "phone": "719-948-9429"
    },
    "Cheyenne": {
        "code": "CYS",
        "areas": "Northeastern Colorado (Courtesy)",
        "url": "https://weather.gov/cys",
        "phone": "307-772-2468"
    }
}

DEFAULT_SWO_ANNOUNCEMENTS = [
    "Weather conditions across Colorado are generally quiet today.",
    "All NWS Weather Forecast Offices report no immediate severe weather threats.",
    "Reminder: Colorado Severe Weather Outlook Net operates Monday through Friday at 1:00 PM MST/MDT.",
    "For current weather information, visit weather.gov or your local NWS office.",
    "No new severe weather outlook announcements at this time."
]

# Utility Functions
def setup_logging():
    """Setup application logging"""
    Config.CONFIG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

def get_lines_from_file(file_path: Path) -> List[str]:
    """Safely read lines from a file with better error handling"""
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            return [line for line in lines if line]
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
    except PermissionError:
        logging.error(f"Permission denied reading: {file_path}")
    except UnicodeDecodeError:
        logging.error(f"Unicode decode error reading: {file_path}")
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
    return []

def get_current_mountain_time() -> Dict[str, str]:
    """Get current Mountain Time with proper DST handling"""
    now = datetime.now()

    # Simple DST check (second Sunday in March to first Sunday in November)
    # This is a basic implementation - for production use pytz or zoneinfo
    year = now.year
    dst_start = datetime(year, 3, 8)  # Approximate
    dst_end = datetime(year, 11, 1)   # Approximate

    is_dst = dst_start <= now <= dst_end

    if is_dst:
        tz = timezone(timedelta(hours=Config.MDT_OFFSET))
        tz_name = "MDT"
    else:
        tz = timezone(timedelta(hours=Config.MST_OFFSET))
        tz_name = "MST"

    mt_time = now.astimezone(tz)

    return {
        'time': mt_time.strftime("%I:%M %p"),
        'timezone': tz_name,
        'full': f"{mt_time.strftime('%I:%M %p')} {tz_name}",
        'date': mt_time.strftime("%A, %B %d, %Y"),
        'day': mt_time.strftime("%A"),
        'datetime': mt_time
    }

def is_net_day() -> bool:
    """Check if today is a net day"""
    return get_current_mountain_time()['day'] in Config.NET_DAYS



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



class SpotterImagePopup(QDialog):
    def __init__(self, parent, url, theme, font_size):
        super().__init__(parent)
        self.setWindowTitle("📋 Skywarn Spotter Checklist")

        # Don't set a fixed minimum size - let it size to content
        # self.setMinimumSize(800, 1200)  # Remove this line

        QTimer.singleShot(50, lambda: self.move(50, 50))


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

        self.status = QLabel("🔄 Loading spotter checklist...")
        layout.addWidget(self.status)

        # Create scroll area for the image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"border: 2px solid {theme['group_border']}; border-radius: 8px;")
        self.img_label.setScaledContents(False)  # Don't force scaling

        scroll_area.setWidget(self.img_label)
        layout.addWidget(scroll_area, 1)

        btn_close = QPushButton("❌ Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self.setLayout(layout)
        QTimer.singleShot(100, lambda: self.load_spotter_image(url))

    def load_spotter_image(self, url):
        try:
            resp = requests.get(url, timeout=15)
            img = Image.open(BytesIO(resp.content))
            qt_img = ImageQt.ImageQt(img)
            pix = QPixmap.fromImage(qt_img)

            # Get the original image size
            original_size = pix.size()

            # Set the pixmap at original size (no scaling)
            self.img_label.setPixmap(pix)

            # Resize the dialog to fit the image plus some padding for UI elements
            # But limit it to reasonable screen dimensions
            max_width = 1000   # Adjust as needed
            max_height = 800   # Adjust as needed

            dialog_width = min(original_size.width() + 50, max_width)
            dialog_height = min(original_size.height() + 150, max_height)  # Extra for status and button

            self.resize(dialog_width, dialog_height)

            QTimer.singleShot(50, lambda: self.move(50, 50))

            self.status.setText("✅ Spotter checklist loaded successfully")
        except Exception as e:
            log_error(f"Image load error: {e}")
            self.status.setText("❌ Failed to load spotter checklist image")

class WebViewPopup(QDialog):
    def __init__(self, parent, url, title, theme, font_size):
        super().__init__(parent)
        self.setWindowTitle(f"🌐 {title}")
        self.setMinimumSize(1200, 800)

        self.setStyleSheet(f"""
            QDialog {{
                background: {theme['bg']};
                color: {theme['fg']};
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
            QLabel {{
                color: {theme['accent']};
                font-weight: 600;
                padding: 5px;
            }}
        """)

        layout = QVBoxLayout()

        # Status and controls
        controls = QHBoxLayout()
        self.status = QLabel(f"🔄 Loading {title}...")
        controls.addWidget(self.status)

        # Navigation buttons
        btn_back = QPushButton("⬅️ Back")
        btn_forward = QPushButton("➡️ Forward")
        btn_refresh = QPushButton("🔄 Refresh")
        btn_external = QPushButton("🌐 Open External")
        btn_close = QPushButton("❌ Close")

        controls.addStretch()
        controls.addWidget(btn_back)
        controls.addWidget(btn_forward)
        controls.addWidget(btn_refresh)
        controls.addWidget(btn_external)
        controls.addWidget(btn_close)

        layout.addLayout(controls)

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(url))

        # Configure web engine settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # Connect signals
        self.web_view.loadStarted.connect(lambda: self.status.setText("🔄 Loading..."))
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.loadProgress.connect(self.on_load_progress)

        # Button connections
        btn_back.clicked.connect(self.web_view.back)
        btn_forward.clicked.connect(self.web_view.forward)
        btn_refresh.clicked.connect(self.web_view.reload)
        btn_external.clicked.connect(lambda: webbrowser.open(url))
        btn_close.clicked.connect(self.close)

        layout.addWidget(self.web_view, 1)
        self.setLayout(layout)

        # Store original URL for external button
        self.original_url = url

    def on_load_finished(self, success):
        if success:
            self.status.setText("✅ Page loaded successfully")
        else:
            self.status.setText("❌ Failed to load page")

    def on_load_progress(self, progress):
        self.status.setText(f"🔄 Loading... {progress}%")


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

class WeatherToolkitWidget(QWidget):
    """
    A reusable weather toolkit widget that can be embedded into other applications.

    Usage:
        widget = WeatherToolkitWidget()
        widget.set_resources(your_resources_dict)
        widget.set_theme(your_theme_dict)
        layout.addWidget(widget)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resources = resources  # Default placeholder
        self.theme = themes["default"]  # Default theme
        self.font_size = 12
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 5  # minutes

        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.refresh_alerts)

        self.setup_ui()
        self.apply_theme()

        # Start auto-refresh if enabled
        if self.auto_refresh_enabled:
            self.alert_timer.start(self.auto_refresh_interval * 60000)

    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)

        # Header
        header = QLabel("🌪️ Weather Toolkit")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(header)

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
        sections_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        left_layout.addWidget(sections_label)

        # Section buttons container
        self.section_buttons_container = QWidget()
        self.section_buttons_layout = QVBoxLayout(self.section_buttons_container)
        left_layout.addWidget(self.section_buttons_container)

        # Quick alerts button
        self.alerts_btn = ModernButton("🚨 Active Alerts")
        self.alerts_btn.clicked.connect(self.show_alerts)
        left_layout.addWidget(self.alerts_btn)

        left_layout.addStretch()
        left_panel.setMaximumWidth(300)

        # Right panel - links
        self.right_panel = QScrollArea()
        self.right_panel.setWidgetResizable(True)
        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_panel.setWidget(self.right_content)

        # Welcome message
        self.welcome_label = QLabel("👈 Select a weather resource category to begin")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 14px; padding: 30px; color: #888;")
        self.right_layout.addWidget(self.welcome_label)
        self.right_layout.addStretch()

        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(self.right_panel)
        content_splitter.setSizes([300, 700])

        main_layout.addWidget(content_splitter)

        # Initialize section buttons
        self.section_buttons = {}
        self.create_section_buttons()

    def create_section_buttons(self):
        """Create buttons for each resource section"""
        # Clear existing buttons
        for button in self.section_buttons.values():
            button.setParent(None)
        self.section_buttons.clear()

        # Create new buttons
        for section_name in self.resources.keys():
            btn = ModernButton(section_name)
            btn.clicked.connect(lambda checked, name=section_name: self.load_section(name))
            self.section_buttons[section_name] = btn
            self.section_buttons_layout.addWidget(btn)
            btn.apply_style(self.theme)

    def load_section(self, section_name):
        """Load a specific resource section"""
        # Clear right panel
        for i in reversed(range(self.right_layout.count())):
            child = self.right_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if section_name not in self.resources:
            return

        # Section header
        header = QLabel(f"{section_name}")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        self.right_layout.addWidget(header)

        # Create link buttons
        links = self.resources[section_name]
        for link_name, url in links.items():
            link_group = ModernGroupBox(link_name)
            link_layout = QVBoxLayout()

            # Button layout
            btn_layout = QHBoxLayout()

            # View button (for text content)
            if any(x in url for x in ["HWO", "AFD", "product.php"]):
                view_btn = ModernButton("📄 View Text")
                view_btn.clicked.connect(lambda checked, u=url, n=link_name: self.show_text_popup(u, n))
                view_btn.apply_style(self.theme)
                btn_layout.addWidget(view_btn)

            # Open in browser button
            open_btn = ModernButton("🌐 Open in Browser")
            open_btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            open_btn.apply_style(self.theme)
            btn_layout.addWidget(open_btn)

            link_layout.addLayout(btn_layout)

            # URL display
            url_label = QLabel(f"🔗 {url}")
            url_label.setStyleSheet("font-size: 10px; padding: 5px; font-family: monospace;")
            url_label.setWordWrap(True)
            link_layout.addWidget(url_label)

            link_group.setLayout(link_layout)
            link_group.apply_style(self.theme)
            self.right_layout.addWidget(link_group)

        self.right_layout.addStretch()

    def show_text_popup(self, url, title, typ, parse_pre=False):
        popup = Toplevel(self.root)
        popup.title(f"{typ} Viewer - {title}")
        popup.geometry("1000x650")
        popup.configure(bg=self.theme["bg"])
        popup.resizable(True, True)
        content_var = tk.StringVar()
        self.status(f"Loading {typ} for {title}...")
        # Status label
        stat_label = Label(popup, text=f"Loading {typ}...",
                           bg=self.theme["bg"], fg=self.theme["accent"],
                           font=("TkDefaultFont", self.font_size))
        stat_label.pack(pady=5)
        # Text area
        text_area = Text(popup, wrap="word", bg=self.theme["bg"], fg=self.theme["fg"],
                         font=("TkDefaultFont", self.font_size))
        text_area.pack(expand=True, fill=BOTH, padx=10, pady=10)
        text_area.config(state="disabled")
        # Bottom controls
        ctrl = Frame(popup, bg=self.theme["bg"])
        ctrl.pack(fill=tk.X)
        Button(ctrl, text="Copy All", command=lambda: self.copy_to_clipboard(text_area.get(1.0, END)),
               bg=self.theme["button_bg"], fg=self.theme["button_fg"]).pack(side=LEFT, padx=5)
        Button(ctrl, text="Save As...", command=lambda: self.save_text_to_file(text_area.get(1.0, END)),
               bg=self.theme["button_bg"], fg=self.theme["button_fg"]).pack(side=LEFT, padx=5)
        Button(ctrl, text="Close (Esc)", command=popup.destroy,
               bg=self.theme["button_bg"], fg=self.theme["button_fg"]).pack(side=RIGHT, padx=5)
        self._popup_bindings(popup, text_area)
        # Context menu
        self._add_context_menu(text_area)
        # Fetch in thread
        def fetch_content():
            try:
                response = requests.get(url, timeout=10)
                if parse_pre:
                    soup = BeautifulSoup(response.content, "html.parser")
                    pre = soup.find("pre")
                    text = pre.text if pre else f"{typ} content not found."
                else:
                    text = response.text
            except Exception as e:
                text = f"Failed to retrieve {typ}:\n{e}"
                log_error(text)
            def update_gui():
                stat_label.config(text=f"{typ} loaded.")
                text_area.config(state="normal")
                text_area.delete(1.0, END)
                text_area.insert(END, text)
                text_area.config(state="disabled")
                self.status(f"{typ} loaded.")
            self.root.after(0, update_gui)
        threading.Thread(target=fetch_content, daemon=True).start()

    # def show_text_popup(self, url, title):
    #     """Show a text popup dialog"""
    #     popup = TextPopup(self, url, title, "NWS Text Product", self.theme, self.font_size, True)
    #     popup.exec()
    #
    # def show_alerts(self):
    #     """Show active weather alerts"""
    #     self.progress_bar.setVisible(True)
    #     self.progress_bar.setValue(0)
    #
    #     # Default URL - can be customized
    #     alerts_url = "https://alerts.weather.gov/cap/co.php?x=0"
    #
    #     self.fetcher = AlertFetcher(alerts_url)
    #     self.fetcher.alerts_loaded.connect(self.display_alerts)
    #     self.fetcher.progress_updated.connect(self.progress_bar.setValue)
    #     self.fetcher.start()
    #
    # def display_alerts(self, alert_text):
    #     """Display fetched alerts in a dialog"""
    #     self.progress_bar.setVisible(False)
    #
    #     popup = QDialog(self)
    #     popup.setWindowTitle("🚨 Active Weather Alerts")
    #     popup.setMinimumSize(800, 600)
    #
    #     layout = QVBoxLayout()
    #
    #     text_area = QTextEdit()
    #     text_area.setPlainText(alert_text)
    #     text_area.setReadOnly(True)
    #     text_area.setFont(QFont("Consolas", self.font_size))
    #     layout.addWidget(text_area)
    #
    #     close_btn = QPushButton("❌ Close")
    #     close_btn.clicked.connect(popup.close)
    #     layout.addWidget(close_btn)
    #
    #     popup.setLayout(layout)
    #     popup.setStyleSheet(self.get_dialog_style())
    #     popup.exec()
    #
    # def refresh_alerts(self):
    #     """Refresh alerts (placeholder - can be customized)"""
    #     print("Refreshing alerts...")

    def fetch_colorado_alerts(self):
        url = "https://alerts.weather.gov/cap/co.php?x=0"
        self._fetch_alerts(url, "Active Colorado Alerts")

    def fetch_area_alerts(self):
        url = "https://www.weather.gov/wwamap/wwatxtget.php?cwa=pub&wwa=all"
        self._fetch_alerts(url, "Active Area Alerts")

    def open_nws_report(self):
        webbrowser.open("https://inws.ncep.noaa.gov/report/")

    def submit_resource(self):
        mailto_link = (
            "mailto:Jon.W5ALC@gmail.com"
            "?subject=Colorado%20SWN%20toolkit%20Resource%20Suggestion"
            "&body=Suggest%20a%20new%20resource%20or%20link%20here:%0A%0A"
            "Name%20of%20Resource:%0AURL:%0ADescription%20(optional):"
        )
        self.launch_item(mailto_link)

    def fetch_us_alerts(self):
        url = "https://api.weather.gov/alerts/active.atom"
        self._fetch_alerts(url, "Active US Alerts")

    def _fetch_alerts(self, url, window_title):
        """
        Fetch and display weather alerts in a popup window with search/filter functionality
        """
        theme = self.theme
        font_size = self.font_size

        # Create popup dialog
        popup = QDialog(self)
        popup.setWindowTitle(window_title)
        popup.resize(950, 700)
        popup.setStyleSheet(f"""
            QDialog {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
            }}
            QLabel {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
                font-size: {font_size}px;
            }}
            QLineEdit {{
                background-color: {theme["entry_bg"]};
                color: {theme["entry_fg"]};
                border: 1px solid #666;
                padding: 6px;
                font-size: {font_size}px;
            }}
            QPushButton {{
                background-color: {theme["button_bg"]};
                color: {theme["button_fg"]};
                border: 1px solid #666;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: {theme.get("button_hover", theme["button_bg"])};
                border-color: {theme.get("accent", "#00d4ff")};
            }}
            QTextEdit {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
                border: 1px solid #666;
                font-size: {font_size}px;
                padding: 8px;
            }}
        """)

        # Main layout
        layout = QVBoxLayout(popup)

        # Hint label
        hint = QLabel("Tip: Search for specific keywords.")
        hint.setStyleSheet(f"color: {theme['accent']};")
        layout.addWidget(hint)

        # Search frame
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_label = QLabel("Filter alerts: ")
        search_layout.addWidget(search_label)

        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Type to filter alerts...")
        search_layout.addWidget(search_entry)

        refresh_btn = QPushButton("Refresh Now")
        search_layout.addWidget(refresh_btn)

        search_layout.addStretch()
        layout.addWidget(search_frame)

        # Status label
        stat_label = QLabel("Loading alerts...")
        stat_label.setStyleSheet(f"color: {theme['accent']};")
        layout.addWidget(stat_label)

        # Text area
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setWordWrapMode(QTextEdit.WrapMode.WordWrap)
        layout.addWidget(text_area)

        # Add context menu (assuming this method exists)
        if hasattr(self, '_add_context_menu'):
            self._add_context_menu(text_area)

        # Bottom controls
        ctrl_frame = QFrame()
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)

        copy_btn = QPushButton("Copy All")
        ctrl_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save As...")
        ctrl_layout.addWidget(save_btn)

        ctrl_layout.addStretch()

        close_btn = QPushButton("Close (Esc)")
        ctrl_layout.addWidget(close_btn)

        layout.addWidget(ctrl_frame)

        # Internal state
        entries = []  # Stores the fetched XML entries
        last_update = ""

        # Setup text formats for different alert types
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(theme["warning"]))
        warning_format.setFontWeight(QFont.Weight.Bold)

        watch_format = QTextCharFormat()
        watch_format.setForeground(QColor(theme["watch"]))

        advisory_format = QTextCharFormat()
        advisory_format.setForeground(QColor(theme["advisory"]))

        statement_format = QTextCharFormat()
        statement_format.setForeground(QColor(theme["advisory"]))

        county_format = QTextCharFormat()
        county_format.setForeground(QColor(theme["county"]))
        county_format.setFontWeight(QFont.Weight.Bold)

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#204060"))
        highlight_format.setForeground(QColor("yellow"))

        link_format = QTextCharFormat()
        link_format.setForeground(QColor("blue"))
        link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        # Create fetcher thread
        fetcher = None

        def load_alerts():
            """Load alerts from the server"""
            nonlocal fetcher, entries, last_update

            stat_label.setText("Loading alerts...")
            if hasattr(self, 'status'):
                self.status("Loading alerts...")

            # Stop any existing fetcher
            if fetcher and fetcher.isRunning():
                fetcher.quit()
                fetcher.wait()

            # Create new fetcher
            fetcher = AlertFetcher(url, popup)
            fetcher.alerts_fetched.connect(on_alerts_fetched)
            fetcher.fetch_error.connect(on_fetch_error)
            fetcher.start()

        def on_alerts_fetched(new_entries, timestamp):
            """Handle successfully fetched alerts"""
            nonlocal entries, last_update
            entries = new_entries
            last_update = timestamp
            apply_filter()

        def on_fetch_error(error_msg):
            """Handle fetch errors"""
            nonlocal entries, last_update
            entries = []
            last_update = ""
            if hasattr(self, 'log_error'):
                self.log_error(f"Error fetching alerts: {error_msg}")
            stat_label.setText(f"Error loading alerts: {error_msg}")
            apply_filter()

        def apply_filter():
            """Apply search filter to the loaded alerts"""
            search_term = search_entry.text().lower()

            # Clear text area
            text_area.clear()

            # Group alerts by county
            grouped_alerts = {}

            for entry in entries:
                # Extract data from XML
                title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                area_elem = entry.find("{urn:oasis:names:tc:emergency:cap:1.1}areaDesc")

                # Get text content
                title = title_elem.text if title_elem is not None else ""
                summary = summary_elem.text if summary_elem is not None else ""
                link = link_elem.attrib.get("href", "") if link_elem is not None else ""

                # Get counties
                if area_elem is not None and area_elem.text:
                    counties = [c.strip() for c in area_elem.text.split(';')]
                else:
                    counties = ["Active NWS Alerts"]

                # Filter by search term
                if not search_term or search_term in title.lower() or search_term in summary.lower():
                    for county in counties:
                        if county not in grouped_alerts:
                            grouped_alerts[county] = []
                        grouped_alerts[county].append((title, summary, link))

            # Display grouped alerts
            cursor = text_area.textCursor()
            links = {}  # Store link positions for click handling

            for county, alerts in grouped_alerts.items():
                # County header
                cursor.insertText(f"=== {county} ===\n", county_format)

                for title, summary, link in alerts:
                    # Determine alert type and format
                    title_lower = title.lower()
                    if "warning" in title_lower:
                        alert_format = warning_format
                    elif "watch" in title_lower:
                        alert_format = watch_format
                    elif "advisory" in title_lower:
                        alert_format = advisory_format
                    elif "statement" in title_lower:
                        alert_format = statement_format
                    else:
                        alert_format = QTextCharFormat()

                    # Insert title
                    title_start = cursor.position()
                    cursor.insertText(f"Title: {title}\n", alert_format)

                    # Highlight search term in title
                    if search_term and search_term in title.lower():
                        highlight_search_term(title_start + 7, title, search_term)  # 7 = len("Title: ")

                    # Insert summary
                    summary_start = cursor.position()
                    cursor.insertText(f"Summary: {summary}\n")

                    # Highlight search term in summary
                    if search_term and search_term in summary.lower():
                        highlight_search_term(summary_start + 9, summary, search_term)  # 9 = len("Summary: ")

                    # Insert link
                    if link:
                        link_start = cursor.position()
                        cursor.insertText(f"Link: {link}\n\n")

                        # Store link for click handling
                        links[link_start] = link

                        # Apply link formatting
                        link_cursor = QTextCursor(text_area.document())
                        link_cursor.setPosition(link_start)
                        link_cursor.setPosition(cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                        link_cursor.mergeCharFormat(link_format)
                    else:
                        cursor.insertText("\n")

            # Update status
            if entries:
                stat_label.setText(f"Alerts loaded. Last update: {last_update}")
                if hasattr(self, 'status'):
                    self.status(f"{window_title} loaded at {last_update}")
            else:
                stat_label.setText("No alerts found" + (f" for '{search_entry.text()}'" if search_entry.text() else ""))

            # Store links for click handling
            text_area.setProperty("alert_links", links)

        def highlight_search_term(start_pos, text, search_term):
            """Highlight search term in text"""
            text_lower = text.lower()
            term_lower = search_term.lower()

            pos = 0
            while True:
                pos = text_lower.find(term_lower, pos)
                if pos == -1:
                    break

                # Create cursor for highlighting
                highlight_cursor = QTextCursor(text_area.document())
                highlight_cursor.setPosition(start_pos + pos)
                highlight_cursor.setPosition(start_pos + pos + len(search_term), QTextCursor.MoveMode.KeepAnchor)
                highlight_cursor.mergeCharFormat(highlight_format)

                pos += len(search_term)

        def handle_text_click(event):
            """Handle mouse clicks on text area (for links)"""
            cursor = text_area.cursorForPosition(event.position().toPoint())
            pos = cursor.position()

            # Get stored links
            links = text_area.property("alert_links")
            if not links:
                return

            # Find clicked link
            for link_pos, url in links.items():
                # Check if click is within link range (approximate)
                if abs(pos - link_pos) < 100:  # Adjust range as needed
                    QDesktopServices.openUrl(QUrl(url))
                    break

        # Override mouse press event for link clicking
        original_mouse_press = text_area.mousePressEvent
        text_area.mousePressEvent = lambda event: (
            handle_text_click(event) if event.button() == Qt.MouseButton.LeftButton else None,
            original_mouse_press(event)
        )[1]

        # Connect signals
        refresh_btn.clicked.connect(load_alerts)
        search_entry.textChanged.connect(apply_filter)
        search_entry.returnPressed.connect(apply_filter)

        # Button actions
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(text_area.toPlainText()) if hasattr(self, 'copy_to_clipboard') else None)
        save_btn.clicked.connect(lambda: self.save_text_to_file(text_area.toPlainText()) if hasattr(self, 'save_text_to_file') else None)
        close_btn.clicked.connect(popup.close)

        # Keyboard shortcuts
        def handle_key_press(event):
            if event.key() == Qt.Key.Key_Escape:
                popup.close()
            else:
                QDialog.keyPressEvent(popup, event)

        popup.keyPressEvent = handle_key_press

        # Set focus to search entry
        search_entry.setFocus()

        # Auto-refresh timer
        if hasattr(self, 'auto_refresh_mins'):
            refresh_timer = QTimer()
            refresh_timer.timeout.connect(load_alerts)
            refresh_timer.start(self.auto_refresh_mins * 60000)

        # Initial load
        load_alerts()

        if hasattr(self, 'status'):
            self.status(f"{window_title} opened.")

        # Show popup
        popup.exec()

    def apply_theme(self):
        """Apply the current theme to the widget"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {self.theme.get('bg', '#2d2d2d')};
                color: {self.theme.get('fg', '#ffffff')};
                font-size: {self.font_size}px;
            }}
            QLabel {{
                color: {self.theme.get('fg', '#ffffff')};
            }}
            QScrollArea {{
                background: {self.theme.get('bg', '#2d2d2d')};
                border: none;
            }}
            QProgressBar {{
                border: 2px solid {self.theme.get('group_border', '#404040')};
                border-radius: 8px;
                text-align: center;
                background: {self.theme.get('bg', '#2d2d2d')};
                color: {self.theme.get('fg', '#ffffff')};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {self.theme.get('accent', '#00d4ff')};
                border-radius: 6px;
            }}
        """)

        # Apply theme to buttons
        for btn in self.section_buttons.values():
            btn.apply_style(self.theme)

        if hasattr(self, 'alerts_btn'):
            self.alerts_btn.apply_style(self.theme)

    def get_dialog_style(self):
        """Get stylesheet for dialogs"""
        return f"""
            QDialog {{
                background: {self.theme.get('bg', '#2d2d2d')};
                color: {self.theme.get('fg', '#ffffff')};
            }}
            QTextEdit {{
                background: {self.theme.get('bg', '#2d2d2d')};
                color: {self.theme.get('fg', '#ffffff')};
                border: 2px solid {self.theme.get('group_border', '#404040')};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton {{
                background: {self.theme.get('button_bg', '#3a3a3a')};
                color: {self.theme.get('fg', '#ffffff')};
                border: 2px solid {self.theme.get('group_border', '#404040')};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                margin: 5px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('button_hover', '#4a4a4a')};
                border-color: {self.theme.get('accent', '#00d4ff')};
            }}
        """

    # Public API methods for customization
    def set_resources(self, resources_dict):
        """Set the resources dictionary and update the UI"""
        self.resources = resources_dict
        self.create_section_buttons()

    def set_theme(self, theme_dict):
        """Set the theme dictionary and apply it"""
        self.theme = theme_dict
        self.apply_theme()

    def set_font_size(self, size):
        """Set the font size"""
        self.font_size = size
        self.apply_theme()

    def set_auto_refresh(self, enabled, interval_minutes=5):
        """Enable/disable auto-refresh of alerts"""
        self.auto_refresh_enabled = enabled
        self.auto_refresh_interval = interval_minutes

        self.alert_timer.stop()
        if enabled:
            self.alert_timer.start(interval_minutes * 60000)

    def set_alerts_url(self, url):
        """Set custom alerts URL (modify show_alerts method to use this)"""
        self.alerts_url = url

class NetData:
    """Data class for net information"""
    def __init__(self):
        self.callsign = ""
        self.name = ""
        self.location = ""
        self.logger_callsign = ""
        self.logger_name = ""
        self.weather_announcements = DEFAULT_SWO_ANNOUNCEMENTS.copy()
        self.special_announcements = []
        self.check_ins = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'callsign': self.callsign,
            'name': self.name,
            'location': self.location,
            'logger_callsign': self.logger_callsign,
            'logger_name': self.logger_name,
            'weather_announcements': self.weather_announcements,
            'special_announcements': self.special_announcements,
            'check_ins': self.check_ins
        }

    def from_dict(self, data: Dict[str, Any]):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class TimeWidget(QLabel):
    """Real-time clock widget"""
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        self.update_time()

    def update_time(self):
        time_info = get_current_mountain_time()
        self.setText(f"{time_info['full']} • {time_info['date']}")

        # Change color if it's net time
        if time_info['datetime'].strftime("%H:%M") == Config.NET_TIME and is_net_day():
            self.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #fff3cd;")
        else:
            self.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

class AnimatedButton(QPushButton):
    """Custom button with hover animations"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self.setStyleSheet(self.styleSheet() + "background-color: #4a90e2;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("background-color: #4a90e2;", ""))
        super().leaveEvent(event)

class StatusBar(QFrame):
    """Enhanced status bar with icons and animations"""
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMaximumHeight(35)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_icon = QLabel("")
        self.status_icon.setFixedWidth(20)

        self.status_label = QLabel("Ready")

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumWidth(200)

        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def show_message(self, message: str, error: bool = False, progress: bool = False):
        """Show a status message with optional progress bar"""
        self.status_label.setText(message)

        if error:
            self.setStyleSheet("background-color: #ffebee; color: #c62828; border: 1px solid #ef5350;")
            self.status_icon.setText("⚠️")
        else:
            self.setStyleSheet("background-color: #e8f5e8; color: #2e7d32; border: 1px solid #66bb6a;")
            self.status_icon.setText("✅")

        self.progress.setVisible(progress)

        if not progress:
            QTimer.singleShot(5000, self.clear_message)

    def set_progress(self, value: int, maximum: int = 100):
        """Update progress bar"""
        self.progress.setVisible(True)
        self.progress.setMaximum(maximum)
        self.progress.setValue(value)

    def clear_message(self):
        """Clear the status message"""
        self.status_label.setText("Ready")
        self.status_icon.setText("")
        self.progress.setVisible(False)
        self.setStyleSheet("")

class WeatherDialog(QDialog):
    """Dialog for managing weather announcements"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weather Announcement Manager")
        self.setMinimumSize(600, 400)
        self.announcements = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Manage weather announcements for the net. You can load from a file, "
            "add custom announcements, or edit existing ones."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # File operations
        file_layout = QHBoxLayout()
        load_btn = QPushButton("📁 Load from File")
        load_btn.clicked.connect(self.load_from_file)
        save_btn = QPushButton("💾 Save to File")
        save_btn.clicked.connect(self.save_to_file)

        file_layout.addWidget(load_btn)
        file_layout.addWidget(save_btn)
        file_layout.addStretch()

        layout.addLayout(file_layout)

        # Announcement list
        self.announcement_list = QTextEdit()
        self.announcement_list.setPlaceholderText(
            "Enter weather announcements, one per line...\n\n"
            "Example:\n"
            "Current weather conditions across Colorado are stable.\n"
            "No severe weather threats reported by NWS offices.\n"
            "Temperature readings normal for this time of year."
        )
        layout.addWidget(self.announcement_list)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def load_from_file(self):
        """Load announcements from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Weather Announcements", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            announcements = get_lines_from_file(Path(file_path))
            if announcements:
                self.announcement_list.setPlainText('\n'.join(announcements))

    def save_to_file(self):
        """Save announcements to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Weather Announcements", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.announcement_list.toPlainText())
                QMessageBox.information(self, "Success", "Announcements saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def get_announcements(self) -> List[str]:
        """Get the list of announcements"""
        text = self.announcement_list.toPlainText().strip()
        if not text:
            return DEFAULT_SWO_ANNOUNCEMENTS.copy()
        return [line.strip() for line in text.split('\n') if line.strip()]

    def set_announcements(self, announcements: List[str]):
        """Set the announcements"""
        self.announcement_list.setPlainText('\n'.join(announcements))

class WeatherForecastTrimmer:

    def trim_afd(self, afd_text: str) -> str:
        if not afd_text or not afd_text.strip():
            return ""

        lines = afd_text.split('\n')
        start_idx = 0
        end_idx = len(lines)

        # Find where the actual discussion starts
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            if any(marker in line_upper for marker in [
                '.KEY MESSAGES', '.DISCUSSION', '.SYNOPSIS', '.SHORT TERM',
                '.LONG TERM', '.AVIATION', '.MARINE', '.FIRE WEATHER'
            ]):
                start_idx = i
                break

            if (line_stripped and
                not line_stripped.startswith(('000', '059', 'FXUS', 'AFDGJT', 'Area Forecast Discussion')) and
                not re.match(r'^[A-Z]{2}\d{3}', line_stripped) and
                not re.match(r'^\d{3} (AM|PM)', line_stripped) and
                not line_stripped.startswith('National Weather Service') and
                not re.match(r'^CO[Z\d].*UT[Z\d]', line_stripped) and
                len(line_stripped) > 10 and
                not line_stripped.startswith('&&')):
                start_idx = i
                break

        # Find where discussion ends
        for i in range(len(lines) - 1, start_idx, -1):
            line = lines[i].strip()
            if (line == '$' or
                line.startswith('&&') or
                re.match(r'^[A-Z]{2,4}$', line)):
                end_idx = i
                break
            if line and not any(marker in line for marker in ['$', '&&']):
                end_idx = i + 1
                break

        # Extract and clean
        trimmed_lines = lines[start_idx:end_idx]

        # Remove leading/trailing blank lines
        while trimmed_lines and not trimmed_lines[0].strip():
            trimmed_lines.pop(0)
        while trimmed_lines and not trimmed_lines[-1].strip():
            trimmed_lines.pop()

        return '\n'.join(trimmed_lines).strip()

    def trim_hwo(self, hwo_text: str) -> str:
        if not hwo_text or not hwo_text.strip():
            return ""

        lines = hwo_text.split('\n')
        start_idx = 0
        end_idx = len(lines)

        # Find where the actual outlook starts
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            if any(marker in line_upper for marker in [
                'THIS HAZARDOUS WEATHER OUTLOOK',
                'HAZARDOUS WEATHER OUTLOOK IS FOR',
                '.DAY ONE', '.DAYS TWO THROUGH SEVEN'
            ]):
                start_idx = i
                break

            if (line_stripped and
                not line_stripped.startswith(('547', 'FLUS45', 'HWOGJT', 'Hazardous Weather Outlook')) and
                not line_stripped.startswith('National Weather Service') and
                not re.match(r'^CO[Z\d].*UT[Z\d]', line_stripped) and
                not re.match(r'^\d{3} (AM|PM)', line_stripped) and
                len(line_stripped) > 15 and
                ('colorado' in line_upper or 'utah' in line_upper or 'day one' in line_upper or 'outlook' in line_upper)):
                start_idx = i
                break

        # Find where outlook ends
        for i in range(len(lines) - 1, start_idx, -1):
            line = lines[i].strip()
            if (line == '$' or
                line.startswith('&&') or
                'SPOTTER INFORMATION STATEMENT' in line.upper() or
                line.startswith('Spotter activation')):
                if 'SPOTTER' in line.upper():
                    end_idx = min(i + 2, len(lines))
                else:
                    end_idx = i
                break

            if line and not any(marker in line for marker in ['$', '&&']):
                end_idx = i + 1
                break

        trimmed_lines = lines[start_idx:end_idx]

        while trimmed_lines and not trimmed_lines[0].strip():
            trimmed_lines.pop(0)
        while trimmed_lines and not trimmed_lines[-1].strip():
            trimmed_lines.pop()

        return '\n'.join(trimmed_lines).strip()

    def trim_forecast_product(self, text: str, product_type: str) -> str:
        if not text or not text.strip():
            return ""

        if product_type == 'auto' or not product_type:
            text_upper = text.upper()
            if 'AREA FORECAST DISCUSSION' in text_upper:
                product_type = 'afd'
            elif 'HAZARDOUS WEATHER OUTLOOK' in text_upper:
                product_type = 'hwo'
            else:
                product_type = 'afd'

        if product_type.lower() == 'afd':
            return self.trim_afd(text)
        elif product_type.lower() == 'hwo':
            return self.trim_hwo(text)
        else:
            return self.trim_afd(text)

    def remove_text_between(self, text, start_marker, end_marker):
        escaped_start = re.escape(start_marker)
        escaped_end = re.escape(end_marker)

        pattern = f'{escaped_start}.*?{escaped_end}'

        result = re.sub(pattern, '', text, flags=re.DOTALL)

        result = re.sub(r'\n\s*\n', '\n\n', result)  # Replace multiple newlines with double newlines

        return result.strip()

    def remove_aviation_forecast(self, text):
        return self.remove_text_between(text, ".AVIATION", "&&")

    def remove_remainder_gjt_forecast(self, text):
        return self.remove_text_between(text, ".GJT WATCHES/WARNINGS/ADVISORIES..." , "TGJT")

    def remove_remainder_bou_forecast(self, text):
        return self.remove_text_between(text, ".BOU WATCHES/WARNINGS/ADVISORIES..." , "AVIATION")

    def remove_remainder_gld_forecast(self, text):
        return self.remove_text_between(text, ".GLD WATCHES/WARNINGS/ADVISORIES..." , "AVIATION")

    def remove_remainder_pub_forecast(self, text):
        return self.remove_text_between(text, ".PUB WATCHES/WARNINGS/ADVISORIES..." , "AVIATION")

    def remove_remainder_cys_forecast(self, text):
        return self.remove_text_between(text, ".CYS WATCHES/WARNINGS/ADVISORIES..." , "AVIATION")

class NWSTextFetcher:
    def __init__(self):
        self.base_url = "https://forecast.weather.gov/product.php"
        self.wfo_codes = {
            'grand_junction': 'GJT',
            'boulder': 'BOU',
            'goodland': 'GLD',
            'pueblo': 'PUB',
            'cheyenne': 'CYS'
        }
        self.session = requests.Session()
        # Set a user agent to be polite to the NWS servers
        self.session.headers.update({
            'User-Agent': 'Python NWS Text Fetcher - Educational Use'
        })

    def fetch_text_product(self, wfo: str, product_code: str) -> Optional[str]:
        try:
            params = {
                'issuedby': wfo.upper(),
                'product': product_code.upper(),
                'site': wfo.lower(),
                'format': 'txt'
            }

            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse HTML to extract just the text content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for the pre tag which contains the text product
            pre_tag = soup.find('pre')
            if pre_tag:
                return pre_tag.get_text()

            # Fallback: look for text in a div or other container
            text_div = soup.find('div', {'class': 'glossaryProduct'}) or soup.find('div', {'id': 'textproduct'})
            if text_div:
                return text_div.get_text()

            # Last resort: strip all HTML tags
            return self._strip_html_tags(response.text)

        except requests.RequestException as e:
            print(f"Error fetching {product_code} from {wfo}: {e}")
            return None

    def _strip_html_tags(self, html_text: str) -> str:
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_text)

        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    def fetch_afd(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'AFD')

    def fetch_hwo(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'HWO')

    def fetch_zfp(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'ZFP')

    def fetch_sps(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'SPS')

    def fetch_now(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'NOW')

    def fetch_rwr(self, wfo: str) -> Optional[str]:
        return self.fetch_text_product(wfo, 'RWR')

    def fetch_multiple_products(self, wfo: str, products: list,
                              delay: float = 1.0) -> Dict[str, Optional[str]]:
        results = {}

        for product in products:
            results[product] = self.fetch_text_product(wfo, product)
            if delay > 0:
                time.sleep(delay)

        return results

    def get_wfo_code(self, location_name: str) -> Optional[str]:
        return self.wfo_codes.get(location_name.lower())

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

class AlertFetcher(QObject):
    """Worker class for fetching alerts in background thread"""
    alerts_fetched = pyqtSignal(list, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def fetch_alerts(self):
        try:
            response = requests.get(self.url, timeout=12)
            root = ET.fromstring(response.content)
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            last_update = time.strftime("%Y-%m-%d %H:%M:%S")
            self.alerts_fetched.emit(entries, last_update)
        except Exception as e:
            self.error_occurred.emit(str(e))

class SevereWeatherWindow(QWidget):
    """Main application window with enhanced features"""
    APP_NAME = "Colorado Severe Weather Outlook Net Controller"
    config = {
        "theme": "dark",
        "font_size": 12,
        "auto_refresh_mins": 5,
        "window_geometry": "1400x1000+50+50",
        "default_section": "",
        "compact_mode": False,
        "show_tooltips": True,
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Application state
        self.net_data = NetData()
        self.sections = []
        self.section_idx = 0
        self.settings = QSettings(Config.ORGANIZATION, "NetApp")
        self.theme_dark = True
        self.auto_advance = False
        self.auto_advance_delay = 30  # seconds

        # Setup logging
        setup_logging()
        logging.info("Application started")

        self.init_ui()
        self.load_settings()
        self.apply_theme()

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)  # Auto-save every minute

        if hasattr(self, 'config') and 'theme' in self.config:
            self.current_theme = themes[self.config["theme"]]
        else:
            # Default fallback
            self.current_theme = themes.get("light", {})

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with real-time clock
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Initialize tabs
        self.init_setup_tab()
        self.init_script_tab()
        self.init_weather_tab()
        self.init_toolkit_tab()
        self.init_settings_tab()

        main_layout.addWidget(self.tab_widget)

        # Enhanced status bar
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

        # Keyboard shortcuts
        self.setup_shortcuts()

    def create_header(self):
        """Create the application header with real-time clock"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.StyledPanel)
        header.setMaximumHeight(90)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        # Logo/Icon
        logo = QLabel("⛈️")
        logo.setStyleSheet("font-size: 56px;")

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Colorado Severe Weather Outlook Net")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")

        subtitle = QLabel("Daily Weather Net • SkyHubLink System • Advanced Controller v3.0")
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; font-style: italic;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        # Time display
        self.time_widget = TimeWidget()

        # Net status indicator
        self.net_status = QLabel()
        self.update_net_status()

        layout.addWidget(logo)
        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addWidget(self.time_widget)
        layout.addWidget(self.net_status)

        header.setLayout(layout)
        return header

    def update_net_status(self):
        """Update the net status indicator"""
        time_info = get_current_mountain_time()
        if is_net_day():
            current_hour = time_info['datetime'].hour
            if current_hour == 13:  # 1 PM
                self.net_status.setText("🔴 NET ACTIVE")
                self.net_status.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
            elif 12 <= current_hour <= 14:  # Around net time
                self.net_status.setText("🟡 NET SOON")
                self.net_status.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px;")
            else:
                self.net_status.setText("🟢 NET DAY")
                self.net_status.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            self.net_status.setText("⚪ OFF DAY")
            self.net_status.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 14px;")

        # Update every 30 seconds
        QTimer.singleShot(30000, self.update_net_status)

    def init_setup_tab(self):
        """Initialize the setup tab with improved layout and validation"""
        self.setup_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Net information display with current status
        net_info_group = QGroupBox("📡 Net Information & Current Status")
        net_info_layout = QVBoxLayout()

        time_info = get_current_mountain_time()

        self.net_info_display = QTextEdit()
        self.net_info_display.setReadOnly(True)
        self.net_info_display.setMaximumHeight(140)
        self.update_net_info_display()

        net_info_layout.addWidget(self.net_info_display)
        net_info_group.setLayout(net_info_layout)

        # Enhanced operator information with validation
        operator_group = QGroupBox("👤 Net Control Operator Information")
        operator_layout = QGridLayout()
        operator_layout.setSpacing(15)

        # Input fields with enhanced validation
        self.callsign_input = QLineEdit()
        self.callsign_input.setPlaceholderText("Enter your callsign (e.g., W0SWO)")
        self.callsign_input.setMinimumHeight(35)
        self.callsign_input.textChanged.connect(self.validate_callsign)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setMinimumHeight(35)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter your location (e.g., Denver, CO)")
        self.location_input.setMinimumHeight(35)

        # Logger information
        self.logger_callsign_input = QLineEdit()
        self.logger_callsign_input.setPlaceholderText("Logger callsign (optional)")
        self.logger_callsign_input.setMinimumHeight(35)

        self.logger_name_input = QLineEdit()
        self.logger_name_input.setPlaceholderText("Logger name (optional)")
        self.logger_name_input.setMinimumHeight(35)

        operator_layout.addWidget(QLabel("Net Control Callsign:"), 0, 0)
        operator_layout.addWidget(self.callsign_input, 0, 1)
        operator_layout.addWidget(QLabel("Name:"), 0, 2)
        operator_layout.addWidget(self.name_input, 0, 3)
        operator_layout.addWidget(QLabel("Location:"), 1, 0)
        operator_layout.addWidget(self.location_input, 1, 1)
        operator_layout.addWidget(QLabel("Logger Callsign:"), 2, 2)
        operator_layout.addWidget(self.logger_callsign_input, 2, 3)
        operator_layout.addWidget(QLabel("Logger Name:"), 2, 0)
        operator_layout.addWidget(self.logger_name_input, 2, 1)

        operator_group.setLayout(operator_layout)

        # Enhanced weather content management
        content_group = QGroupBox("🌦️ Weather Content Management")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)

        # Weather announcements with better management
        weather_frame = QFrame()
        weather_frame.setFrameStyle(QFrame.Shape.Box)
        weather_layout = QVBoxLayout()

        weather_header = QHBoxLayout()
        weather_label = QLabel("Severe Weather Outlook Announcements")
        weather_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        manage_weather_btn = AnimatedButton("🔧 Manage Announcements")
        manage_weather_btn.clicked.connect(self.manage_weather_announcements)

        weather_header.addWidget(weather_label)
        weather_header.addStretch()
        weather_header.addWidget(manage_weather_btn)

        self.weather_status_label = QLabel(f"Using default announcements ({len(DEFAULT_SWO_ANNOUNCEMENTS)} items)")
        self.weather_status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")

        self.weather_preview = QTextEdit()
        self.weather_preview.setReadOnly(True)
        self.weather_preview.setMaximumHeight(100)
        self.weather_preview.setPlainText("\n".join(DEFAULT_SWO_ANNOUNCEMENTS))

        weather_layout.addLayout(weather_header)
        weather_layout.addWidget(self.weather_status_label)
        weather_layout.addWidget(self.weather_preview)
        weather_frame.setLayout(weather_layout)

        content_layout.addWidget(weather_frame)
        content_group.setLayout(content_layout)

        # Enhanced action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)

        self.load_session_btn = AnimatedButton("📂 Load Session")
        self.load_session_btn.clicked.connect(self.load_session)

        self.save_session_btn = AnimatedButton("💾 Save Session")
        self.save_session_btn.clicked.connect(self.save_session)

        reset_btn = AnimatedButton("🔄 Reset Fields")
        reset_btn.clicked.connect(self.reset_fields)

        self.start_btn = AnimatedButton("🚀 Generate Net Script")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #27ae60; color: white;")
        self.start_btn.clicked.connect(self.start_net_script)

        action_layout.addWidget(self.load_session_btn)
        action_layout.addWidget(self.save_session_btn)
        action_layout.addWidget(reset_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.start_btn)

        layout.addWidget(net_info_group)
        layout.addWidget(operator_group)
        layout.addWidget(content_group)
        layout.addLayout(action_layout)
        layout.addStretch()

        self.setup_tab.setLayout(layout)
        self.tab_widget.addTab(self.setup_tab, "📋 Setup")

        # Connect validation
        for field in [self.callsign_input, self.name_input, self.location_input]:
            field.textChanged.connect(self.validate_fields)

        self.validate_fields()

    def update_net_info_display(self):
        """Update the net information display"""
        time_info = get_current_mountain_time()

        net_info_text = f"""Colorado Severe Weather Outlook Net
Schedule: Monday through Friday at 1:00 PM MST/MDT
Current Time: {time_info['full']}
Today: {time_info['day']} ({'NET DAY' if is_net_day() else 'OFF DAY'})
System: SkyHubLink Network
Coverage: All NWS Weather Forecast Offices serving Colorado

NWS Offices: Grand Junction (GJT), Denver/Boulder (BOU), Goodland (GLD),
             Pueblo (PUB), Cheyenne (CYS)"""

        self.net_info_display.setPlainText(net_info_text)

    def validate_callsign(self):
        """Validate amateur radio callsign format"""
        callsign = self.callsign_input.text().upper()
        self.callsign_input.setText(callsign)

        # Basic callsign validation (simplified)
        if callsign and not re.match(r'^[A-Z0-9]{3,7}$', callsign):
            self.callsign_input.setStyleSheet("border-color: #e74c3c;")
        else:
            self.callsign_input.setStyleSheet("border-color: #28a745;")

    def validate_fields(self):
        """Enhanced field validation with better feedback"""
        valid = all([
            self.callsign_input.text().strip(),
            self.name_input.text().strip(),
            self.location_input.text().strip()
        ])

        # Visual feedback for invalid fields
        for field in [self.callsign_input, self.name_input, self.location_input]:
            if not field.text().strip():
                field.setStyleSheet("border: 2px solid #e74c3c;")
            else:
                field.setStyleSheet("border: 2px solid #28a745;")

        self.start_btn.setEnabled(valid)
        return valid

    def manage_weather_announcements(self):
        """Open weather announcement manager dialog"""
        dialog = WeatherDialog(self)
        dialog.set_announcements(self.net_data.weather_announcements)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.net_data.weather_announcements = dialog.get_announcements()
            self.weather_preview.setPlainText("\n".join(self.net_data.weather_announcements))
            self.weather_status_label.setText(
                f"Custom announcements loaded ({len(self.net_data.weather_announcements)} items)"
            )
            self.status_bar.show_message("Weather announcements updated")

    def init_script_tab(self):
        """Initialize enhanced script tab"""
        self.script_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Script control panel
        control_panel = QGroupBox("🎯 Script Control Panel")
        control_layout = QHBoxLayout()

        self.prev_btn = AnimatedButton("⬅️ Previous")
        self.prev_btn.clicked.connect(self.previous_section)
        self.prev_btn.setEnabled(False)

        self.section_label = QLabel("Section 1 of 1")
        self.section_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.section_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.section_label.setFixedWidth(300)

        self.next_btn = AnimatedButton("Next ➡️")
        self.next_btn.clicked.connect(self.next_section)
        self.next_btn.setEnabled(False)

        # Auto-advance controls
        self.auto_advance_cb = QCheckBox("Auto-advance")
        self.auto_advance_cb.toggled.connect(self.toggle_auto_advance)

        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(10, 300)
        self.delay_spinbox.setValue(30)
        self.delay_spinbox.setSuffix(" sec")
        self.delay_spinbox.valueChanged.connect(self.update_auto_advance_delay)

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.section_label)
        control_layout.addWidget(self.next_btn)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("Auto-advance:"))
        control_layout.addWidget(self.auto_advance_cb)
        control_layout.addWidget(self.delay_spinbox)

        control_panel.setLayout(control_layout)

        # Script display area
        script_group = QGroupBox("📜 Net Script")
        script_layout = QVBoxLayout()

        self.script_display = QTextEdit()
        self.script_display.setFont(QFont("Courier New", 12))
        self.script_display.setReadOnly(True)
        self.script_display.setPlaceholderText("Generate the net script from the Setup tab to begin...")

        script_layout.addWidget(self.script_display)
        script_group.setLayout(script_layout)

        # Script action buttons
        script_actions = QHBoxLayout()

        edit_btn = AnimatedButton("📋 Edit Section")
        edit_btn.clicked.connect(self.toggle_section_editing)

        self.edit_toggle = AnimatedButton("✏️ Edit Section")
        self.edit_toggle.setCheckable(True)
        self.edit_toggle.toggled.connect(self.toggle_section_editing)

        copy_btn = AnimatedButton("📋 Copy Section")
        copy_btn.clicked.connect(self.copy_current_section)

        copy_all_btn = AnimatedButton("📄 Copy All")
        copy_all_btn.clicked.connect(self.copy_all_script)

        export_btn = AnimatedButton("💾 Export Script")
        export_btn.clicked.connect(self.export_script)

        print_btn = AnimatedButton("🖨️ Print")
        print_btn.clicked.connect(self.print_script)

        script_actions.addWidget(self.edit_toggle)
        script_actions.addWidget(copy_btn)
        script_actions.addWidget(copy_all_btn)
        script_actions.addWidget(export_btn)
        script_actions.addWidget(print_btn)
        script_actions.addStretch()

        layout.addWidget(control_panel)
        layout.addWidget(script_group)
        layout.addLayout(script_actions)

        self.script_tab.setLayout(layout)
        self.tab_widget.addTab(self.script_tab, "📜 Script")

        # Auto-advance timer
        self.auto_advance_timer = QTimer()
        self.auto_advance_timer.timeout.connect(self.auto_advance_section)

    def init_weather_tab(self):
        """Initialize weather information tab"""
        self.weather_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # NWS Office Information
        nws_group = QGroupBox("🏢 NWS Weather Forecast Offices Serving Colorado")
        nws_layout = QVBoxLayout()

        # Create office cards
        offices_layout = QGridLayout()
        row = 0
        col = 0

        for office_name, office_data in NWS_OFFICES.items():
            office_card = self.create_nws_office_card(office_name, office_data)
            offices_layout.addWidget(office_card, row, col)
            col += 1
            if col > 2:  # 2 columns
                col = 0
                row += 1

        nws_layout.addLayout(offices_layout)
        nws_group.setLayout(nws_layout)

        # Current conditions placeholder
        conditions_group = QGroupBox("🌤️ Current Weather Conditions")
        conditions_layout = QVBoxLayout()

        self.conditions_display = QTextEdit()
        self.conditions_display.setReadOnly(True)
        self.conditions_display.setMaximumHeight(200)
        self.conditions_display.setPlaceholderText(
            "Weather conditions will be displayed here...\n\n"
            "Note: This is a placeholder for weather data integration.\n"
            "In a production environment, this would connect to NWS APIs\n"
            "for real-time weather information."
        )

        refresh_weather_btn = AnimatedButton("🔄 Refresh Weather Data")
        refresh_weather_btn.clicked.connect(self.refresh_weather_data)

        conditions_layout.addWidget(self.conditions_display)
        conditions_layout.addWidget(refresh_weather_btn)
        conditions_group.setLayout(conditions_layout)

        # Announcements preview
        announcements_group = QGroupBox("📢 Current Weather Announcements")
        announcements_layout = QVBoxLayout()

        self.announcements_display = QTextEdit()
        self.announcements_display.setReadOnly(True)
        self.announcements_display.setMaximumHeight(150)

        edit_announcements_btn = AnimatedButton("✏️ Edit Announcements")
        edit_announcements_btn.clicked.connect(self.manage_weather_announcements)

        announcements_layout.addWidget(self.announcements_display)
        announcements_layout.addWidget(edit_announcements_btn)
        announcements_group.setLayout(announcements_layout)

        layout.addWidget(nws_group)
        layout.addWidget(conditions_group)
        layout.addWidget(announcements_group)
        layout.addStretch()

        self.weather_tab.setLayout(layout)
        self.tab_widget.addTab(self.weather_tab, "🌦️ Weather")

        # Update announcements display
        self.update_announcements_display()

    def create_nws_office_card(self, name: str, data: Dict[str, str]) -> QFrame:
        """Create a card widget for NWS office information"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 2px;
                background-color: #000000;
                color: #ffffff;
                padding: 2px;
            }
        """)
        # Remove fixed heights to allow dynamic sizing
        card.setMinimumHeight(80)  # Reduced minimum to allow more shrinking
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Main layout with better spacing
        layout = QVBoxLayout()
        layout.setSpacing(6)  # Slightly reduced for compact view
        layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins for smaller windows

        # Office name and code - larger, more readable font
        header = QLabel(f"{name} ({data['code']})")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        header.setWordWrap(True)  # Allow wrapping for long names
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header.setMinimumHeight(0)  # Allow it to shrink

        # Coverage area - larger font
        areas = QLabel(f"Areas: {data['areas']}")
        areas.setWordWrap(True)
        areas.setStyleSheet("color: #7f8c8d; font-size: 12px;")  # Slightly smaller for compact view
        areas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        areas.setMinimumHeight(0)  # Allow it to shrink

        # Contact info layout with better spacing
        contact_layout = QHBoxLayout()
        contact_layout.setSpacing(12)
        contact_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from nested layout

        # Phone and web labels - larger, more readable fonts
        phone_label = QLabel(f"📞 {data['phone']}")
        phone_label.setStyleSheet("font-size: 11px; color: #34495e;")
        phone_label.setWordWrap(True)  # Allow wrapping
        phone_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        phone_label.setMinimumHeight(0)

        web_label = QLabel(f"🌐 {data['url'].replace('https://', '')}")
        web_label.setStyleSheet("font-size: 11px; color: #3498db;")
        web_label.setWordWrap(True)  # Allow wrapping
        web_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        web_label.setMinimumHeight(0)

        # Add contact widgets to layout
        contact_layout.addWidget(phone_label)
        contact_layout.addWidget(web_label)

        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(areas)
        layout.addLayout(contact_layout)
        # Remove addStretch() to allow natural sizing instead of forcing extra space

        card.setLayout(layout)
        return card

    def init_toolkit_tab(self):
        # FIX: Add parentheses to instantiate QWidget
        self.toolkit_tab = QWidget()

        # Add the tab to the tab widget
        self.tab_widget.addTab(self.toolkit_tab, "🧰 Toolkit")

        # Create the main layout for the toolkit tab
        main_layout = QVBoxLayout()
        self.toolkit_tab.setLayout(main_layout)  # Set layout on the widget, not self
        main_layout.setSpacing(15)

        # Header
        header = QLabel(f"🌪 {self.APP_NAME}")
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
        # self.statusBar().showMessage(f"Ready - {APP_AUTHOR} ({AUTHOR_EMAIL})")

    def show_web_popup(self, url, title):
        if not WEBENGINE_AVAILABLE:
            QMessageBox.information(self, "WebEngine Not Available",
                "PyQtWebEngine is not installed. Opening in external browser instead.\n\n"
                "To install: pip install PyQtWebEngine")
            webbrowser.open(url)
            return

        popup = WebViewPopup(self, url, title, self.current_theme, self.config["font_size"])
        popup.exec()

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
            elif "spotter" in url and url.endswith(".png"):
                view_btn = ModernButton("🛰️ View Image")
                view_btn.clicked.connect(lambda checked, u=url: self.show_spotter_image_popup(u))
                btn_layout.addWidget(view_btn)

            web_btn = ModernButton("🖥️ View in App")
            web_btn.clicked.connect(lambda checked, u=url, n=link_name: self.show_web_popup(u, n))
            btn_layout.addWidget(web_btn)

            # Open in browser button
            # open_btn = ModernButton("🌐 Open in Browser")
            # open_btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            # btn_layout.addWidget(open_btn)

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
        # Make sure current_theme is set from config if not already set
        if not hasattr(self, 'current_theme') or self.current_theme is None:
            self.current_theme = themes[self.config["theme"]]

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
        # Safety check for current_theme
        if not hasattr(self, 'current_theme') or self.current_theme is None:
            self.current_theme = themes[self.config.get("theme", "light")]

        popup = TextPopup(self, url, title, typ, self.current_theme, self.config["font_size"], parse_pre)
        popup.exec()

    def show_image_popup(self, url):
        popup = ImagePopup(self, url, self.current_theme, self.config["font_size"])
        popup.exec()

    def show_spotter_image_popup(self, url):
        popup = SpotterImagePopup(self, url, self.current_theme, self.config["font_size"])
        popup.exec()

    def _fetch_alerts(self, url, window_title):
        theme = self.theme
        font_size = self.font_size

        # Create popup dialog
        popup = QDialog(self.root)
        popup.setWindowTitle(window_title)
        popup.resize(950, 700)
        popup.setStyleSheet(f"""
            QDialog {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
            }}
            QLabel {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
            }}
            QLineEdit {{
                background-color: {theme["entry_bg"]};
                color: {theme["entry_fg"]};
                border: 1px solid #666;
                padding: 4px;
            }}
            QPushButton {{
                background-color: {theme["button_bg"]};
                color: {theme["button_fg"]};
                border: 1px solid #666;
                padding: 6px 12px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {theme.get("button_hover", theme["button_bg"])};
            }}
            QTextEdit {{
                background-color: {theme["bg"]};
                color: {theme["fg"]};
                border: 1px solid #666;
            }}
        """)

        # Main layout
        layout = QVBoxLayout(popup)

        # Hint label
        hint = QLabel("Tip: Search for specific keywords.")
        hint.setStyleSheet(f"color: {theme['accent']};")
        font = QFont("TkDefaultFont", font_size)
        hint.setFont(font)
        layout.addWidget(hint)

        # Search frame
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_label = QLabel("Filter alerts: ")
        search_layout.addWidget(search_label)

        search_entry = QLineEdit()
        search_entry.setFont(font)
        search_layout.addWidget(search_entry)

        refresh_btn = QPushButton("Refresh Now")
        search_layout.addWidget(refresh_btn)

        search_layout.addStretch()
        layout.addWidget(search_frame)

        # Status label
        stat_label = QLabel("Loading alerts...")
        stat_label.setStyleSheet(f"color: {theme['accent']};")
        stat_label.setFont(font)
        layout.addWidget(stat_label)

        # Text area
        text_area = QTextEdit()
        text_area.setFont(font)
        text_area.setReadOnly(True)
        text_area.setWordWrapMode(QTextEdit.WrapMode.WordWrap)
        layout.addWidget(text_area)

        # Add context menu (assuming you have this method)
        self._add_context_menu(text_area)

        # Bottom controls
        ctrl_frame = QFrame()
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)

        copy_btn = QPushButton("Copy All")
        ctrl_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save As...")
        ctrl_layout.addWidget(save_btn)

        ctrl_layout.addStretch()

        close_btn = QPushButton("Close (Esc)")
        ctrl_layout.addWidget(close_btn)

        layout.addWidget(ctrl_frame)

        # Internal state
        entries = []
        last_update = [""]

        # Setup text formats for different alert types
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(theme["warning"]))
        warning_format.setFontWeight(QFont.Weight.Bold)

        watch_format = QTextCharFormat()
        watch_format.setForeground(QColor(theme["watch"]))

        advisory_format = QTextCharFormat()
        advisory_format.setForeground(QColor(theme["advisory"]))

        statement_format = QTextCharFormat()
        statement_format.setForeground(QColor(theme["advisory"]))

        county_format = QTextCharFormat()
        county_format.setForeground(QColor(theme["county"]))
        county_format.setFontWeight(QFont.Weight.Bold)

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#204060"))
        highlight_format.setForeground(QColor("yellow"))

        link_format = QTextCharFormat()
        link_format.setForeground(QColor("blue"))
        link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        # Worker thread and fetcher
        worker_thread = QThread()
        fetcher = AlertFetcher(url)
        fetcher.moveToThread(worker_thread)

        def load_alerts():
            stat_label.setText("Loading alerts...")
            self.status("Loading alerts...")
            # Start worker thread
            worker_thread.started.connect(fetcher.fetch_alerts)
            worker_thread.start()

        def on_alerts_fetched(new_entries, update_time):
            nonlocal entries
            entries.clear()
            entries.extend(new_entries)
            last_update[0] = update_time
            worker_thread.quit()
            apply_filter()

        def on_error(error_msg):
            self.log_error(f"Error fetching alerts: {error_msg}")
            entries.clear()
            last_update[0] = ""
            worker_thread.quit()
            apply_filter()

        # Connect signals
        fetcher.alerts_fetched.connect(on_alerts_fetched)
        fetcher.error_occurred.connect(on_error)

        def apply_filter():
            term = search_entry.text().lower()
            text_area.clear()

            grouped_alerts = {}
            for entry in entries:
                title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                area_elem = entry.find("{urn:oasis:names:tc:emergency:cap:1.1}areaDesc")

                if title_elem is not None and summary_elem is not None:
                    title = title_elem.text or ""
                    summary = summary_elem.text or ""
                    link = link_elem.attrib.get("href", "") if link_elem is not None else ""

                    if area_elem is not None and area_elem.text:
                        counties = [c.strip() for c in area_elem.text.split(';')]
                    else:
                        counties = ["Active NWS Alerts"]

                    if term in title.lower() or term in summary.lower():
                        for county in counties:
                            if county not in grouped_alerts:
                                grouped_alerts[county] = []
                            grouped_alerts[county].append((title, summary, link))

            cursor = text_area.textCursor()

            for county, alerts in grouped_alerts.items():
                # County header
                cursor.insertText(f"=== {county} ===\n", county_format)

                for title, summary, link in alerts:
                    # Determine alert type format
                    title_lower = title.lower()
                    if "warning" in title_lower:
                        alert_format = warning_format
                    elif "watch" in title_lower:
                        alert_format = watch_format
                    elif "advisory" in title_lower:
                        alert_format = advisory_format
                    elif "statement" in title_lower:
                        alert_format = statement_format
                    else:
                        alert_format = QTextCharFormat()

                    # Insert title
                    cursor.insertText(f"Title: {title}\n", alert_format)

                    # Highlight search term in title if present
                    if term and term in title.lower():
                        # Find and highlight the term
                        text = text_area.toPlainText()
                        start_idx = text.rfind(f"Title: {title}")
                        if start_idx != -1:
                            term_idx = title.lower().find(term)
                            if term_idx != -1:
                                abs_start = start_idx + 7 + term_idx  # 7 = len("Title: ")
                                highlight_cursor = text_area.textCursor()
                                highlight_cursor.setPosition(abs_start)
                                highlight_cursor.setPosition(abs_start + len(term), QTextCursor.MoveMode.KeepAnchor)
                                highlight_cursor.mergeCharFormat(highlight_format)

                    # Insert summary
                    cursor.insertText(f"Summary: {summary}\n")

                    # Highlight search term in summary if present
                    if term and term in summary.lower():
                        text = text_area.toPlainText()
                        start_idx = text.rfind(f"Summary: {summary}")
                        if start_idx != -1:
                            term_idx = summary.lower().find(term)
                            if term_idx != -1:
                                abs_start = start_idx + 9 + term_idx  # 9 = len("Summary: ")
                                highlight_cursor = text_area.textCursor()
                                highlight_cursor.setPosition(abs_start)
                                highlight_cursor.setPosition(abs_start + len(term), QTextCursor.MoveMode.KeepAnchor)
                                highlight_cursor.mergeCharFormat(highlight_format)

                    # Insert link
                    if link:
                        link_start = cursor.position()
                        cursor.insertText(f"Link: {link}\n\n")

                        # Make link clickable
                        link_cursor = text_area.textCursor()
                        link_cursor.setPosition(link_start)
                        link_cursor.setPosition(cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                        link_cursor.mergeCharFormat(link_format)

                        # Store link for click handling
                        text_area.setProperty(f"link_{link_start}", link)

            stat_label.setText(f"Alerts loaded. Last update: {last_update[0]}")
            self.status(f"{window_title} loaded at {last_update[0]}")

        # Handle text area mouse clicks for links
        def handle_text_click(event):
            cursor = text_area.cursorForPosition(event.pos())
            pos = cursor.position()

            # Check if click is on a link
            for prop_name in text_area.dynamicPropertyNames():
                prop_name_str = prop_name.data().decode('utf-8')
                if prop_name_str.startswith("link_"):
                    link_pos = int(prop_name_str.split("_")[1])
                    # Simple range check - in production you'd want more precise hit detection
                    if abs(pos - link_pos) < 200:  # Approximate range
                        url = text_area.property(prop_name_str)
                        if url:
                            webbrowser.open(url)
                            break

        text_area.mousePressEvent = handle_text_click

        # Connect buttons
        refresh_btn.clicked.connect(load_alerts)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(text_area.toPlainText()))
        save_btn.clicked.connect(lambda: self.save_text_to_file(text_area.toPlainText()))
        close_btn.clicked.connect(popup.close)

        # Connect search
        search_entry.textChanged.connect(apply_filter)
        search_entry.returnPressed.connect(apply_filter)

        # Keyboard shortcuts
        popup.keyPressEvent = lambda e: popup.close() if e.key() == Qt.Key.Key_Escape else None

        # Set focus
        search_entry.setFocus()

        # Auto-refresh timer
        refresh_timer = QTimer()
        refresh_timer.timeout.connect(load_alerts)
        refresh_timer.start(self.auto_refresh_mins * 60000)

        # Initial load
        load_alerts()

        self.status(f"{window_title} opened.")

        # Show popup
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


    def init_settings_tab(self):
        """Initialize settings tab"""
        self.settings_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Appearance settings
        appearance_group = QGroupBox("🎨 Appearance")
        appearance_layout = QGridLayout()

        # Theme selection
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        # Font settings
        font_label = QLabel("Font:")
        self.font_btn = QPushButton("Select Font")
        self.font_btn.clicked.connect(self.select_font)

        appearance_layout.addWidget(theme_label, 0, 0)
        appearance_layout.addWidget(self.theme_combo, 0, 1)
        appearance_layout.addWidget(font_label, 1, 0)
        appearance_layout.addWidget(self.font_btn, 1, 1)

        appearance_group.setLayout(appearance_layout)

        # Behavior settings
        behavior_group = QGroupBox("⚙️ Behavior")
        behavior_layout = QVBoxLayout()

        self.auto_save_cb = QCheckBox("Auto-save session data")
        self.auto_save_cb.setChecked(True)

        self.confirm_exit_cb = QCheckBox("Confirm before exit")
        self.confirm_exit_cb.setChecked(True)

        self.sound_alerts_cb = QCheckBox("Sound alerts for net time")
        self.sound_alerts_cb.setChecked(False)

        behavior_layout.addWidget(self.auto_save_cb)
        behavior_layout.addWidget(self.confirm_exit_cb)
        behavior_layout.addWidget(self.sound_alerts_cb)

        behavior_group.setLayout(behavior_layout)

        # Default values
        defaults_group = QGroupBox("🔧 Default Values")
        defaults_layout = QGridLayout()

        defaults_layout.addWidget(QLabel("Default Callsign:"), 0, 0)
        self.default_callsign = QLineEdit(Config.DEFAULT_CALLSIGN)
        defaults_layout.addWidget(self.default_callsign, 0, 1)

        defaults_layout.addWidget(QLabel("Default Name:"), 1, 0)
        self.default_name = QLineEdit(Config.DEFAULT_NAME)
        defaults_layout.addWidget(self.default_name, 1, 1)

        defaults_layout.addWidget(QLabel("Default Location:"), 2, 0)
        self.default_location = QLineEdit(Config.DEFAULT_LOCATION)
        defaults_layout.addWidget(self.default_location, 2, 1)

        defaults_group.setLayout(defaults_layout)

        # Action buttons
        settings_actions = QHBoxLayout()

        reset_settings_btn = AnimatedButton("🔄 Reset to Defaults")
        reset_settings_btn.clicked.connect(self.reset_settings)

        save_settings_btn = AnimatedButton("💾 Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)

        settings_actions.addWidget(reset_settings_btn)
        settings_actions.addStretch()
        settings_actions.addWidget(save_settings_btn)

        layout.addWidget(appearance_group)
        layout.addWidget(behavior_group)
        layout.addWidget(defaults_group)
        layout.addLayout(settings_actions)
        layout.addStretch()

        self.settings_tab.setLayout(layout)
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        next_shortcut = QKeySequence("Ctrl+Right")
        next_action = QAction(self)
        next_action.setShortcut(next_shortcut)
        next_action.triggered.connect(self.next_section)
        self.addAction(next_action)

        prev_shortcut = QKeySequence("Ctrl+Left")
        prev_action = QAction(self)
        prev_action.setShortcut(prev_shortcut)
        prev_action.triggered.connect(self.previous_section)
        self.addAction(prev_action)

        # Copy shortcuts
        copy_shortcut = QKeySequence("Ctrl+C")
        copy_action = QAction(self)
        copy_action.setShortcut(copy_shortcut)
        copy_action.triggered.connect(self.copy_current_section)
        self.addAction(copy_action)

        # Save shortcut
        save_shortcut = QKeySequence("Ctrl+S")
        save_action = QAction(self)
        save_action.setShortcut(save_shortcut)
        save_action.triggered.connect(self.save_session)
        self.addAction(save_action)

    def start_net_script(self):
        """Generate and start the net script"""
        if not self.validate_fields():
            QMessageBox.warning(self, "Validation Error",
                              "Please fill in all required fields before generating the script.")
            return

        # Collect data
        self.net_data.callsign = self.callsign_input.text().strip()
        self.net_data.name = self.name_input.text().strip()
        self.net_data.location = self.location_input.text().strip()
        self.net_data.logger_callsign = self.logger_callsign_input.text().strip()
        self.net_data.logger_name = self.logger_name_input.text().strip()

        # Generate script sections
        self.generate_script_sections()

        # Switch to script tab
        self.tab_widget.setCurrentIndex(1)  # Script tab

        # Display first section
        self.section_idx = 0
        self.display_current_section()

        self.status_bar.show_message("Net script generated successfully!")
        logging.info("Net script generated")

    def generate_script_sections(self):
        """Generate all script sections"""
        time_info = get_current_mountain_time()
        fetcher = NWSTextFetcher()
        trimmer = WeatherForecastTrimmer()

        self.sections = []

        pre_opening = f"""1250-1255…
THE Wx OUTLOOK NET COVERING THE CENTRAL ROCKIES & HIGH PLAINS REGION WILL AIR ON THESE FREQUENCIES IN (minutes)…
Open Net following Analog repeater IDs at the top of the hour…"""

        self.sections.append(("Pre-Opening", pre_opening))

    # Section 2: Opening
        opening = f"""NET OPEN

Happy {time_info['day']}! Welcome to the Wx Outlook Net from the Severe Wx Network here on the Skyhub repeater-linking system, where we cover the Central Rockies and High Plains Region.

Your Net Control is {net_data.name}, {net_data.callsign}, {net_data.phonetic_callsign}, located in {net_data.location}.

{net_data.logger_name}, {net_data.logger_callsign} is your net logging host.

This briefing airs Mondays thru Fridays at 1300 MT on the SkyHubLink.com system and whenever else needed.

The Severe Wx Network is on air in the CO Severe Wx Room when the region is under threat. When severe wx threatens your area, your nearest rptrs will be connected to the Svr Rm.

That room operates under 2 conditions:
Before svr wx is widespread, no net is called and the room is open to chat related to the wx at hand by keeping transmissions shorter and leaving 5-7 sec in between.

Once wx goes severe and/or more widespread and/or tornados are involved, the room goes into Net Mode. During that, all transmissions must be short, pass thru NC, and be directly related to a severe storm report.

The 485322 AllStar Weather Hub is now bridged during this net, so those who are connected there for the severe room will hear this net.

PLEASE allow 3-5 seconds between transmissions, 1.5 seconds for keyup and then begin speaking. ALSO, keep the PTT pushed a half second or so after your last word. That allows your last word not to be cut off.

This is a directed NET. All check-ins must go through net control."""

        self.sections.append(("Opening", opening))

    # Section 3: Access Information
        access_info = f"""To access the Severe Wx Room at Reflector XLX303a—

EchoLink NC2WX-L, Node 155536
BM/DMR 31083
Wires-X Room 65045
Allstar on Node 485322 or 289800
YSF 30300 (switch to module A, DGID 10)
D-STAR XRF/DCS303A

To monitor the CO Severe Rm go to hose.brandmeister.network. Click on the player upper right and type 31083."""

        self.sections.append(("Access Information", access_info))

    # Section 4: Weather Announcements
        weather_text = f"""SEVERE WEATHER OUTLOOK ANNOUNCEMENTS:

"""
        if net_data.weather_announcements:
            for i, announcement in enumerate(net_data.weather_announcements, 1):
                weather_text += f"{i}. {announcement}\n\n"
        else:
            weather_text += "(No severe weather announcements at this time)\n\n"

        weather_text += "That concludes our severe weather outlook announcements."

        self.sections.append(("Weather Announcements", weather_text))

    # Section 5: NWS Office Information & Net Procedures
        nws_procedures = f"""During this net, we provide information to Skywarn Storm Spotters for the 5 National Weather Services with whom we are Core Partners here in the central High Plains and Rockies region.

Following some headlines, we pick up with NWS Grand Jct on the Western Slope of CO and eastern UT, then work clockwise around the state before moving to the NWS Cheyenne forecast area.

NATIONAL WEATHER SERVICE OFFICES SERVING COLORADO:

The following NWS Weather Forecast Offices serve Colorado:

• Grand Junction (GJT) - Western Colorado
  Phone: 970-243-7007, Website: weather.gov/gjt

• Denver/Boulder (BOU) - Eastern Colorado and Metro Denver area
  Phone: 303-494-4221, Website: weather.gov/bou

• Goodland (GLD) - Eastern Colorado
  Phone: (785) 899-7119, Website: weather.gov/gld

• Pueblo (PUB) - Southern Colorado
  Phone: 719-948-9429, Website: weather.gov/pub

• Cheyenne (CYS) - Northeastern Colorado
  Phone: 307-772-2468, Website: weather.gov/cys

For current weather information, please visit weather.gov or contact your local NWS office directly.

Should there be an emergency, please key-in with 'break-break-break' and we'll suspend the net for your traffic.

This is a linked system, so please key and wait 1½ or 2 seconds before speaking and hang onto that PTT for an equal time afterward so that we hear your entire transmission.

Just as with severe storm reports, when sending photos, always include:
Event time, specific location (county if possible), direction camera is looking, and detailed explanation of the severe event you see.

If you're sharing a non-severe pic with folks, please type non-severe at the head of the caption so I can quickly overlook it for relay.

You will hear more weather info in the Svr room than on your local repeater, but your rptr will be connected to the room when severe wx is threatening your area. Stay tuned there for severe announcements and to report your severe observations for relay to the appropriate NWS.

The KB5YZB analog 447.100 Mt Chief repeater is often connected to the Svr room when that room is active. Many thanks to Brett for this service. When storms are more than about 50 miles from the metro area, I usually don't connect it. Let us know what you think about this."""

        self.sections.append(("NWS Offices & Procedures", nws_procedures))

    # Section 6: Telegram Information
        telegram_info = f"""SWN has 2 Telegram rooms to serve you...FREE DOWNLOAD incl ph app

The SkyHubLink Weather Information CO/UT/WY/NE is limited to outlooks for the region. It provides a quick-reference platform for viewing the current day's wx and, sometimes, a look at major weather ahead. It usually includes NWS updates throughout the day.

Telegram CO Regional Wx Chat is open to ANY and ALL weather/climate discussion, general chat, photos, educational, and the like. Check-ins. It's a platform for sharing what you believe may be of interest to others. Occasionally, it may include graphics to supplement weather discussion on the SkyHubLink.

Thanks to those of you who have added your callsign after your first name or handle on Telegram. To better facilitate comms, this is now a requirement for amateur operators in the SHL Wx Information and CO Reg Wx Chatrooms.

Also, we plan to implement Ham.Live as the platform for relaying severe storm reports and photos when the CO Severe Wx Room is active. Ham.Live will be restricted to severe reports to Net Control in conjunction with radio reports in the CO Severe Wx Room. This will simplify things for the Severe Wx NC and speed the relay of reports to the NWS. More info on how to use it will be coming soon.

The CO Reg Wx Chatroom on Telegram will continue as always, that is, unrestricted weather-related chat."""

        self.sections.append(("Telegram Information", telegram_info))

    # Section 7: Check-in Procedures
        checkin_text = f"""WE'LL NOW TAKE OVER-THE-AIR CHECKINS FOR THE WEATHER OUTLOOK NET

Please give your callsign twice and—if you use phonetics—use only Standard ITU Phonetics

If possible, please use Netlogger or the CO Reg Wx Chat room on Telegram to check in. The more of you who can check in to this net using them, the better, since the 1-hour time allotment is precious.

Download it for free at Netlogger.org. Click 'Select Net' at bottom left, find the SkyHubLink Wx Outlook Net and click. At upper left, click on the blue AIM tab, which opens that small window. If you're a regular, we'll recognize and log you. If you're somewhat new, just type "check me plz."

First, as a courtesy, mobiles and portables. Mobile and portable stations come now with your callsign twice, please indicate which type you are.

Analog FM Stations, Analog FM only, check in now.
Callsign twice

All Digital Stations, Digital only check in now,
Callsign once (use YSF dashboard for callsign retrieval)

Any Other Check-ins, Any mode, Any location for the Wx Outlook Net? Callsign twice

Thanks for being here with us today!"""

        self.sections.append(("Check-ins", checkin_text))


        afd_text = fetcher.fetch_text_product('GJT', 'AFD')
        clean_afd = trimmer.trim_afd(afd_text)
        afd_text = trimmer.remove_aviation_forecast(clean_afd)
        clean_afd = trimmer.remove_remainder_gjt_forecast(afd_text)

        hwo_text = fetcher.fetch_text_product('GJT', 'HWO')
        clean_hwo = trimmer.trim_hwo(hwo_text)

        grand_junction_NWS_WFO = f"""The Grand Junction weather forecast area

Area Forecast Discussion for the Grand Junction forecast area:

{clean_afd}


Hazardous Weather Outlook for the Grand Junction forecast area:


{clean_hwo}

"""

        self.sections.append(("Grand Junction WFO", grand_junction_NWS_WFO))

        afd_text = fetcher.fetch_text_product('BOU', 'AFD')
        clean_afd = trimmer.trim_afd(afd_text)
        afd_text = trimmer.remove_aviation_forecast(clean_afd)
        clean_afd = trimmer.remove_remainder_bou_forecast(afd_text)

        hwo_text = fetcher.fetch_text_product('BOU', 'HWO')
        clean_hwo = trimmer.trim_hwo(hwo_text)


        boulder_NWS_WFO = f"""The Boulder weather forecast area

Area Forecast Discussion for the Boulder forecast area:


{clean_afd}


Hazardous Weather Outlook for the Boulder forecast area:


{clean_hwo}

"""

        self.sections.append(("Boulder WFO", boulder_NWS_WFO))

        afd_text = fetcher.fetch_text_product('GLD', 'AFD')
        clean_afd = trimmer.trim_afd(afd_text)
        afd_text = trimmer.remove_aviation_forecast(clean_afd)
        clean_afd = trimmer.remove_remainder_gld_forecast(afd_text)

        hwo_text = fetcher.fetch_text_product('GLD', 'HWO')
        clean_hwo = trimmer.trim_hwo(hwo_text)


        goodland_NWS_WFO = f"""The Goodland weather forecast area

Area Forecast Discussion for the Goodland forecast area:


{clean_afd}


Hazardous Weather Outlook for the Goodland forecast area:


{clean_hwo}

"""

        self.sections.append(("Goodland WFO", goodland_NWS_WFO))

        afd_text = fetcher.fetch_text_product('PUB', 'AFD')
        clean_afd = trimmer.trim_afd(afd_text)
        afd_text = trimmer.remove_aviation_forecast(clean_afd)
        clean_afd = trimmer.remove_remainder_pub_forecast(afd_text)

        hwo_text = fetcher.fetch_text_product('PUB', 'HWO')
        clean_hwo = trimmer.trim_hwo(hwo_text)


        pueblo_NWS_WFO = f"""The Pueblo weather forecast area

Area Forecast Discussion for the Pueblo forecast area:


{clean_afd}


Hazardous Weather Outlook for the Pueblo forecast area:


{clean_hwo}

"""

        self.sections.append(("Pueblo WFO", pueblo_NWS_WFO))

        afd_text = fetcher.fetch_text_product('CYS', 'AFD')
        clean_afd = trimmer.trim_afd(afd_text)
        afd_text = trimmer.remove_aviation_forecast(clean_afd)
        clean_afd = trimmer.remove_remainder_cys_forecast(afd_text)

        hwo_text = fetcher.fetch_text_product('CYS', 'HWO')
        clean_hwo = trimmer.trim_hwo(hwo_text)


        cheyenne_NWS_WFO = f"""The Cheyenne weather forecast area

Hazardous Weather Outlook for the Cheyenne forecast area:


{clean_hwo}


Area Forecast Discussion for the Cheyenne forecast area:


{clean_afd}
"""

        self.sections.append(("Cheyenne WFO", cheyenne_NWS_WFO))

    # Section 8: Closing
        closing = f"""NET CLOSE

Many thanks to all of you for being here. The Severe Wx Network and the NWS appreciates your support and concern over threatening weather.

See SkyHubLink.com/Nets and click the Severe Wx Network tab for information on this program and its operations. If you aren't subscribed to the SHL mailing list, please do so to stay abreast of important announcements such as net changes, etc. Go to SkyHubLink.com/join. Your inbox won't be overloaded.

Thanks to the Skyhublink System for the use of its many repeaters and for the Severe Wx Hub 485322. Thanks also to the CO Digital Multiprotocol Group for Reflector xlx303a which is the location of the CO Severe Wx Room. Visit them at ColoradoDigital.net. Thanks to the many other rptr owners who link to the Severe Wx Room for public safety during severe storm outbreaks.

Thanks also to kd0sbn for WiresX 65045 in the CO Severe Rm, which is access for the NC2WX Skywarn repeater.

For the Severe Weather Network, this is {net_data.name} closing the Weather Outlook Net. The systems are returned to open use. Have a great day! 73, {net_data.callsign} is clear.

In Netlogger, click "Close Net" and log the check-ins. Beginning with last check-in, right click on callsign, left click on "Log Contact"."""

        self.sections.append(("Closing", closing))

        # Update navigation
        self.update_navigation()

    def display_current_section(self):
        """Display the current script section"""
        if not self.sections or self.section_idx >= len(self.sections):
            return

        section_name, section_text = self.sections[self.section_idx]

        # Format the display
        display_text = f"=== {section_name.upper()} ===\n\n{section_text}"

        self.script_display.setPlainText(display_text)

        # Update section label
        self.section_label.setText(f"Section {self.section_idx + 1} of {len(self.sections)}: {section_name}")

        # Update navigation buttons
        self.prev_btn.setEnabled(self.section_idx > 0)
        self.next_btn.setEnabled(self.section_idx < len(self.sections) - 1)

        # Start auto-advance timer if enabled
        if self.auto_advance and self.section_idx < len(self.sections) - 1:
            self.auto_advance_timer.start(self.auto_advance_delay * 1000)

    def next_section(self):
        """Move to next section"""
        if self.section_idx < len(self.sections) - 1:
            self.section_idx += 1
            self.display_current_section()
            self.auto_advance_timer.stop()

    def previous_section(self):
        """Move to previous section"""
        if self.section_idx > 0:
            self.section_idx -= 1
            self.display_current_section()
            self.auto_advance_timer.stop()

    def toggle_auto_advance(self, enabled: bool):
        """Toggle auto-advance feature"""
        self.auto_advance = enabled
        if not enabled:
            self.auto_advance_timer.stop()
        elif self.sections and self.section_idx < len(self.sections) - 1:
            self.auto_advance_timer.start(self.auto_advance_delay * 1000)

    def update_auto_advance_delay(self, delay: int):
        """Update auto-advance delay"""
        self.auto_advance_delay = delay
        if self.auto_advance and self.auto_advance_timer.isActive():
            self.auto_advance_timer.start(delay * 1000)

    def auto_advance_section(self):
        """Auto-advance to next section"""
        self.next_section()

    def update_navigation(self):
        """Update navigation controls"""
        has_sections = bool(self.sections)
        self.prev_btn.setEnabled(has_sections and self.section_idx > 0)
        self.next_btn.setEnabled(has_sections and self.section_idx < len(self.sections) - 1)

    def toggle_section_editing(self, enabled):
        """Toggle editing mode for current section"""
        self.script_display.setReadOnly(not enabled)
        if enabled:
            self.script_display.setStyleSheet("background-color: #2c3e50; border: 2px solid #ffc107; color: #ecf0f1;")
            self.status_bar.show_message("Section editing enabled - changes will be saved automatically")
        else:
            # Reset to default styling based on current theme
            if self.theme_dark:
                self.script_display.setStyleSheet("background-color: #34495e; border: 2px solid #7f8c8d; color: #ecf0f1;")
            else:
                self.script_display.setStyleSheet("background-color: #ffffff; border: 2px solid #bdc3c7; color: #2c3e50;")

            # Save changes if we have sections
            if self.sections and self.section_idx < len(self.sections):
                # Extract just the content (remove the header)
                full_text = self.script_display.toPlainText()
                # Find the content after the header line
                lines = full_text.split('\n')
                if len(lines) > 2 and lines[0].startswith('=== ') and lines[0].endswith(' ==='):
                    # Skip the header line and empty line
                    content_lines = lines[2:]
                    new_content = '\n'.join(content_lines)

                    # Update the section
                    title = self.sections[self.section_idx][0]
                    self.sections[self.section_idx] = (title, new_content)

            self.status_bar.show_message("Section editing disabled - changes saved")

    def copy_current_section(self):
        """Copy current section to clipboard"""
        if self.sections and self.section_idx < len(self.sections):
            section_name, section_text = self.sections[self.section_idx]
            clipboard_text = f"=== {section_name.upper()} ===\n\n{section_text}"

            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)

            self.status_bar.show_message(f"Copied {section_name} section to clipboard")

    def copy_all_script(self):
        """Copy entire script to clipboard"""
        if not self.sections:
            QMessageBox.information(self, "No Script", "Please generate a script first.")
            return

        full_script = ""
        for section_name, section_text in self.sections:
            full_script += f"=== {section_name.upper()} ===\n\n{section_text}\n\n" + "="*50 + "\n\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(full_script)

        self.status_bar.show_message("Complete script copied to clipboard")

    def export_script(self):
        """Export script to file"""
        if not self.sections:
            QMessageBox.information(self, "No Script", "Please generate a script first.")
            return

        time_info = get_current_mountain_time()
        default_filename = f"Colorado_SWO_Net_{time_info['datetime'].strftime('%Y%m%d_%H%M')}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Net Script", default_filename,
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Colorado Severe Weather Outlook Net Script\n")
                    f.write(f"Generated: {time_info['date']} at {time_info['full']}\n")
                    f.write(f"Net Control: {self.net_data.callsign} - {self.net_data.name}\n")
                    f.write(f"Location: {self.net_data.location}\n")
                    if self.net_data.logger_callsign:
                        f.write(f"Logger: {self.net_data.logger_callsign} - {self.net_data.logger_name}\n")
                    f.write("\n" + "="*60 + "\n\n")

                    for section_name, section_text in self.sections:
                        f.write(f"=== {section_name.upper()} ===\n\n")
                        f.write(section_text)
                        f.write("\n\n" + "="*50 + "\n\n")

                self.status_bar.show_message(f"Script exported to {file_path}")
                QMessageBox.information(self, "Export Successful", f"Script exported to:\n{file_path}")

            except Exception as e:
                self.status_bar.show_message(f"Export failed: {e}", error=True)
                QMessageBox.critical(self, "Export Error", f"Failed to export script:\n{e}")

    def print_script(self):
        """Print the script"""
        QMessageBox.information(self, "Print", "Print functionality would be implemented here.\nFor now, please use Export and print the file.")

    def refresh_weather_data(self):
        """Refresh weather data (placeholder)"""
        self.status_bar.show_message("Refreshing weather data...", progress=True)
        self.status_bar.set_progress(50)

        # Simulate data refresh
        QTimer.singleShot(2000, lambda: self.status_bar.show_message("Weather data updated"))
        QTimer.singleShot(2000, lambda: self.status_bar.set_progress(100))

        # In a real implementation, this would fetch data from NWS APIs
        placeholder_weather = """CURRENT WEATHER CONDITIONS (Simulated Data):

Denver Metro: Clear, 68°F, Wind: W 5 mph, Visibility: 10 miles
Colorado Springs: Partly cloudy, 65°F, Wind: SW 8 mph
Grand Junction: Sunny, 72°F, Wind: Calm
Fort Collins: Clear, 66°F, Wind: NW 3 mph

No active weather warnings or watches for Colorado.
No severe weather expected through this evening.

Last updated: """ + get_current_mountain_time()['full']

        self.conditions_display.setPlainText(placeholder_weather)

    def update_announcements_display(self):
        """Update the announcements display"""
        announcements_text = "\n".join([f"• {ann}" for ann in self.net_data.weather_announcements])
        self.announcements_display.setPlainText(announcements_text)

    def change_theme(self, theme_name: str):
        """Change application theme"""
        self.theme_dark = (theme_name == "Dark")
        # Fix: Set current_theme to the actual theme dictionary, not a boolean
        self.current_theme = themes[theme_name.lower()]  # Assuming themes dict has lowercase keys
        self.apply_theme()

    def apply_theme(self):
        """Apply the selected theme"""
        if self.theme_dark:
            self.setStyleSheet("""
                QWidget {
                    background-color: #000000;
                    color: #ecf0f1;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #34495e;
                    border-radius: 8px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
                QLineEdit, QTextEdit, QSpinBox, QComboBox {
                    background-color: #34495e;
                    border: 2px solid #7f8c8d;
                    border-radius: 4px;
                    padding: 5px;
                    color: #ecf0f1;
                }
                QTabWidget::pane {
                    border: 1px solid #34495e;
                }
                QTabBar::tab {
                    background-color: #34495e;
                    color: #ecf0f1;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #3498db;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #2c3e50;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QLineEdit, QTextEdit, QSpinBox, QComboBox {
                    background-color: #ffffff;
                    border: 2px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 5px;
                }
                QTabWidget::pane {
                    border: 1px solid #bdc3c7;
                }
                QTabBar::tab {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)

    def select_font(self):
        """Select application font"""
        font, ok = QFontDialog.getFont(self.font(), self)
        if ok:
            self.setFont(font)
            self.status_bar.show_message("Font updated")

    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.theme_combo.setCurrentText("Dark")
            self.auto_save_cb.setChecked(True)
            self.confirm_exit_cb.setChecked(True)
            self.sound_alerts_cb.setChecked(False)
            self.default_callsign.setText(Config.DEFAULT_CALLSIGN)
            self.default_name.setText(Config.DEFAULT_NAME)
            self.default_location.setText(Config.DEFAULT_LOCATION)
            self.status_bar.show_message("Settings reset to defaults")

    def save_settings(self):
        """Save current settings"""
        try:
            self.settings.setValue("theme", self.theme_combo.currentText())
            self.settings.setValue("auto_save", self.auto_save_cb.isChecked())
            self.settings.setValue("confirm_exit", self.confirm_exit_cb.isChecked())
            self.settings.setValue("sound_alerts", self.sound_alerts_cb.isChecked())
            self.settings.setValue("default_callsign", self.default_callsign.text())
            self.settings.setValue("default_name", self.default_name.text())
            self.settings.setValue("default_location", self.default_location.text())
            self.settings.setValue("auto_advance", self.auto_advance)
            self.settings.setValue("auto_advance_delay", self.auto_advance_delay)

            self.status_bar.show_message("Settings saved successfully")
            logging.info("Settings saved")
        except Exception as e:
            self.status_bar.show_message(f"Failed to save settings: {e}", error=True)
            logging.error(f"Failed to save settings: {e}")

    def load_settings(self):
        """Load saved settings"""
        try:
            # Load theme
            theme = self.settings.value("theme", "Dark")
            self.theme_combo.setCurrentText(theme)
            self.theme_dark = (theme == "Dark")

            # Load behavior settings
            self.auto_save_cb.setChecked(self.settings.value("auto_save", True, type=bool))
            self.confirm_exit_cb.setChecked(self.settings.value("confirm_exit", True, type=bool))
            self.sound_alerts_cb.setChecked(self.settings.value("sound_alerts", False, type=bool))

            # Load default values
            self.default_callsign.setText(self.settings.value("default_callsign", Config.DEFAULT_CALLSIGN))
            self.default_name.setText(self.settings.value("default_name", Config.DEFAULT_NAME))
            self.default_location.setText(self.settings.value("default_location", Config.DEFAULT_LOCATION))

            # Load script settings
            self.auto_advance = self.settings.value("auto_advance", False, type=bool)
            self.auto_advance_delay = self.settings.value("auto_advance_delay", 30, type=int)
            self.auto_advance_cb.setChecked(self.auto_advance)
            self.delay_spinbox.setValue(self.auto_advance_delay)

            # Apply defaults to form fields
            if not self.callsign_input.text():
                self.callsign_input.setText(self.default_callsign.text())
            if not self.name_input.text():
                self.name_input.setText(self.default_name.text())
            if not self.location_input.text():
                self.location_input.setText(self.default_location.text())

            logging.info("Settings loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")

    def auto_save(self):
        """Auto-save session data"""
        if self.auto_save_cb.isChecked() and (
            self.callsign_input.text().strip() or
            self.name_input.text().strip() or
            self.location_input.text().strip()
        ):
            self.save_session(auto=True)

    def save_session(self, auto=False):
        """Save current session data"""
        if auto:
            # Auto-save to default location
            save_path = Config.CONFIG_DIR / "last_session.json"
        else:
            # Manual save with file dialog
            time_info = get_current_mountain_time()
            default_filename = f"SWO_Session_{time_info['datetime'].strftime('%Y%m%d_%H%M')}.json"

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Session", default_filename,
                "JSON Files (*.json);;All Files (*)"
            )

            if not save_path:
                return

        try:
            # Collect current data
            session_data = {
                'callsign': self.callsign_input.text().strip(),
                'name': self.name_input.text().strip(),
                'location': self.location_input.text().strip(),
                'logger_callsign': self.logger_callsign_input.text().strip(),
                'logger_name': self.logger_name_input.text().strip(),
                'weather_announcements': self.net_data.weather_announcements,
                'special_announcements': self.net_data.special_announcements,
                'timestamp': get_current_mountain_time()['datetime'].isoformat(),
                'version': Config.APP_VERSION
            }

            # Ensure directory exists
            if auto:
                Config.CONFIG_DIR.mkdir(exist_ok=True)

            # Save to file
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            if not auto:
                self.status_bar.show_message(f"Session saved to {save_path}")
                QMessageBox.information(self, "Session Saved", f"Session saved successfully to:\n{save_path}")

            logging.info(f"Session saved to {save_path}")

        except Exception as e:
            error_msg = f"Failed to save session: {e}"
            self.status_bar.show_message(error_msg, error=True)
            if not auto:
                QMessageBox.critical(self, "Save Error", error_msg)
            logging.error(error_msg)

    def load_session(self):
        """Load session data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Load data into form fields
            self.callsign_input.setText(session_data.get('callsign', ''))
            self.name_input.setText(session_data.get('name', ''))
            self.location_input.setText(session_data.get('location', ''))
            self.logger_callsign_input.setText(session_data.get('logger_callsign', ''))
            self.logger_name_input.setText(session_data.get('logger_name', ''))

            # Load weather announcements
            if 'weather_announcements' in session_data:
                self.net_data.weather_announcements = session_data['weather_announcements']
                self.weather_preview.setPlainText('\n'.join(self.net_data.weather_announcements))
                self.weather_status_label.setText(
                    f"Loaded announcements ({len(self.net_data.weather_announcements)} items)"
                )
                self.update_announcements_display()

            # Load special announcements
            if 'special_announcements' in session_data:
                self.net_data.special_announcements = session_data['special_announcements']

            self.status_bar.show_message("Session loaded successfully")
            QMessageBox.information(self, "Session Loaded", "Session data loaded successfully!")
            logging.info(f"Session loaded from {file_path}")

        except Exception as e:
            error_msg = f"Failed to load session: {e}"
            self.status_bar.show_message(error_msg, error=True)
            QMessageBox.critical(self, "Load Error", error_msg)
            logging.error(error_msg)

    def reset_fields(self):
        """Reset all form fields"""
        reply = QMessageBox.question(
            self, "Reset Fields",
            "Are you sure you want to reset all fields? This will clear all current data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear form fields
            self.callsign_input.clear()
            self.name_input.clear()
            self.location_input.clear()
            self.logger_callsign_input.clear()
            self.logger_name_input.clear()

            # Reset weather announcements to defaults
            self.net_data.weather_announcements = DEFAULT_SWO_ANNOUNCEMENTS.copy()
            self.net_data.special_announcements = []
            self.weather_preview.setPlainText('\n'.join(DEFAULT_SWO_ANNOUNCEMENTS))
            self.weather_status_label.setText(f"Using default announcements ({len(DEFAULT_SWO_ANNOUNCEMENTS)} items)")
            self.update_announcements_display()

            # Clear script
            self.sections = []
            self.section_idx = 0
            self.script_display.clear()
            self.script_display.setPlaceholderText("Generate the net script from the Setup tab to begin...")
            self.update_navigation()

            self.status_bar.show_message("All fields reset")

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
        """Handle application close event"""
        if self.confirm_exit_cb.isChecked():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Are you sure you want to exit the Colorado SWO Net Controller?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Save settings before exit
        self.save_settings()

        # Auto-save session if enabled
        if self.auto_save_cb.isChecked():
            self.auto_save()

        logging.info("Application closing")
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName(Config.APP_NAME)
    app.setApplicationVersion(Config.APP_VERSION)
    app.setOrganizationName(Config.ORGANIZATION)

    # Create and show main window
    window = SevereWeatherWindow()
    window.show()

    # Auto-load last session if it exists
    last_session_path = Config.CONFIG_DIR / "last_session.json"
    if last_session_path.exists():
        try:
            with open(last_session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Auto-populate fields if they're empty
            if not window.callsign_input.text() and session_data.get('callsign'):
                window.callsign_input.setText(session_data['callsign'])
            if not window.name_input.text() and session_data.get('name'):
                window.name_input.setText(session_data['name'])
            if not window.location_input.text() and session_data.get('location'):
                window.location_input.setText(session_data['location'])
            if not window.logger_callsign_input.text() and session_data.get('logger_callsign'):
                window.logger_callsign_input.setText(session_data['logger_callsign'])
            if not window.logger_name_input.text() and session_data.get('logger_name'):
                window.logger_name_input.setText(session_data['logger_name'])

            logging.info("Auto-loaded last session")
        except Exception as e:
            logging.warning(f"Could not auto-load last session: {e}")

    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
