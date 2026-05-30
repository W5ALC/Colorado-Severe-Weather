#!/usr/bin/env python3
"""
CSWN Letter Batch Generator - GUI Version
PyQt6 interface for generating personalized letters
"""

import subprocess
import os
import sys
import platform
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
                             QHeaderView, QCheckBox, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

# CSWN class file content (same as before)
CSWN_CLASS = r"""%
% CSWNletter.cls
% This class based on "brownletter.cls" Copyright 2003, Nesime Tatbul (tatbul@cs.brown.edu)
%
% New version modifications by MincooLee(mincoolee@gmail.com) based on CSWN template, 18 December 2021

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{CSWN}
\RequirePackage{graphicx}
\RequirePackage{epstopdf}
\RequirePackage{epsfig}
\RequirePackage{ifthen}
\RequirePackage{xcolor}
\definecolor{slcolor}{HTML}{882B21}
\DeclareGraphicsExtensions {.png}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{letter}}
\ProcessOptions
\LoadClass[letterpaper]{letter}

\newcommand{\subjectname}{Subject}
\newcommand{\@subject}{}
\newcommand{\subject}[1]{\renewcommand{\@subject}{\subjectname: #1}}

\newboolean{logofound}
\IfFileExists{CSWN-logo-BRAND.png}
    {\setboolean{logofound}{true}}
    {\setboolean{logofound}{false}}

\setlength{\textwidth}{7.25in}
\setlength{\textheight}{7.5in}
\setlength{\topskip}{0.0in}
\setlength{\footskip}{0.5in}
\setlength{\oddsidemargin}{-0.25in}
\setlength{\evensidemargin}{-0.25in}
\setlength{\topmargin}{-0.875in}

\DeclareFixedFont{\xcmrbn}{OT1}{cmr}{b}{n}{10}
\DeclareFixedFont{\xcmrmn}{OT1}{cmr}{m}{n}{10}
\DeclareFixedFont{\ixcmrmn}{OT1}{cmr}{m}{n}{9}

\newsavebox{\departmenthead}
\newsavebox{\departmentfoot}
\newsavebox{\emptyfoot}

\sbox{\departmenthead}{
    \begin{tabular*}{\textwidth}
                    {@{}l@{\extracolsep{0.0in}}@{\extracolsep{0.125in}}l@{}}
    \parbox{4.15in}
    {\raggedright
        \ifthenelse{\boolean{logofound}}
           {\epsfig{file=CSWN-logo-BRAND.png, height=1.75in}}
           {\parbox[t][1.0in][t]{2.0in}{\hfill}
            \ClassWarning{CSWN}{CSWN-logo-BRAND.png COULD NOT BE FOUND!}}
    } &
    \parbox[c][1.8in][c]{1.225in}{{~}\\
}\\
    # \end{tabular*}
}

\savebox{\emptyfoot}[\textwidth][c]{\ixcmrmn
    \hspace*{\textwidth}
}

\renewcommand{\ps@firstpage}{
    \setlength{\headheight}{1.375in}
    \setlength{\headsep}{1.0in}
    \renewcommand{\@oddhead}{\usebox{\departmenthead}}
    \renewcommand{\@oddfoot}{\usebox{\departmentfoot}}
    \renewcommand{\@evenhead}{}
    \renewcommand{\@evenfoot}{}
}

\renewcommand{\ps@empty}{
    \setlength{\headheight}{1.375in}
    \setlength{\headsep}{0.15in}
    \renewcommand{\@oddhead}{}
    \renewcommand{\@oddfoot}{\usebox{\emptyfoot}}
    \renewcommand{\@evenhead}{}
    \renewcommand{\@evenfoot}{\usebox{\emptyfoot}}
}

\providecommand{\@evenhead}{}
\providecommand{\@oddhead}{}
\providecommand{\@evenfoot}{}
\providecommand{\@oddfoot}{}

\pagestyle{empty}

\renewcommand{\opening}[1]{\thispagestyle{firstpage}%
    \ifx\@empty\fromaddress
    \else
        {\raggedleft
            \begin{tabular}{l@{}}\ignorespaces
            \fromaddress \\ *[1\parskip]%
            \end{tabular}\par
        }%
     \fi
     \vspace{-6\parskip}
     \@date \vspace{2\parskip}\\
     {\raggedright \toname \\ \toaddress \par}%
     \vspace{1\parskip}%
     \ifthenelse{\equal{\@subject}{}}{}{\@subject\par}
     \vspace{1\parskip}%
     #1\par\nobreak
}

\renewcommand{\closing}[1]{\par\nobreak\vspace{\parskip}%
    \stopbreaks
    \noindent
    \hspace*{0.6\textwidth}\parbox{0.4\textwidth}{\raggedright
    \ignorespaces #1\\[4\medskipamount]%
    \ifx\@empty\fromsig
        \fromname
    \else \fromsig 
    \fi\strut}%
    \par
}
"""

