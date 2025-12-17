"""
Email Notifications for Employee Vault
Sends notifications for contract expiry, security events, etc.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class EmailNotifier:
    """Email notification service for Employee Vault"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize email notifier with SMTP configuration.
        
        Args:
            config: Dict with smtp_server, smtp_port, username, password, from_email
        """
        self.config = config or {}
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.from_email = self.config.get('from_email', '')
        self.enabled = bool(self.username and self.password)
    
    def is_configured(self) -> bool:
        """Check if email notifications are properly configured"""
        return bool(self.username and self.password and self.from_email)
    
    def send_email(self, to_email: str, subject: str, body_html: str, 
                   body_text: str = None) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, derived from HTML if not provided)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logging.warning("Email notifications not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Plain text version
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            
            # HTML version
            msg.attach(MIMEText(body_html, 'html'))
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logging.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_contract_expiry_notification(self, admin_email: str, 
                                          expiring_employees: List[Dict]) -> bool:
        """
        Send contract expiry notification to admin.
        
        Args:
            admin_email: Admin's email address
            expiring_employees: List of employees with expiring contracts
        
        Returns:
            True if sent successfully
        """
        if not expiring_employees:
            return True
        
        # Group by urgency
        expired = [e for e in expiring_employees if e.get('days_left', 0) < 0]
        critical = [e for e in expiring_employees if 0 <= e.get('days_left', 0) <= 7]
        warning = [e for e in expiring_employees if 7 < e.get('days_left', 0) <= 30]
        
        subject = f"⚠️ Contract Expiry Alert - {len(expiring_employees)} Employees Need Attention"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }}
                .header {{ background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 20px; border-radius: 8px; }}
                .section {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
                .expired {{ background: #ffebee; border-left: 4px solid #f44336; }}
                .critical {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
                .warning {{ background: #fffde7; border-left: 4px solid #ffeb3b; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f5f5f5; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Employee Vault - Contract Expiry Report</h1>
                <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        """
        
        if expired:
            body_html += f"""
            <div class="section expired">
                <h2>🔴 Expired Contracts ({len(expired)})</h2>
                <table>
                    <tr><th>Employee</th><th>ID</th><th>Department</th><th>Expired</th></tr>
            """
            for emp in expired:
                body_html += f"""
                    <tr>
                        <td>{emp.get('name', 'N/A')}</td>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{abs(emp.get('days_left', 0))} days ago</td>
                    </tr>
                """
            body_html += "</table></div>"
        
        if critical:
            body_html += f"""
            <div class="section critical">
                <h2>🟠 Critical - Expiring Within 7 Days ({len(critical)})</h2>
                <table>
                    <tr><th>Employee</th><th>ID</th><th>Department</th><th>Days Left</th></tr>
            """
            for emp in critical:
                body_html += f"""
                    <tr>
                        <td>{emp.get('name', 'N/A')}</td>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{emp.get('days_left', 0)} days</td>
                    </tr>
                """
            body_html += "</table></div>"
        
        if warning:
            body_html += f"""
            <div class="section warning">
                <h2>🟡 Warning - Expiring Within 30 Days ({len(warning)})</h2>
                <table>
                    <tr><th>Employee</th><th>ID</th><th>Department</th><th>Days Left</th></tr>
            """
            for emp in warning:
                body_html += f"""
                    <tr>
                        <td>{emp.get('name', 'N/A')}</td>
                        <td>{emp.get('emp_id', 'N/A')}</td>
                        <td>{emp.get('department', 'N/A')}</td>
                        <td>{emp.get('days_left', 0)} days</td>
                    </tr>
                """
            body_html += "</table></div>"
        
        body_html += """
            <div class="footer">
                <p>This is an automated notification from Employee Vault.</p>
                <p>Please log in to the application to take action on these contracts.</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, body_html)
    
    def send_security_alert(self, admin_email: str, event_type: str, 
                            details: str, severity: str = "WARNING") -> bool:
        """
        Send security alert notification.
        
        Args:
            admin_email: Admin's email address
            event_type: Type of security event
            details: Event details
            severity: Event severity level
        
        Returns:
            True if sent successfully
        """
        severity_colors = {
            'INFO': '#4CAF50',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'CRITICAL': '#9C27B0'
        }
        
        color = severity_colors.get(severity, '#FF9800')
        
        subject = f"🔒 Security Alert [{severity}]: {event_type}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }}
                .alert {{ background: {color}22; border-left: 4px solid {color}; padding: 20px; border-radius: 8px; }}
                .header {{ color: {color}; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h1 class="header">🔒 Security Alert</h1>
                <p><strong>Event Type:</strong> {event_type}</p>
                <p><strong>Severity:</strong> {severity}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}</p>
                <p><strong>Details:</strong> {details}</p>
            </div>
            <p style="color: #666; margin-top: 20px;">
                Please log in to Employee Vault to review the security audit log.
            </p>
        </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, body_html)


def get_email_config_from_db(db) -> Dict:
    """Load email configuration from database settings"""
    try:
        return {
            'smtp_server': db.get_setting('email_smtp_server', 'smtp.gmail.com'),
            'smtp_port': int(db.get_setting('email_smtp_port', '587')),
            'username': db.get_setting('email_username', ''),
            'password': db.get_setting('email_password', ''),
            'from_email': db.get_setting('email_from', ''),
            'admin_email': db.get_setting('email_admin', ''),
            'enabled': db.get_setting('email_notifications_enabled', 'false') == 'true'
        }
    except Exception as e:
        logging.error(f"Failed to load email config: {e}")
        return {}


def save_email_config_to_db(db, config: Dict) -> bool:
    """Save email configuration to database settings"""
    try:
        db.set_setting('email_smtp_server', config.get('smtp_server', 'smtp.gmail.com'))
        db.set_setting('email_smtp_port', str(config.get('smtp_port', 587)))
        db.set_setting('email_username', config.get('username', ''))
        db.set_setting('email_password', config.get('password', ''))
        db.set_setting('email_from', config.get('from_email', ''))
        db.set_setting('email_admin', config.get('admin_email', ''))
        db.set_setting('email_notifications_enabled', 'true' if config.get('enabled') else 'false')
        db.conn.commit()
        return True
    except Exception as e:
        logging.error(f"Failed to save email config: {e}")
        return False
