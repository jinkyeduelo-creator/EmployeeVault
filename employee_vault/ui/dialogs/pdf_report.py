"""
PDF Report Generator
v5.3.0: Professional PDF reports for employee data
Uses Qt's PDF printing capabilities for cross-platform support
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressDialog, QComboBox, QCheckBox,
    QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPixmap, QImage,
    QPageSize, QPageLayout, QTextDocument
)
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from employee_vault.database import DB
from employee_vault.config import EMPLOYEE_PHOTOS_DIR
from employee_vault.ui.widgets import NeumorphicGradientComboBox


class PDFReportGenerator:
    """
    Generates professional PDF reports for employee data
    """
    
    def __init__(self, db: DB):
        self.db = db
        
    def generate_employee_list_html(
        self,
        employees: List[Dict],
        title: str = "Employee Directory",
        include_photos: bool = False,
        columns: List[str] = None
    ) -> str:
        """
        Generate HTML for employee list report
        
        Args:
            employees: List of employee dictionaries
            title: Report title
            include_photos: Whether to include employee photos
            columns: Which columns to include (defaults to all standard)
            
        Returns:
            HTML string for the report
        """
        if columns is None:
            columns = ['emp_id', 'name', 'position', 'department', 'agency', 'hire_date', 'status']
            
        # Column headers mapping
        headers = {
            'emp_id': 'Employee ID',
            'name': 'Name',
            'position': 'Position',
            'department': 'Department',
            'agency': 'Agency',
            'hire_date': 'Hire Date',
            'resign_date': 'Resign Date',
            'contract_expiry': 'Contract Expiry',
            'phone': 'Phone',
            'email': 'Email',
            'status': 'Status'
        }
        
        # Generate report date
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    margin: 1.5cm;
                }}
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 10pt;
                    color: #333;
                    line-height: 1.4;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid #2196F3;
                }}
                .header h1 {{
                    color: #1976D2;
                    margin: 0 0 5px 0;
                    font-size: 20pt;
                }}
                .header .subtitle {{
                    color: #666;
                    font-size: 10pt;
                }}
                .meta-info {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    font-size: 9pt;
                    color: #666;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th {{
                    background-color: #2196F3;
                    color: white;
                    padding: 8px 6px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 9pt;
                    border: 1px solid #1976D2;
                }}
                td {{
                    padding: 6px;
                    border: 1px solid #ddd;
                    font-size: 9pt;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f0f7ff;
                }}
                .status-active {{
                    color: #2e7d32;
                    font-weight: bold;
                }}
                .status-resigned {{
                    color: #c62828;
                }}
                .status-expiring {{
                    color: #f57c00;
                    font-weight: bold;
                }}
                .photo {{
                    width: 35px;
                    height: 35px;
                    border-radius: 50%;
                    object-fit: cover;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    font-size: 8pt;
                    color: #999;
                }}
                .summary {{
                    background: #e3f2fd;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }}
                .summary-item {{
                    display: inline-block;
                    margin-right: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 {title}</h1>
                <div class="subtitle">Cuddly International Corporation</div>
            </div>
            
            <div class="meta-info">
                <span>Generated: {report_date}</span>
                <span>Total Records: {len(employees)}</span>
            </div>
            
            <div class="summary">
        """
        
        # Add summary stats
        active = sum(1 for e in employees if not e.get('resign_date'))
        resigned = len(employees) - active
        html += f"""
                <span class="summary-item">👥 Active: <strong>{active}</strong></span>
                <span class="summary-item">📝 Resigned: <strong>{resigned}</strong></span>
        """
        html += """
            </div>
            
            <table>
                <thead>
                    <tr>
        """
        
        # Add headers
        if include_photos:
            html += "<th>Photo</th>"
        for col in columns:
            html += f"<th>{headers.get(col, col.replace('_', ' ').title())}</th>"
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add rows
        for emp in employees:
            html += "<tr>"
            
            if include_photos:
                photo_path = os.path.join(EMPLOYEE_PHOTOS_DIR, f"{emp.get('emp_id', '')}.jpg")
                if os.path.exists(photo_path):
                    html += f'<td><img src="file:///{photo_path}" class="photo"/></td>'
                else:
                    html += '<td>—</td>'
            
            for col in columns:
                value = emp.get(col, '—') or '—'
                
                # Special formatting
                if col == 'status':
                    if emp.get('resign_date'):
                        value = '<span class="status-resigned">Resigned</span>'
                    else:
                        value = '<span class="status-active">Active</span>'
                        
                html += f"<td>{value}</td>"
            
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
            
            <div class="footer">
                <p>This report was generated by EmployeeVault™ | Confidential</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def generate_employee_profile_html(self, employee: Dict) -> str:
        """
        Generate HTML for single employee profile
        
        Args:
            employee: Employee dictionary
            
        Returns:
            HTML string for the profile
        """
        emp = employee
        report_date = datetime.now().strftime("%B %d, %Y")
        
        # Check for photo
        photo_html = ""
        photo_path = os.path.join(EMPLOYEE_PHOTOS_DIR, f"{emp.get('emp_id', '')}.jpg")
        if os.path.exists(photo_path):
            photo_html = f'<img src="file:///{photo_path}" class="profile-photo"/>'
        else:
            photo_html = '<div class="profile-photo-placeholder">👤</div>'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    margin: 2cm;
                }}
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11pt;
                    color: #333;
                    max-width: 700px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #1976D2, #2196F3);
                    color: white;
                    border-radius: 10px;
                    margin-bottom: 25px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 18pt;
                }}
                .profile-photo {{
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    border: 4px solid white;
                    margin: 15px auto;
                    display: block;
                    object-fit: cover;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                }}
                .profile-photo-placeholder {{
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    border: 4px solid white;
                    margin: 15px auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 48px;
                    background: rgba(255,255,255,0.2);
                }}
                .employee-name {{
                    font-size: 20pt;
                    font-weight: bold;
                    margin: 10px 0 5px 0;
                }}
                .employee-position {{
                    font-size: 12pt;
                    opacity: 0.9;
                }}
                .section {{
                    background: #f5f5f5;
                    padding: 15px 20px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                }}
                .section-title {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #1976D2;
                    margin-bottom: 10px;
                    border-bottom: 2px solid #1976D2;
                    padding-bottom: 5px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }}
                .info-item {{
                    padding: 5px 0;
                }}
                .info-label {{
                    color: #666;
                    font-size: 9pt;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .info-value {{
                    font-weight: 500;
                    margin-top: 2px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 10pt;
                    font-weight: bold;
                }}
                .status-active {{
                    background: #c8e6c9;
                    color: #2e7d32;
                }}
                .status-resigned {{
                    background: #ffcdd2;
                    color: #c62828;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #ddd;
                    font-size: 9pt;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                {photo_html}
                <div class="employee-name">{emp.get('name', 'Unknown')}</div>
                <div class="employee-position">{emp.get('position', 'N/A')} • {emp.get('department', 'N/A')}</div>
            </div>
            
            <div class="section">
                <div class="section-title">📋 Employee Information</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Employee ID</div>
                        <div class="info-value">{emp.get('emp_id', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Status</div>
                        <div class="info-value">
                            <span class="status-badge {'status-resigned' if emp.get('resign_date') else 'status-active'}">
                                {'Resigned' if emp.get('resign_date') else 'Active'}
                            </span>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Department</div>
                        <div class="info-value">{emp.get('department', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Position</div>
                        <div class="info-value">{emp.get('position', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Agency</div>
                        <div class="info-value">{emp.get('agency', 'Direct Hire')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📅 Employment Dates</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Hire Date</div>
                        <div class="info-value">{emp.get('hire_date', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Contract Expiry</div>
                        <div class="info-value">{emp.get('contract_expiry', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Contract Start</div>
                        <div class="info-value">{emp.get('contract_start_date', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Resign Date</div>
                        <div class="info-value">{emp.get('resign_date', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📞 Contact Information</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Phone</div>
                        <div class="info-value">{emp.get('phone', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Email</div>
                        <div class="info-value">{emp.get('email', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Emergency Contact</div>
                        <div class="info-value">{emp.get('emergency_contact_name', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Emergency Phone</div>
                        <div class="info-value">{emp.get('emergency_contact_phone', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">🏦 Government IDs</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">SSS Number</div>
                        <div class="info-value">{emp.get('sss_number', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">TIN Number</div>
                        <div class="info-value">{emp.get('tin_number', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Pag-IBIG Number</div>
                        <div class="info-value">{emp.get('pagibig_number', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">PhilHealth Number</div>
                        <div class="info-value">{emp.get('philhealth_number', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>Generated on {report_date} | EmployeeVault™ | Confidential</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def generate_contract_expiry_html(self, expiring_contracts: List[Dict]) -> str:
        """
        Generate HTML for contract expiry report
        
        Args:
            expiring_contracts: List of employees with expiring contracts
            
        Returns:
            HTML string for the report
        """
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ margin: 1.5cm; }}
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 10pt;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #ff5722, #ff9800);
                    color: white;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 18pt;
                }}
                .alert-box {{
                    background: #fff3e0;
                    border-left: 4px solid #ff9800;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 0 8px 8px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th {{
                    background: #ff5722;
                    color: white;
                    padding: 10px;
                    text-align: left;
                }}
                td {{
                    padding: 8px 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{ background: #fff8e1; }}
                .days-critical {{ color: #c62828; font-weight: bold; }}
                .days-warning {{ color: #ef6c00; font-weight: bold; }}
                .days-notice {{ color: #f57f17; }}
                .footer {{
                    margin-top: 25px;
                    text-align: center;
                    font-size: 9pt;
                    color: #999;
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ Contract Expiry Report</h1>
                <p style="margin:5px 0 0 0; opacity:0.9;">Cuddly International Corporation</p>
            </div>
            
            <div class="alert-box">
                <strong>⏰ Action Required:</strong> {len(expiring_contracts)} contract(s) require attention within the next 30 days.
            </div>
            
            <p style="color:#666;">Report generated: {report_date}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Department</th>
                        <th>Agency</th>
                        <th>Expiry Date</th>
                        <th>Days Left</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for emp in expiring_contracts:
            days = emp.get('days_until_expiry', emp.get('days_left', 999))
            
            if days <= 7:
                days_class = 'days-critical'
            elif days <= 14:
                days_class = 'days-warning'
            else:
                days_class = 'days-notice'
                
            html += f"""
                    <tr>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td><strong>{emp.get('name', 'Unknown')}</strong></td>
                        <td>{emp.get('position', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{emp.get('agency', 'Direct Hire')}</td>
                        <td>{emp.get('contract_expiry', emp.get('expiry_date', 'N/A'))}</td>
                        <td class="{days_class}">{days} days</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <div class="footer">
                <p>This report was generated by EmployeeVault™ | Confidential | Please take action promptly</p>
            </div>
        </body>
        </html>
        """
        
        return html


class PDFExportDialog(QDialog):
    """
    Dialog for exporting PDF reports with options
    """
    
    def __init__(self, db: DB, employees: List[Dict], parent=None):
        super().__init__(parent)
        self.db = db
        self.employees = employees
        self.generator = PDFReportGenerator(db)
        
        self.setWindowTitle("📄 Export PDF Report")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("<h2>📄 Export PDF Report</h2>")
        layout.addWidget(title)
        
        # Report type selection
        type_group = QGroupBox("Report Type")
        type_layout = QVBoxLayout(type_group)
        
        self.report_types = {
            'employee_list': '📋 Employee Directory - All employees in a table format',
            'contract_expiry': '⚠️ Contract Expiry Report - Employees with expiring contracts',
            'active_employees': '✅ Active Employees - Only currently employed staff',
            'department_summary': '🏢 Department Summary - Grouped by department'
        }
        
        self.type_combo = NeumorphicGradientComboBox("Select Report Type")
        self.type_combo.setMinimumHeight(70)
        for key, label in self.report_types.items():
            self.type_combo.combo_box.addItem(label, key)
        type_layout.addWidget(self.type_combo)
        
        layout.addWidget(type_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_photos = QCheckBox("Include employee photos")
        self.include_photos.setChecked(False)
        options_layout.addWidget(self.include_photos)
        
        self.include_contact = QCheckBox("Include contact information")
        self.include_contact.setChecked(True)
        options_layout.addWidget(self.include_contact)
        
        self.include_govt_ids = QCheckBox("Include government IDs (SSS, TIN, etc.)")
        self.include_govt_ids.setChecked(False)
        options_layout.addWidget(self.include_govt_ids)
        
        layout.addWidget(options_group)
        
        # Preview info
        preview_label = QLabel(f"<i>ℹ️ {len(self.employees)} employees will be included in the report</i>")
        preview_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(preview_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        preview_btn = QPushButton("👁️ Preview")
        preview_btn.clicked.connect(self._preview_report)
        btn_layout.addWidget(preview_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("📥 Export PDF")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        export_btn.clicked.connect(self._export_pdf)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
        
    def _get_html(self) -> str:
        """Get HTML based on selected options"""
        report_type = self.type_combo.combo_box.currentData()
        
        # Build column list
        columns = ['emp_id', 'name', 'position', 'department', 'agency', 'hire_date', 'status']
        
        if self.include_contact.isChecked():
            columns.extend(['phone', 'email'])
            
        if report_type == 'employee_list':
            return self.generator.generate_employee_list_html(
                self.employees,
                title="Employee Directory",
                include_photos=self.include_photos.isChecked(),
                columns=columns
            )
        elif report_type == 'contract_expiry':
            from datetime import datetime, timedelta
            today = datetime.now()
            expiring = []
            
            for emp in self.employees:
                if emp.get('resign_date'):
                    continue
                if exp := emp.get('contract_expiry'):
                    try:
                        exp_date = datetime.strptime(exp, "%Y-%m-%d")
                        days = (exp_date - today).days
                        if 0 <= days <= 30:
                            emp_copy = dict(emp)
                            emp_copy['days_until_expiry'] = days
                            expiring.append(emp_copy)
                    except:
                        pass
                        
            expiring.sort(key=lambda x: x.get('days_until_expiry', 999))
            return self.generator.generate_contract_expiry_html(expiring)
            
        elif report_type == 'active_employees':
            active = [e for e in self.employees if not e.get('resign_date')]
            return self.generator.generate_employee_list_html(
                active,
                title="Active Employees",
                include_photos=self.include_photos.isChecked(),
                columns=columns
            )
        else:
            return self.generator.generate_employee_list_html(
                self.employees,
                title="Employee Report",
                include_photos=self.include_photos.isChecked(),
                columns=columns
            )
            
    def _preview_report(self):
        """Show print preview"""
        html = self._get_html()
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("PDF Preview")
        preview.paintRequested.connect(lambda p: doc.print_(p))
        preview.exec()
        
    def _export_pdf(self):
        """Export to PDF file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            f"employee_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not filename:
            return
            
        try:
            html = self._get_html()
            
            doc = QTextDocument()
            doc.setHtml(html)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            doc.print_(printer)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"PDF report saved to:\n{filename}"
            )
            self.accept()
            
        except Exception as e:
            logging.error(f"PDF export error: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export PDF:\n{str(e)}"
            )
