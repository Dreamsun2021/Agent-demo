# skills/communication_skill.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def send_email(to_address: str, subject: str, body: str) -> str:
    """发送电子邮件"""
    try:
        from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    except ImportError:
        return "错误：缺少 SMTP 配置，请在 config.py 中添加 SMTP_SERVER 等变量。"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SMTP_FROM
    msg["To"] = to_address

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) if SMTP_PORT == 465 else smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if SMTP_PORT == 587:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_address], msg.as_string())
        server.quit()
        return f"邮件已成功发送至 {to_address}"
    except Exception as e:
        return f"邮件发送失败：{str(e)}"

COMM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "发送电子邮件。收件人地址、邮件主题和正文都需要提供。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_address": {"type": "string", "description": "收件人邮箱地址，例如 user@example.com"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"}
                },
                "required": ["to_address", "subject", "body"]
            }
        }
    }
]

COMM_FUNCTIONS = {
    "send_email": send_email
}