# https://github.com/xhdndmm/hamster
# src/main.py
# v1.0_beta

import cv2
import logging
import os
import uuid
import sqlite3
import time

# 配置
logger = logging.getLogger(__name__)
logging.basicConfig(filename='hamster.log',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
db_path = "hamster.db"
img_path = "img_path"
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

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
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("无法打开摄像头")
        exit()

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

# 主循环
def main():
    print("hamster v1.0_beta")
    init()
    while True:
        capture_face_from_camera()
        time.sleep(1)

if __name__ == "__main__":
    main()