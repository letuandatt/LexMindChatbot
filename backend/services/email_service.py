"""
Email Service
Handles sending verification emails via Gmail SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import jwt

from chatbot.config import config as app_config


def generate_verification_token(user_id: str) -> str:
    """
    Generate a JWT token for email verification.
    Token expires in 24 hours.
    """
    expire = datetime.utcnow() + timedelta(hours=app_config.VERIFICATION_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "type": "email_verification",
        "exp": expire
    }
    token = jwt.encode(payload, app_config.JWT_SECRET_KEY, algorithm=app_config.JWT_ALGORITHM)
    return token


def decode_verification_token(token: str) -> Optional[str]:
    """
    Decode a verification token and return the user_id.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, app_config.JWT_SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        print("[email_service] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[email_service] Invalid token: {e}")
        return None


def send_verification_email(to_email: str, user_name: Optional[str], verification_token: str) -> bool:
    """
    Send a verification email to the user.
    Returns True if email was sent successfully.
    """
    if not app_config.GMAIL_USER or not app_config.GMAIL_APP_PASSWORD:
        print("[email_service] Gmail credentials not configured")
        return False
    
    # Build verification URL
    verify_url = f"{app_config.FRONTEND_URL}/verify?token={verification_token}"
    
    # Also provide an API endpoint for direct verification
    api_verify_url = f"http://localhost:8000/auth/verify?token={verification_token}"
    
    # Create email content
    subject = "Xác thực email - Law Chatbot"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .button:hover {{ background: #5a6fd6; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
            .code {{ background: #e9ecef; padding: 10px 20px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Xác Thực Email</h1>
            </div>
            <div class="content">
                <p>Xin chào <strong>{user_name or 'bạn'}</strong>,</p>
                <p>Cảm ơn bạn đã đăng ký tài khoản Law Chatbot!</p>
                <p>Vui lòng click nút bên dưới để xác thực email của bạn:</p>
                
                <p style="text-align: center;">
                    <a href="{verify_url}" class="button">✅ Xác Thực Email</a>
                </p>
                
                <p><strong>Lưu ý:</strong> Link này sẽ hết hạn sau 24 giờ.</p>
                
                <p>Nếu bạn không đăng ký tài khoản, vui lòng bỏ qua email này.</p>
            </div>
            <div class="footer">
                <p>© 2025 Law Chatbot. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    text_body = f"""
    Xin chào {user_name or 'bạn'},
    
    Cảm ơn bạn đã đăng ký tài khoản Law Chatbot!
    
    Vui lòng click link sau để xác thực email:
    {api_verify_url}
    
    Link này sẽ hết hạn sau 24 giờ.
    
    Nếu bạn không đăng ký tài khoản, vui lòng bỏ qua email này.
    """
    
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Law Chatbot <{app_config.GMAIL_USER}>"
    msg["To"] = to_email
    
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(app_config.GMAIL_USER, app_config.GMAIL_APP_PASSWORD)
            server.sendmail(app_config.GMAIL_USER, to_email, msg.as_string())
        
        print(f"[email_service] Verification email sent to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[email_service] Gmail authentication failed: {e}")
        print("[email_service] Please check GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        return False
    except Exception as e:
        print(f"[email_service] Failed to send email: {e}")
        return False


def send_password_reset_email(to_email: str, user_name: Optional[str], reset_token: str) -> bool:
    """
    Send a password reset email to the user.
    (For future implementation)
    """
    # TODO: Implement password reset email
    pass
