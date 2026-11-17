# 1. 不降级解锁 Bootloader

## 适用范围和准备

实测：RMX2117CN / 真我 Q2，MT6853，UFS，A-only，Android 12 / Realme UI 3.0，
`RMX2117_11.F.12_3120_202312261231`，安全补丁 2024-01-05。
电脑为 Linux，ADB 已授权，开发者选项已开启 USB 调试和 OEM 解锁。
正式解锁会清空用户数据；事先完成照片、账户、验证码等个人资料备份。

以下以仓库根目录为当前目录；`backups/`、`downloads/`、`output/` 都是本地目录，禁止提交。
MTKClient 按 [上游安装说明](https://github.com/bkerler/mtkclient#installation) 安装 Python 依赖和 libusb。
本次使用提交 `118a000a83ea31c4f427fe5225abfe964546e05e`。示例中 `python3 mtkclient/mtk.py` 应使用安装这些依赖的解释器。

```bash
git clone https://github.com/bkerler/mtkclient.git
git -C mtkclient checkout 118a000a83ea31c4f427fe5225abfe964546e05e
python3 scripts/fetch_materials.py
mkdir -p backups output
adb devices -l
```

仅在电脑上存在目标一台设备时执行示例命令，多设备时自行指定正确目标。不要把实际序列号写进公开记录。

## 打开真正的 Preloader USB 枚举开关

本次从同版本官方 OTA 的 `system_ext/etc/engineermode/engineer_order_list.xml` 确认：
`*#872#` 对应 `com.oplus.engineermode.usb.manualtest.UsbPreloaderEnabled`。
它与 `--query_download_mode` 查询的工厂登录状态不是一回事。

```bash
adb shell 'dumpsys engineer --execute_engineer_order --es order "*#872#"'
```

在手机页面点击 **ENABLE PRELOADER USB ENUM**。本次原始读值从 `[0]` 变成 `[49]`（ASCII `1`），页面显示开启。
随后先启动 MTKClient 等待连接，再正常 `adb reboot`，捕获短暂的 `22d9:0006` OPLUS Preloader 接口。
这里使用的是系统工程指令转发，没有修改 SELinux 或应用权限，也不是直接调用受限的 Binder 解锁事务。

Linux 权限：先把 `config/70-realmeq2-download.rules` 的 `YOUR_LINUX_USER` 改成自己的用户名，再安装：

```bash
sudo install -m 0644 config/70-realmeq2-download.rules /etc/udev/rules.d/70-realmeq2-download.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb
```

只读测试，在一个终端等待：

```bash
python3 mtkclient/mtk.py printgpt --loader downloads/DA_BR_MT6853.bin
```

另一个终端执行 `adb reboot`。本次此 DA 能握手、加载阶段 2 扩展并读取 GPT。
原厂 Recovery 的 Download mode 所呈现 `0e8d:20ff` HID 接口没有走通，不能与上述 Preloader 接口混用。

## 备份本机启动区和关键分区

每个 MTKClient 命令都要在设备可连接的同一 DA 会话中操作，或先让命令等待再重启捕获 Preloader。
以下是一条条独立命令；不要一次粘贴后假定手机每次都会自动重新连接。

```bash
python3 mtkclient/mtk.py rf backups/boot1.bin --parttype boot1 --length 0x400000 --loader downloads/DA_BR_MT6853.bin
python3 mtkclient/mtk.py rf backups/boot2.bin --parttype boot2 --length 0x400000 --loader downloads/DA_BR_MT6853.bin
python3 mtkclient/mtk.py r seccfg,lk,lk2,boot,frp,opporeserve1,oppo_custom,nvram,nvdata,nvcfg,protect1,protect2,proinfo backups/seccfg.bin,backups/lk.bin,backups/lk2.bin,backups/boot.bin,backups/frp.bin,backups/opporeserve1.bin,backups/oppo_custom.bin,backups/nvram.bin,backups/nvdata.bin,backups/nvcfg.bin,backups/protect1.bin,backups/protect2.bin,backups/proinfo.bin --loader downloads/DA_BR_MT6853.bin
sha256sum backups/boot1.bin backups/boot2.bin
```

本次 boot1、boot2 均为完整 4194304 字节，SHA256 均为：
`deee5b7ff2e8c3a42c663b47314fa01135c0e2d0e1ee9842fd26594f910fca89`。
这只是本次参考，其他输入不应强行套用。OTA 的 `preloader_ufs.img` 只有 428812 字节，不能冒充完整 boot1。
`rf --parttype lu1` 本次产生了 0 字节文件，不能当作有效备份，改用 `boot1` / `boot2`。

`nvram/nvdata/protect/proinfo/oppo_custom` 等备份可能含设备标识、校准和用户相关数据，只在本地安全保存。

## 生成补丁、刷 boot1 并完整读回

补丁来自 [Shocked-Cat 的 Fastboot 入口方法](https://github.com/Shocked-Cat/oppo-mtk-fastboot-unlock)。
本次确认完整 RAW Preloader 与官方 F.12 相同，补丁保留其代码字节，搬移布局并修改 ROMINFO 标志。
本仓库的严格生成器只接受上面的已验证原始 boot1 哈希，输出也必须与本次已刷版本一致。

```bash
python3 scripts/prepare_boot1.py backups/boot1.bin output/boot1-fastboot.bin
```

得到 4 MiB 镜像，预期 SHA256：
`c5359d4b96ef1000fcf4cf73046df72cc55165e7b6fce3bec04db50cb40ef022`。
工具只生成文件，不连接设备。保留原始 boot1，写入前再次确认型号、固件、完整备份和生成结果。

```bash
python3 mtkclient/mtk.py wf output/boot1-fastboot.bin --parttype boot1 --loader downloads/DA_BR_MT6853.bin
python3 mtkclient/mtk.py rf output/boot1-readback.bin --parttype boot1 --length 0x400000 --loader downloads/DA_BR_MT6853.bin
cmp output/boot1-fastboot.bin output/boot1-readback.bin
python3 mtkclient/mtk.py rf output/boot2-readback.bin --parttype boot2 --length 0x400000 --loader downloads/DA_BR_MT6853.bin
cmp backups/boot2.bin output/boot2-readback.bin
```

`cmp` 无输出且返回 0 才算一致。本次 boot1 全量读回相同，boot2 未改变。
退出 DA 软件复位未及时返回时，本次通过拔线后同时长按音量上和电源约 10–15 秒，出现标志后重新连接。
先确认手机仍能正常进入原厂 Android。

## 正式解锁

```bash
adb reboot bootloader
fastboot devices
fastboot getvar unlocked
fastboot flashing unlock
```

手机显示英文确认页面：**音量上 = Yes / Unlock；音量下 = No**。
这个界面没有必须用电源键点击的图形选项。本次按实体音量上完成确认，命令返回 `OKAY`。

```bash
fastboot getvar unlocked
fastboot getvar secure
fastboot reboot
```

预期 `unlocked: yes`、`secure: no`。清除数据并完成首次开机设置后，重新允许 USB 调试：

```bash
adb shell 'getprop sys.boot_completed; getprop ro.boot.flash.locked; getprop ro.boot.vbmeta.device_state; getprop ro.boot.verifiedbootstate; getprop ro.build.version.ota'
```

本次依次为 `1`、`0`、`unlocked`、`orange` 和原 F.12 版本。
此前直接将 seccfg 状态从 1 改为 3 的尝试无效，并已恢复原始内容；那一步不是成功路径，也不需要重复。
