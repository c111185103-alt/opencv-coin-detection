import cv2
import time
import numpy as np

def process_coin_video_final_fixed(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("錯誤：無法開啟影片檔案。")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 動態追蹤字典：{(x, y): [生命值計數, 半徑]}
    tracked_circles = {}
    
    # 【修正點】定義歸一化目標座標系為 0 - 100
    TARGET_WIDTH = 100
    TARGET_HEIGHT = 100
    
    # 【修正點】將原本未定義的 orig_width 改為讀取到的 width 與 height
    print(f"原始影片解析度: {width}x{height}")
    print(f"正規化處理解析度: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        start_time = time.time()

        # 1. 影像基礎預處理：轉灰階
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 使用中值模糊：對於鍵盤區的注音文字雜訊濾除效果，遠好於高斯模糊
        blurred = cv2.medianBlur(gray, 7)

        # 2. 全畫面霍夫圓變換
        circles = cv2.HoughCircles(
            blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2, 
            minDist=60, 
            param1=50, 
            param2=26, 
            minRadius=30,  # 下限防注音文字雜訊
            maxRadius=50   # 上限防按鍵組合巨大假圓
        )

        current_frame_detected = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cx, cy, r = int(i[0]), int(i[1]), int(i[2])
                current_frame_detected.append((cx, cy, r))

        # 3. 穩定性投票與幾何驗證
        new_tracked_circles = {}
        for (cx, cy, r) in current_frame_detected:
            match_found = False
            for (tx, ty) in tracked_circles.keys():
                distance = np.sqrt((cx - tx)**2 + (cy - ty)**2)
                if distance < 20:
                    count, _ = tracked_circles[(tx, ty)]
                    # 配對成功，生命值+1，上限鎖定在 25
                    new_tracked_circles[(cx, cy)] = [min(count + 1, 25), r]
                    match_found = True
                    break
            
            if not match_found:
                new_tracked_circles[(cx, cy)] = [1, r]

        # 【衰減機制】：將那些一閃而逝的雜訊快速清空
        for (tx, ty), [count, r] in tracked_circles.items():
            if (tx, ty) not in new_tracked_circles:
                still_around = False
                for (cx, cy, _) in current_frame_detected:
                    if np.sqrt((cx - tx)**2 + (cy - ty)**2) < 20:
                        still_around = True
                        break
                if not still_around and count > 1:
                    new_tracked_circles[(tx, ty)] = [count - 1, r] # 緩慢衰減

        tracked_circles = new_tracked_circles

        # 4. 【座標百分比與標註】：同步成教授範例格式（紅色框與文字）
        for (cx, cy), [count, r] in tracked_circles.items():
            # 提高生命週期門檻：雜訊連續出現 16 幀（約 0.5 秒）以上才標示
            if count >= 16:
                # 計算全畫面歸一化百分比座標 (0-100)
                norm_x = int((cx / width) * 100)
                norm_y = int((cy / height) * 100)
                coord_text = f"({norm_x},{norm_y})"

                # 繪製紅色物件框與紅色兩位數文字
                cv2.rectangle(frame, (cx - r, cy - r), (cx + r, cy + r), (0, 0, 255), 2)
                cv2.putText(frame, coord_text, (cx - r, cy - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

        # 需求：每幀運算不超過 0.1 秒
        elapsed_time = time.time() - start_time
        if elapsed_time > 0.1:
            print(f"警告：第 {frame_count} 幀耗時: {elapsed_time:.4f} 秒")

        out.write(frame)

    cap.release()
    out.release()
    print(f"優化完成！影片已成功儲存至：{output_path}")

if __name__ == "__main__":
    # 請確保此路徑與你的電腦檔案路徑完全一致
    input_video = r"C:\Users\hsing_h7p0uel\OneDrive\桌面\Report\第一題\vidio\coin_detect_test.mp4"
    output_video = r"C:\Users\hsing_h7p0uel\OneDrive\桌面\Report\第一題\vidio\coin_output_test.mp4"
    process_coin_video_final_fixed(input_video, output_video)