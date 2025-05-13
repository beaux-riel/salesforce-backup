# 🔄 Salesforce Backup Tool

> Effortlessly backup your Salesforce data with a few clicks.

![Salesforce Backup Tool Banner](https://shields.io/badge/Salesforce-Backup_Tool-00A1E0?style=for-the-badge&logo=salesforce&logoColor=white)

A powerful, user-friendly desktop application for backing up your Salesforce data with an intuitive graphical interface. Easily select and export your Salesforce objects to CSV files with just a few clicks.

## ✨ Features

- 🖥️ **User-friendly GUI** built with Tkinter
- 🔍 **Smart search** to quickly find objects
- ✅ **Multiple selection** with persistent selection state
- 📁 **Custom output directory** selection
- ⏳ **Background processing** with progress tracking
- 🛑 **Graceful cancellation** of long-running backups
- 📊 **Pagination support** for large datasets
- 🔒 **Secure credential handling**

![Demo Screenshot](https://shields.io/badge/Screenshot-Coming_Soon-lightgray?style=flat-square)

## 🚀 Quick Start

### Prerequisites
- Python 3.7+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/salesforce-backup-tool.git
   cd salesforce-backup-tool
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. Run the application:
   ```bash
   python salesforce_backup.py
   ```

2. Enter your Salesforce credentials:
   - Username
   - Password
   - Security Token
   - Check "Sandbox" if connecting to a sandbox org

3. Select the objects you want to back up:
   - Use the search box to filter objects
   - Click to select/deselect objects
   - Use "Select All" or "Clear Selection" as needed

4. (Optional) Click "Browse Output Directory" to change the backup location

5. Click "Start Backup" to begin the export process

## 📂 Output

Backups are saved in the `backups` directory by default, with each backup session in a timestamped folder:

```
backups/
└── YYYYMMDD_HHMMSS/
    ├── Account.csv
    ├── Contact.csv
    └── ...
```

## 🛠️ Requirements

- `simple-salesforce>=1.12.0`
- `pandas>=1.3.0`

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is provided as-is, without any warranty. Always verify your backups and test in a sandbox environment before using in production.

---

<p align="center">
  Made with ❤️ for Salesforce admins and developers
</p>
