"""
Main entry point for the Smart Waste IoT Dashboard
"""
import sys
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Enable high DPI scaling BEFORE creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Waste IoT Dashboard")
    app.setOrganizationName("SmartWaste")
    
    # Create and show main window
    logger.info("Starting Smart Waste IoT Dashboard...")
    window = MainWindow()
    window.show()
    
    # Run application event loop
    logger.info("Application started. Waiting for events...")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

