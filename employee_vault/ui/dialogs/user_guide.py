"""
Built-in User Guide Dialog
Comprehensive help system for EmployeeVault
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from employee_vault.ui.widgets import (
    AnimatedDialogBase, ModernAnimatedButton,
    NeumorphicGradientLineEdit
)
from employee_vault.ui.ios_button_styles import apply_ios_style


class UserGuideDialog(AnimatedDialogBase):
    """Interactive user guide with searchable content"""

    def __init__(self, parent=None):
        super().__init__(parent, animation_style="fade")
        self.setWindowTitle("📚 EmployeeVault User Guide")
        self.resize(1000, 700)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user guide interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h1>📚 EmployeeVault User Guide</h1>")
        header.setStyleSheet("color: #4a9eff; padding: 10px;")
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search:"))
        self.search_input = NeumorphicGradientLineEdit("Search for help topics...")
        self.search_input.setMinimumHeight(70)
        self.search_input.line_edit.textChanged.connect(self._filter_content)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Main content area (splitter for sidebar and content)
        splitter = QSplitter(Qt.Horizontal)

        # Left sidebar - Table of Contents
        self.toc_list = QListWidget()
        self.toc_list.setMaximumWidth(250)
        self.toc_list.currentItemChanged.connect(self._on_topic_changed)
        self._populate_toc()
        splitter.addWidget(self.toc_list)

        # Right content area
        self.content_area = QTextBrowser()
        self.content_area.setOpenExternalLinks(True)
        self.content_area.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(45, 45, 48, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        splitter.addWidget(self.content_area)

        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Show first topic
        self.toc_list.setCurrentRow(0)

    def _populate_toc(self):
        """Populate table of contents"""
        topics = [
            ("🚀 Getting Started", "getting_started"),
            ("👤 Managing Employees", "managing_employees"),
            ("🔍 Search & Filter", "search_filter"),
            ("📊 Reports & Analytics", "reports"),
            ("🎴 ID Cards & Letters", "id_cards_letters"),
            ("📁 File Management", "file_management"),
            ("👥 User Management", "user_management"),
            ("⚙️ Settings & Configuration", "settings"),
            ("💾 Backup & Restore", "backup_restore"),
            ("⌨️ Keyboard Shortcuts", "keyboard_shortcuts"),
            ("❓ Troubleshooting", "troubleshooting"),
            ("💡 Tips & Tricks", "tips_tricks"),
        ]

        for title, key in topics:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, key)
            self.toc_list.addItem(item)

    def _on_topic_changed(self, current, previous):
        """Display content when topic is selected"""
        if not current:
            return

        topic_key = current.data(Qt.UserRole)
        content = self._get_content(topic_key)
        self.content_area.setHtml(content)

    def _filter_content(self, search_text):
        """Filter topics based on search"""
        search_text = search_text.lower()

        for i in range(self.toc_list.count()):
            item = self.toc_list.item(i)
            topic_key = item.data(Qt.UserRole)
            topic_content = self._get_content(topic_key)

            # Check if search text appears in title or content
            visible = search_text in item.text().lower() or search_text in topic_content.lower()
            item.setHidden(not visible)

    def _get_content(self, topic_key):
        """Get HTML content for each topic"""

        content_map = {
            "getting_started": """
                <h2>🚀 Getting Started with EmployeeVault</h2>

                <h3>Welcome!</h3>
                <p>EmployeeVault is a comprehensive employee management system designed for businesses
                of all sizes. This guide will help you get started quickly.</p>

                <h3>First Login</h3>
                <ol>
                    <li><b>Default Credentials:</b> Username: <code>admin</code> / Password: <code>admin</code></li>
                    <li><b>Change Password:</b> Go to Settings → Change Password immediately</li>
                    <li><b>Security:</b> Use a strong password (12+ characters, uppercase, lowercase, numbers, special chars)</li>
                </ol>

                <h3>Main Dashboard</h3>
                <p>After logging in, you'll see:</p>
                <ul>
                    <li><b>Quick Stats:</b> Total employees, active/inactive counts, contract expiries</li>
                    <li><b>Sidebar:</b> Navigate between Employees, Reports, Settings</li>
                    <li><b>Search Bar:</b> Quick search for any employee</li>
                </ul>

                <h3>Adding Your First Employee</h3>
                <ol>
                    <li>Click <b>"➕ Add Employee"</b> button</li>
                    <li>Fill in required fields (marked with *)</li>
                    <li>Upload employee photo (optional)</li>
                    <li>Click <b>"💾 Save"</b></li>
                </ol>

                <h3>Quick Tips</h3>
                <ul>
                    <li>✅ Employee ID is auto-generated based on department and hire date</li>
                    <li>✅ Photos are automatically compressed to save space</li>
                    <li>✅ Duplicate employee detection prevents accidental duplicates</li>
                    <li>✅ Auto-save every 30 minutes (session timeout)</li>
                </ul>
            """,

            "managing_employees": """
                <h2>👤 Managing Employees</h2>

                <h3>Adding a New Employee</h3>
                <ol>
                    <li>Click <b>"➕ Add Employee"</b> in the toolbar</li>
                    <li>Fill in employee information:
                        <ul>
                            <li><b>Required:</b> First Name, Last Name, Department, Position, Hire Date</li>
                            <li><b>Optional:</b> Middle Name, Email, Phone, Salary, etc.</li>
                        </ul>
                    </li>
                    <li>Select <b>Department:</b> Office, Warehouse, or Store (with branch)</li>
                    <li>Upload photo by clicking <b>"Upload Photo"</b></li>
                    <li>Add any notes in the Notes section</li>
                    <li>Click <b>"💾 Save"</b></li>
                </ol>

                <h3>Editing Employee Information</h3>
                <ol>
                    <li>Find the employee using search or browse the list</li>
                    <li>Click on the employee row</li>
                    <li>Click <b>"✏️ Edit"</b> button</li>
                    <li>Make your changes</li>
                    <li>Click <b>"💾 Save"</b> to update</li>
                </ol>

                <h3>Viewing Employee Details</h3>
                <p>Click on any employee row to see full details:</p>
                <ul>
                    <li>Personal Information</li>
                    <li>Employment Details</li>
                    <li>Contract Information</li>
                    <li>Attached Files</li>
                    <li>Modification History</li>
                </ul>

                <h3>Deleting an Employee</h3>
                <ol>
                    <li>Select the employee</li>
                    <li>Click <b>"🗑️ Delete"</b> button</li>
                    <li>Confirm deletion</li>
                    <li><b>Note:</b> Deleted employees are archived, not permanently removed</li>
                </ol>

                <h3>Employee Status</h3>
                <ul>
                    <li><b>Active:</b> Currently employed (no resign date)</li>
                    <li><b>Inactive:</b> No longer employed (has resign date)</li>
                    <li><b>Contract:</b> Employment type (Regular or Agency)</li>
                </ul>

                <h3>Special Features</h3>
                <ul>
                    <li>✨ <b>Duplicate Detection:</b> System warns if similar name exists</li>
                    <li>✨ <b>Auto-complete:</b> Position field suggests common positions</li>
                    <li>✨ <b>Photo Compression:</b> Large photos are automatically optimized</li>
                    <li>✨ <b>Validation:</b> Email, phone, and ID formats are checked</li>
                </ul>
            """,

            "search_filter": """
                <h2>🔍 Search & Filter</h2>

                <h3>Quick Search</h3>
                <p>Use the search bar at the top to find employees instantly:</p>
                <ul>
                    <li>Search by <b>Name</b> (first, middle, or last)</li>
                    <li>Search by <b>Employee ID</b></li>
                    <li>Search by <b>Department</b></li>
                    <li>Search by <b>Position</b></li>
                </ul>
                <p><b>Tip:</b> Search updates in real-time as you type (300ms delay)</p>

                <h3>Filter Options</h3>
                <p>Click the <b>"Filter"</b> button to access advanced filtering:</p>
                <ul>
                    <li><b>Status:</b> All, Active, Inactive</li>
                    <li><b>Department:</b> Office, Warehouse, Store, or specific branch</li>
                    <li><b>Employment Type:</b> Regular, Agency</li>
                    <li><b>Contract Expiry:</b> Expiring soon, Expired, etc.</li>
                </ul>

                <h3>Sorting</h3>
                <p>Click on column headers to sort:</p>
                <ul>
                    <li>Employee ID (ascending/descending)</li>
                    <li>Name (A-Z or Z-A)</li>
                    <li>Department</li>
                    <li>Hire Date (newest/oldest)</li>
                </ul>

                <h3>Multi-Select</h3>
                <ol>
                    <li>Check the checkbox next to employee names</li>
                    <li>Select multiple employees</li>
                    <li>Use bulk operations (see Bulk Operations section)</li>
                </ol>

                <h3>Search Tips</h3>
                <ul>
                    <li>💡 Partial matches work: "John" finds "Johnny", "Johnson", etc.</li>
                    <li>💡 Case-insensitive: "smith" finds "Smith"</li>
                    <li>💡 Search is instant after 300ms of typing</li>
                    <li>💡 Clear search to see all employees</li>
                </ul>
            """,

            "reports": """
                <h2>📊 Reports & Analytics</h2>

                <h3>Available Reports</h3>
                <p>Access reports from the sidebar → <b>Reports</b></p>

                <h4>1. Employee Summary Report</h4>
                <ul>
                    <li>Total employees by department</li>
                    <li>Active vs. Inactive breakdown</li>
                    <li>Employment type distribution</li>
                    <li>Export to Excel or JSON</li>
                </ul>

                <h4>2. Contract Expiry Report</h4>
                <ul>
                    <li>Contracts expiring this month</li>
                    <li>Contracts expiring next month</li>
                    <li>Expired contracts</li>
                    <li>Renewal recommendations</li>
                </ul>

                <h4>3. Department Analysis</h4>
                <ul>
                    <li>Headcount by department</li>
                    <li>Average tenure</li>
                    <li>Turnover rate</li>
                    <li>Position distribution</li>
                </ul>

                <h4>4. Advanced Reports</h4>
                <ul>
                    <li>Custom date ranges</li>
                    <li>Salary analysis (if permitted)</li>
                    <li>Hiring trends</li>
                    <li>Audit log reports</li>
                </ul>

                <h3>Generating Reports</h3>
                <ol>
                    <li>Go to <b>Reports</b> section</li>
                    <li>Select report type</li>
                    <li>Set date range (if applicable)</li>
                    <li>Click <b>"Generate Report"</b></li>
                    <li>Preview on screen</li>
                    <li>Export to Excel or JSON</li>
                </ol>

                <h3>Export Formats</h3>
                <ul>
                    <li><b>Excel (.xlsx):</b> Full formatting, charts, formulas</li>
                    <li><b>JSON (.json):</b> Raw data for further processing</li>
                    <li><b>Print:</b> Formatted printable version</li>
                </ul>

                <h3>Scheduling Reports (Future Feature)</h3>
                <p><i>Coming soon: Automatic report generation on schedule</i></p>
            """,

            "id_cards_letters": """
                <h2>🎴 ID Cards & Letters</h2>

                <h3>Generating ID Cards</h3>
                <ol>
                    <li>Select one or more employees</li>
                    <li>Click <b>"🎴 Generate ID Card"</b></li>
                    <li>Choose template:
                        <ul>
                            <li>Standard Card (front only)</li>
                            <li>Front & Back Card</li>
                            <li>Custom template</li>
                        </ul>
                    </li>
                    <li>Preview the card</li>
                    <li>Click <b>"💾 Save"</b> or <b>"🖨️ Print"</b></li>
                </ol>

                <h3>ID Card Features</h3>
                <ul>
                    <li>✅ Employee photo automatically included</li>
                    <li>✅ QR code with employee ID</li>
                    <li>✅ Company logo (configurable)</li>
                    <li>✅ Professional layout</li>
                    <li>✅ Print-ready format</li>
                </ul>

                <h3>Generating Letters</h3>
                <p>Generate professional letters for employees:</p>

                <h4>Letter Types:</h4>
                <ul>
                    <li><b>Employment Certificate:</b> Proof of employment</li>
                    <li><b>Salary Certificate:</b> For loan applications</li>
                    <li><b>Contract Letter:</b> Employment contract</li>
                    <li><b>Termination Letter:</b> End of employment</li>
                    <li><b>Custom Letter:</b> Use template editor</li>
                </ul>

                <h3>Letter Generation Steps</h3>
                <ol>
                    <li>Select employee</li>
                    <li>Click <b>"📄 Generate Letter"</b></li>
                    <li>Choose letter type</li>
                    <li>Fill in additional details</li>
                    <li>Preview letter</li>
                    <li>Save as PDF or Print</li>
                </ol>

                <h3>Letter Templates</h3>
                <p>Letters include:</p>
                <ul>
                    <li>Company letterhead</li>
                    <li>Employee details (auto-filled)</li>
                    <li>Professional formatting</li>
                    <li>Signature block</li>
                    <li>Date and reference number</li>
                </ul>

                <h3>Customization</h3>
                <p>Customize templates in Settings:</p>
                <ul>
                    <li>Company name and logo</li>
                    <li>Letterhead design</li>
                    <li>Signature</li>
                    <li>Footer information</li>
                </ul>
            """,

            "file_management": """
                <h2>📁 File Management</h2>

                <h3>Attaching Files to Employees</h3>
                <ol>
                    <li>Open employee details</li>
                    <li>Go to <b>"Files"</b> section</li>
                    <li>Click <b>"📎 Attach File"</b></li>
                    <li>Select file(s) from your computer</li>
                    <li>Files are automatically stored</li>
                </ol>

                <h3>Supported File Types</h3>
                <ul>
                    <li><b>Documents:</b> PDF, DOCX, DOC, TXT</li>
                    <li><b>Images:</b> JPG, PNG, GIF, BMP</li>
                    <li><b>Spreadsheets:</b> XLSX, XLS, CSV</li>
                    <li><b>Others:</b> ZIP, RAR (archives)</li>
                </ul>

                <h3>Managing Files</h3>
                <ul>
                    <li><b>View:</b> Double-click to open file</li>
                    <li><b>Download:</b> Right-click → Save As</li>
                    <li><b>Delete:</b> Select file → Click Delete button</li>
                    <li><b>Rename:</b> Not supported (re-upload if needed)</li>
                </ul>

                <h3>File Storage</h3>
                <p>Files are stored in: <code>employee_files/[Employee_ID]/</code></p>
                <ul>
                    <li>✅ Organized by employee ID</li>
                    <li>✅ Original filenames preserved</li>
                    <li>✅ Included in backups</li>
                    <li>✅ Portable (can be moved with database)</li>
                </ul>

                <h3>Photo Management</h3>
                <ul>
                    <li><b>Upload:</b> Click "Upload Photo" in employee form</li>
                    <li><b>Compression:</b> Photos over 500KB are auto-compressed</li>
                    <li><b>Format:</b> Converted to PNG for consistency</li>
                    <li><b>Location:</b> <code>employee_photos/[Employee_ID].png</code></li>
                </ul>

                <h3>Batch Photo Upload</h3>
                <ol>
                    <li>Go to <b>Tools → Batch Photo Upload</b></li>
                    <li>Select multiple photos</li>
                    <li>Match photos to employees by filename</li>
                    <li>Upload all at once</li>
                </ol>

                <h3>File Limitations</h3>
                <ul>
                    <li>Max file size: 10MB per file</li>
                    <li>Photos: Auto-compressed to ~500KB</li>
                    <li>Total storage: Limited by disk space</li>
                </ul>
            """,

            "user_management": """
                <h2>👥 User Management</h2>
                <p><i>Admin users only</i></p>

                <h3>User Roles</h3>
                <ul>
                    <li><b>Admin:</b> Full access to everything</li>
                    <li><b>Manager:</b> View, add, edit employees (no delete)</li>
                    <li><b>User:</b> View-only access</li>
                </ul>

                <h3>Adding a New User</h3>
                <ol>
                    <li>Go to <b>Settings → User Management</b></li>
                    <li>Click <b>"➕ Add User"</b></li>
                    <li>Fill in user details:
                        <ul>
                            <li>Username (alphanumeric, no spaces)</li>
                            <li>Full Name</li>
                            <li>Password (12+ characters, complex)</li>
                            <li>Role (Admin/Manager/User)</li>
                        </ul>
                    </li>
                    <li>Click <b>"Create User"</b></li>
                </ol>

                <h3>Password Requirements</h3>
                <p>Passwords must have:</p>
                <ul>
                    <li>✅ At least 12 characters</li>
                    <li>✅ Uppercase letters (A-Z)</li>
                    <li>✅ Lowercase letters (a-z)</li>
                    <li>✅ Numbers (0-9)</li>
                    <li>✅ Special characters (!@#$%^&*)</li>
                </ul>
                <p><b>New Feature:</b> Password strength meter shows real-time strength!</p>

                <h3>Editing Users</h3>
                <ol>
                    <li>Select user from list</li>
                    <li>Click <b>"✏️ Edit"</b></li>
                    <li>Modify name or role</li>
                    <li>Click <b>"Save"</b></li>
                </ol>

                <h3>Resetting Passwords</h3>
                <ol>
                    <li>Select user</li>
                    <li>Click <b>"🔑 Reset Password"</b></li>
                    <li>Enter new password</li>
                    <li>Confirm password</li>
                    <li>Click <b>"Reset"</b></li>
                </ol>

                <h3>Deleting Users</h3>
                <ol>
                    <li>Select user</li>
                    <li>Click <b>"🗑️ Delete"</b></li>
                    <li>Confirm deletion</li>
                    <li><b>Note:</b> Cannot delete yourself or last admin</li>
                </ol>

                <h3>Session Management</h3>
                <ul>
                    <li><b>Auto-logout:</b> After 30 minutes of inactivity</li>
                    <li><b>Active Sessions:</b> View in Session Monitor</li>
                    <li><b>Force Logout:</b> Admin can end user sessions</li>
                </ul>

                <h3>Permissions by Role</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Permission</th><th>Admin</th><th>Manager</th><th>User</th></tr>
                    <tr><td>View Employees</td><td>✅</td><td>✅</td><td>✅</td></tr>
                    <tr><td>Add Employees</td><td>✅</td><td>✅</td><td>❌</td></tr>
                    <tr><td>Edit Employees</td><td>✅</td><td>✅</td><td>❌</td></tr>
                    <tr><td>Delete Employees</td><td>✅</td><td>❌</td><td>❌</td></tr>
                    <tr><td>Manage Users</td><td>✅</td><td>❌</td><td>❌</td></tr>
                    <tr><td>Generate Reports</td><td>✅</td><td>✅</td><td>✅</td></tr>
                    <tr><td>Backup/Restore</td><td>✅</td><td>❌</td><td>❌</td></tr>
                </table>
            """,

            "settings": """
                <h2>⚙️ Settings & Configuration</h2>

                <h3>Application Settings</h3>
                <p>Access: Menu → Settings</p>

                <h4>General Settings</h4>
                <ul>
                    <li><b>Company Name:</b> Displayed on headers and documents</li>
                    <li><b>Company Logo:</b> Upload your logo (PNG/JPG)</li>
                    <li><b>Theme:</b> Choose UI color theme</li>
                    <li><b>Language:</b> Currently English only</li>
                </ul>

                <h4>Department Management</h4>
                <ul>
                    <li>Add new departments</li>
                    <li>Add store branches</li>
                    <li>Edit existing departments</li>
                    <li>Cannot delete if employees assigned</li>
                </ul>

                <h4>Agency Management</h4>
                <ul>
                    <li>Add new agencies</li>
                    <li>Edit agency names</li>
                    <li>Used for contract employees</li>
                </ul>

                <h4>Security Settings</h4>
                <ul>
                    <li><b>Session Timeout:</b> Default 30 minutes</li>
                    <li><b>Password Policy:</b> Enforcement level</li>
                    <li><b>Login Attempts:</b> Max failed attempts</li>
                </ul>

                <h4>Backup Settings</h4>
                <ul>
                    <li><b>Auto-Backup:</b> Schedule automatic backups</li>
                    <li><b>Backup Location:</b> Choose where to save</li>
                    <li><b>Retention:</b> Keep last N backups</li>
                </ul>

                <h3>ID Card Settings</h3>
                <ul>
                    <li>Choose template design</li>
                    <li>Customize card layout</li>
                    <li>Set QR code options</li>
                    <li>Logo placement</li>
                </ul>

                <h3>Letter Settings</h3>
                <ul>
                    <li>Edit letter templates</li>
                    <li>Customize letterhead</li>
                    <li>Set default signature</li>
                    <li>Footer information</li>
                </ul>

                <h3>Network Settings (LAN)</h3>
                <ul>
                    <li><b>Database Location:</b> Local or network path</li>
                    <li><b>Shared Photos:</b> Network photo storage</li>
                    <li><b>Server Mode:</b> Enable multi-user access</li>
                </ul>

                <h3>Advanced Settings</h3>
                <ul>
                    <li><b>Database Optimization:</b> Rebuild indexes</li>
                    <li><b>Clear Cache:</b> Reset temporary data</li>
                    <li><b>Audit Log:</b> View/export system logs</li>
                    <li><b>Debug Mode:</b> Enable detailed logging</li>
                </ul>
            """,

            "backup_restore": """
                <h2>💾 Backup & Restore</h2>

                <h3>Creating Backups</h3>
                <p>Regular backups are essential for data safety!</p>

                <h4>Manual Backup</h4>
                <ol>
                    <li>Go to <b>Settings → Backup & Restore</b></li>
                    <li>Click <b>"💾 Create Backup Now"</b></li>
                    <li>Choose backup location</li>
                    <li>Wait for completion</li>
                    <li>Verify backup file created</li>
                </ol>

                <h4>Scheduled Backups</h4>
                <ol>
                    <li>Go to <b>Settings → Scheduled Backup</b></li>
                    <li>Enable automatic backups</li>
                    <li>Set schedule:
                        <ul>
                            <li>Daily (recommended)</li>
                            <li>Weekly</li>
                            <li>Monthly</li>
                        </ul>
                    </li>
                    <li>Set backup time</li>
                    <li>Choose retention (how many to keep)</li>
                </ol>

                <h3>Backup Contents</h3>
                <p>Backups include:</p>
                <ul>
                    <li>✅ All employee data</li>
                    <li>✅ Employee photos</li>
                    <li>✅ Attached files</li>
                    <li>✅ User accounts</li>
                    <li>✅ Settings and configuration</li>
                    <li>✅ Audit logs</li>
                </ul>

                <h3>Backup Location</h3>
                <ul>
                    <li><b>Default:</b> <code>backups/</code> folder</li>
                    <li><b>Network:</b> NAS or network drive</li>
                    <li><b>External:</b> USB drive or external HD</li>
                    <li><b>Cloud:</b> Copy to cloud storage manually</li>
                </ul>

                <h3>Restoring from Backup</h3>
                <p><b>⚠️ Warning:</b> This will replace current data!</p>
                <ol>
                    <li>Go to <b>Settings → Backup & Restore</b></li>
                    <li>Click <b>"📂 Restore from Backup"</b></li>
                    <li>Select backup file</li>
                    <li>Preview backup contents</li>
                    <li>Confirm restore (creates current backup first)</li>
                    <li>Wait for restore to complete</li>
                    <li>Restart application</li>
                </ol>

                <h3>Archive Manager</h3>
                <p>Deleted employees are archived, not permanently deleted:</p>
                <ul>
                    <li>View archived employees</li>
                    <li>Restore from archive</li>
                    <li>Permanently delete from archive</li>
                    <li>Export archived data</li>
                </ul>

                <h3>Backup Best Practices</h3>
                <ul>
                    <li>✅ Back up daily (or after major changes)</li>
                    <li>✅ Keep multiple backup versions</li>
                    <li>✅ Store backups in different locations</li>
                    <li>✅ Test restore occasionally</li>
                    <li>✅ Protect backups (encrypted storage)</li>
                </ul>

                <h3>Disaster Recovery</h3>
                <p>If database is corrupted:</p>
                <ol>
                    <li>Don't panic! Backups are your safety net</li>
                    <li>Close application</li>
                    <li>Locate latest backup</li>
                    <li>Restore from backup</li>
                    <li>Verify data integrity</li>
                </ol>
            """,

            "keyboard_shortcuts": """
                <h2>⌨️ Keyboard Shortcuts</h2>

                <h3>Global Shortcuts</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Shortcut</th><th>Action</th></tr>
                    <tr><td>Ctrl + N</td><td>New Employee</td></tr>
                    <tr><td>Ctrl + F</td><td>Search/Find</td></tr>
                    <tr><td>Ctrl + S</td><td>Save Current Form</td></tr>
                    <tr><td>Ctrl + P</td><td>Print</td></tr>
                    <tr><td>Ctrl + Q</td><td>Quit Application</td></tr>
                    <tr><td>F1</td><td>Help (this guide)</td></tr>
                    <tr><td>F5</td><td>Refresh Data</td></tr>
                    <tr><td>Esc</td><td>Close Dialog/Cancel</td></tr>
                </table>

                <h3>Employee List</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Shortcut</th><th>Action</th></tr>
                    <tr><td>↑ ↓</td><td>Navigate employees</td></tr>
                    <tr><td>Enter</td><td>Open selected employee</td></tr>
                    <tr><td>Delete</td><td>Delete selected employee</td></tr>
                    <tr><td>Ctrl + A</td><td>Select all</td></tr>
                    <tr><td>Ctrl + Click</td><td>Multi-select</td></tr>
                </table>

                <h3>Form Editing</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Shortcut</th><th>Action</th></tr>
                    <tr><td>Tab</td><td>Next field</td></tr>
                    <tr><td>Shift + Tab</td><td>Previous field</td></tr>
                    <tr><td>Ctrl + S</td><td>Save form</td></tr>
                    <tr><td>Esc</td><td>Cancel editing</td></tr>
                </table>

                <h3>Navigation</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Shortcut</th><th>Action</th></tr>
                    <tr><td>Alt + 1</td><td>Go to Dashboard</td></tr>
                    <tr><td>Alt + 2</td><td>Go to Employees</td></tr>
                    <tr><td>Alt + 3</td><td>Go to Reports</td></tr>
                    <tr><td>Alt + 4</td><td>Go to Settings</td></tr>
                </table>

                <h3>Tips</h3>
                <ul>
                    <li>💡 Most dialogs respond to Enter (confirm) and Esc (cancel)</li>
                    <li>💡 Use Tab to navigate forms quickly</li>
                    <li>💡 Ctrl+Click for multi-select in lists</li>
                    <li>💡 F5 refreshes data from database</li>
                </ul>
            """,

            "troubleshooting": """
                <h2>❓ Troubleshooting</h2>

                <h3>Common Issues</h3>

                <h4>1. Application Won't Start</h4>
                <p><b>Symptoms:</b> Application crashes or shows error on startup</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Check <code>logs/employee_vault.log</code> for errors</li>
                    <li>Verify database file exists and is not corrupted</li>
                    <li>Try running database integrity check</li>
                    <li>Restore from backup if needed</li>
                    <li>Check disk space (need at least 100MB free)</li>
                </ul>

                <h4>2. Can't Login</h4>
                <p><b>Symptoms:</b> Login fails with correct credentials</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Verify username and password (case-sensitive)</li>
                    <li>Check Caps Lock is OFF</li>
                    <li>Reset password using security questions</li>
                    <li>Contact admin to reset your password</li>
                    <li>Check session limit not reached</li>
                </ul>

                <h4>3. Slow Performance</h4>
                <p><b>Symptoms:</b> Application is slow, searches take long</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Go to Settings → Advanced → Rebuild Indexes</li>
                    <li>Check database size (optimize if >1GB)</li>
                    <li>Close other applications</li>
                    <li>Verify network connection (if using network DB)</li>
                    <li>Check system RAM (need at least 4GB)</li>
                </ul>

                <h4>4. Photo Upload Fails</h4>
                <p><b>Symptoms:</b> Can't upload employee photos</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Check file size (max 5MB)</li>
                    <li>Verify file format (JPG, PNG, BMP, GIF)</li>
                    <li>Check disk space available</li>
                    <li>Verify <code>employee_photos/</code> folder exists</li>
                    <li>Check file permissions</li>
                </ul>

                <h4>5. Database Locked Error</h4>
                <p><b>Symptoms:</b> "Database is locked" message</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Close all other instances of EmployeeVault</li>
                    <li>Wait a few seconds and retry</li>
                    <li>Check no other program is using the database</li>
                    <li>Restart application</li>
                    <li>If persists, restore from backup</li>
                </ul>

                <h4>6. Reports Won't Generate</h4>
                <p><b>Symptoms:</b> Report generation fails or shows errors</p>
                <p><b>Solutions:</b></p>
                <ul>
                    <li>Check you have employees in database</li>
                    <li>Verify date range is valid</li>
                    <li>Check permissions (need Manager or Admin)</li>
                    <li>Try smaller date range</li>
                    <li>Check logs for specific error</li>
                </ul>

                <h3>Error Messages</h3>

                <h4>"Access Denied"</h4>
                <p>Your user role doesn't have permission for this action. Contact admin.</p>

                <h4>"Database Integrity Check Failed"</h4>
                <p>Database may be corrupted. Restore from latest backup immediately.</p>

                <h4>"Session Timeout"</h4>
                <p>You've been idle for 30+ minutes. Login again to continue.</p>

                <h4>"Duplicate Employee Detected"</h4>
                <p>Similar name already exists. Verify you're not creating duplicate entry.</p>

                <h3>Getting Help</h3>
                <ul>
                    <li><b>Check Logs:</b> <code>logs/employee_vault.log</code></li>
                    <li><b>Audit Trail:</b> Settings → Audit Log</li>
                    <li><b>Database Check:</b> Automatic on startup</li>
                    <li><b>Backup First:</b> Always backup before major troubleshooting</li>
                </ul>

                <h3>When to Restore from Backup</h3>
                <ul>
                    <li>Database corruption detected</li>
                    <li>Data loss occurred</li>
                    <li>Application unstable after changes</li>
                    <li>Accidental bulk delete</li>
                </ul>
            """,

            "tips_tricks": """
                <h2>💡 Tips & Tricks</h2>

                <h3>Productivity Tips</h3>

                <h4>1. Quick Search</h4>
                <ul>
                    <li>Use Ctrl+F to instantly jump to search</li>
                    <li>Search updates in real-time (300ms delay)</li>
                    <li>Partial names work: "Jon" finds "Jonathan"</li>
                </ul>

                <h4>2. Bulk Operations</h4>
                <ul>
                    <li>Select multiple employees with checkboxes</li>
                    <li>Change department for many at once</li>
                    <li>Export selected employees only</li>
                    <li>Generate ID cards in batch</li>
                </ul>

                <h4>3. Auto-Complete</h4>
                <ul>
                    <li>Position field suggests common positions</li>
                    <li>Type a few letters, get suggestions</li>
                    <li>Saves time on repetitive data entry</li>
                </ul>

                <h4>4. Smart Photo Upload</h4>
                <ul>
                    <li>Photos over 500KB are auto-compressed</li>
                    <li>No need to manually resize</li>
                    <li>Maintains quality while saving space</li>
                    <li>Saves 84% storage on average!</li>
                </ul>

                <h3>Data Entry Tips</h3>

                <h4>Employee ID Auto-Generation</h4>
                <ul>
                    <li>Format: <code>DEPT-XXX-YY</code></li>
                    <li>DEPT = Department code (O/W/S)</li>
                    <li>XXX = Sequential number</li>
                    <li>YY = Hire year (last 2 digits)</li>
                    <li>Example: <code>O-001-25</code> (Office, 1st, 2025)</li>
                </ul>

                <h4>Contract Tracking</h4>
                <ul>
                    <li>Set contract start date and duration</li>
                    <li>Expiry date auto-calculated</li>
                    <li>Get reminders before expiry</li>
                    <li>Generate renewal letters easily</li>
                </ul>

                <h4>Phone Number Format</h4>
                <ul>
                    <li>Philippine numbers: +63 9XX XXX XXXX</li>
                    <li>Auto-formatted from 09XX, 9XX formats</li>
                    <li>Validated for correct format</li>
                </ul>

                <h3>Organization Tips</h3>

                <h4>Department Structure</h4>
                <ul>
                    <li><b>Office:</b> Admin, HR, Accounting, etc.</li>
                    <li><b>Warehouse:</b> Operations, Logistics</li>
                    <li><b>Store:</b> Retail locations (with branch names)</li>
                </ul>

                <h4>File Attachments</h4>
                <ul>
                    <li>Attach important documents per employee</li>
                    <li>Examples: Resume, Certificates, IDs</li>
                    <li>Organized automatically by employee</li>
                    <li>Included in backups</li>
                </ul>

                <h4>Notes Section</h4>
                <ul>
                    <li>Use for important remarks</li>
                    <li>Training records</li>
                    <li>Performance notes</li>
                    <li>Special instructions</li>
                </ul>

                <h3>Security Tips</h3>

                <h4>Strong Passwords</h4>
                <ul>
                    <li>Use password strength meter (new!)</li>
                    <li>Aim for "Strong" (90+ points)</li>
                    <li>Mix: uppercase, lowercase, numbers, symbols</li>
                    <li>Avoid: birthdays, names, common words</li>
                    <li>Example: <code>Empl0y33V@ult2025!</code></li>
                </ul>

                <h4>Session Security</h4>
                <ul>
                    <li>Auto-logout after 30 minutes idle</li>
                    <li>Lock screen when away (Ctrl+L)</li>
                    <li>Don't share credentials</li>
                    <li>Change password periodically</li>
                </ul>

                <h3>Backup Tips</h3>

                <h4>3-2-1 Backup Rule</h4>
                <ul>
                    <li>3 copies of data (original + 2 backups)</li>
                    <li>2 different storage types (HD + USB)</li>
                    <li>1 copy off-site (different location)</li>
                </ul>

                <h4>Backup Schedule</h4>
                <ul>
                    <li><b>Daily:</b> If adding employees frequently</li>
                    <li><b>Weekly:</b> For moderate use</li>
                    <li><b>Before:</b> Major changes, updates</li>
                    <li><b>After:</b> Bulk operations, imports</li>
                </ul>

                <h3>Advanced Features</h3>

                <h4>Audit Trail</h4>
                <ul>
                    <li>Every action is logged</li>
                    <li>View who changed what and when</li>
                    <li>Export for compliance</li>
                    <li>Searchable by date, user, action</li>
                </ul>

                <h4>Archive vs Delete</h4>
                <ul>
                    <li>Delete = Move to archive (reversible)</li>
                    <li>Archive = Soft delete, can restore</li>
                    <li>Permanent delete = From archive only</li>
                    <li>Protects against accidental deletion</li>
                </ul>

                <h4>Excel Import (Future)</h4>
                <ul>
                    <li>Import employee data from Excel</li>
                    <li>Bulk data entry made easy</li>
                    <li>Validation before import</li>
                    <li>Preview changes first</li>
                </ul>

                <h3>Hidden Features</h3>
                <ul>
                    <li>🎯 Double-click photo to view fullscreen</li>
                    <li>🎯 Right-click on table for context menu</li>
                    <li>🎯 Ctrl+Click for multi-select</li>
                    <li>🎯 F5 to refresh data instantly</li>
                    <li>🎯 Click column headers to sort</li>
                </ul>

                <h3>Performance Optimization</h3>
                <ul>
                    <li>Rebuild indexes monthly (Settings)</li>
                    <li>Archive old employees periodically</li>
                    <li>Compress photos before upload (or let auto-compress)</li>
                    <li>Clean up old backups (keep last 10)</li>
                </ul>
            """
        }

        return content_map.get(topic_key, "<p>Content not found</p>")
