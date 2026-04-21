import os
import json
from datetime import datetime
from contextvars import ContextVar
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from agent.react_agent import ReactAgent
from agent.tools.agent_tools import (
    rag_summarize, get_weather, get_user_location,
    get_used_month, fetch_external_data, fill_context_for_report,
    get_user_email, send_email, get_repairman_info
)
from utils.db import get_db
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import jinja2

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)

SECRET_KEY = os.environ.get('FASTAPI_SECRET_KEY', 'dev-secret-key-change-in-production')
COOKIE_NAME = 'session'
MAX_AGE = 60 * 60 * 24 * 7  # 7 days


# --- Signed cookie session ---

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt='session')


def load_session(request: Request) -> dict:
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return {}
    try:
        return json.loads(_serializer.loads(cookie, max_age=MAX_AGE))
    except (BadSignature, SignatureExpired):
        return {}


def save_session(session_data: dict) -> str:
    token = _serializer.dumps(json.dumps(session_data))
    return token


# --- Chat history (in-memory) ---

_user_id_var = ContextVar('user_id', default='')
_chat_histories: dict[str, list] = {}
MAX_HISTORY = 40
_agent = None


def get_agent() -> ReactAgent:
    global _agent
    if _agent is None:
        _agent = ReactAgent(tools=[
            get_user_id, rag_summarize, get_weather, get_user_location,
            get_used_month, fetch_external_data, fill_context_for_report,
            get_user_email, send_email, get_repairman_info
        ])
    return _agent


@tool(description="获取用户的ID，以纯字符串形式返回")
def get_user_id() -> str:
    return _user_id_var.get()


def set_current_user_id(user_id: str):
    _user_id_var.set(user_id)


def get_chat_history(user_id: str) -> list:
    if user_id not in _chat_histories:
        _chat_histories[user_id] = []
    return _chat_histories[user_id]


def clear_chat_history(user_id: str):
    _chat_histories[user_id] = []


def execute_chat_stream(messages, user_id):
    set_current_user_id(user_id)
    input_dict = {"messages": messages}
    final_content = None
    for chunk in get_agent().agent.stream(input_dict, stream_mode="values", context={"report": False}):
        if isinstance(chunk, dict) and "messages" in chunk:
            latest = chunk["messages"][-1]
            if isinstance(latest, AIMessage) and latest.content:
                final_content = latest.content
    if final_content:
        yield final_content.strip() + "\n"


# --- Routes ---

@app.get('/')
async def index(request: Request):
    session = load_session(request)
    if session.get('logged_in'):
        return RedirectResponse('/chat', status_code=302)
    return RedirectResponse('/login', status_code=302)


@app.get('/login')
async def login_page(request: Request):
    session = load_session(request)
    if session.get('logged_in'):
        return RedirectResponse('/chat', status_code=302)
    return HTMLResponse(env.get_template('login.html').render())

@app.post('/api/login')
async def api_login(request: Request):
    body = await request.json()
    user_id = body.get('user_id', '').strip()
    password = body.get('password', '').strip()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password FROM user_info WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row and row["password"] == password:
        conn.execute(
            "INSERT INTO login_records (user_id, login_time) VALUES (?, ?)",
            (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

        session_data = {'logged_in': True, 'user_id': user_id}
        clear_chat_history(user_id)

        response = JSONResponse({"success": True, "message": "登录成功"})
        response.set_cookie(COOKIE_NAME, save_session(session_data), httponly=True, samesite='lax', max_age=MAX_AGE)
        return response

    conn.close()
    return JSONResponse({"success": False, "message": "用户ID或密码错误"}, status_code=401)


@app.post('/api/logout')
async def api_logout():
    response = JSONResponse({"success": True, "message": "已退出登录"})
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get('/chat')
async def chat_page(request: Request):
    session = load_session(request)
    if not session.get('logged_in'):
        return RedirectResponse('/login', status_code=302)
    return HTMLResponse(env.get_template('chat.html').render())


@app.post('/api/chat')
async def api_chat(request: Request):
    session = load_session(request)
    if not session.get('logged_in'):
        return JSONResponse({"error": "未登录"}, status_code=401)

    body = await request.json()
    message = body.get('message', '').strip()
    if not message:
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    user_id = session['user_id']
    history = get_chat_history(user_id)
    user_msg = HumanMessage(content=message)
    history.append(user_msg)

    def generate():
        full_response = ""
        for chunk in execute_chat_stream(history, user_id):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

        ai_msg = AIMessage(content=full_response.strip())
        history.append(ai_msg)
        if len(history) > MAX_HISTORY:
            history[:] = history[-MAX_HISTORY:]

        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type='text/event-stream')


@app.get('/api/chat/history')
async def api_chat_history(request: Request):
    session = load_session(request)
    if not session.get('logged_in'):
        return JSONResponse({"error": "未登录"}, status_code=401)

    user_id = session['user_id']
    history = get_chat_history(user_id)

    serialized = []
    for msg in history:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        serialized.append({"role": role, "content": msg.content})

    return serialized
