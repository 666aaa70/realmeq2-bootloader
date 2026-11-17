# realmeq2-bootloader

真我 Q2（RMX2117CN）在 **F.12 / Android 12 / Realme UI 3.0** 上，不回退系统，解锁 Bootloader、安装 TWRP，并解决开机后被原厂 Recovery 覆盖的实测记录。

实测日期：2026-11-17。仅代表这一台设备和这一版本的结果，不把相近机型或其他固件的经验当作兼容性保证。

## 最终结果

| 项目 | 实测结果 |
| --- | --- |
| 原系统 | RMX2117_11.F.12_3120_202312261231，未降级 |
| Bootloader | 正式 `fastboot flashing unlock` 成功，手机音量上键确认 |
| Android | 正常开机；`flash.locked=0`，`vbmeta.device_state=unlocked`，`verifiedbootstate=orange` |
| Recovery | TWRP 3.7.0_12-perilouspike，触屏正常，ADB 可用 |
| 数据解密 | 当前无自设锁屏密码的环境通过，`tw_is_decrypted=1` |
| 持久性 | 正常启动原厂 Android 后再进入，仍为 TWRP，分区 SHA256 一致 |
| 系统分区 | 未修改 system/vendor/三个 vbmeta，未安装 Magisk 或其他 Root |

**解锁会清空用户数据。boot1 是关键启动区，写错可能无法开机。先完成个人数据和本机原始分区备份，再按对应步骤核对。仓库中的脚本只生成本地文件，不自动刷机。**

## 这次走通的路径

1. 从同版本官方 OTA 的工程指令表确认 `*#872#` 是 Preloader USB 枚举开关。
2. 用系统自带 `dumpsys engineer` 打开该页，手动开启枚举。
3. MTKClient 配合 `DA_BR_MT6853.bin` 在 Preloader 模式下连接，备份关键分区。
4. 从**本机完整 boot1 备份**生成 Fastboot 入口补丁，只刷 boot1，完整读回验证，boot2 保持原始内容。
5. 正常启动 Android，`adb reboot bootloader`，执行正式 Fastboot 解锁并在手机确认。
6. 刷入原作者发布的 RMX2117 / RUI3 TWRP，立即重启到 Recovery。
7. 定位原厂 `vendor_flash_recovery` 自动恢复脚本；只修改原始 boot 的未使用填充区 1 字节，让其重建源校验失配。boot 的 OEM 签名和有效载荷哈希仍通过 AVB 校验。
8. 验证 Android 正常开机，再进入 TWRP，核对实际分区哈希与数据解密状态。

## 文档与文件

- [解锁步骤](docs/01-bootloader.md)：准备、USB、备份、boot1、正式解锁。
- [TWRP 与防止原厂覆盖](docs/02-recovery.md)：安装、定位原因、单字节填充修改、验证及撤销。
- [失败路径与结论边界](docs/03-troubleshooting.md)：哪些尝试失败、哪些没有实际执行。
- [工具和材料](docs/04-materials.md)：来源、版本、下载及许可证。
- [发布前隐私检查](docs/05-privacy-review.md)：发布范围与排除项。
- [材料清单](materials.json)：下载地址、大小及 SHA256。
- [脱敏验证摘要](evidence/validated-result.json)：手工挑选的非设备唯一字段。

```bash
# 只下载 DA 与 TWRP，并校验 SHA256；不连接或修改手机
python3 scripts/fetch_materials.py

# 可选下载备用 OrangeFox；本次没有安装它
python3 scripts/fetch_materials.py --include-optional
```

实际使用的第三方补丁原脚本保留在 `vendor/oppo-mtk-fastboot-unlock/`，附原许可证与归属说明。另提供只接受本次已核对输入哈希的离线生成脚本。

仓库不包含手机分区备份、固件大文件、设备唯一标识、原始日志或授权凭据。请用自己的备份，不要刷别人的 nvram/nvdata/protect/seccfg 等设备数据。

## 鸣谢与许可证

- [bkerler/mtkclient](https://github.com/bkerler/mtkclient)：设备读写工具。
- [Shocked-Cat/oppo-mtk-fastboot-unlock](https://github.com/Shocked-Cat/oppo-mtk-fastboot-unlock)：Fastboot 入口补丁方法及 Max_Goblin 的原脚本。
- [Ravinderrohilla/recovery-tree-A12-and-14，V.12.1](https://github.com/Ravinderrohilla/recovery-tree-A12-and-14/releases/tag/V.12.1)：实际使用的 RMX2117 TWRP，以及备用 OrangeFox。
- [Android AVB](https://android.googlesource.com/platform/external/avb/)：镜像格式与离线校验工具。

仓库文档及脚本采用 AGPL-3.0-only，见 [COPYING](COPYING)。第三方内容保留各自归属，见 [THIRD_PARTY.md](THIRD_PARTY.md)；下载材料不会因此被重新授权。
