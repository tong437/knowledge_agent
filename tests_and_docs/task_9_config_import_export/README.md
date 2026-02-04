# 任务9: 配置和扩展功能

## 概述

任务9实现了知识管理智能体的配置管理和数据导入导出功能，为系统提供了灵活的配置能力和数据迁移支持。

## 功能模块

### 9.1 配置管理系统

**实现文件**: `knowledge_agent/core/config_manager.py`

**功能特性**:
- ✅ 支持YAML和JSON配置文件格式
- ✅ 用户自定义分类规则管理
- ✅ 搜索参数配置
- ✅ 配置验证和热重载
- ✅ 全局配置管理器单例模式

**配置项**:
1. **存储配置** (StorageConfig)
   - 数据库类型和路径
   - 备份设置

2. **搜索参数** (SearchParameters)
   - 最小相关度阈值
   - 最大结果数量
   - 语义搜索和关键词搜索开关
   - 结果分组和高亮设置

3. **组织配置** (OrganizationConfig)
   - 自动分类、标签、关联关系开关
   - 分类置信度阈值
   - 关系强度阈值
   - 自定义分类规则

4. **处理配置** (ProcessingConfig)
   - 最大文件大小
   - 支持的编码格式
   - 网页抓取超时和重试设置

**使用示例**:

```python
from knowledge_agent.core.config_manager import ConfigManager, ClassificationRule

# 创建配置管理器
manager = ConfigManager("config.yaml")

# 更新搜索参数
manager.update_search_parameters(
    min_relevance=0.3,
    max_results=100
)

# 添加自定义分类规则
rule = ClassificationRule(
    name="Python代码",
    keywords=["python", "def", "class"],
    category="编程",
    priority=10
)
manager.add_classification_rule(rule)

# 保存配置
manager.save()

# 热重载配置
if manager.reload_if_changed():
    print("配置已更新")
```

**配置文件示例** (config.yaml):

```yaml
server:
  version: "1.0.0"

storage:
  type: sqlite
  path: knowledge_base.db
  backup_enabled: true
  backup_interval: 3600

search:
  min_relevance: 0.1
  max_results: 50
  enable_semantic: true
  enable_keyword: true
  result_grouping: true
  highlight_matches: true

organization:
  auto_classify: true
  auto_tag: true
  auto_relationships: true
  classification_confidence_threshold: 0.7
  relationship_strength_threshold: 0.5
  custom_classification_rules:
    - name: "Python代码"
      keywords: ["python", "def", "class"]
      category: "编程"
      priority: 10
      enabled: true

processing:
  max_file_size: 10485760  # 10MB
  supported_encodings:
    - utf-8
    - utf-16
    - latin-1
  web_scraping:
    timeout: 30
    max_retries: 3
```

### 9.3 数据导入导出功能

**实现文件**: `knowledge_agent/core/data_import_export.py`

**功能特性**:
- ✅ JSON格式数据导出
- ✅ JSON格式数据导入
- ✅ 数据完整性验证
- ✅ 支持完整数据库和单独数据类型的导入导出
- ✅ 往返一致性保证

**支持的数据类型**:
1. 知识条目 (Knowledge Items)
2. 分类 (Categories)
3. 标签 (Tags)
4. 关联关系 (Relationships)
5. 完整数据库 (Full Database)

**使用示例**:

```python
from knowledge_agent.core.data_import_export import DataExporter, DataImporter

# 导出数据
exporter = DataExporter()

# 导出完整数据库
exporter.export_full_database(
    items=knowledge_items,
    categories=categories,
    tags=tags,
    relationships=relationships,
    output_path="backup_2024.json"
)

# 导出单独的知识条目
exporter.export_knowledge_items(
    items=knowledge_items,
    output_path="items_only.json",
    include_metadata=True
)

# 导入数据
importer = DataImporter()

# 导入完整数据库（带验证）
data = importer.import_full_database(
    input_path="backup_2024.json",
    validate=True
)

# 访问导入的数据
items = data['items']
categories = data['categories']
tags = data['tags']
relationships = data['relationships']

# 导入单独的知识条目
items = importer.import_knowledge_items(
    input_path="items_only.json",
    validate=True
)
```

**数据格式示例**:

```json
{
  "version": "1.0",
  "export_date": "2024-02-04T00:00:00",
  "statistics": {
    "item_count": 3,
    "category_count": 2,
    "tag_count": 5,
    "relationship_count": 2
  },
  "items": [
    {
      "id": "item_001",
      "title": "Python编程基础",
      "content": "Python是一种高级编程语言...",
      "source_type": "document",
      "source_path": "/docs/python.md",
      "categories": ["编程"],
      "tags": ["Python", "编程语言"],
      "metadata": {"difficulty": "beginner"},
      "created_at": "2024-02-01T10:00:00",
      "updated_at": "2024-02-04T15:30:00"
    }
  ],
  "categories": [...],
  "tags": [...],
  "relationships": [...]
}
```

## 测试文件

### 1. test_import_demo.py

**功能**: 完整的数据导入导出功能演示

**运行方法**:
```bash
python tests_and_docs/task_9_config_import_export/test_import_demo.py
```

**测试内容**:
- 创建示例数据文件
- 导入完整数据库
- 显示导入的知识条目、分类、标签和关联关系
- 测试单独文件导入
- 测试数据验证功能
- 往返一致性测试

### 2. import_knowledge_data.py

**功能**: 交互式数据导入工具

**运行方法**:
```bash
# 导入数据文件
python tests_and_docs/task_9_config_import_export/import_knowledge_data.py example_knowledge_data.json

# 查看帮助
python tests_and_docs/task_9_config_import_export/import_knowledge_data.py --help
```

