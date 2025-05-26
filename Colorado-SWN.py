#!/usr/bin/env python3

import webbrowser
import subprocess
import sys
import threading
import json
import os
import time
from tkinter import (
    Tk, Label, LabelFrame, Button, Scrollbar, Canvas, Frame, Entry, StringVar,
    VERTICAL, RIGHT, LEFT, BOTH, Y, Toplevel, Text, END, filedialog, messagebox, Menu, simpledialog
)
import tkinter as tk

try:
    import requests
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET
    from PIL import Image, ImageTk
    from io import BytesIO
except Exception as e:
    print(f"Import error: {e.__class__.__name__}: {e}")
    sys.exit(1)

### --- Constants and config --- ###
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
    "Storm Prediction Center": {
        "SPC Outlooks": "https://www.spc.noaa.gov/products/outlook/",
        "SPC Mesoscale Discussions": "https://www.spc.noaa.gov/products/md/",
        "SPC Watches": "https://www.spc.noaa.gov/products/watch/",
        "SPC Storm Reports": "https://www.spc.noaa.gov/climo/reports/",
        "SPC Mesoanalysis": "https://www.spc.noaa.gov/exper/mesoanalysis/",
    },
    "Radar & Satellite": {
        "COD NEXRAD Viewer SW": "https://weather.cod.edu/satrad/?parms=regional-southwest-comp_radar-24-0-100-1&checked=map",
        "Ventusky Radar": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=radar",
        "NWS Enhanced Radar": "https://radar.weather.gov/",
        "Ventusky Satellite": "https://www.ventusky.com/?p=38.9972;-105.5478;6&l=satellite",
        "GOES Geocolor (Day/Night Composite)": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/latest.jpg",
        "GOES Sandwich RGB (Cloud Detail)": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/Sandwich/2500x1500.jpg",
        "GOES SLIDER (Interactive Viewer)": "https://rammb-slider.cira.colostate.edu/",
        "Zoom Earth": "https://zoom.earth/",
        "Tropical Tidbits Satellite": "https://www.tropicaltidbits.com/sat/satlooper.php?region=us&product=truecolor"
    },
    "Observations": {
        "Mesowest Observations": "https://mesowest.utah.edu/cgi-bin/droman/my_local_weather_station.cgi?stid=E9174&days=1",
        "MPing Reports": "https://mping.ou.edu/display/",
        "NWS EDD": "https://digital.weather.gov/",
    },
    "Forecast Tools": {
        "WPC QPF Forecast": "https://www.wpc.ncep.noaa.gov/qpf/qpf2.shtml",
        "NDFD Graphical Forecast": "https://digital.weather.gov/?zoom=6&lat=38.9972&lon=-105.5478&layers=F00BTTTFFTT&region=0&element=4&mxmz=false&barbs=false&subl=TFFFFF&units=english&wunits=nautical&coords=latlon&tunits=localt",
        "WPC Homepage": "https://www.wpc.ncep.noaa.gov/",
    },
    "Forecast Models": {
        "HRRR Model Viewer": "https://rapidrefresh.noaa.gov/hrrr/HRRR/",
        "NAM NEST Model": "https://mag.ncep.noaa.gov/model-guidance-model-area.php?group=Model Guidance&model=NAM NEST&area=CONUS&sector=conus&element=Precipitation&plot=REFC&timing=Most Recent",
        "COD Model Viewer": "https://weather.cod.edu/forecast/",
        "Tropical Tidbits": "https://www.tropicaltidbits.com/analysis/models/",
    },
    "Skywarn Spotter Resources": {
        "Skywarn Spotter's Field Guide": "https://www.weather.gov/spotterguide/",
        "Skywarn Spotter Checklist": "https://www.weather.gov/gjt/spotterchecklist"
    },
    "NWS Office Homepages": {
        "Grand Junction Homepage": "https://www.weather.gov/gjt/",
        "Boulder Homepage": "https://www.weather.gov/bou/",
        "Goodland Homepage": "https://www.weather.gov/gld/",
        "Pueblo Homepage": "https://www.weather.gov/pub/",
        "Cheyenne Homepage": "https://www.weather.gov/cys/",
    },
}

