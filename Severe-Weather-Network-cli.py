#!/usr/bin/env python3
"""
Colorado Severe Weather Network - Net Script Generator (CLI)
Generates a LaTeX document and compiles it to PDF without any GUI.

Usage:
    python Severe-Weather-Network-cli.py
    python Severe-Weather-Network-cli.py --callsign W0SWO --name "Alice" --location "Denver, CO"
    python Severe-Weather-Network-cli.py --output /path/to/output --tex-only
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pytz
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Config:
    APP_VERSION = "3.2.0 CLI"
    DEFAULT_CALLSIGN = os.environ.get('NET_CONTROL_CALLSIGN', 'NC2WX')
    DEFAULT_NAME     = os.environ.get('NET_CONTROL_NAME',     'Gary')
    DEFAULT_LOCATION = os.environ.get('NET_CONTROL_LOCATION', 'Pueblo West, Colorado')
    DEFAULT_LOGGER_CALLSIGN = os.environ.get('LOGGER_CALLSIGN', 'W7JPJ')
    DEFAULT_LOGGER_NAME     = os.environ.get('LOGGER_NAME',     'John')
    DEFAULT_LOGGER_LOCATION = os.environ.get('LOGGER_LOCATION', 'Denver, CO')
    NET_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def get_current_mountain_time() -> dict:
    try:
        mt = pytz.timezone('America/Denver')
        now = datetime.now(mt)
        return {
            'full':      now.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'date':      now.strftime('%A, %B %d, %Y'),
            'day':       now.strftime('%A'),
            'datetime':  now,
        }
    except Exception:
        now = datetime.now()
        return {
            'full':     now.strftime('%Y-%m-%d %H:%M:%S'),
            'date':     now.strftime('%A, %B %d, %Y'),
            'day':      now.strftime('%A'),
            'datetime': now,
        }

def is_net_day() -> bool:
    return get_current_mountain_time()['day'] in Config.NET_DAYS

# ---------------------------------------------------------------------------
# NWS text fetcher
# ---------------------------------------------------------------------------

class NWSTextFetcher:
    BASE_URL = "https://forecast.weather.gov/product.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Python NWS CLI Fetcher - Educational Use'})

    def fetch_text_product(self, wfo: str, product: str) -> Optional[str]:
        try:
            params = {'issuedby': wfo.upper(), 'product': product.upper(),
                      'site': wfo.lower(), 'format': 'txt'}
            r = self.session.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            pre = soup.find('pre')
            if pre:
                return pre.get_text()
            div = soup.find('div', {'class': 'glossaryProduct'}) or \
                  soup.find('div', {'id': 'textproduct'})
            if div:
                return div.get_text()
            return re.sub(r'\n\s*\n', '\n\n', re.sub('<.*?>', '', r.text)).strip()
        except Exception as e:
            logging.warning(f"Could not fetch {product} from {wfo}: {e}")
            return None

# ---------------------------------------------------------------------------
# Forecast text trimmer
# ---------------------------------------------------------------------------

class WeatherForecastTrimmer:

    def _trim(self, text: str, start_markers: List[str], end_triggers: List[str]) -> str:
        if not text or not text.strip():
            return ""
        lines = text.split('\n')
        start_idx, end_idx = 0, len(lines)

        for i, line in enumerate(lines):
            lu = line.strip().upper()
            if any(m in lu for m in start_markers):
                start_idx = i
                break

        for i in range(len(lines) - 1, start_idx, -1):
            ln = lines[i].strip()
            if ln == '$' or ln.startswith('&&') or \
               any(t in ln.upper() for t in end_triggers):
                end_idx = i
                break
            if ln:
                end_idx = i + 1
                break

        result = lines[start_idx:end_idx]
        while result and not result[0].strip():  result.pop(0)
        while result and not result[-1].strip(): result.pop()
        return '\n'.join(result).strip()

    def trim_afd(self, text: str) -> str:
        return self._trim(text,
            ['.KEY MESSAGES', '.DISCUSSION', '.SYNOPSIS', '.SHORT TERM',
             '.LONG TERM', '.AVIATION', '.MARINE', '.FIRE WEATHER'],
            [])

    def trim_hwo(self, text: str) -> str:
        return self._trim(text,
            ['THIS HAZARDOUS WEATHER OUTLOOK', 'HAZARDOUS WEATHER OUTLOOK IS FOR',
             '.DAY ONE', '.DAYS TWO THROUGH SEVEN'],
            ['SPOTTER'])

    def remove_between(self, text: str, start: str, end: str) -> str:
        pattern = re.escape(start) + '.*?' + re.escape(end)
        result = re.sub(pattern, '', text, flags=re.DOTALL)
        return re.sub(r'\n\s*\n', '\n\n', result).strip()

    def remove_aviation_forecast(self, text):
        return self.remove_between(text, ".AVIATION", "&&")

    def remove_remainder_gjt_forecast(self, text):
        return self.remove_between(text, ".GJT WATCHES/WARNINGS/ADVISORIES...", "TGJT")

    def remove_remainder_bou_forecast(self, text):
        return self.remove_between(text, ".BOU WATCHES/WARNINGS/ADVISORIES...", "AVIATION")

    def remove_remainder_gld_forecast(self, text):
        return self.remove_between(text, ".GLD WATCHES/WARNINGS/ADVISORIES...", "AVIATION")

    def remove_remainder_pub_forecast(self, text):
        return self.remove_between(text, ".PUB WATCHES/WARNINGS/ADVISORIES...", "AVIATION")

    def remove_remainder_cys_forecast(self, text):
        return self.remove_between(text, ".CYS WATCHES/WARNINGS/ADVISORIES...", "AVIATION")

    def remove_long_term_forecast(self, text):
        return self.remove_between(text, ".LONG TERM", "&&")

    def extract_key_messages(self, text: str) -> str:
        """Return only the .KEY MESSAGES block from an AFD, or a fallback message."""
        if not text:
            return "[Key messages unavailable]"
        lines = text.split('\n')
        in_section = False
        result = []
        for line in lines:
            if re.match(r'^\s*\.KEY MESSAGES', line, re.IGNORECASE):
                in_section = True
                result.append(line)
                continue
            if in_section:
                # A new section starts with a dot at the beginning of a line
                if re.match(r'^\s*\.[A-Z]', line) or line.strip() in ('&&', '$'):
                    break
                result.append(line)
        if not result:
            return "[No key messages found in today's AFD]"
        # Strip trailing blank lines
        while result and not result[-1].strip():
            result.pop()
        return '\n'.join(result).strip()

# ---------------------------------------------------------------------------
# Script section builder
# ---------------------------------------------------------------------------

def build_sections(callsign: str, name: str, location: str,
                   logger_callsign: str, logger_name: str, logger_location: str,
                   weather_announcements: Optional[List[str]] = None) -> List[tuple]:

    time_info = get_current_mountain_time()
    fetcher   = NWSTextFetcher()
    trimmer   = WeatherForecastTrimmer()
    sections  = []

    # --- Setup (NC operational notes — not read on air) ---
    sections.append(("Setup & Pre-Net Checklist", """\