**功能特性**:
- 自动验证数据完整性
- 显示详细的导入统计
- 预览导入的数据
- 友好的错误提示

### 3. example_knowledge_data.json

**功能**: 示例知识数据文件

**内容**:
- 5个知识条目（Python Web开发、深度学习、API设计、Docker、Git）
- 3个分类（Web开发、人工智能、DevOps）
- 8个标签
- 3个关联关系

**使用方法**:
```bash
python tests_and_docs/task_9_config_import_export/import_knowledge_data.py \
    tests_and_docs/task_9_config_import_export/example_knowledge_data.json
```

## 单元测试

### 配置管理器测试

**测试文件**: `knowledge_agent/tests/test_config_manager.py`

**测试覆盖**:
- ✅ 默认配置加载
- ✅ YAML配置文件加载和保存
- ✅ JSON配置文件加载和保存
- ✅ 自定义分类规则管理
- ✅ 搜索参数更新
- ✅ 配置验证
- ✅ 配置热重载
- ✅ 错误处理（文件不存在、格式错误）
- ✅ 全局配置管理器

**运行测试**:
```bash
pytest knowledge_agent/tests/test_config_manager.py -v
```

**测试结果**: 14个测试全部通过 ✓

### 数据导入导出测试

**测试文件**: `knowledge_agent/tests/test_data_import_export.py`

**测试覆盖**:
- ✅ 知识条目导出（带/不带元数据）
- ✅ 分类、标签、关联关系导出
- ✅ 完整数据库导出
- ✅ 空列表导出
- ✅ 知识条目导入
- ✅ 分类、标签、关联关系导入
- ✅ 完整数据库导入
- ✅ 数据验证（有效数据、缺少字段、缺少版本）
- ✅ 错误处理（文件不存在、无效JSON、验证失败）
- ✅ 往返一致性测试

**运行测试**:
```bash
pytest knowledge_agent/tests/test_data_import_export.py -v
```

**测试结果**: 22个测试全部通过 ✓

## 验证需求

### 需求 6.2: 自定义分类规则
✅ **已实现**: 配置管理器支持添加、删除、查询自定义分类规则

### 需求 6.4: 算法参数调整
✅ **已实现**: 支持调整搜索和分类算法参数

### 需求 5.2: 数据导出
✅ **已实现**: 提供标准JSON格式的数据导出功能

### 需求 5.3: 数据导入
✅ **已实现**: 支持数据导入并验证数据完整性

## 快速开始

### 1. 配置系统

```python
from knowledge_agent.core.config_manager import get_config_manager

# 获取配置管理器
config = get_config_manager("knowledge_agent/config.yaml")

# 获取搜索参数
search_params = config.get_search_parameters()
print(f"最小相关度: {search_params.min_relevance}")
print(f"最大结果数: {search_params.max_results}")

# 获取自定义分类规则
rules = config.get_classification_rules()
for rule in rules:
    print(f"规则: {rule.name}, 分类: {rule.category}")
```

### 2. 导出数据

```python
from knowledge_agent.core.data_import_export import DataExporter
from knowledge_agent.storage.sqlite_storage import SQLiteStorage

# 从数据库获取数据
storage = SQLiteStorage("knowledge_agent.db")
items = storage.get_all_items()
categories = storage.get_all_categories()
tags = storage.get_all_tags()
relationships = storage.get_all_relationships()

# 导出
exporter = DataExporter()
exporter.export_full_database(
    items=items,
    categories=categories,
    tags=tags,
    relationships=relationships,
    output_path="backup.json"
)
print("数据已导出到 backup.json")
```

### 3. 导入数据

```python
from knowledge_agent.core.data_import_export import DataImporter

# 导入数据
importer = DataImporter()
data = importer.import_full_database("backup.json", validate=True)

print(f"导入了 {len(data['items'])} 个知识条目")
print(f"导入了 {len(data['categories'])} 个分类")
print(f"导入了 {len(data['tags'])} 个标签")
print(f"导入了 {len(data['relationships'])} 个关联关系")

# 将数据保存到数据库
# storage.save_items(data['items'])
# storage.save_categories(data['categories'])
# ...
```

## 性能特性

- **配置热重载**: 支持在不重启系统的情况下重新加载配置
- **数据验证**: 导入前自动验证数据完整性，防止损坏的数据
- **往返一致性**: 导出后再导入的数据保持一致
- **灵活格式**: 支持YAML和JSON两种配置格式
- **错误处理**: 完善的错误处理和友好的错误提示

## 注意事项

1. **配置文件路径**: 确保配置文件路径正确，支持相对路径和绝对路径
2. **数据备份**: 导入数据前建议先备份现有数据
3. **版本兼容**: 导入的数据格式版本应与系统兼容
4. **编码格式**: 配置和数据文件使用UTF-8编码
5. **文件权限**: 确保有读写配置文件和数据文件的权限

## 未来扩展

可选的属性测试任务（标记为 `*`）:
- [ ] 9.2 为配置系统编写属性测试
  - 属性 27: 配置规则生效
  - 属性 28: 算法参数调整
- [ ] 9.4 为数据导入导出编写属性测试
  - 属性 24: 数据导出标准化
  - 属性 25: 数据导入完整性

这些可以在需要更全面的测试覆盖时实现。

## 总结

任务9成功实现了配置管理和数据导入导出功能，为知识管理智能体提供了：
- 灵活的配置能力
- 完整的数据迁移支持
- 可靠的数据验证机制
- 友好的用户接口

所有核心功能已实现并通过测试（36个单元测试全部通过），满足需求规格说明中的所有要求。
