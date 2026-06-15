"""管理员账号管理脚本。

用法:
    python -m app.admin_cli create-admin <username> <password> [display_name]
    python -m app.admin_cli list-users
    python -m app.admin_cli set-role <username> <role>

示例:
    python -m app.admin_cli create-admin admin mySecretPwd123 "系统管理员"
    python -m app.admin_cli list-users
    python -m app.admin_cli set-role someuser admin
"""

import asyncio
import sys
import uuid

# Add parent dir to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import (
    init_db, close_db, create_user_db, get_user_by_username_db,
    get_user_by_id_db, get_db
)
from app.auth import hash_password


async def create_admin(username: str, password: str, display_name: str = ""):
    await init_db()

    existing = await get_user_by_username_db(username)
    if existing:
        print(f"[ERROR] 用户名 '{username}' 已存在")
        return

    user_id = f"admin_{uuid.uuid4().hex[:8]}"
    pw_hash = hash_password(password)
    user = await create_user_db(user_id, username, pw_hash, display_name or username, "admin")
    print(f"[OK] 管理员账号创建成功")
    print(f"     用户名: {user['username']}")
    print(f"     显示名: {user['displayName']}")
    print(f"     角色:   {user['role']}")
    print(f"     用户ID: {user['id']}")

    await close_db()


async def list_users():
    await init_db()
    db = await get_db()
    cursor = await db.execute("SELECT id, username, display_name, role, created_at FROM users ORDER BY created_at")
    rows = await cursor.fetchall()

    if not rows:
        print("[INFO] 暂无用户")
    else:
        print(f"{'用户名':<20} {'显示名':<16} {'角色':<10} {'创建时间':<20} {'ID'}")
        print("-" * 90)
        for r in rows:
            print(f"{r['username']:<20} {r['display_name']:<16} {r['role']:<10} {r['created_at']:<20} {r['id']}")

    await close_db()


async def set_role(username: str, role: str):
    if role not in ("user", "admin"):
        print(f"[ERROR] 角色必须为 'user' 或 'admin'")
        return

    await init_db()
    db = await get_db()

    user = await get_user_by_username_db(username)
    if not user:
        print(f"[ERROR] 用户 '{username}' 不存在")
        await close_db()
        return

    import datetime
    now = datetime.datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE users SET role = ?, updated_at = ? WHERE username = ?",
        (role, now, username)
    )
    await db.commit()
    print(f"[OK] 用户 '{username}' 角色已更新为 '{role}'")

    await close_db()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "create-admin":
        if len(sys.argv) < 4:
            print("用法: python -m app.admin_cli create-admin <username> <password> [display_name]")
            return
        username = sys.argv[2]
        password = sys.argv[3]
        display_name = sys.argv[4] if len(sys.argv) > 4 else ""
        asyncio.run(create_admin(username, password, display_name))

    elif cmd == "list-users":
        asyncio.run(list_users())

    elif cmd == "set-role":
        if len(sys.argv) < 4:
            print("用法: python -m app.admin_cli set-role <username> <role>")
            return
        asyncio.run(set_role(sys.argv[2], sys.argv[3]))

    else:
        print(f"[ERROR] 未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