NC: Please use a repeater with which you have a solid signal, since repeaters are usually much more \
reliable. If you have a hotspot, please use it ONLY as backup. Hotspots can be glitchy, which often \
results in frequent digital-side dropouts.

Timeouts are 3 minutes. Watch dashboards or select a countdown timer from your app store.

1235-1240...
1. Have Jon, Bryan or Bucky open SHL Dashboards (NC should also have them open):
   a. https://hubnm.skyhublink.com/allmon3/
   b. https://kg0sky.duckdns.org/allmon2/link.php?nodes=46079
   c. Open YSF Dashboard: http://ysfbridge.skyhublink.com/
2. In AllStar 485322 (Weather Hub): first DISCONNECT 289800, then CONNECT 41694.
3. IN 46079 CONNECT 41304 (WestCO N2KNK System, auto-disconnects at 1330.)

1240-45...
A. Logger or NC open Netlogger, promote the other. List NC and Logger callsigns.
B. Set "Net Official Status" for each and type same in "Remarks".
C. Logger, open Telegram CO Severe Weather Network chatroom. Under 'Check-ins' tab, paste "Net Open".
D. Run comms checks between NC and Logger, see that all dashboards light up.
   If not, contact Bucky @ 303-882-0095 or Jack @ 303-704-3290.

