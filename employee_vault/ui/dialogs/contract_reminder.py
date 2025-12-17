"""
Contract Renewal Reminder Dialog
Shows expiring contracts on dashboard load
"""

from datetime import datetime, timedelta
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.ui.widgets import ModernAnimatedButton, SmoothAnimatedDialog
from employee_vault.ui.ios_button_styles import apply_ios_style


class ContractReminderDialog(SmoothAnimatedDialog):
    """Dialog showing contracts expiring within 30 days"""

    def __init__(self, parent=None, expiring_employees=None):
        super().__init__(parent, animation_style="scale")
        self.expiring_employees = expiring_employees or []
        self.setWindowTitle("⚠️ Contract Renewal Reminders")
        self.resize(800, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title with icon
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 10)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 48px;")
        title_layout.addWidget(icon_label)

        title_text = QLabel(f"<h2>Contract Renewal Reminders</h2><p style='color: #ff9800;'>{len(self.expiring_employees)} contract(s) expiring soon!</p>")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        layout.addWidget(title_container)

        # Info message
        info = QLabel("The following employee contracts are expiring within the next 30 days. Please take action to renew or update their contracts.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 12px; background-color: #fff3e0; border-left: 4px solid #ff9800; border-radius: 6px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Table of expiring contracts
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Department", "Position",
            "Contract Expiry", "Days Remaining"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #BBDEFB;
                color: #1976D2;
            }
        """)

        self._populate_table()
        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QHBoxLayout()

        # View Employee button
        self.view_btn = ModernAnimatedButton("👤 View Employee")
        apply_ios_style(self.view_btn, 'blue')
        self.view_btn.setToolTip("View selected employee details")
        self.view_btn.setEnabled(False)
        self.view_btn.clicked.connect(self._view_employee)
        btn_layout.addWidget(self.view_btn)

        # Export List button
        export_btn = ModernAnimatedButton("📄 Export List")
        apply_ios_style(export_btn, 'green')
        export_btn.setToolTip("Export expiring contracts to file")
        export_btn.clicked.connect(self._export_list)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        # Don't Show Again (for today)
        dont_show_btn = ModernAnimatedButton("🔕 Don't Show Today")
        apply_ios_style(dont_show_btn, 'orange')
        dont_show_btn.setToolTip("Skip reminder for today only")
        dont_show_btn.clicked.connect(self._dont_show_today)
        btn_layout.addWidget(dont_show_btn)

        # Close button
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Enable view button when selection changes
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _populate_table(self):
        """Fill table with expiring employee data"""
        today = datetime.now().date()
        self.table.setRowCount(len(self.expiring_employees))

        for row, emp in enumerate(self.expiring_employees):
            self.table.setItem(row, 0, QTableWidgetItem(emp.get('emp_id', 'N/A')))
            self.table.setItem(row, 1, QTableWidgetItem(emp.get('name', 'N/A')))
            self.table.setItem(row, 2, QTableWidgetItem(emp.get('department', 'N/A')))
            self.table.setItem(row, 3, QTableWidgetItem(emp.get('position', 'N/A')))

            contract_expiry = emp.get('contract_expiry', '')
            self.table.setItem(row, 4, QTableWidgetItem(contract_expiry))

            # Calculate days remaining
            try:
                expiry_date = datetime.strptime(contract_expiry, "%m-%d-%Y").date()
                days_left = (expiry_date - today).days

                # Color code based on urgency
                days_item = QTableWidgetItem(str(days_left))
                if days_left < 0:
                    days_item.setBackground(QColor("#ffebee"))  # Red - expired
                    days_item.setForeground(QColor("#c62828"))
                    days_item.setText(f"{days_left} (EXPIRED)")
                elif days_left <= 7:
                    days_item.setBackground(QColor("#fff3e0"))  # Orange - critical
                    days_item.setForeground(QColor("#e65100"))
                elif days_left <= 15:
                    days_item.setBackground(QColor("#fff9c4"))  # Yellow - warning
                    days_item.setForeground(QColor("#f57f17"))
                else:
                    days_item.setBackground(QColor("#e3f2fd"))  # Blue - upcoming
                    days_item.setForeground(QColor("#1565c0"))

                self.table.setItem(row, 5, days_item)
            except ValueError:
                # Invalid date format
                self.table.setItem(row, 5, QTableWidgetItem("Invalid Date"))

        self.table.resizeColumnsToContents()

    def _on_selection_changed(self):
        """Enable/disable view button based on selection"""
        self.view_btn.setEnabled(len(self.table.selectedItems()) > 0)

    def _view_employee(self):
        """Open employee details"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            emp = self.expiring_employees[selected_row]
            # Emit signal or call parent method to open employee form
            QMessageBox.information(
                self,
                "View Employee",
                f"Opening details for: {emp.get('name', 'Unknown')}\n\n"
                f"Employee ID: {emp.get('emp_id', 'N/A')}\n"
                f"Department: {emp.get('department', 'N/A')}\n"
                f"Contract Expiry: {emp.get('contract_expiry', 'N/A')}\n\n"
                f"Note: Use the main employee list to edit this record."
            )

    def _export_list(self):
        """Export expiring contracts to HTML file"""
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Expiring Contracts",
            f"expiring_contracts_{datetime.now().strftime('%Y%m%d')}.html",
            "HTML Files (*.html)"
        )

        if not filename:
            return

        try:
            html = f"""
            <html>
            <head>
                <title>Contract Renewal Reminders</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2196F3; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #2196F3; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .critical {{ background-color: #fff3e0; color: #e65100; font-weight: bold; }}
                    .expired {{ background-color: #ffebee; color: #c62828; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>⚠️ Contract Renewal Reminders</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                <p><strong>Total Expiring:</strong> {len(self.expiring_employees)} contracts</p>

                <table>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Position</th>
                        <th>Contract Expiry</th>
                        <th>Days Remaining</th>
                    </tr>
            """

            today = datetime.now().date()
            for emp in self.expiring_employees:
                try:
                    expiry_date = datetime.strptime(emp.get('contract_expiry', ''), "%m-%d-%Y").date()
                    days_left = (expiry_date - today).days

                    css_class = ""
                    if days_left < 0:
                        css_class = "expired"
                        days_text = f"{days_left} (EXPIRED)"
                    elif days_left <= 7:
                        css_class = "critical"
                        days_text = str(days_left)
                    else:
                        days_text = str(days_left)

                    html += f"""
                    <tr>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td>{emp.get('name', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{emp.get('position', 'N/A')}</td>
                        <td>{emp.get('contract_expiry', 'N/A')}</td>
                        <td class="{css_class}">{days_text}</td>
                    </tr>
                    """
                except ValueError:
                    # Invalid date format, show invalid date
                    html += f"""
                    <tr>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td>{emp.get('name', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{emp.get('position', 'N/A')}</td>
                        <td>{emp.get('contract_expiry', 'N/A')}</td>
                        <td>Invalid Date</td>
                    </tr>
                    """

            html += """
                </table>
            </body>
            </html>
            """

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Contract reminders exported successfully to:\n{filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export contract reminders:\n{str(e)}"
            )

    def _dont_show_today(self):
        """Set flag to not show reminder for today"""
        # Save preference to settings
        try:
            from datetime import date
            with open('contract_reminder_skip.txt', 'w') as f:
                f.write(date.today().isoformat())

            QMessageBox.information(
                self,
                "Reminder Disabled",
                "Contract renewal reminders will not be shown again today.\n\n"
                "They will appear tomorrow if there are still expiring contracts."
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Could Not Save Preference",
                f"Failed to save reminder preference:\n{str(e)}\n\n"
                "The reminder will still be skipped for this session."
            )
            self.accept()
