"""
Notification System - Email notification for new SCADA RFPs

This module implements the notification system for alerting users
about new SCADA-related RFPs that match their criteria.
"""

import logging
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

logger = logging.getLogger("rfp_scraper.notification")

class NotificationSystem:
    """
    Implements notification functionality for alerting users about new
    SCADA-related RFPs that match their criteria.
    """
    
    def __init__(self, db_connection, config=None):
        """
        Initialize the notification system.
        
        Args:
            db_connection: SQLite database connection
            config (dict, optional): Configuration dictionary with email settings
        """
        self.conn = db_connection
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            'smtp_server': 'localhost',
            'smtp_port': 25,
            'smtp_username': '',
            'smtp_password': '',
            'from_email': 'scada-rfp-finder@example.com',
            'from_name': 'SCADA RFP Finder',
            'min_relevance_score': 50,
            'notification_frequency': 'daily',  # 'daily', 'realtime'
            'include_low_relevance': False
        }
        
        # Merge provided config with defaults
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        logger.info("Notification system initialized")
    
    def send_notification_email(self, recipient, subject, rfps):
        """
        Send notification email about new RFPs.
        
        Args:
            recipient (str): Email address of recipient
            subject (str): Email subject
            rfps (list): List of RFP dictionaries to include in notification
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not rfps:
            logger.info(f"No RFPs to send to {recipient}, skipping notification")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            msg['To'] = recipient
            
            # Create plain text content
            text_content = f"SCADA RFP Finder - {len(rfps)} new RFPs found\n\n"
            
            for rfp in rfps:
                text_content += f"Title: {rfp['title']}\n"
                text_content += f"State: {rfp['state']}\n"
                text_content += f"Agency: {rfp['agency']}\n"
                text_content += f"Due Date: {rfp['due_date']}\n"
                text_content += f"Relevance Score: {rfp['scada_relevance_score']}\n"
                text_content += f"URL: {rfp['url']}\n"
                text_content += f"Description: {rfp['description'][:200]}...\n\n"
                text_content += "-" * 50 + "\n\n"
            
            # Create HTML content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .rfp {{ margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 20px; }}
                    .title {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                    .meta {{ font-size: 14px; color: #7f8c8d; margin: 5px 0; }}
                    .score {{ font-weight: bold; }}
                    .high {{ color: #27ae60; }}
                    .medium {{ color: #f39c12; }}
                    .low {{ color: #e74c3c; }}
                    .description {{ font-size: 14px; color: #34495e; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <h1>SCADA RFP Finder - {len(rfps)} new RFPs found</h1>
            """
            
            for rfp in rfps:
                # Determine score class
                score_class = "low"
                if rfp['scada_relevance_score'] >= 80:
                    score_class = "high"
                elif rfp['scada_relevance_score'] >= 50:
                    score_class = "medium"
                
                # Format due date
                due_date = rfp['due_date']
                if due_date:
                    try:
                        due_date = datetime.fromisoformat(due_date).strftime('%B %d, %Y')
                    except:
                        pass
                
                # Build HTML for this RFP
                html_content += f"""
                <div class="rfp">
                    <div class="title">{rfp['title']}</div>
                    <div class="meta">
                        <strong>State:</strong> {rfp['state']} | 
                        <strong>Agency:</strong> {rfp['agency']} | 
                        <strong>Due Date:</strong> {due_date} | 
                        <strong>Relevance:</strong> <span class="score {score_class}">{rfp['scada_relevance_score']}%</span>
                    </div>
                    <div class="meta">
                        <a href="{rfp['url']}">View RFP Details</a>
                    </div>
                    <div class="description">{rfp['description'][:300]}...</div>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                if self.config['smtp_username'] and self.config['smtp_password']:
                    server.login(self.config['smtp_username'], self.config['smtp_password'])
                server.send_message(msg)
            
            logger.info(f"Sent notification email to {recipient} with {len(rfps)} RFPs")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification email to {recipient}: {e}")
            return False
    
    def get_new_rfps(self, min_score=None, since=None):
        """
        Get new RFPs that haven't been notified yet.
        
        Args:
            min_score (int, optional): Minimum relevance score
            since (datetime, optional): Only include RFPs since this time
            
        Returns:
            list: List of RFP dictionaries
        """
        cursor = self.conn.cursor()
        
        # Build query
        query = "SELECT * FROM RFPs WHERE notified = 0"
        params = []
        
        if min_score is not None:
            query += " AND scada_relevance_score >= ?"
            params.append(min_score)
        
        if since is not None:
            query += " AND created_at >= ?"
            params.append(since.isoformat())
        
        query += " ORDER BY scada_relevance_score DESC, due_date ASC"
        
        # Execute query
        cursor.execute(query, params)
        
        # Convert to list of dictionaries
        columns = [col[0] for col in cursor.description]
        rfps = []
        
        for row in cursor.fetchall():
            rfps.append(dict(zip(columns, row)))
        
        return rfps
    
    def mark_rfps_as_notified(self, rfp_ids):
        """
        Mark RFPs as notified in the database.
        
        Args:
            rfp_ids (list): List of RFP IDs to mark as notified
            
        Returns:
            int: Number of RFPs marked as notified
        """
        if not rfp_ids:
            return 0
        
        try:
            cursor = self.conn.cursor()
            
            # Update RFPs
            placeholders = ', '.join(['?'] * len(rfp_ids))
            query = f"UPDATE RFPs SET notified = 1 WHERE id IN ({placeholders})"
            cursor.execute(query, rfp_ids)
            
            self.conn.commit()
            return cursor.rowcount
            
        except sqlite3.Error as e:
            logger.error(f"Database error marking RFPs as notified: {e}")
            return 0
    
    def send_daily_digest(self, recipient):
        """
        Send daily digest of new RFPs.
        
        Args:
            recipient (str): Email address of recipient
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Get RFPs from the last 24 hours
        since = datetime.now() - timedelta(days=1)
        min_score = self.config['min_relevance_score']
        
        # Get high relevance RFPs
        high_relevance_rfps = self.get_new_rfps(min_score, since)
        
        # Get low relevance RFPs if configured
        low_relevance_rfps = []
        if self.config['include_low_relevance']:
            low_relevance_rfps = self.get_new_rfps(1, since)
            # Filter out high relevance RFPs
            low_relevance_rfps = [rfp for rfp in low_relevance_rfps 
                                if rfp['scada_relevance_score'] < min_score]
        
        # Combine RFPs
        all_rfps = high_relevance_rfps + low_relevance_rfps
        
        if not all_rfps:
            logger.info(f"No new RFPs for daily digest to {recipient}")
            return True
        
        # Send notification
        subject = f"SCADA RFP Finder - Daily Digest ({len(all_rfps)} new RFPs)"
        result = self.send_notification_email(recipient, subject, all_rfps)
        
        if result:
            # Mark RFPs as notified
            rfp_ids = [rfp['id'] for rfp in all_rfps]
            self.mark_rfps_as_notified(rfp_ids)
        
        return result
    
    def send_realtime_notification(self, recipient, rfp):
        """
        Send real-time notification for a single RFP.
        
        Args:
            recipient (str): Email address of recipient
            rfp (dict): RFP dictionary
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"SCADA RFP Alert - {rfp['title']}"
        result = self.send_notification_email(recipient, subject, [rfp])
        
        if result:
            # Mark RFP as notified
            self.mark_rfps_as_notified([rfp['id']])
        
        return result