1250-1255... Announce:
"THE WEATHER OUTLOOK NET COVERING THE CENTRAL ROCKIES & HIGH PLAINS REGION WILL AIR ON THESE FREQUENCIES IN (minutes)."

[Open Net following Analog repeater IDs at the top of the hour]

AFTER NET CLOSE:
  In AllStar 485322 (Weather Hub): DISCONNECT 41694, CONNECT 289800.
  Close Dashboards."""))

    # --- Opening ---
    sections.append(("Opening", f"""\
Good afternoon and welcome to the Weather Outlook Net from the Colorado Severe Weather Network here on the \
Skyhub repeater-linking system; where we cover the Central Rockies and High Plains Region including the \
eastern UT border counties, CO, southeast WY, and Panhandle Nebraska. Todays Net Control is {name}, {callsign} located in {location}. \
Today's net logger is {logger_name}, {logger_callsign} located in {logger_location}.

This briefing airs Mondays thru Fridays at 1300 MT on the SkyHubLink.com system. Important alerts are \
also announced here as needed. During this net, we provide detailed information to Skywarn Storm Spotters for the National Weather \
Services with whom we are Core Partners in this Region. For those new to this net, we usually cover USA \
wx headlines, usually followed by Regional headlines. Then, we cover each NWS Forecast Office in our region.

This is a directed net, all traffic must pass thru Net Control unless otherwise instructed. Should there \
be an emergency, please key-in with 'break-break-break' and we'll suspend the net for your traffic. This \
is a linked system, so please key and wait 1.5 to 2 seconds before speaking and hang onto that PTT for \
an equal time afterward so that everyone hears your entire transmission.

The Severe Weather Network is on air in the CO Severe Weather Ops Room, Reflector xlx303a, when our region \
is under threat. When that occurs, your nearest repeaters will be connected to the room as needed. \
When the Severe Room is active, we will now be using Ham.Live in addition to Telegram. \
For details, visit our website at CSWN.net. \

[OPTIONAL — To access the Severe Weather Room at any time at Reflector XLX303a:]-
EchoLink NC2WX-L
Node 155536
Droid-STAR XRF/DCS303A
BM/DMR 31083
Allstar Weather Hub 485322 (preferred)
Allstar 289800 xlx303a
Wires-X Room 65045
YSF 30300 (switch to module A, DGID 10)
To monitor the CO Severe Rm go to hose.brandmeister.network, click the player upper right, type 31083."""))

    # --- Check-ins ---
    sections.append(("Check-ins", """\
WE'LL NOW TAKE OVER-THE-AIR CHECKINS FOR THE WEATHER OUTLOOK NET

Please give your callsign twice and — if you use phonetics — use only Standard ITU Phonetics.

If possible, use Netlogger.org or the CO Severe Weather Network chatroom on Telegram in the Check-in Tab. \
The more of you who can check in using them, the better, since the 1-hour allotment is precious.

[Check-ins should end by 1:12]

Western Slope of CO only: NW CO to I-70; I-70 to Hwy 50; Hwy 50 and south

Mobiles/portables only — callsign twice, please indicate which type you are.

Analog FM Stations, Analog FM — callsign twice.

Digital Stations, Digital only — callsign once. (Check YSF dashboard for callsign retrieval.)

