# GelMa

![License](https://img.shields.io/badge/license-MPL--2.0-blue)
![Python](https://img.shields.io/badge/python-3.10--3.14-blue)

<p align="center">
  <img src="windows/templates/figure/logo_readme.png" width="500">
</p>

Copyright (c) 2026 LingXuan-Li

GelMa [ゲルマ] is a Python application designed to compensate for overscan issues on older televisions and similar display devices.

It allows users to manually adjust and fit web content into visible screen areas using a modern PyQt-based GUI.

## Features

- Manual overscan adjustment
- Web content display optimization
- Modern PyQt-based graphical interface
- Lightweight and simple operation

## Tested Environment

### OS and Language

- Windows 11
- Python 3.14

### Python libraries

- PyQt6 6.11.0
- PyQt6-Qt6 6.11.0
- PyQt6-WebEngine 6.11.0
- PyQt6-WebEngine-Qt6 6.11.0
- PyQt6_sip 13.11.1

## Usage

### 1. Launch the application

```bash
python main.py
```

### 2. Window layout

- The main screen displays the control panel.
- The secondary screen displays the web content. (display window)

### 3. Language selection

- Use the language selector in the control panel to switch the UI language
- The interface updates immediately after selection
- The HOME screen is not affected because it contains static content

#### Supported languages

- English
- Japanese
- Chinese (Simplified)
- Chinese (Traditional)
- Korean
- French
- German
- Italian
- Russian
- Ukrainian

### 4. Adjust overscan

- Use the control panel to adjust overscan margins (Margin / Vertical Scale / Horizontal Scale)
- Changes are reflected in real time on the display window

### 5. Display preview

- The display window shows the adjusted web content
- This helps align content within the visible area of older displays

## License

This project is licensed under the Mozilla Public License 2.0.

## Contact

- **GitHub**: [![GitHub](https://img.shields.io/badge/-GitHub-181717?logo=github\&logoColor=white)](https://github.com/LingXuan-Li)
- **Twitter/X**: [![Twitter](https://img.shields.io/twitter/follow/RaccoonDog_329?style=social)](https://x.com/RaccoonDog_329)

For bug reports, please use GitHub [Issues](https://github.com/LingXuan-Li/GelMa/issues). For questions, please contact me via Twitter/X [chat](https://x.com/RaccoonDog_329).
