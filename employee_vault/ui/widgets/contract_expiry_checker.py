"""
Contract Expiry Notification System
v4.5.0: Alerts admins when employee contracts are about to expire
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.database import DB


class ContractExpiryChecker(QObject):
    """
    Background checker for contract expiry notifications
    Runs periodically to check for expiring contracts
    """

    # Signal emitted when contracts are expiring soon
    contracts_expiring = Signal(list)  # List of employee dicts

    def __init__(self, db: DB, parent=None):
        super().__init__(parent)
        self.db = db
        self.warning_days = 30  # Days before expiry to show warning

        # Timer for periodic checks (check every 30 minutes)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_expiring_contracts)
        self.timer.setInterval(30 * 60 * 1000)  # 30 minutes in milliseconds

    def start_monitoring(self):
        """Start monitoring contract expiries"""
        # Check immediately on start
        self.check_expiring_contracts()
        # Then check periodically
        self.timer.start()
        logging.info("Contract expiry monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.timer.stop()
        logging.info("Contract expiry monitoring stopped")

    def check_expiring_contracts(self):
        """Check for contracts expiring within warning period"""
        try:
            expiring = self.get_expiring_contracts()

            if expiring:
                logging.info(f"Found {len(expiring)} contracts expiring soon")
                self.contracts_expiring.emit(expiring)
            else:
                logging.debug("No contracts expiring soon")

        except Exception as e:
            logging.error(f"Error checking contract expiries: {e}")

    def get_expiring_contracts(self) -> List[Dict]:
        """
        Get list of employees with contracts expiring soon

        Returns:
            List of employee dictionaries with expiring contracts
        """
        expiring = []
        today = datetime.now()
        warning_date = today + timedelta(days=self.warning_days)

        try:
            # Query employees with contract_expiry dates
            rows = self.db.conn.execute("""
                SELECT emp_id, name, position, department, contract_expiry, agency
                FROM employees
                WHERE contract_expiry IS NOT NULL
                  AND contract_expiry != ''
                  AND resign_date IS NULL
            """).fetchall()

            for row in rows:
                try:
                    # Parse contract expiry date
                    expiry_str = row['contract_expiry']
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")

                    # Check if expiring within warning period
                    if today <= expiry_date <= warning_date:
                        days_until_expiry = (expiry_date - today).days

                        expiring.append({
                            'emp_id': row['emp_id'],
                            'name': row['name'],
                            'position': row['position'] or 'N/A',
                            'department': row['department'] or 'N/A',
                            'contract_expiry': expiry_str,
                            'days_until_expiry': days_until_expiry,
                            'agency': row['agency'] or 'Direct Hire'
                        })

                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid date format for {row['emp_id']}: {e}")
                    continue

        except Exception as e:
            logging.error(f"Database error getting expiring contracts: {e}")

        # Sort by days until expiry (most urgent first)
        expiring.sort(key=lambda x: x['days_until_expiry'])

        return expiring


class ContractExpiryNotificationDialog(QDialog):
    """
    Dialog to show contract expiry notifications
    """

    def __init__(self, expiring_contracts: List[Dict], parent=None):
        super().__init__(parent)
        self.expiring_contracts = expiring_contracts
        self.setWindowTitle("⚠️ Contract Expiry Alert")
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)

        # Title with warning
        title = QLabel(f"<h2>⚠️ {len(expiring_contracts)} Contract(s) Expiring Soon</h2>")
        title.setStyleSheet("color: #FF6B35; font-weight: bold;")
        layout.addWidget(title)

        # Info text
        info = QLabel(
            "The following employee contracts will expire within 30 days. "
            "Please take action to renew or update their contract status."
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background: #FFF3CD; border-radius: 5px;")
        layout.addWidget(info)

        # Table of expiring contracts
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Position", "Department", "Expiry Date", "Days Left"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Apply table fixes (remove cursor and focus rectangle)
        from employee_vault.ui.widgets import apply_table_fixes
        apply_table_fixes(self.table)

        # Populate table
        self.table.setRowCount(len(expiring_contracts))
        for row, contract in enumerate(expiring_contracts):
            self.table.setItem(row, 0, QTableWidgetItem(contract['emp_id']))
            self.table.setItem(row, 1, QTableWidgetItem(contract['name']))
            self.table.setItem(row, 2, QTableWidgetItem(contract['position']))
            self.table.setItem(row, 3, QTableWidgetItem(contract['department']))
            self.table.setItem(row, 4, QTableWidgetItem(contract['contract_expiry']))

            # Days left - color coded by urgency
            days_left = contract['days_until_expiry']
            days_item = QTableWidgetItem(str(days_left))

            if days_left <= 7:
                # Critical (1 week or less) - Red
                days_item.setForeground(QColor(220, 38, 38))
                days_item.setFont(QFont("Arial", 10, QFont.Bold))
            elif days_left <= 14:
                # Warning (2 weeks or less) - Orange
                days_item.setForeground(QColor(234, 88, 12))
                days_item.setFont(QFont("Arial", 10, QFont.Bold))
            else:
                # Caution (more than 2 weeks) - Yellow/Brown
                days_item.setForeground(QColor(161, 98, 7))

            self.table.setItem(row, 5, days_item)

        # Auto-resize columns to content
        self.table.resizeColumnsToContents()

        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        # Export button
        export_btn = QPushButton("📄 Export Report")
        export_btn.clicked.connect(self.export_report)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        # Close button
        close_btn = QPushButton("✓ Acknowledged")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #22C55E;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #16A34A;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def export_report(self):
        """Export expiring contracts report to CSV"""
        from datetime import datetime
        import csv

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Contract Expiry Report",
            f"contract_expiry_report_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow([
                    "Employee ID", "Name", "Position", "Department",
                    "Agency", "Contract Expiry Date", "Days Until Expiry"
                ])

                # Data
                for contract in self.expiring_contracts:
                    writer.writerow([
                        contract['emp_id'],
                        contract['name'],
                        contract['position'],
                        contract['department'],
                        contract['agency'],
                        contract['contract_expiry'],
                        contract['days_until_expiry']
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported to:\n{filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export report:\n{str(e)}"
            )


class ContractExpiryWidget(QWidget):
    """
    Widget to show contract expiry summary on dashboard
    """

    def __init__(self, db: DB, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("📅 Contract Expiry Alerts")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        # Count label
        self.count_label = QLabel("Checking...")
        self.count_label.setStyleSheet("""
            padding: 10px;
            background: #FEF3C7;
            border-left: 4px solid #F59E0B;
            border-radius: 4px;
        """)
        layout.addWidget(self.count_label)

        # View details button
        self.view_btn = QPushButton("📋 View Details")
        self.view_btn.clicked.connect(self.show_details)
        self.view_btn.setEnabled(False)
        layout.addWidget(self.view_btn)

        layout.addStretch()

        # Initialize
        self.expiring_contracts = []
        self.update_counts()

    def update_counts(self):
        """Update the count of expiring contracts"""
        checker = ContractExpiryChecker(self.db)
        self.expiring_contracts = checker.get_expiring_contracts()

        if self.expiring_contracts:
            count = len(self.expiring_contracts)
            self.count_label.setText(f"⚠️ {count} contract(s) expiring within 30 days")
            self.count_label.setStyleSheet("""
                padding: 10px;
                background: #FEE2E2;
                border-left: 4px solid #EF4444;
                border-radius: 4px;
                font-weight: bold;
            """)
            self.view_btn.setEnabled(True)
        else:
            self.count_label.setText("✓ No contracts expiring soon")
            self.count_label.setStyleSheet("""
                padding: 10px;
                background: #D1FAE5;
                border-left: 4px solid #10B981;
                border-radius: 4px;
            """)
            self.view_btn.setEnabled(False)

    def show_details(self):
        """Show detailed expiry notification dialog"""
        if self.expiring_contracts:
            dialog = ContractExpiryNotificationDialog(self.expiring_contracts, self)
            dialog.exec()