Any other Check-ins, any mode, any location for the Weather Outlook Net? Callsign twice.

Thanks for being here with us today!

Consult your NWS homepage hazards map and DSS Packet for today's Warnings, Watches, and Advisories.
[Continue with Weather information]"""))

    # --- Regional ---
    sections.append(("Regional—Central Rockies/High Plains", """\
NOTE: Check the following resources for current regional conditions:

CONVECTIVE OUTLOOKS: https://www.spc.noaa.gov/products/outlook/
  - Review Day 1, Day 2, and Day 3 outlooks when applicable

FIRE WEATHER: https://www.spc.noaa.gov/products/fire_wx/overview.html
  - Review Day 1, Day 2, and Day 3 fire weather outlooks when applicable

EXCESSIVE RAINFALL: https://www.wpc.ncep.noaa.gov/qpf/excessive_rainfall_outlook_ero.php
  - Check Day 1, Day 2, and Day 3 excessive rainfall outlooks when applicable"""))

    # --- WFO sections ---
    wfo_configs = [
        ('GJT', 'Grand Junction',  'remove_remainder_gjt_forecast', 'forecast'),
        ('BOU', 'Boulder',          'remove_remainder_bou_forecast', 'forecast'),
        ('GLD', 'Goodland',         'remove_remainder_gld_forecast', 'forecast'),
        ('PUB', 'Pueblo',           'remove_remainder_pub_forecast', 'forecast'),
        ('CYS', 'Cheyenne',         'remove_remainder_cys_forecast', 'weather forecast'),
    ]

    for code, name_wfo, trim_method, area_label in wfo_configs:
        print(f"  Fetching {code} AFD...", end=' ', flush=True)
        afd_raw  = fetcher.fetch_text_product(code, 'AFD') or f"[AFD unavailable for {code}]"
        # clean    = trimmer.trim_afd(afd_raw)
        # clean    = trimmer.remove_aviation_forecast(clean)
        # clean    = trimmer.remove_long_term_forecast(clean)
        # clean    = getattr(trimmer, trim_method)(clean)
        clean    = trimmer.extract_key_messages(afd_raw)

        print("done")

        print(f"  Fetching {code} HWO...", end=' ', flush=True)
        hwo_raw  = fetcher.fetch_text_product(code, 'HWO') or f"[HWO unavailable for {code}]"
        hwo      = trimmer.trim_hwo(hwo_raw)
        print("done")

        time.sleep(0.5)   # be polite to NWS servers

        sections.append((f"{name_wfo} WFO", f"""\
The Area Forecast Discussion for the {name_wfo} {area_label} area:

{clean}

Hazardous Weather Outlook for the {name_wfo} {area_label} area:

{hwo}

Break for repeater reset.

"""))

    # --- Closing ---
    sections.append(("Closing", f"""\
NET CLOSE

At this time, we will take the last round of check-ins. Any other Check-ins, any mode, any location for the Weather Outlook Net? Come now with your callsign twice.

**Recap the Callsigns that have checked in today** once all have been called.
Call for any check-ins that were not acknowledged and any other check-ins

Thanks to all of you for your support and for playing your part on the Colorado Severe Weather Network \
team. We and the NWS appreciate all of you. Let's continue working together to keep amateur radio at the \
forefront of the SKYWARN program, for the benefit of the National Weather Service and public safety.

Visit our website and connect with us at CSWN.net. The legacy webpage will continue for the time being at \
skyhublink.com/wx-net. Follow the Colorado Severe Weather Network on Facebook. Email us at: CO.SEVERE.WX@gmail.com.

Many thanks to the Skyhublink.com System for the use of its many repeaters and for the Severe Weather Hub \
485322. Thanks also to the CO Digital Multiprotocol Group for Reflector xlx303a, home to the CO Severe \
Weather Ops Room. Visit them at ColoradoDigital.net. Thanks to the many other repeater owners who link \
here and to the Severe Weather Room for public safety during severe storm outbreaks.

