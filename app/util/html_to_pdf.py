import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QPageSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QApplication

def conv_html_to_pdf(html_content: str, output_path: str, page_size: QPageSize = QPageSize(QPageSize.PageSizeId.A4)) -> None:
    """
    Convert HTML content to PDF using PyQt6.
    
    Args:
        html_content (str): HTML content to convert.
        output_path (str): Path where the PDF will be saved.
        page_size (QPageSize): Page size for the PDF (default: A4).
    """
    # Ensure QApplication exists
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create WebEngineView
    view = QWebEngineView()
    
    def on_load_finished(success: bool):
        if not success:
            print("Failed to load HTML content")
            return
        
        # Create printer and set PDF options
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(page_size)
        
        # Print to PDF
        view.page().printToPdf(output_path)
    
    # Load HTML content
    view.setHtml(html_content, QUrl.fromLocalFile(output_path))
    view.page().loadFinished.connect(on_load_finished)
    
    # Run event loop if needed
    if not QApplication.topLevelWidgets():
        app.exec()