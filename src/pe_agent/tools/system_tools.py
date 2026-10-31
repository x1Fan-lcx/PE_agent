"""内置系统工具：挂载 / 修引导 / 查日志 / 修文件系统 / 读写配置 / 网络检查。

说明：初版为「模拟实现」——按 dry_run 返回确定性结果，跑通链路；
真实实现可把 run() 内部替换为对 D-Bus / subprocess / chroot bind-mount 的调用，
接口保持不变（这正是麒麟实习「D-Bus singleton + chroot bind-mount」的映射点）。
"""
from __future__ import annotations

from typing import Any

from pe_agent.config import get_settings
from pe_agent.tools.base import ActionResult, Tool


class MountPartitionTool(Tool):
    name = "mount_partition"
    description = "挂载目标系统的分区到指定挂载点（chroot bind-mount 前置步骤）"
    params_schema = {
        "type": "object",
        "properties": {
            "device": {"type": "string", "description": "块设备，如 /dev/sda1"},
            "mount_point": {"type": "string", "description": "挂载点，如 /mnt/sysroot"},
        },
        "required": ["device", "mount_point"],
    }
    risk_level = "medium"

    def run(self, **kwargs: Any) -> ActionResult:
        device = kwargs["device"]
        mount_point = kwargs["mount_point"]
        # 白名单校验（安全管控在 guard 层也会做，这里兜底）
        if not any(mount_point.startswith(p) for p in get_settings().mount_whitelist):
            return ActionResult(success=False, message=f"挂载点 {mount_point} 不在白名单内")
        if get_settings().safety_dry_run:
            return ActionResult(
                success=True,
                message=f"[dry-run] 模拟挂载 {device} -> {mount_point}",
                data={"device": device, "mount_point": mount_point, "mounted": True},
            )
        # 真实实现预留：subprocess mount / bind-mount
        return ActionResult(success=True, message=f"已挂载 {device} -> {mount_point}")


class UnmountPartitionTool(Tool):
    name = "unmount_partition"
    description = "卸载指定挂载点"
    params_schema = {
        "type": "object",
        "properties": {"mount_point": {"type": "string"}},
        "required": ["mount_point"],
    }
    risk_level = "low"

    def run(self, **kwargs: Any) -> ActionResult:
        return ActionResult(
            success=True,
            message=f"[dry-run] 模拟卸载 {kwargs['mount_point']}",
            data={"unmounted": True},
        )


class ReinstallBootloaderTool(Tool):
    name = "reinstall_bootloader"
    description = "重装引导（GRUB/bootloader 或修复 EFI 引导项）"
    params_schema = {
        "type": "object",
        "properties": {
            "device": {"type": "string", "description": "系统盘，如 /dev/sda"},
            "method": {"type": "string", "enum": ["grub", "efi", "auto"]},
        },
        "required": ["device"],
    }
    risk_level = "high"

    def run(self, **kwargs: Any) -> ActionResult:
        device = kwargs["device"]
        method = kwargs.get("method", "auto")
        return ActionResult(
            success=True,
            message=f"[dry-run] 模拟以 {method} 方式重装 {device} 引导",
            data={"device": device, "method": method, "bootloader_reinstalled": True},
        )


class RunFsckTool(Tool):
    name = "run_fsck"
    description = "检查并修复文件系统（fsck 类操作）"
    params_schema = {
        "type": "object",
        "properties": {
            "device": {"type": "string"},
            "fs_type": {"type": "string", "enum": ["ext4", "xfs", "btrfs", "ntfs", "auto"]},
        },
        "required": ["device"],
    }
    risk_level = "high"

    def run(self, **kwargs: Any) -> ActionResult:
        device = kwargs["device"]
        fs_type = kwargs.get("fs_type", "auto")
        return ActionResult(
            success=True,
            message=f"[dry-run] 模拟 fsck 修复 {device} 文件系统({fs_type})",
            data={"device": device, "fs_type": fs_type, "errors_fixed": 3},
        )


class ReadLogTool(Tool):
    name = "read_log"
    description = "读取系统日志并按关键字过滤，用于定位故障根因"
    params_schema = {
        "type": "object",
        "properties": {
            "log_path": {"type": "string", "default": "/var/log/syslog"},
            "keyword": {"type": "string", "default": ""},
        },
        "required": [],
    }
    risk_level = "read_only"

    def run(self, **kwargs: Any) -> ActionResult:
        log_path = kwargs.get("log_path", "/var/log/syslog")
        keyword = kwargs.get("keyword", "")
        lines = [
            "systemd[1]: Failed to mount /boot",
            "kernel: EXT4-fs error (device sda1)",
            "grub-install: error: cannot find EFI directory",
        ]
        if keyword:
            lines = [l for l in lines if keyword.lower() in l.lower()]
        return ActionResult(
            success=True,
            message=f"[dry-run] 读取 {log_path} 命中 {len(lines)} 条",
            data={"lines": lines, "log_path": log_path},
        )


class ReadFileTool(Tool):
    name = "read_file"
    description = "读取目标系统内的配置文件（如 /etc/fstab、/boot/grub/grub.cfg）"
    params_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }
    risk_level = "read_only"

    def run(self, **kwargs: Any) -> ActionResult:
        return ActionResult(
            success=True,
            message=f"[dry-run] 读取 {kwargs['path']}",
            data={"path": kwargs["path"], "content": "# mock config content"},
        )


class WriteFileTool(Tool):
    name = "write_file"
    description = "修改目标系统内的配置文件（高风险，需安全管控确认）"
    params_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }
    risk_level = "high"

    def run(self, **kwargs: Any) -> ActionResult:
        return ActionResult(
            success=True,
            message=f"[dry-run] 模拟写入 {kwargs['path']}",
            data={"path": kwargs["path"], "written": True},
        )


class CheckNetworkTool(Tool):
    name = "check_network"
    description = "检查网络连通性（判断是否需要联网下载修复包）"
    params_schema = {"type": "object", "properties": {}, "required": []}
    risk_level = "read_only"

    def run(self, **kwargs: Any) -> ActionResult:
        return ActionResult(
            success=True, message="[dry-run] 网络可达", data={"online": True}
        )


# 内置工具清单（后续可在运行时通过 Skill/Manager 动态注册更多）
BUILTIN_TOOLS: dict[str, Tool] = {
    t.name: t
    for t in [
        MountPartitionTool(),
        UnmountPartitionTool(),
        ReinstallBootloaderTool(),
        RunFsckTool(),
        ReadLogTool(),
        ReadFileTool(),
        WriteFileTool(),
        CheckNetworkTool(),
    ]
}


def get_tool(name: str) -> Tool | None:
    return BUILTIN_TOOLS.get(name)


def list_tools() -> list[dict[str, Any]]:
    return [t.manifest() for t in BUILTIN_TOOLS.values()]
