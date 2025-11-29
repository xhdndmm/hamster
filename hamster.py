# https://github.com/xhdndmm/hamster
# src/main.py
# v1.0_beta

import cv2
import logging
import os
import uuid
import sqlite3
import time
import threading
from flask import Flask, Response, render_template_string, request, jsonify, send_from_directory

# 配置
logger = logging.getLogger(__name__)
logging.basicConfig(filename='hamster.log',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
db_path = "hamster.db"
img_path = "img_path"
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)
app = Flask(__name__)
TEMPLATE= '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>Hamster</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        #camera { border: 2px solid #444; width: 480px; }
        #results img { width: 120px; margin: 5px; border: 1px solid #ccc; }
    </style>
</head>
<body>

<h2>实时摄像头</h2>
<img id="camera" src="/camera">

<hr>

<h2>按日期搜索（YYYY-MM-DD）</h2>
<input id="dateInput" type="text" placeholder="例如: 2025-11-29">
<button onclick="search()">搜索</button>

<h3>搜索结果：</h3>
<div id="results"></div>

<script>
function search() {
    const date = document.getElementById("dateInput").value;

    fetch(`/search?date=${date}`)
        .then(r => r.json())
        .then(data => {
            const results = document.getElementById("results");
            results.innerHTML = "";

            if (data.length === 0) {
                results.innerHTML = "<p>无记录</p>";
                return;
            }

            data.forEach(item => {
                const img = document.createElement("img");
                img.src = item.url;
                results.appendChild(img);
            });
        });
}
</script>

</body>
</html>
'''

# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    logger.error("无法打开摄像头")
    exit()

# 初始化
def init():
    # 创建图片目录
    if not os.path.exists(img_path):
        try:
            os.mkdir(img_path)
            logger.info("创建图片目录成功")
        except Exception as e:
            logger.error("图片目录创建失败: %s", e)

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS IMG (
            ID TEXT PRIMARY KEY,
            TIME REAL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("数据库检查完成")

# 捕捉并保存人脸
def capture_face_from_camera():
    ret, frame = cap.read()
    if not ret:
        logger.error("无法读取摄像头画面")
        exit()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 检测人脸
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(100, 100)
    )

    if len(faces) == 0:
        logger.info("未检测到人脸")
        return

    x, y, w, h = faces[0]
    face_img = frame[y:y+h, x:x+w]

    # 自动生成 UUID
    uid = uuid.uuid4().hex
    save_path = f"{img_path}/{uid}.jpg"

    cv2.imwrite(save_path, face_img)

    # 写入数据库
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO IMG (ID, TIME) VALUES (?, ?)", (uid, time.time()))
    conn.commit()
    conn.close()
    logger.info("人脸保存成功: %s", save_path)

# 生成视频流
def gen_camera_stream():
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # 转为 JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        # 输出 MJPEG frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# web控制台
def web():
    # 主页路由
    @app.route('/')
    def index():
        return render_template_string(TEMPLATE)
    # 摄像头视频流路由
    @app.route("/camera")
    def camera():
        return Response(gen_camera_stream(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")
    # 搜素路由
    @app.route("/search")
    def search():
        date_str = request.args.get("date", "")
        if not date_str:
            return jsonify([])

        # 将 YYYY-MM-DD 转为当天 00:00~23:59 的 Unix 时间戳
        try:
            start_ts = int(time.mktime(time.strptime(date_str, "%Y-%m-%d")))
            end_ts = start_ts + 86400
        except:
            return jsonify([])

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT ID, TIME FROM IMG WHERE TIME >= ? AND TIME < ?", (start_ts, end_ts))
        rows = cur.fetchall()
        conn.close()

        results = [
            {
                "id": r[0],
                "time": r[1],
                "url": f"/img/{r[0]}.jpg"
            } for r in rows
        ]

        return jsonify(results)

    @app.route("/img/<name>")
    #返回保存的图片
    def get_img(name):
        return send_from_directory(img_path, name)

    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)

# 后端计算
def compute():
    init()
    while True:
        capture_face_from_camera()
        time.sleep(1)

# 主循环
def main():
    thread01 = threading.Thread(target=web)
    thread02 = threading.Thread(target=compute)
    thread01.start()
    thread02.start()
    thread01.join()
    thread02.join()

if __name__ == "__main__":
    main()