from flask import Flask, request, render_template, session, redirect, url_for
import requests
import json
import uuid

API_KEY = ""
SECRET_KEY = ""


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    response = requests.post(url, params=params)
    data = response.json()
    return data.get("access_token")

def get_ai_response(user_messages):
    access_token = get_access_token()
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"
    payload = {
        "messages": user_messages,
        "temperature": 0.95,
        "top_p": 0.8,
        "penalty_score": 1,
        "enable_system_memory": False,
        "disable_search": False,
        "enable_citation": False
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    ai_response = result.get("result", "抱歉，我未能理解您的请求。")
    return ai_response
@app.route("/chat/<chat_id>/api", methods=["POST"])
def chat_api(chat_id):
    if "conversations" not in session:
        session["conversations"] = {}
    if chat_id not in session["conversations"]:
        return json.dumps({"error": "Chat not found"}), 404

    chat_history = session["conversations"][chat_id]
    data = request.form
    user_input = data.get("user_input", "").strip()
    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        ai_response = get_ai_response([{"role": "user", "content": user_input}])
        chat_history.append({"role": "assistant", "content": ai_response})
        session["conversations"][chat_id] = chat_history
        session.modified = True

        return json.dumps({
            "chat_history": chat_history
        }, ensure_ascii=False), 200

    return json.dumps({"chat_history": chat_history}, ensure_ascii=False), 200

@app.route("/", methods=["GET"])
def home():
    # 显示会话列表（如果没有则为空）
    if "conversations" not in session:
        session["conversations"] = {}
    conversations = session["conversations"]
    return render_template("index.html", chat_history=None, conversations=conversations, current_chat_id=None)

@app.route("/new_chat", methods=["GET"])
def new_chat():
    # 创建新的会话ID
    chat_id = str(uuid.uuid4())
    if "conversations" not in session:
        session["conversations"] = {}
    session["conversations"][chat_id] = []  # 空会话
    session.modified = True
    return redirect(url_for("chat", chat_id=chat_id))

@app.route("/chat/<chat_id>", methods=["GET", "POST"])
def chat(chat_id):
    if "conversations" not in session:
        session["conversations"] = {}
    if chat_id not in session["conversations"]:
        # 如果传入的chat_id不存在，重定向回首页或新建
        return redirect(url_for("home"))

    chat_history = session["conversations"][chat_id]

    if request.method == "POST":
        user_input = request.form.get("user_input", "").strip()
        if user_input:
            # 用户消息
            chat_history.append({"role": "user", "content": user_input})
            ai_response = get_ai_response([{"role": "user", "content": user_input}])
            chat_history.append({"role": "assistant", "content": ai_response})
            session["conversations"][chat_id] = chat_history
            session.modified = True

    conversations = session["conversations"]
    return render_template("index.html", chat_history=chat_history, conversations=conversations, current_chat_id=chat_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
