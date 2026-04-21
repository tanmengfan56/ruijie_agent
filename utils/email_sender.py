import smtplib
from email.mime.text import MIMEText
from email.header import Header

from email.utils import formataddr

from utils.config_handler import email_conf
from utils.logger_handler import logger


def send_email(email: str, report_data: str):
    # 1. 配置发件人信息
    smtp_server = email_conf['smtp_server']  # SMTP服务器
    smtp_port = email_conf['smtp_port']  # SSL端口
    sender_email = email_conf['sender_email']  # 发件人邮箱
    auth_code = email_conf['auth_code']  # 授权码

    # 2. 构建邮件内容
    receiver_email = email
    subject = "用户报告"
    body = report_data

    # 创建 MIMEText 对象，'plain' 表示纯文本，'utf-8' 是编码格式
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = formataddr((email_conf['sender_name'], sender_email))  # 发件人昵称
    msg['To'] = Header(email, 'utf-8')  # 收件人昵称
    msg['Subject'] = Header(subject, 'utf-8')

    # 3. 连接服务器并发送邮件
    try:
        # 建立 SSL 连接
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # 登录
        server.login(sender_email, auth_code)
        # 发送
        server.sendmail(sender_email, [receiver_email], msg.as_string())
        logger.info("邮件发送成功！")
    except Exception as e:
        logger.info("邮件发送失败！", e)
    finally:
        # 关闭连接
        server.quit()


if __name__ == '__main__':
    send_email("1253725056@qq.com", "测试邮件")
