# HOOPS 27 · 街頭鬥牛 🏀

3D 網頁版 1v1 街頭籃球(Three.js),打開瀏覽器就能玩，電腦跟手機都支援。

**▶ 立即遊玩：https://swimbikerun730718-maker.github.io/hoops27/**

## 特色
- 投籃時機條：按住起跳、在最高點放開，綠區 = 完美出手
- 花式運球可晃倒對手、禁區衝刺灌籃、跳起火鍋、抄截
- 4 種球員類型(神射手 / 灌籃怪物 / 控球魔術師 / 全能前鋒)
- 3 種難度(新秀 / 職業 / 名人堂)，可選搶 11 / 15 / 21 分
- 街頭規則：進球換球權、防守籃板要先清球(帶出三分線)、14 秒進攻時間

## 操作
| 動作 | 電腦 | 手機 |
|---|---|---|
| 移動 | WASD / 方向鍵 | 左下搖桿 |
| 衝刺 | Shift | 衝刺鈕 |
| 投籃 / 防守跳起 | 空白鍵(按住→放開) | 投籃鈕 |
| 花式運球 / 抄截 | E | 花式/抄截鈕 |
| 暫停 | P / Esc | ⏸ |

`index.html` + 內附 Three.js r160(`lib/`)。球員是 Adobe Mixamo 人物，搭配真人動作捕捉動畫(跑步、運球、防守滑步、跳投、灌籃掛框、火鍋、晃倒、慶祝…),持球與投籃時的手臂由程式即時疊加;場館、籃架、籃網、觀眾為程式建模，即時陰影，音效用 WebAudio 合成。原創作品，與任何職業聯盟或遊戲公司無關。

## 素材授權
- 球員人物與動畫：[Adobe Mixamo](https://www.mixamo.com)(Bryce、David 與 19 段動作),依 Mixamo 條款可免權利金用於本遊戲;**請勿把 `assets/*.glb` 抽出當獨立素材再散布**
- 跳投與防守滑步：[CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu/)(06_15 跳投、102_28 防守滑步;BVH 轉檔版 by Bruce Hahne),依 CMU 條款可自由使用。`tools/cmu_to_json.py` 轉成關節軌跡，遊戲載入時重定向到 Mixamo 骨架
- 轉檔流程：Blender 5(`tools/build_glb.py` 合併人物與動作)→ glTF-Transform(meshopt + WebP 壓縮)
- 場館光照：Blender Cycles 在 qqs34 烘焙地板光照貼圖(`tools/bake_arena.py`)
- 畫面後製：GTAO 環境光遮蔽(桌機)、Bloom、調色暗角、MSAA/SMAA 抗鋸齒;幀率不足時自動降畫質
- 3D 引擎：[three.js](https://threejs.org/) r160(MIT)