#############################
#  Helper: Config Loading   #
#############################
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
        print(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f)
    except Exception as e:
        print(f"Error saving config: {e}")

def log_error(msg):
    try:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{time.ctime()}: {msg}\n")
    except Exception:
        pass

#############################
#   Helper: Theme/Fonts     #
#############################
def get_font(cfg):
    return ("TkDefaultFont", cfg["font_size"])

def apply_theme(widget, theme, font_size=None):
    try:
        widget.configure(
            bg=theme["bg"],
            fg=theme["fg"],
            highlightbackground=theme["bg"]
        )
        if font_size:
            widget.configure(font=("TkDefaultFont", font_size))
    except Exception:
        pass

#############################
#   Helper: Tooltips        #
#############################
class ToolTip:
    def __init__(self, widget, text, theme, font_size):
        self.widget = widget
        self.text = text
        self.theme = theme
        self.font_size = font_size
        self.tipwindow = None
        widget.bind("<Enter>", self.showtip)
        widget.bind("<Leave>", self.hidetip)
        widget.bind("<Motion>", self.movetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=self.theme["status_bg"],
            foreground=self.theme["status_fg"],
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", self.font_size)
        )
        label.pack(ipadx=5, ipady=2)

    def hidetip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def movetip(self, event):
        if self.tipwindow:
            x = event.x_root + 10
            y = event.y_root + 10
            self.tipwindow.wm_geometry(f"+{x}+{y}")

#############################
#   Helper: Status Bar      #
#############################
class StatusBar(Frame):
    def __init__(self, master, theme, font_size):
        Frame.__init__(self, master, bg=theme["status_bg"])
        self.label = Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                           bg=theme["status_bg"], fg=theme["status_fg"],
                           font=("TkDefaultFont", font_size))
        self.label.pack(fill=tk.BOTH, expand=True)
        self.set("Ready.")

    def set(self, msg):
        self.label.config(text=msg)
        self.label.update_idletasks()

    def clear(self):
        self.set("")

#############################
#   Main Application        #
#############################
class WeatherToolkitApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.theme = themes[self.config["theme"]]
        self.font_size = self.config["font_size"]
        self.auto_refresh_mins = self.config["auto_refresh_mins"]
        self.window_geometry = self.config["window_geometry"]
        self.default_section = self.config["default_section"]
        self._loading = False

        self.root.title(APP_TITLE)
        self.root.geometry(self.window_geometry)
        self.root.minsize(1920, 1080)
        self.root.configure(bg=self.theme["bg"])

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Alt-q>", lambda e: self.safe_quit())
        self.root.bind("<Alt-c>", lambda e: self.fetch_colorado_alerts())
        self.root.bind("<Alt-u>", lambda e: self.fetch_us_alerts())
        self.root.bind("<Alt-g>", lambda e: self.show_satellite_image())
        self.root.bind("<F1>", lambda e: self.show_help())
        self.root.bind("<Control-s>", lambda e: self.open_settings())
        self.root.bind("<Configure>", self.save_window_geometry)

        self.create_menu()
        self.create_top_buttons()
        self.create_sections()
        self.create_status_bar()
        self.status("Ready.")

    #####################
    #   Menu Bar        #
    #####################
    def create_menu(self):
        self.menubar = Menu(self.root, bg=self.theme["bg"], fg=self.theme["fg"], tearoff=0)