[OPTIONAL — occasionally when time permits, read team listing:]
  - Gary Maier NC2WX — Coordinator, Colorado Severe Weather Network, NCS
  - Bucky Buckwalter W0SUN — Communications, IT, Digital Engineer, Weather Ops Support, Consultant
  - Jon Poindexter W5ALC — Technical Systems Specialist & Consultant, Web Design
  - Jay Wuensch AI7OF — Technical Support Consultant, Alternate Logger
  - Abraham Sandy WX0ABE — Director of Public Relations and Social Media
  - John Julian W7JPJ — Telegram Rooms Administrator, Primary Logger, Website Host
  - Bryan Gunsher K6SKI — Alternate CSWN NC, HF Weather Net NC
  - Terry Koelling AD0A — Weather Information Room / Telegram
  - Kathleen 'Kat' Hickman W0KPH — Consultant, Alternate Logger

For the Colorado Severe Weather Network, this is {name} closing the Weather Outlook Net. The systems are \
returned to open use. Have a great day! 73, {callsign} is clear.

POST-CLOSE STEPS:
1. In Netlogger, click "Close Net".
2. In AllStar 485322 (Weather Hub): DISCONNECT 41694, then CONNECT 289800.
3. In Netlogger, log the check-ins. Beginning with last check-in, right click on callsign, left click on "Log Contact"."""))

    return sections

# ---------------------------------------------------------------------------
# LaTeX generator
# ---------------------------------------------------------------------------

def linkify(text: str) -> str:
    """Escape a line of text for LaTeX, wrapping any URLs in \\url{} so
    they become clickable hyperlinks in the PDF (requires hyperref)."""
    url_re = re.compile(r'(https?://\S+)')
    parts  = url_re.split(text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:                  # this chunk is a URL
            # Strip trailing punctuation that belongs to the sentence, not the URL
            trail = ''
            while part and part[-1] in '.,;:)>\'\"':
                trail = part[-1] + trail
                part  = part[:-1]
            result.append(f'\\url{{{part}}}')
            if trail:
                result.append(escape_latex(trail))
        else:
            result.append(escape_latex(part))
    return ''.join(result)


def escape_latex(text: str) -> str:
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&',  r'\&'),
        ('%',  r'\%'),
        ('$',  r'\$'),
        ('#',  r'\#'),
        ('_',  r'\_'),
        ('{',  r'\{'),
        ('}',  r'\}'),
        ('~',  r'\textasciitilde{}'),
        ('^',  r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def generate_latex(sections: List[tuple], callsign: str, name: str,
                   location: str, logger_callsign: str, logger_name: str,
                   logger_location: str) -> str:

    time_info = get_current_mountain_time()
    date_str  = time_info['date']

    FORECAST_KEYWORDS = ['.key messages', '.short term', '.long term',
                         'forecast discussion', 'hazardous weather outlook']
    TOP_LEVEL = {'SETUP & PRE-NET CHECKLIST', 'OPENING', 'CHECK-INS', 'CLOSING',
                 'REGIONAL\u2014CENTRAL ROCKIES/HIGH PLAINS'}

    # Use placeholder tokens so the entire preamble stays a single raw string.
    # No Python backslash escaping fighting with LaTeX backslashes.
    HEADER_TEMPLATE = r"""\documentclass[11pt,letterpaper]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{microtype}
\usepackage{tcolorbox}
\usepackage{listings}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{xcolor}
\tcbuselibrary{skins,breakable}

\definecolor{primary}{RGB}{0,102,204}
\definecolor{secondary}{RGB}{102,51,153}
\definecolor{codebg}{RGB}{248,248,248}

\hypersetup{colorlinks=true,linkcolor=primary,urlcolor=primary}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textbf{Severe Weather Outlook Net}}
\fancyhead[R]{DATETOKEN}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}

