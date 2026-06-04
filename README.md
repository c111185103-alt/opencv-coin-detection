# 國立高雄科技大學 電子工程系 研究所專案報告
* **指導教授：** 陳朝烈 教授
* **開發環境：** Windows 11 / VS Code
* **對應題目：** 題目一 (電腦視覺) - 基於多幀共識之高效率全自動硬幣辨識系統

---

# 基於多幀共識與時序生命週期高效率全自動硬幣辨識系統
### High-Efficiency Automatic Coin Recognition System with Temporal Lifecycle Deadlock Mechanism

本專案開發了一套基於 **傳統電腦視覺（OpenCV）** 的高效率、全畫面不分區自動硬幣辨識與時序追蹤系統。在**不依賴任何深度學習模型與標註資料（No AI Training Required）**的前提下，利用純幾何幾何特徵、局部對比增強與時間軸狀態機，成功克服了極端複雜的鍵盤文字紋路干擾、環境光學眩光（Glare）、手部遮擋（Occlusion）以及動態閃爍痛點，完美適配嵌入式系統與 SoC 晶片的低功耗、低延遲實時運算規範。

---

## 核心技術亮點 (Key Features)

* **全畫面自主動態偵測 (No Region Splitting)**：摒棄傳統寫死固定座標或人為劃分 ROI 遮罩的作法，具備 100% 全畫面辨識能力。
* **低解像檢索，高解像標註 (Resolution Scalability)**：將高解像度原始視訊等比例降維至 800像素 寬度進行核心矩陣運算，大幅降低時脈消耗，並在最終輸出端將座標自動還原逆映射，兼顧效能與精準度。
* **空間幾何魯棒性 (Geometric Robustness)**：透過調校特徵空間累積矩陣，針對手機斜拍引起的「透視橢圓化畸變」進行數學容錯，維持穩定的幾何不變性。
* **時序生命週期死鎖機制 (Temporal Lifecycle Deadlock)**：多幀一致性驗證。當物件通過時間門檻後，即鎖定紅框，完全根除傳統幾何演算法最嚴重的標註框閃爍（Flickering）痛點。
* **重疊抑制 (NMS Overlap Suppression)**：當降低幾何門檻導致鍵盤縫隙產生幽靈重疊框時，系統自動依據「物件資歷 (Age)」進行空間碰撞檢測，汰弱留強。

---

## 演算法技術核心流程 (System Architecture)

本系統的處理架構分為四大核心層級，實現數據的逐層清洗與特徵收斂：

```text
[ 原始視訊串流 (WxH) ]
         │
         ▼
 1. 影像降維與預處理 ───► 縮放至 800px + 灰階化 + CLAHE 局部對比活化 + 23x23 中值模糊
         │
         ▼
 2. 特徵幾何提取層 ───► 全畫面霍夫圓變換 (Hough Circles) 沿亮度梯度法線進行參數空間投票
         │
         ▼
 3. 時序狀態追蹤大腦 ───► 跨幀歐氏距離點對點匹配 (Age 壽命遞增 / Missed 失蹤計數)
         │
         ▼
 4. 碰撞抑制與死鎖 ───► NMS 空間碰撞去重 + 0.5秒門檻死鎖機制 + 逆映射還原原始座標標註

```

### 1. 前端非線性空間預處理：對抗複雜高頻雜訊

面對「複雜鍵盤背景」與「字體紋路」，常規的高斯模糊（Gaussian Blur）平均效應會導致字體邊緣暈開形成灰色干擾帶，且鈍化硬幣外圈邊緣。

本系統採用非線性空間濾波器 `cv2.medianBlur(gray, 23)`，配合適應性局部直方圖均衡化（CLAHE）：

* **CLAHE(8x8 網格)**：局部活化硬幣邊緣與背景的黑白階調差（Gradient），限制 `clipLimit=3.0` 防止純色背景爆出雪花雜訊。
* **中值模糊 (核心大小 23)**：利用鄰域統計排序取中位數的特性，**100% 抹平鍵盤複雜注音符號與硬幣內部的國父頭像**，同時**完美保留硬幣外圈銳利的階躍邊緣（Edge Preservation）**。

### 2. 特徵提取層：參數空間投票與椭圓容錯

利用圓形幾何中「邊緣法線必過圓心」的不變性，讓邊緣像素沿著梯度方向向累加器矩陣進行投票。當無數射線在幾何中心點交會時，會在矩陣中堆疊出強烈的局部極大值（Local Maxima）。

* 將投票箱門檻 `param2` 設定為 `32`，容許斜拍時因透視投影變形為橢圓而導致圓心投票率散開的物理誤差。
* 限制半徑範圍 `minRadius=28` 與 `maxRadius=110` 作為空間物理尺寸防線，徹底隔絕微小噪訊。

