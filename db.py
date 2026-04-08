"""
数据层：Supabase 云存储
优先使用 Supabase，失败时降级到本地 JSON（保证不中断）
"""
import json
import streamlit as st
from pathlib import Path
from datetime import datetime

_LOCAL_FILE = Path(__file__).parent / "data" / "orders.json"

# ── Supabase 客户端（懒加载）─────────────────────────
_sb = None

def _client():
    global _sb
    if _sb is not None:
        return _sb
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        _sb = create_client(url, key)
    except Exception:
        _sb = None
    return _sb

# ── 本地 JSON 降级读写 ────────────────────────────────
def _local_load():
    if not _LOCAL_FILE.exists():
        return []
    try:
        return json.loads(_LOCAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _local_save(orders):
    _LOCAL_FILE.parent.mkdir(exist_ok=True)
    _LOCAL_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 公共接口 ──────────────────────────────────────────

def insert_order(order: dict) -> bool:
    """新增订单，成功返回 True"""
    sb = _client()
    if sb:
        try:
            sb.table("orders").insert(order).execute()
            return True
        except Exception as e:
            st.warning(f"云端保存失败，已存本地备份：{e}")
    # 降级到本地
    orders = _local_load()
    orders.append(order)
    _local_save(orders)
    return False  # 标识用了本地

def load_orders() -> list:
    """读取所有订单，按提交时间降序"""
    sb = _client()
    if sb:
        try:
            res = sb.table("orders").select("*").order("submitted_at", desc=True).execute()
            return res.data or []
        except Exception:
            pass
    # 降级到本地
    orders = _local_load()
    return sorted(orders, key=lambda o: o.get("submitted_at", ""), reverse=True)

def update_order(order_id: str, fields: dict) -> bool:
    """更新订单字段"""
    sb = _client()
    if sb:
        try:
            sb.table("orders").update(fields).eq("id", order_id).execute()
            return True
        except Exception:
            pass
    # 降级本地
    orders = _local_load()
    for o in orders:
        if o["id"] == order_id:
            o.update(fields)
    _local_save(orders)
    return False

def delete_order(order_id: str) -> bool:
    """删除订单"""
    sb = _client()
    if sb:
        try:
            sb.table("orders").delete().eq("id", order_id).execute()
            return True
        except Exception:
            pass
    # 降级本地
    orders = [o for o in _local_load() if o["id"] != order_id]
    _local_save(orders)
    return False