\titleformat{\section}{\color{primary}\Large\bfseries}{\thesection}{1em}{}[\titlerule]
\titleformat{\subsection}{\color{secondary}\large\bfseries}{\thesubsection}{1em}{}
\titlespacing*{\section}{0pt}{1em}{0.5em}
\titlespacing*{\subsection}{0pt}{0.8em}{0.3em}

\newtcolorbox{commandbox}{colback=codebg,colframe=primary,
  fonttitle=\bfseries,title={NWS Forecast Text},breakable}

\lstdefinestyle{nws}{basicstyle=\small\ttfamily,
  backgroundcolor=\color{codebg},numbers=none,
  showstringspaces=false,breaklines=true,frame=single,
  rulecolor=\color{gray!30},tabsize=4}
\lstset{style=nws}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}

\title{\textbf{\Large Colorado Severe Weather Outlook Net Script}}
\author{Net Control: NCTOKEN \\
        Location:    LOCTOKEN \\
        Logger:      LOGTOKEN}
\date{DATETOKEN}

\begin{document}
\maketitle
\thispagestyle{fancy}
\tableofcontents
\newpage
"""

    header = (HEADER_TEMPLATE
              .replace('DATETOKEN', escape_latex(date_str))
              .replace('NCTOKEN',   escape_latex(f"{callsign} -- {name}"))
              .replace('LOCTOKEN',  escape_latex(location))
              .replace('LOGTOKEN',  escape_latex(f"{logger_callsign} -- {logger_name}, {logger_location}"))
              )

    body = ""
    for section_name, section_text in sections:
        su = section_name.upper()
        # Choose section depth
        if su in TOP_LEVEL or 'WFO' in su or su.startswith('REGIONAL'):
            body += f"\n\\section{{{escape_latex(section_name)}}}\n\n"
        else:
            body += f"\n\\subsection{{{escape_latex(section_name)}}}\n\n"

        is_forecast = any(k in section_text.lower() for k in FORECAST_KEYWORDS)

        if is_forecast or 'WFO' in su:
            body += "\\begin{commandbox}\n\\begin{lstlisting}[style=nws]\n"
            body += section_text.strip()
            body += "\n\\end{lstlisting}\n\\end{commandbox}\n\n"
        else:
            for line in section_text.split('\n'):
                stripped = line.strip()
                if not stripped:
                    body += "\n"
                elif stripped.endswith(':'):
                    body += f"\\textbf{{{escape_latex(stripped)}}}\n\n"
                else:
                    body += linkify(stripped) + "\n\n"

    footer = r"""
\vfill
\begin{center}
\textit{73 de Colorado Severe Weather Network}
\end{center}

\end{document}
"""
    return header + body + footer


# ---------------------------------------------------------------------------
# PDF compiler
# ---------------------------------------------------------------------------

def compile_pdf(latex_content: str, output_pdf: Path) -> bool:
    """Write LaTeX to a temp dir, run pdflatex twice, copy result."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tex_file = tmp_path / "net_script.tex"
        tex_file.write_text(latex_content, encoding='utf-8')

        for pass_num in range(1, 3):
            print(f"  pdflatex pass {pass_num}...", end=' ', flush=True)
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                 '-output-directory', str(tmp_path), str(tex_file)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print("FAILED")
                # Print the last few error lines from the log
                log_file = tmp_path / "net_script.log"
                if log_file.exists():
                    log_lines = log_file.read_text(errors='replace').split('\n')
                    errors = [l for l in log_lines if l.startswith('!') or 'Error' in l]
                    for e in errors[:10]:
                        print(f"    {e}")
                return False
            print("ok")

        pdf_src = tmp_path / "net_script.pdf"
        if not pdf_src.exists():
            print("  ERROR: pdflatex succeeded but no PDF found.")
            return False

        shutil.copy2(pdf_src, output_pdf)
        return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Colorado SWO Net Script as LaTeX/PDF (no GUI)"
    )
    p.add_argument('--callsign',          default=Config.DEFAULT_CALLSIGN)
    p.add_argument('--name',              default=Config.DEFAULT_NAME)
    p.add_argument('--location',          default=Config.DEFAULT_LOCATION)
    p.add_argument('--logger-callsign',   default=Config.DEFAULT_LOGGER_CALLSIGN)
    p.add_argument('--logger-name',       default=Config.DEFAULT_LOGGER_NAME)
    p.add_argument('--logger-location',   default=Config.DEFAULT_LOGGER_LOCATION)
    p.add_argument('--output', '-o',      default=None,
                   help="Output file path (without extension). Defaults to cwd with date stamp.")
    p.add_argument('--tex-only',          action='store_true',
                   help="Write .tex file only; do not run pdflatex")
    p.add_argument('--skip-nws',          action='store_true',
                   help="Skip NWS fetches (for testing layout offline)")
    return p.parse_args()