# LaTeX template header (same as before)
LATEX_HEADER = r"""\documentclass[12pt]{CSWN}
\usepackage{fontspec}
\usepackage{hyperref} 
\usepackage{tikz} 
\usepackage{xcolor}
\definecolor{HITblue}{RGB}{139, 0, 0}
\usepackage{lipsum}
\RequirePackage{fancyhdr}
\usepackage{lastpage}
\usepackage{background}
\usepackage{eso-pic}
\usepackage[base]{babel}

% Configure hyperref
\hypersetup{
	pdfauthor={},
	pdftitle={},
	colorlinks=true,
	linkcolor=blue,
	urlcolor=blue,
	citecolor=blue
}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\rhead{Page \thepage \hspace{1pt} of \pageref{LastPage}}

\backgroundsetup{
	scale=1,
	angle=0,
	opacity=0.1,
	position=current page.center,  % or "current page.north", "current page.south", etc.
	vshift=0cm,  % Vertical shift
	hshift=0cm,  % Horizontal shift
	contents={%
		\includegraphics[height=0.85\paperheight]{CSWN-logo-BRAND.png}
	}
}

\makeatletter
\def\parsecomma#1,#2\endparsecomma{\def\page@x{#1}\def\page@y{#2}}
\tikzdeclarecoordinatesystem{page}{
    \parsecomma#1\endparsecomma
    \pgfpointanchor{current page}{north east}
    \pgf@xc=\pgf@x%
    \pgf@yc=\pgf@y%
    \pgfpointanchor{current page}{south west}
    \pgf@xb=\pgf@x%
    \pgf@yb=\pgf@y%
    \pgfmathparse{(\pgf@xc-\pgf@xb)/2.*\page@x+(\pgf@xc+\pgf@xb)/2.}
    \expandafter\pgf@x\expandafter=\pgfmathresult pt
    \pgfmathparse{(\pgf@yc-\pgf@yb)/2.*\page@y+(\pgf@yc+\pgf@yb)/2.}
    \expandafter\pgf@y\expandafter=\pgfmathresult pt
}
\makeatother

\def\name{Gary Maier\\
            NC2WX\\
            Severe Weather Coordinator\\
            Colorado Severe Weather Network
}

\def\Where{\hspace{-1.2mm}\textbf{\color{HITblue}
Colorado Severe Weather Network
}} 

\def\Address{{\fontsize{9.5pt}{11pt}\selectfont "Providing Ground Truth Under the Radar"}}

\def\Email{\textbf{\color{HITblue}E-mail}: \href{{mailto:CO.SEVERE.WX@gmail.com}}{{CO.SEVERE.WX@gmail.com}}}

\def\TEL{\textbf{\color{HITblue}Phone}: (719) 281 0693}
\def\SITE{\textbf{\color{HITblue}Website}: \href{https://www.cswn.net}{CSWN.net}}

\def\school{\small{
  HIT $\cdot$
     ~School of Computing $\cdot$
     ~No.92, Xidazhi Street $\cdot$
     ~Harbin, China P.R} } 

\signature{ 
\vspace{-1mm} \vspace{.5cm} \vspace{2mm}
\name}

\date{\vspace{10mm} Invitation to partner with the Colorado Severe Weather Network}

\begin{document}
"""

