# 测试和文档分类目录

本目录包含按任务分类的所有测试文件和文档。

## 目录结构

```
tests_and_docs/
├── README.md                          # 本文件
├── task_1_project_setup/              # 任务1: 建立项目结构和核心接口
├── task_2_data_models_storage/        # 任务2: 实现数据模型和存储层
├── task_3_knowledge_collection/       # 任务3: 实现知识收集引擎
├── task_5_knowledge_organization/     # 任务5: 实现知识整理引擎
├── task_6_search_engine/              # 任务6: 实现搜索引擎
└── task_7_mcp_server/                 # 任务7: 实现MCP服务器接口
```

## 快速导航

### 任务1: 建立项目结构和核心接口
- 状态: ✅ 已完成
- 测试: 无专门测试（基础设施）
- 文档: 项目配置文件

### 任务2: 实现数据模型和存储层
- 状态: ✅ 已完成
- 测试: `test_models.py`, `test_storage.py`
- 文档: 数据模型说明

### 任务3: 实现知识收集引擎
- 状态: ✅ 已完成
- 测试: 处理器相关测试
- 文档: 处理器使用说明

### 任务5: 实现知识整理引擎
- 状态: ✅ 已完成
- 测试: `test_relationship_analyzer.py`
- 文档: 整理引擎说明

### 任务6: 实现搜索引擎
- 状态: ✅ 已完成
- 测试: `test_search.py`
- 文档: `SEARCH_ENGINE_USAGE.md`

### 任务7: 实现MCP服务器接口
- 状态: ✅ 已完成
- 测试: `test_mcp_integration.py` + 手动测试脚本
- 文档: `TASK_7_TESTING_GUIDE.md`, `TASK_7_COMPLETION_SUMMARY.md`

## 运行所有测试

```bash
# 运行所有单元测试
python -m pytest knowledge_agent/tests/ -v

# 按任务运行测试
python -m pytest knowledge_agent/tests/test_models.py -v          # 任务2
python -m pytest knowledge_agent/tests/test_storage.py -v         # 任务2
python -m pytest knowledge_agent/tests/test_relationship_analyzer.py -v  # 任务5
python -m pytest knowledge_agent/tests/test_search.py -v          # 任务6
python -m pytest knowledge_agent/tests/test_mcp_integration.py -v # 任务7
```

## 快速验证

每个任务都有快速验证脚本，可以快速检查功能是否正常：

```bash
# 任务7快速验证
python tests_and_docs/task_7_mcp_server/quick_test_task7.py
```
