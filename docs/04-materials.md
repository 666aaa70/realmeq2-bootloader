# 工具、材料与校验

## 直接随仓库提供

- `vendor/oppo-mtk-fastboot-unlock/path_preloader.py`：本次实际用到的上游原脚本及 AGPL 许可证。
- `scripts/prepare_boot1.py`：只接受已验证 F.12 输入的离线 boot1 生成器；结果与已刷入、完整读回的镜像相同。
- `scripts/prepare_boot_padding.py`：只接受已验证 F.12 原始 boot 的单字节填充修改，强制调用 avbtool 验证。
- `scripts/fetch_materials.py`：从发布者原始地址下载 DA、TWRP，可选 OrangeFox；校验大小与 SHA256，不刷机。
- `config/70-realmeq2-download.rules`：实际使用 USB 规则的脱敏模板，用户名需自行替换。
- `materials.json`、`evidence/validated-result.json`：材料来源、校验值和脱敏结果。

## 外部工具

| 工具 | 本次用途 / 版本 |
| --- | --- |
| Android Platform Tools：adb、fastboot | 设备授权、工程入口、启动模式切换及正式解锁/刷入；使用官方发行版即可，未锁定具体版本 |
| Python / MTKClient | 提交 `118a000a83ea31c4f427fe5225abfe964546e05e`，本机读写 DA/启动区/分区 |
| libusb、PyUSB、PyCryptodome 等 | MTKClient 依赖，遵循其固定版本安装说明；按所用解释器环境安装 |
| avbtool、unpack_bootimg | 来自 AOSP，检查镜像布局、内嵌签名和哈希覆盖范围 |
| erofs-utils | `fsck.erofs` 提取工程指令表，`dump.erofs` 只读检查；没有重打包 vendor |
| requests、brotli 等 | 本次研究阶段的 OTA HTTP Range 下载、Brotli 解压和 transfer-list 重建 |
| jadx、反汇编/字符串检查工具 | 研究阶段检查工程服务、APK/JAR 和 Preloader，不参与最后的刷写步骤 |

MTKClient 与 Platform Tools 请从各自上游安装，不把本机虚拟环境、缓存和整个第三方项目复制到仓库。
上游安装说明：https://github.com/bkerler/mtkclient#installation
Platform Tools：https://developer.android.com/tools/releases/platform-tools

## DA 与 Recovery

下载脚本中的 DA 来自 [mtkclient Discussion #61](https://github.com/bkerler/mtkclient/discussions/61) 的
[原始附件](https://github.com/user-attachments/files/25299661/DA_BR_MT6853.bin.zip)。
脚本读取指定 ZIP 成员，不展开其他路径，得到 `DA_BR_MT6853.bin` 后核对本次使用文件的 SHA256。
附件由社区提供，来源和校验值用于复核，不代表 OEM 认证。

TWRP 和备用 OrangeFox 都来自 [原作者 V.12.1 release](https://github.com/Ravinderrohilla/recovery-tree-A12-and-14/releases/tag/V.12.1)。
两者的 kernel、DTB、DTBO 在本次离线比较中相同，但只有 TWRP 在本机实际启动和安装。
Recovery 镜像大于 GitHub 普通 Git 单文件限制，仓库保留可校验的原始下载方式，不上传手机备份或重复分发镜像。

## 官方 F.12 OTA

本次从 OPPO / realme CN OTA 服务取得同版本 `system_vendor` 组件。
查询时使用公开零值设备标识，没有提交手机真实 IMEI。
公开组件 URL、长度和服务器提供的 MD5 见 `materials.json`；URL 未附授权令牌。
没有下载完整 OTA，故**没有声称整包 MD5 或签名验证通过**。
实际只对提取条目做 ZIP CRC 和 SHA256 校验。

为避免混入接口密钥、身份数据和动态响应，原始 OTA 查询脚本/响应不复制发布。
最终复现步骤不需要重新调用查询服务：工程入口已确认，boot1/boot 一律从本机备份生成。
研究阶段取得的 APK/JAR、完整系统镜像、内核和反编译目录也不发布。

各材料的精确哈希以 [materials.json](../materials.json) 为准。二进制下载后先核对；不要仅凭文件名或相同芯片刷入。