def generate_letter_body(owner, callsign):
    return rf"""
\begin{{letter}}{{}}

\address{{}}

\def\newaddress{{
\Where \\
\Address \\
\TEL \\
\Email\\
\SITE
}}

\begin{{tikzpicture}}[remember picture,overlay,every node/.style={{anchor=center}}]
    \node[text width=7cm] at (page cs:0.5,0.73){{\small \newaddress}};
\end{{tikzpicture}}

\opening{{Dear {owner},}}


I am writing on behalf of the Colorado Severe Weather Network (CSWN), a SKYWARN$^{{\tiny{{\textregistered}}}}$ Trained Amateur Radio Support (STARS) Team, to invite you to partner with us in building a unified SKYWARN$^{{\tiny{{\textregistered}}}}$ amateur radio network across the South-Central Rockies \& High Plains Region immediately surrounding Colorado. We have a proven track record with six NWS offices throughout the region.

Our mission is to provide reliable and prompt delivery of vital ground truth from SKYWARN$^{{\tiny{{\textregistered}}}}$ storm spotters to the National Weather Service, in accordance with its severe criteria and in support of its mission to protect lives and property during severe weather. To generate an interest in—and understanding of—weather phenomena; and to promote NWS SKYWARN$^{{\tiny{{\textregistered}}}}$ training and participation within an all-inclusive environment. To ensure that amateur radio plays a vital and strategic role within the SKYWARN$^{{\tiny{{\textregistered}}}}$ program.

Your repeater {callsign} serves a critical area for severe weather communication. We would like to explore how the CSWN and your repeater might collaborate to strengthen SKYWARN$^{{\tiny{{\textregistered}}}}$ operations and enhance storm reporting capabilities. This could include coordinating weather nets, sharing NWS alerts, fielding severe reports to the NWS, or other approaches that align with your repeater's mission.

We respect your repeater's autonomy and operational needs. Any partnership would be developed collaboratively to serve both our networks, the general public and the NWS effectively.

I would welcome the opportunity to discuss this further at your convenience. Please contact me at 719-281-0693, \href{{mailto:Weather.NC2WX@gmail.com}}{{Weather.NC2WX@gmail.com}} or \href{{mailto:CO.SEVERE.WX@gmail.com}}{{CO.SEVERE.WX@gmail.com}}.

Thank you for considering this partnership and for your service to the amateur radio community.

\closing{{73,}}

\end{{letter}}
"""


