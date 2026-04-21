from datetime import datetime, timedelta

from utils.logger_handler import logger
from utils.db import get_db
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
import requests
import utils.email_sender
from utils.semantic_Similarity_handler import get_similarity

rag = RagSummarizeService()
email_sender = utils.email_sender
external_data = {}


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


def get_city_code(city_name: str) -> int:
    conn = get_db()
    cur = conn.cursor()

    # 优先匹配区县
    cur.execute("SELECT areacode FROM city WHERE district = ?", (city_name,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row["areacode"]

    # 匹配城市
    cur.execute("SELECT areacode FROM city WHERE city = ? LIMIT 1", (city_name,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row["areacode"]

    # 匹配省份
    cur.execute("SELECT areacode FROM city WHERE city LIKE ? LIMIT 1", (f"%{city_name}%",))
    row = cur.fetchone()
    if row:
        conn.close()
        return row["areacode"]

    conn.close()
    return 101010100


@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    url = "https://eolink.o.apispace.com/456456/weather/v001/now"
    city_code = get_city_code(city)
    payload = {"areacode": city_code}
    headers = {
        "X-APISpace-Token": "1mvo1s163efd6qtb984j7ppfa7puh71u"
    }
    response = requests.get(url, params=payload, headers=headers)
    data = response.json()
    temp = data.get('result').get('realtime').get('temp')
    wd = data.get('result').get('realtime').get('text')
    return f'城市{city}的天气：{wd}，温度：{temp}°C'


def get_user_location_from_records(user_id: str) -> str:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT city FROM user_info WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["city"] if row else ''


@tool(description="根据用户id获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location(user_id: str) -> str:
    return get_user_location_from_records(user_id)


def get_user_id_from_login_records() -> str:
    logger.info("执行get_user_id_from_login_records")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM login_records ORDER BY login_time DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    result = row["user_id"] if row else ''
    logger.info(f'获取到的用户ID：{result}')
    return result


@tool(description="根据用户id在使用记录中获取使用月份，如果没有记录则返回最近一个月的月份，以纯字符串形式返回")
def get_used_month(user_id: str) -> str:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT time FROM records WHERE user_id = ? ORDER BY time DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    if row:
        print(f"返回{row['time']}")
        return row['time']
    conn.close()

    now = datetime.now()
    last_month = now - timedelta(days=30)
    return last_month.strftime("%Y-%m")


def generate_external_data():
    if external_data:
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, feature, efficiency, consumables, comparison, time FROM records")
    for row in cur.fetchall():
        uid = str(row["user_id"])
        if uid not in external_data:
            external_data[uid] = {}
        external_data[uid][row["time"]] = {
            "特征": row["feature"],
            "效率": row["efficiency"],
            "耗材": row["consumables"],
            "对比": row["comparison"],
        }
    conn.close()


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""


@tool(
    description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"


@tool(description="根据用户id获取用户的邮箱地址，以纯字符串形式返回")
def get_user_email(user_id: str) -> str:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM user_info WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["email"] if row else ""


@tool(
    description="通过用户的邮箱地址进行邮件发送,发送内容为生成的报告内容")
def send_email(email: str, report_data: str):
    email_sender.send_email(email, report_data)
    return "send_email已调用"


@tool(
    description="根据用户描述的问题信息筛选合适的维修工，返回一个元组，第一个是维修工姓名，第二个是电话号码，第三项为擅长维修的领域")
def get_repairman_info(issue: str) -> tuple[str, str, str]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, phone, expertise FROM repairman_info")
    rows = cur.fetchall()
    conn.close()

    info = {}
    for idx, row in enumerate(rows):
        info[idx] = get_similarity(issue, row["expertise"])
    max_key = max(info, key=info.get)
    return rows[max_key]["name"], rows[max_key]["phone"], rows[max_key]["expertise"]


@tool(description="获取当前时间，以字符串形式返回")
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
