"""
知识管理的 MCP 提示模板注册模块。

提供预定义的提示模板，帮助 LLM 更好地与知识库交互，
包括知识摘要、搜索辅助和整理建议等功能。
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from ..core.exceptions import KnowledgeAgentError


def register_knowledge_prompts(app: FastMCP, knowledge_core) -> None:
    """
    注册知识管理提示模板到 MCP 服务器。

    提示模板为 LLM 提供结构化的交互方式，
    帮助用户更高效地利用知识库。

    Args:
        app: FastMCP 应用实例
        knowledge_core: 知识代理核心实例
    """
    logger = logging.getLogger("knowledge_agent.mcp_prompts")

    @app.prompt()
    def summarize_knowledge(item_id: str) -> str:
        """
        生成知识条目摘要的提示模板。

        根据 item_id 获取知识条目，返回包含条目完整信息的提示文本，
        要求 LLM 对该条目内容生成结构化摘要。

        Args:
            item_id: 知识条目 ID

        Returns:
            包含条目信息和摘要要求的提示文本
        """
        try:
            logger.info(f"Generating summarize prompt for item: {item_id}")

            item = knowledge_core.get_knowledge_item(item_id)

            if not item:
                return (
                    f"错误：未找到 ID 为 '{item_id}' 的知识条目。\n"
                    "请检查条目 ID 是否正确，或使用搜索功能查找相关条目。"
                )

            # 构建分类信息
            categories_text = "无"
            if item.categories:
                categories_text = "、".join(cat.name for cat in item.categories)

            # 构建标签信息
            tags_text = "无"
            if item.tags:
                tags_text = "、".join(tag.name for tag in item.tags)

            return (
                "请对以下知识条目生成一份结构化摘要。\n\n"
                f"## 条目信息\n"
                f"- 标题：{item.title}\n"
                f"- 分类：{categories_text}\n"
                f"- 标签：{tags_text}\n"
                f"- 来源类型：{item.source_type.value}\n"
                f"- 来源路径：{item.source_path}\n\n"
                f"## 条目内容\n"
                f"{item.content}\n\n"
                "## 要求\n"
                "1. 用简洁的语言概括核心内容\n"
                "2. 提取关键要点（不超过 5 条）\n"
                "3. 如果内容涉及技术概念，请给出通俗解释\n"
                "4. 建议可能相关的知识领域或扩展阅读方向"
            )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error in summarize prompt: {e}")
            return f"获取知识条目时发生错误：{e}"
        except Exception as e:
            logger.error(f"Error generating summarize prompt: {e}")
            return f"生成摘要提示时发生错误：{e}"

    @app.prompt()
    def search_assistant(topic: str) -> str:
        """
        搜索辅助提示模板。

        接受主题参数，先在知识库中搜索相关结果，
        然后返回包含搜索结果的提示文本，要求 LLM 进行分析和总结。

        Args:
            topic: 搜索主题

        Returns:
            包含搜索结果和分析要求的提示文本
        """
        try:
            logger.info(f"Generating search assistant prompt for topic: {topic}")

            # 执行搜索获取相关结果
            search_results = knowledge_core.search_knowledge(
                topic, max_results=10
            )

            total = search_results.get("total_results", 0)
            results = search_results.get("results", [])

            if total == 0:
                return (
                    f"在知识库中搜索主题「{topic}」，未找到相关结果。\n\n"
                    "请基于你的知识回答以下问题：\n"
                    f"1. 关于「{topic}」的核心概念是什么？\n"
                    "2. 建议用户可以从哪些方面补充相关知识？\n"
                    "3. 推荐一些学习资源或关键词供进一步搜索。"
                )

            # 构建搜索结果文本
            results_text = ""
            for i, result in enumerate(results, 1):
                title = result.get("title", "未知标题")
                content = result.get("content", "")
                score = result.get("relevance_score", 0)
                categories = result.get("categories", [])
                tags = result.get("tags", [])

                cat_names = "、".join(c.get("name", "") for c in categories) or "无"
                tag_names = "、".join(t.get("name", "") for t in tags) or "无"

                results_text += (
                    f"### 结果 {i}（相关度：{score:.2f}）\n"
                    f"- 标题：{title}\n"
                    f"- 分类：{cat_names}\n"
                    f"- 标签：{tag_names}\n"
                    f"- 内容摘要：{content}\n\n"
                )

            return (
                f"在知识库中搜索主题「{topic}」，共找到 {total} 条相关结果。\n\n"
                f"## 搜索结果\n\n"
                f"{results_text}"
                "## 要求\n"
                f"1. 基于以上搜索结果，综合分析「{topic}」相关的知识\n"
                "2. 指出各条目之间的关联和互补之处\n"
                "3. 总结当前知识库中关于该主题的覆盖情况\n"
                "4. 如果存在知识空白，建议需要补充的内容"
            )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error in search assistant: {e}")
            return f"搜索知识库时发生错误：{e}"
        except Exception as e:
            logger.error(f"Error generating search assistant prompt: {e}")
            return f"生成搜索辅助提示时发生错误：{e}"

    @app.prompt()
    def organize_suggestions() -> str:
        """
        知识库整理建议提示模板。

        获取知识库统计信息，返回包含统计数据的提示文本，
        要求 LLM 基于当前状态提供整理和优化建议。

        Returns:
            包含统计数据和整理建议要求的提示文本
        """
        try:
            logger.info("Generating organize suggestions prompt")

            # 获取统计信息
            stats = knowledge_core.get_statistics()

            total_items = stats.get("total_items", 0)
            total_categories = stats.get("total_categories", 0)
            total_tags = stats.get("total_tags", 0)
            total_relationships = stats.get("total_relationships", 0)

            # 尝试获取分类和标签详情以提供更丰富的上下文
            categories_detail = ""
            try:
                categories = knowledge_core.get_all_categories()
                if categories:
                    cat_names = "、".join(cat.name for cat in categories)
                    categories_detail = f"- 现有分类：{cat_names}\n"
            except Exception:
                pass

            tags_detail = ""
            try:
                tags = knowledge_core.get_all_tags()
                if tags:
                    tag_names = "、".join(tag.name for tag in tags)
                    tags_detail = f"- 现有标签：{tag_names}\n"
            except Exception:
                pass

            return (
                "请基于以下知识库统计数据，提供整理和优化建议。\n\n"
                "## 知识库统计\n"
                f"- 知识条目总数：{total_items}\n"
                f"- 分类总数：{total_categories}\n"
                f"- 标签总数：{total_tags}\n"
                f"- 关联关系总数：{total_relationships}\n"
                f"{categories_detail}"
                f"{tags_detail}\n"
                "## 请提供以下方面的建议\n"
                "1. 分类体系评估：当前分类结构是否合理？是否需要调整层级或合并/拆分分类？\n"
                "2. 标签优化：标签使用是否规范？是否存在冗余或缺失的标签？\n"
                "3. 知识关联：条目之间的关联关系是否充分？如何发现更多潜在关联？\n"
                "4. 内容质量：基于条目数量和分类分布，是否存在知识空白区域？\n"
                "5. 整理优先级：建议优先处理哪些方面的整理工作？"
            )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error in organize suggestions: {e}")
            return f"获取知识库统计信息时发生错误：{e}"
        except Exception as e:
            logger.error(f"Error generating organize suggestions prompt: {e}")
            return f"生成整理建议提示时发生错误：{e}"

    logger.info("Knowledge management prompts registered successfully")
