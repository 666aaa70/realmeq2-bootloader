# 失败路径与结论边界

| 尝试 / 现象 | 本次结果和处理 |
| --- | --- |
| 解锁前 `adb reboot bootloader` | 没有可用 Fastboot；boot1 入口补丁后才成功。 |
| 某官方深度测试 APK | 要求 SDK 33，本机 SDK 31，安装失败，未继续依赖此路线。 |
| 原厂 Recovery 的 Download mode | 枚举为 `0e8d:20ff` HID，本次未能用它完成 MTKClient 握手。 |
| 泛用按键和冷插线 | 没有解决枚举；最终由已核对的工程入口开启 USB Preloader 枚举。 |
| `--query_download_mode` 显示 Off | 对应工厂登录状态，不能据此断言真正的 USB 枚举开关关闭。 |
| 直接启动非导出工程 Activity | 权限拒绝；走系统自带的工程命令转发才打开实际页面。 |
| Binder 的 `fastbootUnlock` 接口 | 静态检查发现身份限制；没有执行该事务，不是本次解锁方法。 |
| seccfg 的 1 → 3 | 写入读回成功，但实际仍锁定，重启后系统改成 4；恢复原始备份后改用正式 Fastboot 流程。 |
| `rf --parttype lu1` | 本次得到 0 字节文件，不是成功备份；换成 boot1 / boot2 加完整长度。 |
| MTKClient 显式指定 VID/PID | 本次工具有相关参数行为问题，实际命令使用自动识别。 |
| DA 的软件 reset 未及时返回 | 在写入和全量读回已经完成后，用户通过硬件组合键重新启动。 |
| `fastboot fetch` | 本机 Bootloader 不支持，原厂 Recovery 和 vbmeta 改走 DA 读取。 |
| `fastboot boot TWRP.img` | 镜像发送成功，启动失败并返回 Android，启动原因 LK crash；不等于已验证临时启动可用。 |
| 首次刷 TWRP 后再开机 | 原厂服务覆盖 Recovery；定位脚本后用 boot 填充区单字节改动处理。 |
| 直接删除 install-recovery.sh | 真实 vendor 为只读 EROFS，没有实际删除或重打包 vendor。 |
| TWRP 下 `/vendor` 找不到原厂脚本 | 初始路径是 Recovery 自身 ramdisk；真实 vendor 需单独只读挂载。 |
| OrangeFox 自带防覆盖安装逻辑 | 离线检查见其主要是改名/删除脚本；不能据此认定可修改原厂 EROFS，未安装。 |
| Recovery 截图工具 | 输出错误文本，不是有效 PNG；未把该文件上传作成功证据。 |

## 固件分析做了什么

这次查询了同版本官方 OTA，使用 HTTP Range 提取 boot、preloader、LK、AVB 及 system_ext 相关组件。
system_ext 的 ZIP 条目 CRC32 为 `b6caa6e3`，重建 EROFS 后取得工程指令表，找到了实际可用开关。
ZIP 条目 CRC 与本地 SHA256 校验不等于验证整个 OTA 的数字签名或整包 MD5。

分析过若干 MediaTek / Mali CVE 和 Preloader 字符串、调用路径，但没有靠执行内核漏洞或未知固件漏洞完成这次解锁。
未确认适配本固件的公开漏洞利用链；不把旧安全补丁日期、日志里的 disabled 字符串或函数名称当作漏洞存在的证明。
最后走通的是工程枚举入口、已公开的 boot1 布局方法以及手机端确认的 Fastboot 正式解锁。

## 没有做的事情

没有降级；没有刷别的型号系统；没有刷写 LK；没有更改 system/vendor/vbmeta；
没有安装 Magisk；没有使用测试点；没有通过漏洞读取他人数据。
解锁时的用户数据清除由正式解锁流程执行，之后安装 TWRP 没有额外格式化数据。

记录只证明本机 F.12 的实际结果。后续固件、锁屏密码解密、OTA 后持久性或其他 RMX 型号需要分别验证。
