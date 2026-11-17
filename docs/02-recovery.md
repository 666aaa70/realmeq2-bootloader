# TWRP 安装与原厂覆盖处理

前提：已按解锁文档完成正式解锁，并确认原厂 F.12 正常开机。以下没有安装 Root，也没有刷第三方系统。

## 使用的 Recovery

发布页：[Ravinderrohilla / V.12.1](https://github.com/Ravinderrohilla/recovery-tree-A12-and-14/releases/tag/V.12.1)。
作者标注 RMX2117、Realme UI 3.0，在 Narzo 30 Pro 5G 的 F.08/F.09 测试。
本机是国行 Q2 F.12，兼容性来自本次实际启动、触控、解密和重启验证，不能仅靠相同芯片推断。

实际使用 `TWRP_RIUI3.img`，下载脚本保存为 `TWRP-RMX2117-RUI3.img`。
大小 134217728 字节；SHA256：
`d74090bd746d9b9d8bac4afe0ce0e6cc1b1c9f77304020fce07f21d26ea93d61`。
版本字符串为 `3.7.0_12-perilouspike`。
其 DTB 与本机原厂 Recovery 逐字节相同；内核比当前原厂旧，实际功能需逐项验证。
镜像内的特殊 OS/安全补丁版本字段不代表手机真的升级到了那个系统版本。

备用 OrangeFox 仅下载和离线检查，未安装。Q2 Pro / RMX2173 镜像仅作离线参考，从未启动或刷入本机。

## 先备份原厂 Recovery 和 AVB

在仍可进入 DA 时，用与解锁阶段相同的等待连接方式读取：

```bash
python3 mtkclient/mtk.py r recovery,vbmeta,vbmeta_system,vbmeta_vendor backups/recovery-stock.img,backups/vbmeta-stock.bin,backups/vbmeta-system-stock.bin,backups/vbmeta-vendor-stock.bin --loader downloads/DA_BR_MT6853.bin
```

另外保留解锁阶段的原始 `backups/boot.bin`。本机独立 Recovery 为 128 MiB，boot 为 32 MiB，三个 vbmeta 各为 8 MiB。
Fastboot 的 `fetch` 在本机不受支持，不能把失败的读取当作备份。

## 刷入并立即进入 TWRP

```bash
adb reboot bootloader
fastboot getvar unlocked
fastboot flash recovery downloads/TWRP-RMX2117-RUI3.img
fastboot reboot recovery
```

刷入前 `unlocked` 应为 `yes`。发送和写入都应返回 `OKAY`。
本机 `fastboot boot` 临时启动此完整镜像失败，表现为 LK crash 后返回 Android，故没有把它作为可用路径。
`fastboot reboot recovery` 则正常进入已刷入的 TWRP。

首轮核验：

```bash
adb shell id
adb shell getprop ro.twrp.version
adb shell sha256sum /dev/block/by-name/recovery
adb shell twrp get tw_is_decrypted
```

应为 TWRP 内 `uid=0(root)`，Recovery 实际哈希与下载文件一致；这不表示 Android 已安装 Root。
本次用户确认触控正常，日志出现 `User 0 Decrypted Successfully`、`Data successfully decrypted`，内部存储可读取。
只验证了当前无自设锁屏密码的环境，不延伸到所有 PIN、密码或后续固件。

## 为什么正常开机后变回原厂

首次 TWRP 启动完全正常，但从原厂 Android 再次进入 Recovery 时已被替换。
在 TWRP 中只读挂载真实 vendor 后，确认：

```text
/vendor/etc/init/vendor_flash_recovery.rc
service vendor_flash_recovery /vendor/bin/install-recovery.sh
    class main
    oneshot
```

该脚本对 Recovery 完整 128 MiB 做 SHA1 检查；不匹配时，用完整 32 MiB 的 boot 作为源，
通过 `/vendor/recovery-from-boot.p` 重建原厂 Recovery。要求 boot 源 SHA1 等于
`c34cdd8e5d29d6bc53041aa83b01d81c7d73586f`。
vendor 是只读 EROFS，普通重命名或删除脚本不适用。

TWRP 初始 `/vendor` 是它自己的 ramdisk 文件，不等于真实原厂 vendor。
本次只读诊断挂载方式如下，先确认该映射实际存在，且不要重复覆盖已有挂载：

```bash
adb shell 'ls -l /dev/block/mapper/vendor'
adb shell 'mkdir -p /tmp/stockvendor; mount -t erofs -o ro /dev/block/mapper/vendor /tmp/stockvendor'
adb shell 'cat /tmp/stockvendor/etc/init/vendor_flash_recovery.rc; cat /tmp/stockvendor/bin/install-recovery.sh'
```

## 仅改变 boot 未使用填充区的 1 字节

本次未修改 vendor，也未关闭 AVB。采用的最小改动是让原厂恢复程序对完整 boot 的 SHA1 失配，
但保持用于启动和 AVB 校验的内容不变。

| boot 区域 | 范围或位置 |
| --- | --- |
| AVB Hash descriptor 覆盖的有效载荷 | 前 20056064 字节 |
| 内嵌 vbmeta | 偏移 20058112，长度 1600 字节 |
| 修改位置 | `0x1322000` / 20062208，从 `00` 改为 `01` |
| AVB footer | 镜像末尾 64 字节，未修改 |
| 完整分区大小 | 33554432 字节 |

修改位置在有效载荷和 vbmeta 之后、footer 之前的零填充区。除这一字节外全部一致。
离线 `avbtool verify_image` 验证修改后的 OEM 签名及 boot payload 哈希仍通过。
又在 TWRP 中用手机实际的 `applypatch` 对临时测试文件验证：原始源通过，修改后的源被拒绝；
目标设为临时文件，未用试验命令写实际 Recovery。

只适用于本次精确 boot 镜像，原始 SHA256：
`06e21577d95029c898e8e4d7d8b1bd44afb80e72642566399bbdeb482d588113`。
不要把此偏移套用于别的版本或重打包过的 boot。

电脑安装 `avbtool` 后，在本地生成：

```bash
python3 scripts/prepare_boot_padding.py backups/boot.bin output/persistence/boot.img
```

该工具拒绝不同输入，不覆盖现有文件，并自动运行 AVB 验证。
输出文件名需为 `boot.img`，以便 avbtool 对应 `boot` descriptor。
预期 SHA256：`d30d34b27209aa8d7fe472bf573c31733c26a0e3d6364f419c56b4715fab187b`。
看见签名结构和 boot hash 都验证通过后，确认 TWRP 已刷入，再执行：

```bash
adb reboot bootloader
fastboot flash boot output/persistence/boot.img
fastboot reboot
```

本次发送与写入均 `OKAY`，随后原厂 Android 正常开机，F.12 和 `unlocked/orange` 状态保持不变。
`ro.boot.recovery.updated=false` 与原厂恢复脚本未能重建的预期相符；这个属性本身不足以证明 TWRP 还在，需要下一步实测。

## 持久性验证与撤销

```bash
adb shell getprop sys.boot_completed
adb reboot recovery
# 等待 Recovery 的 ADB 重新连接，再核对：
adb shell getprop ro.twrp.version
adb shell sha256sum /dev/block/by-name/boot /dev/block/by-name/recovery
adb shell twrp get tw_is_decrypted
```

本次正常 Android 启动完成后再进入，仍为 `3.7.0_12-perilouspike`。
boot 与单字节修改版一致，Recovery 与原 TWRP 发布镜像一致，三个 vbmeta 仍与原始备份一致，解密变量仍为 `1`。
这是一次完整 Android 启动后的保留验证，没有额外刷 Root、禁用 AVB 或格式化用户数据。

以后 OTA 或重刷 boot 可能覆盖该填充改动；系统可能再次写回原厂 Recovery。
要撤销此次 Recovery 安装，在已解锁且仍能进入 Fastboot 时，用**本机原始备份**：

```bash
fastboot flash boot backups/boot.bin
fastboot flash recovery backups/recovery-stock.img
fastboot reboot
```

这不撤销 BL 解锁，也不撤销此前 boot1 补丁。不要将重新锁 BL 当作普通恢复步骤。