#	filemenu = Menu(self.menubar, tearoff=0, bg=self.theme["bg"], fg=self.theme["fg"])
#	filemenu.add_command(label="Quit", command=self.safe_quit, accelerator="Alt+Q")
#	self.menubar.add_cascade(label="File", menu=filemenu)
        self.settings_menu = Menu(self.menubar, tearoff=0, bg=self.theme["bg"], fg=self.theme["fg"])
        self.settings_menu.add_command(label="Settings...", command=self.open_settings, accelerator="Ctrl+S")
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
        helpmenu = Menu(self.menubar, tearoff=0, bg=self.theme["bg"], fg=self.theme["fg"])
        helpmenu.add_command(label="Help", command=self.show_help, accelerator="F1")
        helpmenu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=helpmenu)
        self.root.config(menu=self.menubar)

    #####################
    #   Top Buttons     #
    #####################
    def create_top_buttons(self):
        self.top_frame = Frame(self.root, bg=self.theme["bg"])
        self.top_frame.pack(pady=10)
        self.quick_buttons = []
        b1 = Button(self.top_frame, text="Colorado Alerts (Alt+C)", command=self.fetch_colorado_alerts,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"], activeforeground=self.theme["button_active_fg"],
                cursor="hand2")
        b1.pack(side=LEFT, padx=5)
        ToolTip(b1, "Show current Colorado NWS alerts.", self.theme, self.font_size)
        self.quick_buttons.append(b1)

        b2 = Button(self.top_frame, text="US Alerts (Alt+U)", command=self.fetch_us_alerts,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"], activeforeground=self.theme["button_active_fg"],
                cursor="hand2")
        b2.pack(side=LEFT, padx=5)
        ToolTip(b2, "Show all US NWS alerts.", self.theme, self.font_size)
        self.quick_buttons.append(b2)

        b3 = Button(self.top_frame, text="GOES Snapshot (Alt+G)", command=self.show_satellite_image,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"], activeforeground=self.theme["button_active_fg"],
                cursor="hand2")
        b3.pack(side=LEFT, padx=5)
        ToolTip(b3, "Show latest GOES satellite image.", self.theme, self.font_size)
        self.quick_buttons.append(b3)

        b4 = Button(self.top_frame, text="Settings", command=self.open_settings,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"], activeforeground=self.theme["button_active_fg"],
                cursor="hand2")
        b4.pack(side=LEFT, padx=5)
        ToolTip(b4, "Open application settings.", self.theme, self.font_size)
        self.quick_buttons.append(b4)

        b5 = Button(self.top_frame, text="Help (F1)", command=self.show_help,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"], activeforeground=self.theme["button_active_fg"],
                cursor="hand2")
        b5.pack(side=LEFT, padx=5)
        ToolTip(b5, "Show help/documentation.", self.theme, self.font_size)
        self.quick_buttons.append(b5)

        b6 = Button(self.top_frame, text="Exit (Alt+Q)", command=self.safe_quit,
                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                activebackground="red", activeforeground="white", cursor="hand2")
        b6.pack(side=LEFT, padx=20)
        ToolTip(b6, "Exit the application.", self.theme, self.font_size)
        self.quick_buttons.append(b6)

    #####################
    #   Sections        #
    #####################
    def create_sections(self):
        self.section_frame = Frame(self.root, bg=self.theme["bg"])
        self.section_frame.pack(fill="both", expand=True)
        max_columns = (len(resources) + 1) // 3
        for i, (title, items) in enumerate(resources.items()):
            row = i // max_columns
            col = i % max_columns
            section = LabelFrame(self.section_frame, text=title,
                                 bg=self.theme["bg"], fg=self.theme["section_fg"],
                                 padx=8, pady=8, relief="ridge",
                                 font=("TkDefaultFont", self.font_size))
            section.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            inner_frame = Frame(section, bg=self.theme["bg"])
            inner_frame.pack()
            self.create_button_grid(inner_frame, title, items)
            self.section_frame.grid_rowconfigure(row, weight=1)
            self.section_frame.grid_columnconfigure(col, weight=1)

    def create_button_grid(self, window, section_title, items):
        frame = Frame(window, bg=self.theme["bg"])
        frame.pack()
        row = 0
        col = 0
        for name, link in items.items():
            cmd = self.make_resource_command(section_title, name, link)
            btn = Button(
                frame,
                text=name,
                width=28,
                height=1,
                command=cmd,
                bg=self.theme["button_bg"],
                fg=self.theme["button_fg"],
                activebackground=self.theme["button_active_bg"],
                activeforeground=self.theme["button_active_fg"],
                cursor="hand2",
                relief="groove",
                font=("TkDefaultFont", self.font_size)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            ToolTip(btn, f"Open: {name}", self.theme, self.font_size)
            col += 1
            if col >= 2:
                col = 0
                row += 1

    def make_resource_command(self, section_title, name, link):
        # Used to avoid late binding capture in lambda
        def cmd():
            if section_title == "Hazardous Weather Outlooks":
                self.show_hwo(link, name)
            elif section_title == "Area Forecast Discussions":
                self.show_afd(link, name)
            else:
                self.launch_item(link)
        return cmd

    #####################
    #   Status Bar      #
    #####################
    def create_status_bar(self):
        self.status_bar = StatusBar(self.root, self.theme, self.font_size)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def status(self, msg):
        self.status_bar.set(msg)

    #####################
    #   Settings        #
    #####################
    def open_settings(self):
        dialog = SettingsDialog(self.root, self.config, themes)
        self.root.wait_window(dialog.top)
        if dialog.result:
            # Update config, save, and apply settings
            self.config.update(dialog.result)
            save_config(self.config)
            self.theme = themes[self.config["theme"]]
            self.font_size = self.config["font_size"]
            self.auto_refresh_mins = self.config["auto_refresh_mins"]
            self.apply_all_theme()
            self.status("Settings updated.")

    def apply_all_theme(self):
        self.root.configure(bg=self.theme["bg"])
        for widget in self.root.winfo_children():
            try:
                widget.configure(bg=self.theme["bg"], fg=self.theme["fg"])
            except Exception:
                pass
        # Recreate all sections/buttons/status bar
        self.section_frame.destroy()
        self.create_sections()
        self.status_bar.destroy()
        self.create_status_bar()

    #####################
    #   About/Help      #
    #####################
    def show_about(self):
        msg = (
            f"{APP_TITLE}\nVersion: {APP_VERSION}\nAuthor: {APP_AUTHOR}\n\n"
            "A toolkit for quick access to weather resources for Colorado and the US.\n\n"
            "Keyboard shortcuts:\n"
            "  Alt+C: Colorado Alerts\n"
            "  Alt+U: US Alerts\n"
            "  Alt+G: GOES Snapshot\n"
            "  Ctrl+S: Settings\n"
            "  F1: Help\n"
            "  Alt+Q: Exit"
        )
        messagebox.showinfo("About", msg)

    def show_help(self):
        help_text = (
            "=== Colorado Severe Weather Network Toolkit Help ===\n\n"
            "Quickly access hazardous weather outlooks, forecast discussions, "
            "radar/satellite imagery, observations, models, and more.\n\n"
            "Main Features:\n"
            "• Keyboard navigation (Tab, Shift+Tab, Enter)\n"
            "• Hotkeys for all main actions (see About)\n"
            "• Right-click to copy text in alert popups\n"
            "• Save/copy all AFD, HWO, or alert info\n"
            "• Auto-refresh and filter/search for alerts\n"
            "• Tooltips on all buttons\n"
            "• Choice of dark or light theme, font size\n"
            "• Status bar for tips, errors, loading\n"
            "• Remembers window size and settings\n\n"
            f"Contact: {AUTHOR_EMAIL}"
        )
        HelpDialog(self.root, help_text, self.theme, self.font_size)

    #####################
    #   Window Save     #
    #####################
    def save_window_geometry(self, event=None):
        try:
            geom = self.root.geometry()
            if "x" in geom and "+" in geom:
                self.config["window_geometry"] = geom
                save_config(self.config)
        except Exception:
            pass

    #####################
    #   Exit/Closing    #
    #####################
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.save_window_geometry()
            self.root.destroy()

    def safe_quit(self):
        self.on_closing()

    #####################
    #   Resource Launch #
    #####################
    def launch_item(self, item):
        try:
            self.status(f"Opening: {item}")
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", item])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", item])
            else:
                webbrowser.open(item)
        except Exception as e:
            log_error(f"Error launching: {e}")
            self.status(f"Error launching: {e}")
            messagebox.showerror("Error launching resource", f"Error launching: {e}")

    #####################
    #   Text Popups     #
    #####################
    def show_afd(self, url, title):
        self._show_text_popup(url, title, "AFD", parse_pre=True)

    def show_hwo(self, url, title):
        self._show_text_popup(url, title, "HWO", parse_pre=True)

    def _show_text_popup(self, url, title, typ, parse_pre=False):
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

    #####################
    #   Satellite Image #
    #####################
    def show_satellite_image(self):
        popup = Toplevel(self.root)
        popup.title("GOES Snapshot")
        popup.geometry("1240x720")
        popup.configure(bg=self.theme["bg"])
        stat_label = Label(popup, text="Loading image...", 
                           bg=self.theme["bg"], fg=self.theme["accent"],
                           font=("TkDefaultFont", self.font_size))
        stat_label.pack(pady=6)
        img_label = Label(popup, bg=self.theme["bg"])
        img_label.pack(expand=True, fill=BOTH)
        Button(popup, text="Close (Esc)", command=popup.destroy,
               bg=self.theme["button_bg"], fg=self.theme["button_fg"]).pack(pady=8)
        self._popup_bindings(popup, img_label)
        def fetch_img():
            try:
                url = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/latest.jpg"
                response = requests.get(url, timeout=10)
                img = Image.open(BytesIO(response.content))
                img.thumbnail((1200, 675))
                photo = ImageTk.PhotoImage(img)
            except Exception as e:
                log_error(f"Image load error: {e}")
                photo = None
            def show_img():
                if photo:
                    img_label.config(image=photo)
                    img_label.image = photo
                    stat_label.config(text="GOES Snapshot loaded.")
                else:
                    img_label.config(text="Image failed to load.")
            self.root.after(0, show_img)
        threading.Thread(target=fetch_img, daemon=True).start()

    #####################
    #   Alert Windows   #
    #####################
    def fetch_colorado_alerts(self):
        url = "https://alerts.weather.gov/cap/co.php?x=0"
        self._fetch_alerts(url, "Active Colorado Alerts")

    def fetch_us_alerts(self):
        url = "https://api.weather.gov/alerts/active.atom"
        self._fetch_alerts(url, "Active US Alerts")

    def _fetch_alerts(self, url, window_title):
        theme = self.theme
        font_size = self.font_size
        popup = Toplevel(self.root, bg=theme["bg"])
        popup.title(window_title)
        popup.geometry("950x700")
        popup.resizable(True, True)
        # Accessibility and status
        hint = Label(popup, text="Tip: Search for specific keywords.",
                     bg=theme["bg"], fg=theme["accent"], font=("TkDefaultFont", font_size))
        hint.pack(pady=(6, 0))
        # Search/filter
        search_var = StringVar()
        search_frame = Frame(popup, bg=theme["bg"])
        search_frame.pack(pady=5)
        Label(search_frame, text="Filter alerts: ", bg=theme["bg"], fg=theme["fg"]).pack(side=LEFT)
        search_entry = Entry(search_frame, textvariable=search_var, width=40, bg=theme["entry_bg"],
                             fg=theme["entry_fg"], insertbackground=theme["entry_insert"], font=("TkDefaultFont", font_size))
        search_entry.pack(side=LEFT)
        Button(search_frame, text="Refresh Now", command=lambda: load_alerts(), 
               bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=LEFT, padx=12)

        # Status label
        stat_label = Label(popup, text="Loading alerts...", bg=theme["bg"], fg=theme["accent"],
                           font=("TkDefaultFont", font_size))
        stat_label.pack(pady=2)
        # Text area
        text_area = Text(popup, wrap="word", bg=theme["bg"], fg=theme["fg"],
                         font=("TkDefaultFont", font_size))
        text_area.pack(expand=True, fill=BOTH, padx=10, pady=10)
        text_area.config(state="disabled")
        self._add_context_menu(text_area)
        # Bottom controls
        ctrl = Frame(popup, bg=theme["bg"])
        ctrl.pack(fill=tk.X)
        Button(ctrl, text="Copy All", command=lambda: self.copy_to_clipboard(text_area.get(1.0, END)),
               bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=LEFT, padx=5)
        Button(ctrl, text="Save As...", command=lambda: self.save_text_to_file(text_area.get(1.0, END)),
               bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=LEFT, padx=5)
        Button(ctrl, text="Close (Esc)", command=popup.destroy,
               bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=RIGHT, padx=5)
        self._popup_bindings(popup, text_area)
        # Internal state
        entries = []
        last_update = [""]
        # Load alerts
        def load_alerts():
            stat_label.config(text="Loading alerts...")
            self.status("Loading alerts...")
            def run_fetch():
                try:
                    response = requests.get(url, timeout=12)
                    rootx = ET.fromstring(response.content)
                    entries.clear()
                    entries.extend(rootx.findall("{http://www.w3.org/2005/Atom}entry"))
                    last_update[0] = time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    log_error(f"Error fetching alerts: {e}")
                    entries.clear()
                    last_update[0] = ""
                self.root.after(0, apply_filter)
            threading.Thread(target=run_fetch, daemon=True).start()
        # Filtering/highlight
        def apply_filter(*args):
            term = search_var.get().lower()
            text_area.config(state="normal")
            text_area.delete(1.0, END)
            grouped_alerts = {}
            for i, entry in enumerate(entries):
                title = entry.find("{http://www.w3.org/2005/Atom}title").text
                summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
                link = entry.find("{http://www.w3.org/2005/Atom}link").attrib.get("href")
                area = entry.find("{urn:oasis:names:tc:emergency:cap:1.1}areaDesc")
                counties = [c.strip() for c in area.text.split(';')] if area is not None and area.text else ["Unknown Area"]
                if title and summary:
                    if term in title.lower() or term in summary.lower():
                        for county in counties:
                            grouped_alerts.setdefault(county, []).append((title, summary, link))
            link_counter = 0
            # Alert tags
            text_area.tag_config("warning", foreground=theme["warning"], font=("TkDefaultFont", font_size, "bold"))
            text_area.tag_config("watch", foreground=theme["watch"])
            text_area.tag_config("advisory", foreground=theme["advisory"])
            text_area.tag_config("county", foreground=theme["county"], font=("TkDefaultFont", font_size, "bold"))
            text_area.tag_config("highlight", background="#204060", foreground="yellow")
            for county, alerts in grouped_alerts.items():
                text_area.insert(END, f"=== {county} ===\n", "county")
                for title, summary, link in alerts:
                    tag = "warning" if "warning" in title.lower() else "watch" if "watch" in title.lower() else "advisory" if "advisory" in title.lower() else ""
                    text_area.insert(END, f"Title: {title}\n", tag)
                    # Highlight filter term in title/summary
                    if term and term in title.lower():
                        start = f"{float(text_area.index(END))-2} linestart + 7c"
                        end = f"{start} + {len(title)}c"
                        text_area.tag_add("highlight", start, end)
                    text_area.insert(END, f"Summary: {summary}\n")
                    if term and term in summary.lower():
                        idx = text_area.search(term, f"{float(text_area.index(END))-2} linestart", END, nocase=1)
                        if idx:
                            text_area.tag_add("highlight", idx, f"{idx}+{len(term)}c")
                    # Link
                    start_index = text_area.index(END)
                    text_area.insert(END, f"Link: {link}\n\n")
                    end_index = text_area.index(END)
                    tag_name = f"link_{link_counter}"
                    text_area.tag_add(tag_name, f"{start_index} linestart", f"{end_index} linestart")
                    text_area.tag_config(tag_name, foreground="blue", underline=1)
                    # Lambda must bind current link!
                    def make_open(url):
                        return lambda e, url=url: webbrowser.open(url)
                    text_area.tag_bind(tag_name, "<Button-1>", make_open(link))
                    link_counter += 1
            text_area.config(state="disabled")
            stat_label.config(text=f"Alerts loaded. Last update: {last_update[0]}")
            self.status(f"{window_title} loaded at {last_update[0]}")
        # Save/restore filter focus, keyboard navigation
        search_entry.focus_set()
        search_entry.bind("<Return>", lambda e: apply_filter())
        popup.bind("<Escape>", lambda e: popup.destroy())
        search_var.trace_add("write", lambda *a: apply_filter())
        # Auto-refresh
        def refresher():
            load_alerts()
            popup.after(self.auto_refresh_mins * 60000, refresher)
        refresher()
        self.status(f"{window_title} opened.")
        # Context menu
        self._add_context_menu(text_area)

    #####################
    #   Clipboard/Save  #
    #####################
    def copy_to_clipboard(self, s):
        self.root.clipboard_clear()
        self.root.clipboard_append(s)
        self.status("Copied to clipboard.")

    def save_text_to_file(self, s):
        filetypes = [("Text Files", "*.txt"), ("All Files", "*.*")]
        fname = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=filetypes)
        if fname:
            try:
                with open(fname, "w") as f:
                    f.write(s)
                self.status(f"Saved to {fname}")
            except Exception as e:
                log_error(f"Save error: {e}")
                messagebox.showerror("Save Error", f"Could not save file: {e}")
                self.status("Save failed.")

    #####################
    #   Context Menu    #
    #####################
    def _add_context_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Copy All", command=lambda: self.copy_to_clipboard(widget.get(1.0, END)))
        def context(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        widget.bind("<Button-3>", context)
        widget.bind("<Control-c>", lambda e: self.copy_to_clipboard(widget.get(1.0, END)))

    #####################
    #   Popup Bindings  #
    #####################
    def _popup_bindings(self, popup, widget):
        widget.focus_set()
        popup.bind("<Escape>", lambda e: popup.destroy())
        popup.bind("<Control-c>", lambda e: self.copy_to_clipboard(widget.get(1.0, END)))


#############################
#   Settings Dialog         #
#############################
class SettingsDialog:
    def __init__(self, master, config, themes):
        self.result = None
        self.top = Toplevel(master)
        self.top.title("Settings")
        self.top.transient(master)
        self.top.grab_set()
        self.theme = themes[config["theme"]]
        self.top.configure(bg=self.theme["bg"])
        Label(self.top, text="Theme:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w", padx=8, pady=5)
        self.theme_var = StringVar(value=config["theme"])
        tk.OptionMenu(self.top, self.theme_var, *themes.keys()).grid(row=0, column=1, sticky="e", padx=8, pady=5)
        Label(self.top, text="Font Size:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, sticky="w", padx=8, pady=5)
        self.font_var = StringVar(value=str(config["font_size"]))
        tk.OptionMenu(self.top, self.font_var, "10", "12", "14", "16", "18", "20").grid(row=1, column=1, sticky="e", padx=8, pady=5)
        Label(self.top, text="Auto-refresh Alerts (mins):", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=2, column=0, sticky="w", padx=8, pady=5)
        self.refresh_var = StringVar(value=str(config.get("auto_refresh_mins", 5)))
        tk.OptionMenu(self.top, self.refresh_var, "2", "5", "10", "15", "30").grid(row=2, column=1, sticky="e", padx=8, pady=5)
        Label(self.top, text="Default Section:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=3, column=0, sticky="w", padx=8, pady=5)
        self.section_var = StringVar(value=config.get("default_section", ""))
        tk.Entry(self.top, textvariable=self.section_var).grid(row=3, column=1, sticky="e", padx=8, pady=5)
        btn = Button(self.top, text="Save", command=self.save, bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        btn.grid(row=4, column=0, columnspan=2, pady=12)
        self.top.bind("<Return>", lambda e: self.save())
        self.top.bind("<Escape>", lambda e: self.top.destroy())
        btn.focus_set()

    def save(self):
        self.result = {
            "theme": self.theme_var.get(),
            "font_size": int(self.font_var.get()),
            "auto_refresh_mins": int(self.refresh_var.get()),
            "default_section": self.section_var.get(),
        }
        self.top.destroy()

#############################
#   Help Dialog             #
#############################
class HelpDialog:
    def __init__(self, master, text, theme, font_size):
        top = Toplevel(master)
        top.title("Help")
        top.configure(bg=theme["bg"])
        l = Label(top, text=text, bg=theme["bg"], fg=theme["help_fg"], justify="left", font=("TkDefaultFont", font_size))
        l.pack(expand=True, fill=BOTH, padx=16, pady=16)
        Button(top, text="Close (Esc)", command=top.destroy,
               bg=theme["button_bg"], fg=theme["button_fg"]).pack(pady=10)
        top.bind("<Escape>", lambda e: top.destroy())
        l.focus_set()

#############################
#   Main Entrypoint         #
#############################
def main():
    root = Tk()
    def toggle_fullscreen(event):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False)) # Optional: Exit fullscreen on Escape

    app = WeatherToolkitApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
