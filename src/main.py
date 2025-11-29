# https://github.com/xhdndmm/hamster
# src/main.py
# v1.0_beta

import cv2
import logging
import os
import uuid
import sqlite3
import time
import face_recognition

# 配置
logger = logging.getLogger(__name__)
logging.basicConfig(filename='hamster.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
db_path = "hamster.db"
img_path = "img_path"

# 初始化
def init():
    # 创建目录
    files_and_dirs = os.listdir()
    if img_path not in files_and_dirs:
        try:
            os.mkdir(img_path)
            logger.info("创建图片目录")
        except Exception as e:
            logger.error("图片目录创建失败",e)
    # 数据库初始化
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE IMG (
            ID TEXT,
            TIME TEXT
        )
    """)
    logger.info("数据库创建成功")
    conn.commit()
    conn.close()


def capture_face_from_camera():
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("无法打开摄像头")
        exit()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.error("无法读取摄像头画面")

    # 将BGR转为RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 人脸位置检测
    face_locations = face_recognition.face_locations(rgb_frame)
    if len(face_locations) == 0:
        print("未检测到人脸")
        return None

    # 获取人脸
    logger.info("获取人脸")
    top, right, bottom, left = face_locations[0]
    face_img = rgb_frame[top:bottom, left:right]

    # 保存图片
    bgr_face = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
    uid = uuid.uuid4().hex
    save_path = img_path + "/" + str(uid) + ".jpg"
    # 写入数据库
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("INSERT IMG (ID,TIME) \
               VALUES (?,?)",(uid,time.time()))
    conn.commit()
    logger.info("数据库写入成功")
    conn.close()
    cv2.imwrite(save_path, bgr_face)

# 主循环
def main():
    init()
    while True:
        capture_face_from_camera()
        time.sleep(1)

if __name__ == "__main__":
    print("hamster v1.0_beta")
    main()

