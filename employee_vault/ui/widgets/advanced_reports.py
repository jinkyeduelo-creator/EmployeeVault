"""
Advanced Reporting Module with Charts and Visualizations
Professional reports with data visualization for business intelligence
v4.6.0: Added animated charts with smooth transitions
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import math
from employee_vault.ui.ios_button_styles import apply_ios_style


class ChartWidget(QWidget):
    """Base class for chart widgets with animation support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.data = []
        self.title = ""
        self.colors = [
            "#2196F3", "#4CAF50", "#FF9800", "#9C27B0",
            "#F44336", "#00BCD4", "#FFEB3B", "#795548"
        ]
        
        # Animation properties
        self._animation_progress = 0.0
        self._animation = QPropertyAnimation(self, b"animationProgress")
        self._animation.setDuration(800)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)

    def get_animation_progress(self):
        return self._animation_progress
    
    def set_animation_progress(self, value):
        self._animation_progress = value
        self.update()
    
    animationProgress = Property(float, get_animation_progress, set_animation_progress)

    def set_data(self, data: List, title: str = ""):
        """Set chart data and trigger animation"""
        self.data = data
        self.title = title
        # Reset and start animation
        self._animation_progress = 0.0
        self._animation.start()

    def paintEvent(self, event):
        """Paint the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw title
        if self.title:
            painter.setPen(QColor("#212121"))
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect().adjusted(10, 10, -10, -10),
                           Qt.AlignTop | Qt.AlignHCenter, self.title)


class PieChartWidget(ChartWidget):
    """Animated pie chart for showing distribution data"""

    def paintEvent(self, event):
        """Draw animated pie chart"""
        super().paintEvent(event)

        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate chart area
        margin = 60
        chart_rect = self.rect().adjusted(margin, margin + 40, -margin, -margin - 40)

        # Calculate total
        total = sum(item['value'] for item in self.data if item['value'] > 0)
        if total == 0:
            return

        # Animate: only draw portion of pie based on animation progress
        animated_total_angle = int(360 * 16 * self._animation_progress)
        
        # Draw pie slices with animation
        start_angle = 0
        for i, item in enumerate(self.data):
            if item['value'] <= 0:
                continue

            # Calculate span angle
            full_span_angle = int((item['value'] / total) * 360 * 16)
            
            # Apply animation - limit span based on remaining animated angle
            remaining_animated = animated_total_angle - start_angle
            if remaining_animated <= 0:
                break
            span_angle = min(full_span_angle, remaining_animated)

            # Draw slice
            color = QColor(self.colors[i % len(self.colors)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawPie(chart_rect, start_angle, span_angle)

            start_angle += full_span_angle

        # Draw legend (fade in with animation)
        if self._animation_progress > 0.5:
            legend_opacity = (self._animation_progress - 0.5) * 2
            painter.setOpacity(legend_opacity)
            self._draw_legend(painter, total)
            painter.setOpacity(1.0)

    def _draw_legend(self, painter: QPainter, total: float):
        """Draw legend below pie chart"""
        legend_y = self.height() - 35
        legend_x = 20

        painter.setFont(QFont("Arial", 9))

        for i, item in enumerate(self.data):
            if item['value'] <= 0:
                continue

            # Draw color box
            color = QColor(self.colors[i % len(self.colors)])
            painter.fillRect(legend_x, legend_y, 15, 15, color)

            # Draw label
            percentage = (item['value'] / total) * 100 if total > 0 else 0
            label = f"{item['label']}: {item['value']} ({percentage:.1f}%)"

            painter.setPen(QColor("#424242"))
            painter.drawText(legend_x + 20, legend_y + 12, label)

            legend_x += 200
            if legend_x > self.width() - 200:
                legend_x = 20
                legend_y += 20


class BarChartWidget(ChartWidget):
    """Animated bar chart for showing comparison data"""

    def paintEvent(self, event):
        """Draw animated bar chart"""
        super().paintEvent(event)

        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate chart area
        margin = 60
        chart_rect = self.rect().adjusted(margin, margin + 40, -margin, -margin - 60)

        # Find max value for scaling
        max_value = max((item['value'] for item in self.data), default=1)
        if max_value == 0:
            max_value = 1

        # Calculate bar dimensions
        bar_count = len(self.data)
        if bar_count == 0:
            return

        bar_spacing = 20
        available_width = chart_rect.width() - ((bar_count - 1) * bar_spacing)
        bar_width = max(20, available_width // bar_count)

        # Draw bars with animation (grow from bottom)
        x = chart_rect.left()
        for i, item in enumerate(self.data):
            # Calculate bar height with animation
            full_bar_height = int((item['value'] / max_value) * chart_rect.height())
            animated_bar_height = int(full_bar_height * self._animation_progress)
            
            bar_rect = QRect(
                x,
                chart_rect.bottom() - animated_bar_height,
                bar_width,
                animated_bar_height
            )

            # Draw bar with gradient
            color = QColor(self.colors[i % len(self.colors)])
            gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)

            painter.fillRect(bar_rect, gradient)

            # Draw value on top of bar (fade in after 70% animation)
            if self._animation_progress > 0.7:
                value_opacity = (self._animation_progress - 0.7) / 0.3
                painter.setOpacity(value_opacity)
                painter.setPen(QColor("#212121"))
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                value_text = str(item['value'])
                painter.drawText(bar_rect.adjusted(0, -20, 0, 0),
                               Qt.AlignHCenter | Qt.AlignBottom, value_text)
                painter.setOpacity(1.0)

            # Draw label below bar
            painter.setPen(QColor("#616161"))
            painter.setFont(QFont("Arial", 8))
            label_rect = QRect(x, chart_rect.bottom() + 5, bar_width, 40)
            painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                           item['label'])

            x += bar_width + bar_spacing

        # Draw Y-axis
        self._draw_y_axis(painter, chart_rect, max_value)

    def _draw_y_axis(self, painter: QPainter, chart_rect: QRect, max_value: float):
        """Draw Y-axis with labels"""
        painter.setPen(QColor("#BDBDBD"))
        painter.setFont(QFont("Arial", 8))

        # Draw 5 horizontal grid lines
        for i in range(6):
            y = chart_rect.bottom() - (i * chart_rect.height() // 5)
            painter.drawLine(chart_rect.left() - 5, y, chart_rect.right(), y)

            # Draw value label
            value = int(max_value * i / 5)
            painter.drawText(QRect(5, y - 10, 40, 20), Qt.AlignRight | Qt.AlignVCenter,
                           str(value))


class LineChartWidget(ChartWidget):
    """Line chart for showing trends over time"""

    def paintEvent(self, event):
        """Draw line chart"""
        super().paintEvent(event)

        if not self.data or len(self.data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate chart area
        margin = 60
        chart_rect = self.rect().adjusted(margin, margin + 40, -margin, -margin - 40)

        # Find max value for scaling
        max_value = max((item['value'] for item in self.data), default=1)
        if max_value == 0:
            max_value = 1

        # Calculate points
        points = []
        point_count = len(self.data)
        x_step = chart_rect.width() / (point_count - 1) if point_count > 1 else 0

        for i, item in enumerate(self.data):
            x = chart_rect.left() + (i * x_step)
            y_ratio = item['value'] / max_value
            y = chart_rect.bottom() - (y_ratio * chart_rect.height())
            points.append(QPointF(x, y))

        # Draw grid
        self._draw_grid(painter, chart_rect, max_value)

        # Draw line
        pen = QPen(QColor("#2196F3"), 3)
        painter.setPen(pen)

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Draw points
        painter.setBrush(QBrush(QColor("#2196F3")))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))

        for i, point in enumerate(points):
            painter.drawEllipse(point, 6, 6)

            # Draw value label
            painter.setPen(QColor("#212121"))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            value_text = str(self.data[i]['value'])
            painter.drawText(QRectF(point.x() - 30, point.y() - 25, 60, 20),
                           Qt.AlignHCenter | Qt.AlignBottom, value_text)

            # Draw x-axis label
            painter.setPen(QColor("#616161"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(QRectF(point.x() - 40, chart_rect.bottom() + 5, 80, 30),
                           Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                           self.data[i]['label'])

            painter.setBrush(QBrush(QColor("#2196F3")))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))

    def _draw_grid(self, painter: QPainter, chart_rect: QRect, max_value: float):
        """Draw grid lines and Y-axis labels"""
        painter.setPen(QPen(QColor("#E0E0E0"), 1, Qt.DashLine))
        painter.setFont(QFont("Arial", 8))

        # Draw 5 horizontal grid lines
        for i in range(6):
            y = chart_rect.bottom() - (i * chart_rect.height() // 5)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

            # Draw value label
            painter.setPen(QColor("#757575"))
            value = int(max_value * i / 5)
            painter.drawText(QRect(5, y - 10, 40, 20), Qt.AlignRight | Qt.AlignVCenter,
                           str(value))
            painter.setPen(QPen(QColor("#E0E0E0"), 1, Qt.DashLine))


class AdvancedReportsDialog(QDialog):
    """Advanced reports dialog with charts and visualizations"""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("📊 Advanced Reports & Analytics")
        self.setMinimumSize(1200, 800)
        self._setup_ui()
        self._load_reports()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h1>📊 Advanced Reports & Analytics</h1>")
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tab widget for different reports
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 5px;
                border-radius: 6px 6px 0 0;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
        """)

        # Tab 1: Department Distribution
        tabs.addTab(self._create_department_tab(), "📁 Department Distribution")

        # Tab 2: Employment Timeline
        tabs.addTab(self._create_timeline_tab(), "📅 Employment Timeline")

        # Tab 3: Contract Status
        tabs.addTab(self._create_contract_tab(), "📋 Contract Status")

        # Tab 4: Summary Statistics
        tabs.addTab(self._create_summary_tab(), "📈 Summary Statistics")

        layout.addWidget(tabs)

        # Close button - Phase 3: iOS frosted glass styling
        close_btn = QPushButton("✕ Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(40)
        layout.addWidget(close_btn)

    def _create_department_tab(self) -> QWidget:
        """Create department distribution tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc = QLabel("Distribution of employees across departments")
        desc.setStyleSheet("font-size: 13px; color: #757575; margin: 10px;")
        layout.addWidget(desc)

        # Pie chart
        self.dept_pie_chart = PieChartWidget()
        layout.addWidget(self.dept_pie_chart)

        # Bar chart
        self.dept_bar_chart = BarChartWidget()
        layout.addWidget(self.dept_bar_chart)

        return widget

    def _create_timeline_tab(self) -> QWidget:
        """Create employment timeline tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc = QLabel("Employee growth trend over the past 12 months")
        desc.setStyleSheet("font-size: 13px; color: #757575; margin: 10px;")
        layout.addWidget(desc)

        # Line chart
        self.timeline_chart = LineChartWidget()
        layout.addWidget(self.timeline_chart, 1)

        return widget

    def _create_contract_tab(self) -> QWidget:
        """Create contract status tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc = QLabel("Overview of contract statuses and expiry timeline")
        desc.setStyleSheet("font-size: 13px; color: #757575; margin: 10px;")
        layout.addWidget(desc)

        # Contract status pie chart
        self.contract_pie_chart = PieChartWidget()
        layout.addWidget(self.contract_pie_chart)

        # Contract expiry bar chart
        self.contract_bar_chart = BarChartWidget()
        layout.addWidget(self.contract_bar_chart)

        return widget

    def _create_summary_tab(self) -> QWidget:
        """Create summary statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc = QLabel("Quick summary statistics and key metrics")
        desc.setStyleSheet("font-size: 13px; color: #757575; margin: 10px;")
        layout.addWidget(desc)

        # Summary text
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.summary_text)

        return widget

    def _load_reports(self):
        """Load and display all reports"""
        if not self.db:
            return

        employees = self.db.all_employees()

        # Department distribution
        self._load_department_report(employees)

        # Employment timeline
        self._load_timeline_report(employees)

        # Contract status
        self._load_contract_report(employees)

        # Summary statistics
        self._load_summary_report(employees)

    def _load_department_report(self, employees: List[Dict]):
        """Load department distribution data"""
        dept_counts = {}
        for emp in employees:
            dept = emp.get('department', 'Unassigned')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Prepare data for charts
        chart_data = [
            {'label': dept, 'value': count}
            for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        self.dept_pie_chart.set_data(chart_data, "Department Distribution (Pie)")
        self.dept_bar_chart.set_data(chart_data, "Department Distribution (Bar)")

    def _load_timeline_report(self, employees: List[Dict]):
        """Load employment timeline data"""
        # Get employee count for past 12 months
        today = datetime.now()
        monthly_counts = []

        for i in range(12, 0, -1):
            month_date = today - timedelta(days=i*30)
            month_label = month_date.strftime("%b %Y")

            # Count employees hired by this month
            count = 0
            for emp in employees:
                hire_date_str = emp.get('hire_date', '')
                if hire_date_str:
                    try:
                        hire_date = datetime.strptime(hire_date_str, "%m-%d-%Y")
                        if hire_date <= month_date:
                            count += 1
                    except ValueError:
                        # Invalid date format, skip this employee
                        pass

            monthly_counts.append({'label': month_label, 'value': count})

        self.timeline_chart.set_data(monthly_counts, "Employee Growth Over Time")

    def _load_contract_report(self, employees: List[Dict]):
        """Load contract status data"""
        today = datetime.now().date()

        expired = 0
        expiring_soon = 0  # Within 30 days
        active = 0
        no_contract = 0

        expiry_months = {}

        for emp in employees:
            contract_expiry = emp.get('contract_expiry', '')
            if not contract_expiry:
                no_contract += 1
                continue

            try:
                expiry_date = datetime.strptime(contract_expiry, "%m-%d-%Y").date()
                days_left = (expiry_date - today).days

                if days_left < 0:
                    expired += 1
                elif days_left <= 30:
                    expiring_soon += 1
                else:
                    active += 1

                # Group by month for bar chart
                month_key = expiry_date.strftime("%b %Y")
                expiry_months[month_key] = expiry_months.get(month_key, 0) + 1
            except ValueError:
                # Invalid date format, count as no contract
                no_contract += 1

        # Pie chart data
        pie_data = [
            {'label': 'Active', 'value': active},
            {'label': 'Expiring Soon', 'value': expiring_soon},
            {'label': 'Expired', 'value': expired},
            {'label': 'No Contract', 'value': no_contract},
        ]
        self.contract_pie_chart.set_data(pie_data, "Contract Status Distribution")

        # Bar chart data (upcoming expirations)
        bar_data = [
            {'label': month, 'value': count}
            for month, count in sorted(list(expiry_months.items())[:6])
        ]
        self.contract_bar_chart.set_data(bar_data, "Upcoming Contract Expirations")

    def _load_summary_report(self, employees: List[Dict]):
        """Load summary statistics"""
        total = len(employees)
        if total == 0:
            self.summary_text.setHtml("<h3>No employee data available</h3>")
            return

        # Calculate statistics
        active = sum(1 for e in employees if e.get('status') == 'Active')
        resigned = sum(1 for e in employees if e.get('status') == 'Resigned')

        # Department breakdown
        dept_counts = {}
        for emp in employees:
            dept = emp.get('department', 'Unassigned')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Average tenure
        total_days = 0
        valid_count = 0
        for emp in employees:
            hire_date_str = emp.get('hire_date', '')
            if hire_date_str:
                try:
                    hire_date = datetime.strptime(hire_date_str, "%m-%d-%Y")
                    days = (datetime.now() - hire_date).days
                    total_days += days
                    valid_count += 1
                except ValueError:
                    # Invalid date format, skip this employee
                    pass

        avg_tenure_days = total_days // valid_count if valid_count > 0 else 0
        avg_tenure_months = avg_tenure_days // 30

        # Generate HTML report
        html = f"""
        <html>
        <body style="font-family: Arial; line-height: 1.8;">
            <h2 style="color: #2196F3;">📊 Employee Summary Report</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>

            <hr style="border: 1px solid #E0E0E0;">

            <h3 style="color: #4CAF50;">👥 Overall Statistics</h3>
            <ul>
                <li><strong>Total Employees:</strong> {total}</li>
                <li><strong>Active Employees:</strong> {active} ({active/total*100:.1f}%)</li>
                <li><strong>Resigned Employees:</strong> {resigned} ({resigned/total*100:.1f}%)</li>
                <li><strong>Average Tenure:</strong> {avg_tenure_months} months</li>
            </ul>

            <h3 style="color: #FF9800;">📁 Department Breakdown</h3>
            <ul>
        """

        for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            html += f"<li><strong>{dept}:</strong> {count} employees ({percentage:.1f}%)</li>"

        html += """
            </ul>

            <h3 style="color: #9C27B0;">📋 Data Quality</h3>
            <ul>
        """

        # Data completeness
        with_photos = sum(1 for e in employees if e.get('emp_id'))
        with_emergency = sum(1 for e in employees if e.get('emergency_contact_name'))
        with_gov_ids = sum(1 for e in employees if e.get('sss_number') or e.get('tin_number'))

        html += f"""
                <li><strong>Employees with Photos:</strong> Estimated {with_photos}</li>
                <li><strong>Emergency Contacts Recorded:</strong> {with_emergency} ({with_emergency/total*100:.1f}%)</li>
                <li><strong>Government IDs Recorded:</strong> {with_gov_ids} ({with_gov_ids/total*100:.1f}%)</li>
            </ul>
        </body>
        </html>
        """

        self.summary_text.setHtml(html)
