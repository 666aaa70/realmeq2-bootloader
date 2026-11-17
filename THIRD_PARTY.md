# 第三方来源

| 内容 | 来源和归属 | 本仓库处理 |
| --- | --- | --- |
| `vendor/oppo-mtk-fastboot-unlock/path_preloader.py` | Shocked-Cat/oppo-mtk-fastboot-unlock，脚本署名 Max_Goblin / 4pda | 保留本次实际使用版本，SHA256 `f9308e21b65be38dca9fe46e86373690c709a42807612bc493f608e38fe61d7f`；附上游 AGPL 许可证 |
| `scripts/prepare_boot1.py` | 基于上述补丁布局方法，加入本次固件的严格输入/输出校验 | AGPL-3.0-or-later；离线生成，不自动写设备 |
| MTKClient | bkerler/mtkclient，实测提交 `118a000a83ea31c4f427fe5225abfe964546e05e` | 仅引用原项目，不复制整个源码树 |
| DA_BR_MT6853.bin | bkerler/mtkclient Discussion #61 中 Shocked-Cat 提供的附件 | 不重新分发二进制；提供原附件下载和哈希 |
| TWRP / OrangeFox | Ravinderrohilla / perilouspike，RMX2117 V.12.1 release | 不重新分发二进制；提供作者原始下载地址和哈希 |
| 官方 OTA / boot / preloader | OPPO / realme | 不重新分发固件镜像；仅列出公共固件来源和校验值 |
| avbtool、unpack_bootimg | Android Open Source Project | 依赖外部安装；不复制工具源码 |

原脚本上游：https://github.com/Shocked-Cat/oppo-mtk-fastboot-unlock/blob/main/path_preloader.py

本仓库保留的是本次使用的脚本文件，不保证与上游未来版本相同。其原有交互、宽松忽略检查等行为保留不变；本次精确版本重现建议用 `scripts/prepare_boot1.py`，该脚本输入不匹配时直接停止。