class CompileThread(QThread):
    """Background thread for LaTeX compilation"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, letters, output_path):
        super().__init__()
        self.letters = letters
        self.output_path = output_path
    
    def run(self):
        try:
            tex_filename = self.output_path + ".tex"
            
            # Generate LaTeX file
            self.progress.emit("Generating LaTeX file...")
            with open(tex_filename, 'w') as f:
                f.write(LATEX_HEADER)
                for letter in self.letters:
                    f.write(generate_letter_body(letter['owner'], letter['callsign']))
                f.write("\n\\end{document}\n")
            
            # Compile twice for page numbering
            self.progress.emit("Compiling PDF (pass 1/2)...")
            for i in range(2):
                self.progress.emit(f"Compiling PDF (pass {i+1}/2)...")
                result = subprocess.run(
                    ['lualatex', '-interaction=nonstopmode', tex_filename],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(tex_filename) or '.'
                )
                
                if result.returncode != 0:
                    self.finished.emit(False, f"LaTeX compilation failed:\n{result.stdout}")
                    return
            
            # Cleanup
            self.progress.emit("Cleaning up...")
            base = self.output_path
            for ext in ['.aux', '.log', '.out', '.fdb_latexmk', '.fls', '.synctex.gz']:
                try:
                    os.remove(base + ext)
                except:
                    pass
            
            self.finished.emit(True, self.output_path + ".pdf")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class CSWNLetterGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.letters = []
        self.init_ui()
        self.check_requirements()
    
    def init_ui(self):
        self.setWindowTitle("CSWN Letter Batch Generator")
        self.setGeometry(100, 100, 1000, 800)
        self.setMinimumSize(800, 600)
        
        # Apply modern stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1d29;
            }
            QWidget {
                background-color: #1a1d29;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #2d3142;
                border: 2px solid #3d4152;
                border-radius: 8px;
                padding: 10px 8px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #4a90e2;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #323546;
            }
            QLineEdit::placeholder {
                color: #7a7e8f;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #5ba3f5;
            }
            QPushButton:pressed {
                background-color: #3a7bc8;
            }
            QPushButton:disabled {
                background-color: #3d4152;
                color: #7a7e8f;
            }
            QPushButton#deleteBtn {
                background-color: #e74c3c;
                padding: 6px 12px;
                min-height: 15px;
                min-width: 80px;
            }
            QPushButton#deleteBtn:hover {
                background-color: #ff6b5a;
            }
            QPushButton#secondaryBtn {
                background-color: #5d6578;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #6d7588;
            }
            QPushButton#generateBtn {
                background-color: #4a90e2;
                font-size: 15px;
                font-weight: 700;
                min-height: 50px;
                letter-spacing: 1px;
            }
            QPushButton#generateBtn:hover {
                background-color: #5ba3f5;
            }
            QTableWidget {
                background-color: #252936;
                border: 1px solid #3d4152;
                border-radius: 12px;
                gridline-color: #3d4152;
                selection-background-color: #4a90e2;
                padding: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                background-color: #252936;
            }
            QTableWidget::item:selected {
                background-color: #4a90e2;
            }
            QHeaderView::section {
                background-color: #1e2130;
                color: #b0b5c8;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QTextEdit {
                background-color: #1e2130;
                border: 1px solid #3d4152;
                border-radius: 8px;
                padding: 10px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid #3d4152;
                background-color: #2d3142;
            }
            QCheckBox::indicator:hover {
                border-color: #4a90e2;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            QGroupBox {
                border: 2px solid #3d4152;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: 600;
                background-color: #252936;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #4a90e2;
                font-size: 13px;
                background-color: transparent;
            }
            QFrame#divider {
                background-color: #3d4152;
                max-height: 1px;
            }
        """)
        
        # Central widget with margins
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 20, 25, 20)
        
        # Header section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("CSWN Letter Generator")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; margin-bottom: 0px;")
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Colorado Severe Weather Network • Repeater Trustee Outreach")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        subtitle.setStyleSheet("color: #8a8fa3; font-size: 12px; margin-top: 0px;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_widget)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setMaximumHeight(1)
        main_layout.addWidget(divider)
        
        # Input group with modern card style
        input_group = QGroupBox("Add New Letter")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(15, 20, 15, 15)
        
        # Single row with both fields
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)

        # Owner field
        owner_label = QLabel("Owner/Trustee:")
        owner_label.setMinimumWidth(120)
        owner_label.setMaximumWidth(120)
        owner_label.setStyleSheet("font-weight: 600; color: #b0b5c8;")
        fields_layout.addWidget(owner_label)

        self.owner_input = QLineEdit()
        self.owner_input.setPlaceholderText("Enter full name...")
        fields_layout.addWidget(self.owner_input, 1)

        # Callsign field (same row)
        callsign_label = QLabel("Callsign/Location:")
        callsign_label.setMinimumWidth(120)
        callsign_label.setMaximumWidth(120)
        callsign_label.setStyleSheet("font-weight: 600; color: #b0b5c8;")
        fields_layout.addWidget(callsign_label)

        self.callsign_input = QLineEdit()
        self.callsign_input.setPlaceholderText("e.g., W1ABC/Denver Metro")
        fields_layout.addWidget(self.callsign_input, 1)

        input_layout.addLayout(fields_layout)
        
        # Add button row
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        add_btn = QPushButton("✓  Add Letter")
        add_btn.setMinimumWidth(140)
        add_btn.setMaximumWidth(200)
        add_btn.clicked.connect(self.add_letter)
        add_btn_layout.addWidget(add_btn)
        input_layout.addLayout(add_btn_layout)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Table section header
        table_header_layout = QHBoxLayout()
        table_header_layout.setSpacing(10)
        table_label = QLabel("Letters Queue")
        table_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        table_header_layout.addWidget(table_label)
        
        self.count_label = QLabel("0 letters")
        self.count_label.setStyleSheet("color: #8a8fa3; font-size: 12px;")
        table_header_layout.addWidget(self.count_label)
        table_header_layout.addStretch()
        main_layout.addLayout(table_header_layout)
        
        # Table - this should stretch to fill available space
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["OWNER/TRUSTEE", "CALLSIGN/LOCATION", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(200)
        main_layout.addWidget(self.table, 1)  # Stretch factor of 1
        main_layout.addStretch(1)
        
        # Action buttons
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(10)
        
        import_btn = QPushButton("📁  Import")
        import_btn.setObjectName("secondaryBtn")
        import_btn.clicked.connect(self.import_file)
        action_buttons.addWidget(import_btn)
        
        export_btn = QPushButton("💾  Export")
        export_btn.setObjectName("secondaryBtn")
        export_btn.clicked.connect(self.export_file)
        action_buttons.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑  Clear All")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self.clear_all)
        action_buttons.addWidget(clear_btn)
        
        action_buttons.addStretch()
        main_layout.addLayout(action_buttons)

        main_layout.addStretch(1)
        
        # Status section
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        self.status_label = QLabel("● Ready")
        self.status_label.setStyleSheet("color: #4caf50; font-weight: 600; font-size: 13px;")
        status_layout.addWidget(self.status_label, 1)
        
        # Email checkbox with modern styling
        self.email_checkbox = QCheckBox("Open email client after generation")
        self.email_checkbox.setChecked(False)
        status_layout.addWidget(self.email_checkbox)
        
        main_layout.addLayout(status_layout)
        
        # Generate button (prominent)
        self.generate_btn = QPushButton("🚀  GENERATE PDF")
        self.generate_btn.setObjectName("generateBtn")
        self.generate_btn.clicked.connect(self.generate_pdf)
        main_layout.addWidget(self.generate_btn)
        
        # Log output (collapsible style)
        log_header = QHBoxLayout()
        log_label = QLabel("Activity Log")
        log_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #b0b5c8;")
        log_header.addWidget(log_label)
        log_header.addStretch()
        main_layout.addLayout(log_header)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        self.log_output.setMinimumHeight(80)
        main_layout.addWidget(self.log_output)
    
    def check_requirements(self):
        """Check if lualatex is available"""
        try:
            subprocess.run(['lualatex', '--version'], capture_output=True, check=True)
            self.log("✓ LuaLaTeX found")
        except:
            self.log("✗ ERROR: lualatex not found! Please install TeXLive or MiKTeX.")
            self.generate_btn.setEnabled(False)
            QMessageBox.critical(self, "Missing Requirement", 
                               "lualatex not found!\n\nPlease install TeXLive or MiKTeX with LuaLaTeX support.")
        
        # Check for logo
        if not os.path.exists('CSWN-logo-BRAND.png'):
            self.log("⚠ WARNING: CSWN-logo-BRAND.png not found - logo will be missing")
        else:
            self.log("✓ Logo file found")
        
        # Create CSWN.cls if needed
        if not os.path.exists('CSWN.cls'):
            with open('CSWN.cls', 'w') as f:
                f.write(CSWN_CLASS)
            self.log("✓ Created CSWN.cls")
    
    def log(self, message):
        """Add message to log output"""
        self.log_output.append(message)
        
        # Update status with color coding
        if "✓" in message or "SUCCESS" in message:
            self.status_label.setText(f"● {message}")
            self.status_label.setStyleSheet("color: #4caf50; font-weight: 600; font-size: 13px;")
        elif "✗" in message or "ERROR" in message:
            self.status_label.setText(f"● {message}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: 600; font-size: 13px;")
        elif "⚠" in message or "WARNING" in message:
            self.status_label.setText(f"● {message}")
            self.status_label.setStyleSheet("color: #f39c12; font-weight: 600; font-size: 13px;")
        else:
            self.status_label.setText(f"● {message}")
            self.status_label.setStyleSheet("color: #4a90e2; font-weight: 600; font-size: 13px;")
    
    def update_count(self):
        """Update the letter count display"""
        count = len(self.letters)
        self.count_label.setText(f"{count} letter{'s' if count != 1 else ''}")
        self.generate_btn.setEnabled(count > 0)
    
    def add_letter(self):
        """Add a letter to the table"""
        owner = self.owner_input.text().strip()
        callsign = self.callsign_input.text().strip()
        
        if not owner or not callsign:
            QMessageBox.warning(self, "Invalid Input", "Both Owner and Callsign fields are required!")
            return
        
        # Add to internal list
        self.letters.append({'owner': owner, 'callsign': callsign})
        
        # Add to table
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(owner))
        self.table.setItem(row, 1, QTableWidgetItem(callsign))
        
        # Add delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(lambda: self.delete_letter(row))
        self.table.setCellWidget(row, 2, delete_btn)
        
        # Clear inputs
        self.owner_input.clear()
        self.callsign_input.clear()
        self.owner_input.setFocus()
        
        self.update_count()
        self.log(f"✓ Added: {owner} ({callsign})")
    
    def delete_letter(self, row):
        """Delete a letter from the table"""
        owner = self.table.item(row, 0).text()
        callsign = self.table.item(row, 1).text()
        
        # Remove from internal list
        self.letters = [l for l in self.letters 
                       if not (l['owner'] == owner and l['callsign'] == callsign)]
        
        # Rebuild table
        self.rebuild_table()
        self.update_count()
        self.log(f"✓ Deleted: {owner} ({callsign})")
    
    def rebuild_table(self):
        """Rebuild the entire table from letters list"""
        self.table.setRowCount(0)
        for i, letter in enumerate(self.letters):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(letter['owner']))
            self.table.setItem(row, 1, QTableWidgetItem(letter['callsign']))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("deleteBtn")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_letter(r))
            self.table.setCellWidget(row, 2, delete_btn)
    
    def import_file(self):
        """Import letters from a pipe-delimited file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Import File", "", 
                                                  "Text Files (*.txt);;All Files (*)")
        if not filename:
            return
        
        try:
            count = 0
            with open(filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    if '|' not in line:
                        self.log(f"⚠ Line {line_num}: Missing '|' delimiter")
                        continue
                    
                    parts = [p.strip() for p in line.split('|', 1)]
                    if len(parts) != 2 or not parts[0] or not parts[1]:
                        self.log(f"⚠ Line {line_num}: Invalid format")
                        continue
                    
                    self.letters.append({'owner': parts[0], 'callsign': parts[1]})
                    count += 1
            
            self.rebuild_table()
            self.update_count()
            self.log(f"✓ Imported {count} letter(s) from {os.path.basename(filename)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import file:\n{e}")
    
    def export_file(self):
        """Export letters to a pipe-delimited file"""
        if not self.letters:
            QMessageBox.warning(self, "No Data", "No letters to export!")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export File", "", 
                                                  "Text Files (*.txt);;All Files (*)")
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# CSWN Letter Recipients\n")
                f.write("# Format: Owner | Callsign/Location\n\n")
                for letter in self.letters:
                    f.write(f"{letter['owner']} | {letter['callsign']}\n")
            
            self.log(f"✓ Exported {len(self.letters)} letter(s) to {os.path.basename(filename)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export file:\n{e}")
    
    def clear_all(self):
        """Clear all letters"""
        if not self.letters:
            return
        
        reply = QMessageBox.question(self, "Clear All", 
                                    f"Are you sure you want to clear all {len(self.letters)} letter(s)?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.letters.clear()
            self.table.setRowCount(0)
            self.update_count()
            self.log("✓ Cleared all letters")
    
    def generate_pdf(self):
        """Generate the PDF"""
        if not self.letters:
            QMessageBox.warning(self, "No Letters", "Please add at least one letter before generating!")
            return
        
        # Get output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"cswn_letters_{timestamp}"
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF As", default_name,
                                                  "PDF Files (*.pdf)")
        if not filename:
            return
        
        # Remove .pdf extension if present (we'll add it)
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        
        # Disable generate button
        self.generate_btn.setEnabled(False)
        self.log(f"Generating {len(self.letters)} letter(s)...")
        
        # Start compilation thread
        self.compile_thread = CompileThread(self.letters, filename)
        self.compile_thread.progress.connect(self.log)
        self.compile_thread.finished.connect(self.on_compile_finished)
        self.compile_thread.start()
    
    def on_compile_finished(self, success, result):
        """Handle compilation completion"""
        self.generate_btn.setEnabled(True)
        
        if success:
            self.log(f"✓ SUCCESS! PDF saved to: {os.path.basename(result)}")
            QMessageBox.information(self, "Success", 
                                  f"PDF generated successfully!\n\n{result}")
            
            # Open email if requested
            if self.email_checkbox.isChecked():
                self.open_email_client(result)
        else:
            self.log(f"✗ ERROR: {result}")
            QMessageBox.critical(self, "Compilation Failed", 
                               f"Failed to generate PDF:\n\n{result}")
    
    def open_email_client(self, pdf_path):
        """Open email client with attachment"""
        from urllib.parse import quote
        subject = "Repeater Trustee Letters"
        abs_pdf_path = os.path.abspath(pdf_path)
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                script = f'''
                tell application "Mail"
                    activate
                    set newMessage to make new outgoing message with properties {{subject:"{subject}", visible:true}}
                    tell newMessage
                        make new attachment with properties {{file name:POSIX file "{abs_pdf_path}"}} at after the last paragraph
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                self.log("✓ Opened Mail.app with attachment")

            elif system == "Linux":
                # Try Thunderbird directly first — it has reliable compose support
                thunderbird_compose = (
                    f"subject='{subject}',"
                    f"attachment='file://{abs_pdf_path}'"
                )
                try:
                    subprocess.Popen(['thunderbird', '-compose', thunderbird_compose])
                    self.log("✓ Opened Thunderbird with subject and attachment")
                except FileNotFoundError:
                    # Fall back to xdg-email
                    try:
                        subprocess.run([
                            'xdg-email',
                            '--subject', subject,
                            '--attach', abs_pdf_path
                        ])
                        self.log("✓ Opened email client with attachment")
                    except FileNotFoundError:
                        # Last resort: bare mailto
                        subprocess.run(['xdg-open', f'mailto:?subject={quote(subject)}'])
                        self.log("✓ Opened email client (attach PDF manually)")

            elif system == "Windows":
                subprocess.run(f'start "" "mailto:?subject={quote(subject)}"', shell=True)
                self.log("✓ Opened email client (attach manually)")

        except Exception as e:
            self.log(f"✗ Failed to open email client: {e}")

def main():
    app = QApplication(sys.argv)
    window = CSWNLetterGenerator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
