# app/utils/email.py

import aiosmtplib
from email.message import EmailMessage
from app.config import settings


async def send_verification_email(to_email: str, token: str) -> bool:
    """
    Sends a verification email.
    Returns True if sent successfully, False otherwise.
    """
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("⚠️  Email not configured. Skipping real email send.")
        return False

    verification_link = f"{settings.BACKEND_URL}/api/v1/auth/verify-email?token={token}"

    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = "Verify your email - Adaptive AI Tutor"

    message.set_content(f"""
Hello,

Thank you for registering with Adaptive AI Tutor.

Please click the link below to verify your email address:

{verification_link}

This link will expire in 10 minutes.

If you did not create an account, you can safely ignore this email.

Best regards,
Adaptive AI Tutor Team
""")

    # HTML version
    message.add_alternative(f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Verify your email</h2>
        <p>Thank you for registering with <strong>Adaptive AI Tutor</strong>.</p>
        <p>Please click the button below to verify your email address:</p>
        <p style="margin: 30px 0;">
          <a href="{verification_link}"
             style="background-color: #4f46e5; color: white; padding: 12px 24px;
                    text-decoration: none; border-radius: 6px; font-weight: bold;">
            Verify Email
          </a>
        </p>
        <p style="font-size: 0.9em; color: #666;">
          Or copy this link into your browser:<br>
          <a href="{verification_link}">{verification_link}</a>
        </p>
        <p style="font-size: 0.85em; color: #999;">
          This link expires in 10 minutes. If you did not create an account, ignore this email.
        </p>
      </body>
    </html>
    """, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            username=settings.MAIL_USERNAME,
            password=settings.MAIL_PASSWORD,
            start_tls=True,
        )
        print(f"✅ Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False