def main():
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    args = parse_args()

    time_info = get_current_mountain_time()
    stamp     = time_info['datetime'].strftime('%Y%m%d_%H%M')

    if args.output:
        base = Path(args.output)
    else:
        base = Path.cwd() / f"Colorado_SWO_Net_{stamp}"

    tex_path = base.with_suffix('.tex')
    pdf_path = base.with_suffix('.pdf')

    print(f"Colorado Severe Weather Network — Script Generator CLI")
    print(f"Net Control : {args.callsign} ({args.name}) @ {args.location}")
    print(f"Logger      : {args.logger_callsign} ({args.logger_name}) @ {args.logger_location}")
    print(f"Date        : {time_info['date']}")
    print()

    # Build sections
    print("Building script sections...")
    if args.skip_nws:
        # Stub out NWS sections for offline testing
        sections = build_sections.__wrapped__(args.callsign, args.name, args.location,
                                              args.logger_callsign, args.logger_name,
                                              args.logger_location) \
                   if hasattr(build_sections, '__wrapped__') else \
                   _offline_sections(args.callsign, args.name, args.location,
                                     args.logger_callsign, args.logger_name, args.logger_location)
    else:
        sections = build_sections(
            args.callsign, args.name, args.location,
            args.logger_callsign, args.logger_name, args.logger_location
        )
    print(f"  {len(sections)} sections built.")
    print()

    # Generate LaTeX
    print("Generating LaTeX...")
    latex = generate_latex(
        sections,
        args.callsign, args.name, args.location,
        args.logger_callsign, args.logger_name, args.logger_location
    )
    tex_path.write_text(latex, encoding='utf-8')
    print(f"  Written: {tex_path}")
    print()

    if args.tex_only:
        print("--tex-only set; skipping PDF compilation.")
        return

    # Compile PDF
    if not shutil.which('pdflatex'):
        print("WARNING: pdflatex not found in PATH. Skipping PDF compilation.")
        print(f"  You can compile manually: pdflatex {tex_path}")
        return

    print("Compiling PDF...")
    ok = compile_pdf(latex, pdf_path)
    if ok:
        print(f"  Written: {pdf_path}")
    else:
        print(f"  PDF compilation failed. The .tex source is still at: {tex_path}")
        sys.exit(1)


def _offline_sections(callsign, name, location, lcs, lname, lloc):
    """Minimal stub used with --skip-nws."""
    return [
        ("Setup & Pre-Net Checklist", "Test stub — NWS fetch skipped. See full script for setup steps."),
        ("Opening", f"Good afternoon and welcome to the Weather Outlook Net. Net Control: {name}, {callsign}."),
        ("Check-ins", "WE'LL NOW TAKE OVER-THE-AIR CHECKINS FOR THE WEATHER OUTLOOK NET\n[stub]"),
        ("Closing", f"For the Colorado Severe Weather Network, this is {name} closing the Weather Outlook Net. 73, {callsign} is clear."),
    ]


if __name__ == '__main__':
    main()
