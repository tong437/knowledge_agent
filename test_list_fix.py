"""
测试 list_knowledge_items 的精简模式修复
"""
from knowledge_agent.core.knowledge_agent_core import KnowledgeAgentCore
from knowledge_agent.storage.sqlite_storage import SQLiteStorageManager
from knowledge_agent.models import DataSource, SourceType


def test_list_items():
    """测试列出知识条目的精简模式"""
    # 初始化核心
    storage = SQLiteStorageManager("knowledge_agent.db")
    core = KnowledgeAgentCore(storage)
    
    # 获取所有知识条目
    items = core.list_knowledge_items(limit=100)
    
    print(f"\n总共有 {len(items)} 个知识条目\n")
    
    # 模拟精简模式输出
    print("=== 精简模式输出（默认） ===")
    for item in items[:5]:  # 只显示前 5 个
        summary = {
            "id": item.id,
            "title": item.title,
            "source_path": item.source_path,
            "source_type": item.source_type.value,
            "created_at": item.created_at.isoformat(),
            "categories": [{"id": c.id, "name": c.name} for c in item.categories] if item.categories else [],
            "tags": [{"id": t.id, "name": t.name} for t in item.tags] if item.tags else []
        }
        # 添加内容预览
        if hasattr(item, 'content') and item.content:
            content_preview = item.content[:200]
            if len(item.content) > 200:
                content_preview += "..."
            summary["content_preview"] = content_preview
        
        print(f"\nID: {summary['id']}")
        print(f"标题: {summary['title']}")
        print(f"来源: {summary['source_path']}")
        print(f"类型: {summary['source_type']}")
        if summary.get('content_preview'):
            print(f"内容预览: {summary['content_preview'][:100]}...")
    
    # 计算数据大小对比
    import json
    
    # 完整模式
    full_data = [item.to_dict() for item in items]
    full_size = len(json.dumps(full_data, ensure_ascii=False))
    
    # 精简模式
    summary_data = []
    for item in items:
        summary = {
            "id": item.id,
            "title": item.title,
            "source_path": item.source_path,
            "source_type": item.source_type.value,
            "created_at": item.created_at.isoformat(),
            "categories": [{"id": c.id, "name": c.name} for c in item.categories] if item.categories else [],
            "tags": [{"id": t.id, "name": t.name} for t in item.tags] if item.tags else []
        }
        if hasattr(item, 'content') and item.content:
            content_preview = item.content[:200]
            if len(item.content) > 200:
                content_preview += "..."
            summary["content_preview"] = content_preview
        summary_data.append(summary)
    
    summary_size = len(json.dumps(summary_data, ensure_ascii=False))
    
    print(f"\n\n=== 数据大小对比 ===")
    print(f"完整模式: {full_size:,} 字节 ({full_size / 1024:.2f} KB)")
    print(f"精简模式: {summary_size:,} 字节 ({summary_size / 1024:.2f} KB)")
    print(f"减少: {(1 - summary_size / full_size) * 100:.1f}%")
    print(f"\n精简模式可以减少约 {(full_size - summary_size) / 1024:.2f} KB 的数据传输")


if __name__ == "__main__":
    asyncio.run(test_list_items())
