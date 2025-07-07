
# Colorado Severe Weather Network Toolkit

![CSWN Interface Dark Mode](CSWN-Main-Dark.png)

![CSWN Interface Light Mode](CSWN-Main.png)

## 🌀 Overview

**Colorado Severe Weather Network Toolkit** is a streamlined, GUI-based application designed to provide quick access to critical weather tools, forecasts, and radar products specific to Colorado and nearby regions. It aggregates links and resources from the National Weather Service (NWS), Storm Prediction Center (SPC), and other weather platforms to assist meteorologists, storm spotters, emergency managers, and weather enthusiasts in severe weather monitoring and preparedness.

---

## 🧰 Features

- **Net control script generator**  
 - Easily generate a net script for the current day.
 - Includes the AFD and HWO for each of the 5 WFO we partner with.
 - Easily modify parameters to keep information relevent

- **Hazardous Weather Outlooks**  
  - One-click access to HWO pages for Grand Junction, Boulder, Pueblo, Cheyenne, and Goodland offices.

- **Area Forecast Discussions (AFDs)**  
  - Quickly view detailed forecast discussions from multiple NWS offices.

- **Storm Prediction Center (SPC) Resources**  
  - SPC Outlooks  
  - Mesoscale Discussions  
  - Watches & Warnings  
  - Storm Reports  
  - Mesoanalysis

- **Radar & Satellite Tools**  
  - NEXRAD Radar (COD, NWS Enhanced, etc.)  
  - GOES Satellite Viewers (RGB Cloud Detail, SLIDER, Zoom Earth)  
  - Ventusky Radar & Satellite  
  - Tropical Tidbits

- **Observations**  
  - Mesowest Observations  
  - MPing Reports  
  - NWS EDD

- **Forecast Tools**  
  - WPC QPF Forecast  
  - NDFD Graphical Forecast  
  - WPC Homepage

- **Forecast Models**  
  - HRRR, NAM NEST, COD, and Tropical Tidbits

- **Skywarn Spotter Resources**  
  - Field Guide  
  - Spotter Checklist

- **NWS Office Homepages**  
  - Quick access to individual office websites

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x  
- `PyQT6`
- `PyQt6-WebEngine`
- `requests`
- `beautifulsoup4`
- `pillow`
- Internet connection (for live web links)

### Installation (Source Code)

```bash
git clone https://github.com/W5ALC/Colorado-Severe-Weather.git
cd Colorado-Severe-Weather
python3 Colorado-Severe-Weather.py
```

> Or run the compiled executable: `CSWN-toolkit.exe` (Windows)
> [Windows Release](https://github.com/W5ALC/Colorado-Severe-Weather/releases/download/v2.1.0/CSWN-Toolkit-v2.1.0-windows.zip))
>
> Or run the compiled executable: `CSWN-Toolkit-v2.1.0-macos.dmg` (MacOS)
> [MacOS Release](https://github.com/W5ALC/Colorado-Severe-Weather/releases/download/v2.1.0/CSWN-Toolkit-v2.1.0-macos.dmg)

> Or run the compiled executable: `CSWN-toolkit.exe` (Linux) (AppImage)
> [Linux Release](https://github.com/W5ALC/Colorado-Severe-Weather/releases/download/v2.1.0/CSWN-Toolkit-v2.1.0-linux.tar.gz)
Installation:
1. Make executable: chmod +x CSWN-Toolkit-linux-x86_64
2. Run: ./CSWN-Toolkit-linux-x86_64

Or use the AppImage (if available):
1. Make executable: chmod +x *.AppImage
2. Run: ./CSWN*.AppImage

---

## 📸 Interface Preview

Screenshots of the program in action:

![Toolkit Tab](CSWN-toolkit.png)
![SPC and Severe Weather](CSWN-SPC.png)
![Active Alerts](CSWN-CO-Alert.png)
![No Active Alerts](CSWN-alert-none.png)
![GOES Viewer](CSWN-GOES.png)
![Additional View - GEOS](CSWN-GOES-zoom.png)
![AFD Tool](CSWN-AFD.png)
![HWO Tool](CSWN-HWO.png)
![METED](CSWN-METED,png)


---

---

## 🛠️ Contributing

Pull requests are welcome! If you have suggestions for improvements or new features, feel free to open an issue or fork and submit a PR.

---

## 📄 License

This project is licensed under the 'Its not that serious' v1 license.

---

## 🙏 Acknowledgments

- National Weather Service (weather.gov)  
- Storm Prediction Center (spc.noaa.gov)  
- College of DuPage NEXRAD Tools  
- Mesowest, Ventusky, Zoom Earth  
- Skywarn Spotter program  