### 3. 時序狀態機：跨幀匹配與 0.5 固定硬幣

為了解決「硬幣放上去因表面鏡面反射（眩光）漏抓，手伸過去產生陰影才短暫抓到、隨即手抽離又消失」的經典光學環境問題，本演算法捨棄了傳統的背景分離（MOG2）或局部 ROI 矩陣切片（這會引發邊界強制截斷 boundary truncation 與 SNR 崩潰），建立的**時間序列狀態機**：

* **點對點歐氏距離匹配**：利用 <img width="146" height="25" alt="image" src="https://github.com/user-attachments/assets/5423f337-a6a9-4c5e-9d55-28020de11373" />
 進行跨影格關聯。
* **新進候選物件（資歷未滿 0.5 秒）**：允許 3 幀（`MAX_MISSED_FRAMES`）的短暫失蹤容錯，若超過則判定為隨機光影噪訊（如鍵盤縫隙反射），直接從清單淘汰。
* **永久鎖定條款（免死金牌）**：結合影片 FPS 動態計算，當物件穩定被辨識的時間累計超過 **0.5 秒**（即 age >= frames_to_lock），該物件即獲得永久留任權。此後**即使遭遇嚴重眩光使邊緣梯度完全消失，紅框依然會釘在最後已知座標，不會閃爍消失**。

---

## 關鍵參數配置表 (Parameters Configuration)

| 參數名稱 | 實際設定值 | 說明 |
| --- | --- | --- |
| `TARGET_WIDTH` | `800` | 歸一化檢索寬度。將 4K/1080p 視訊降維運算，確保在 SoC 嵌入式平台之實時性。 |
| `clipLimit` | `3.0` | CLAHE 對比度限制。強制拉開反光硬幣與背景的對比，模擬人為陰影的物理效應。 |
| `medianBlur` | `23` | 中值濾波核心。大視窗非線性濾波，專門攻克鍵盤複雜字體雜訊。 |
| `dp` | `1.0` | 累加器解析度倒數。若傾斜拍攝角大於 30° 導致橢圓畸變嚴重，可調高至 `1.4` 模糊投票誤差。 |
| `param1` | `130` | 內建 Canny 邊緣檢測的高閥值，用以過濾桌面刮痕等弱邊緣。 |
| `param2` | `32` | 圓心累積投票門檻。調低至 32 可包容斜拍橢圓，缺點是雜訊感度會同步上升。 |
| `LOCK_TIME_THRESH` | `0.5` | 死鎖時間門檻（秒）。越過此防線之物件將啟動跨幀共識死鎖機制。 |

---

## 核心程式碼架構解析 (Code Snippet)

```python
# 1. 影像降維與非線性空間預處理
frame_small = cv2.resize(frame, (TARGET_WIDTH, target_h))
gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
gray = clahe.apply(gray)
blurred = cv2.medianBlur(gray, 23)

# 2. 全畫面霍夫幾何解算與參數空間投票
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=60,
    param1=130, param2=32, minRadius=28, maxRadius=110
)

# [座標逆映射還原]：將 800px 空間下的幾何圓心還原至原始視訊解析度
orig_x = int(cx / scale_factor)
orig_y = int(cy / scale_factor)

# 3. 跨幀時序追蹤與死鎖判定 (清單過濾器)
tracked_coins = [
    c for c in tracked_coins 
    if c['missed'] <= MAX_MISSED_FRAMES or c['age'] >= frames_to_lock
] # 核心：停留超過 0.5 秒 (frames_to_lock) 觸發死鎖免除權，無視 missed 幀數

# 4. NMS 空間碰撞去重 (老手優先機制)
tracked_coins = sorted(tracked_coins, key=lambda x: x['age'], reverse=True)
# 若兩圓心距離小於半徑和的 70% (OVERLAP_THRESH_RATIO)，無條件捨棄資歷淺的幽靈重疊框

```

---

## 實作建議 (Practical suggestions)

雖然本系統成功透過軟體層面的 **CLAHE 演算法** 與 **時序固定機制** 克服了「手部陰影消除眩光後才能辨識」的物理瑕疵，但若要將本專案正式部署至工業檢測流水線，提出以下優化建議：

1. **背景優化**：更換檢測平台底色，勿使用會產生鏡面反射的白色背景或高頻紋理表面，建議改用**霧面（不反光）深黑色或墨綠色耐磨軟墊**。深色背景能使銀色硬幣的階躍邊緣（Gradient）在任何光線下皆保持極高對比度。
2. **光源配置**：避免光源從鏡頭正上方直射硬幣。應採用工業級環形無影光源（Ring Light）或帶有擴散板的斜角側光源，從根本消滅眩光。

```
***

```
