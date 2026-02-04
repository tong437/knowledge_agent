# 任务9使用指南

## 目录
1. [配置管理](#配置管理)
2. [数据导入导出](#数据导入导出)
3. [测试工具](#测试工具)
4. [常见问题](#常见问题)

---

## 配置管理

### 基本使用

#### 1. 加载配置文件

```python
from knowledge_agent.core.config_manager import ConfigManager

# 加载YAML配置
manager = ConfigManager("config.yaml")

# 或加载JSON配置
manager = ConfigManager("config.json")
```

#### 2. 获取配置

```python
# 获取完整配置
config = manager.get_config()

# 获取搜索参数
search_params = manager.get_search_parameters()
print(f"最小相关度: {search_params.min_relevance}")
print(f"最大结果数: {search_params.max_results}")

# 获取存储配置
storage_config = manager.get_storage_config()
print(f"数据库路径: {storage_config.path}")

# 获取组织配置
org_config = manager.get_organization_config()
print(f"自动分类: {org_config.auto_classify}")
```

#### 3. 更新配置

```python
# 更新搜索参数
manager.update_search_parameters(
    min_relevance=0.3,
    max_results=100,
    enable_semantic=True
)

# 保存到文件
manager.save()
```

### 自定义分类规则

#### 添加规则

```python
from knowledge_agent.core.config_manager import ClassificationRule

# 创建规则
rule = ClassificationRule(
    name="Python代码",
    keywords=["python", "def", "class", "import"],
    category="编程",
    priority=10,
    enabled=True
)

# 添加到配置
manager.add_classification_rule(rule)
manager.save()
```

#### 查询规则

```python
# 获取所有启用的规则（按优先级排序）
rules = manager.get_classification_rules(enabled_only=True)

for rule in rules:
    print(f"规则: {rule.name}")
    print(f"  分类: {rule.category}")
    print(f"  关键词: {', '.join(rule.keywords)}")
    print(f"  优先级: {rule.priority}")
```

#### 删除规则

```python
# 按名称删除规则
success = manager.remove_classification_rule("Python代码")
if success:
    print("规则已删除")
    manager.save()
```

### 配置验证

```python
# 验证配置有效性
errors = manager.validate()

if errors:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置有效")
```

### 配置热重载

```python
# 检查配置文件是否已修改，如果是则重新加载
if manager.reload_if_changed():
    print("配置已更新")
    # 重新获取配置
    search_params = manager.get_search_parameters()
```

### 全局配置管理器

```python
from knowledge_agent.core.config_manager import get_config_manager, reset_config_manager

# 获取全局单例
manager = get_config_manager("config.yaml")

# 在其他地方使用同一个实例
manager2 = get_config_manager()  # 返回同一个实例
assert manager is manager2

# 重置（主要用于测试）
reset_config_manager()
```

---

## 数据导入导出

### 导出数据

#### 1. 导出完整数据库

```python
from knowledge_agent.core.data_import_export import DataExporter

exporter = DataExporter()

# 准备数据（从存储或其他来源获取）
items = [...]           # KnowledgeItem列表
categories = [...]      # Category列表
tags = [...]           # Tag列表
relationships = [...]  # Relationship列表

# 导出到单个文件
exporter.export_full_database(
    items=items,
    categories=categories,
    tags=tags,
    relationships=relationships,
    output_path="backup_2024.json"
)

print("数据已导出到 backup_2024.json")
```

#### 2. 导出单独的数据类型

```python
# 只导出知识条目
exporter.export_knowledge_items(
    items=items,
    output_path="items_only.json",
    include_metadata=True  # 包含创建/更新时间
)

# 只导出分类
exporter.export_categories(
    categories=categories,
    output_path="categories.json"
)

# 只导出标签
exporter.export_tags(
    tags=tags,
    output_path="tags.json"
)

# 只导出关联关系
exporter.export_relationships(
    relationships=relationships,
    output_path="relationships.json"
)
```

### 导入数据

#### 1. 导入完整数据库

```python
from knowledge_agent.core.data_import_export import DataImporter

importer = DataImporter()

# 导入并验证数据
data = importer.import_full_database(
    input_path="backup_2024.json",
    validate=True  # 启用数据验证
)

# 访问导入的数据
items = data['items']
categories = data['categories']
tags = data['tags']
relationships = data['relationships']

print(f"导入了 {len(items)} 个知识条目")
```

#### 2. 导入单独的数据类型

```python
# 导入知识条目
items = importer.import_knowledge_items(
    input_path="items_only.json",
    validate=True
)

# 导入分类
categories = importer.import_categories(
    input_path="categories.json",
    validate=True
)

# 导入标签
tags = importer.import_tags(
    input_path="tags.json",
    validate=True
)

# 导入关联关系
relationships = importer.import_relationships(
    input_path="relationships.json",
    validate=True
)
```

#### 3. 跳过验证导入

```python
# 如果数据格式不完整但仍想导入
data = importer.import_full_database(
    input_path="partial_data.json",
    validate=False  # 跳过验证
)
```

### 数据验证

```python
import json

# 手动验证数据
with open("data.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

errors = importer.validate_import_data(data)

if errors:
    print("数据验证失败:")
    for error in errors:
        print(f"  - {error}")
else:
    print("数据验证通过")
```

---

## 测试工具

### 1. 完整演示脚本

运行完整的功能演示：

```bash
cd tests_and_docs/task_9_config_import_export
python test_import_demo.py
```

这个脚本会：
- 创建示例数据
- 演示导出功能
- 演示导入功能
- 显示导入的数据
- 测试数据验证
- 测试往返一致性

### 2. 交互式导入工具

使用命令行工具导入数据：

```bash
# 导入数据文件
python import_knowledge_data.py example_knowledge_data.json

# 查看帮助
python import_knowledge_data.py --help
```

### 3. 快速测试

快速验证功能是否正常：

```bash
python quick_test.py
```

---

## 常见问题

### Q1: 如何创建配置文件？

**A**: 参考 `example_config.yaml` 文件，复制并修改为你的需求：

```bash
cp example_config.yaml my_config.yaml
# 编辑 my_config.yaml
```

### Q2: 配置文件支持哪些格式？

**A**: 支持YAML (.yaml, .yml) 和 JSON (.json) 格式。

### Q3: 如何备份现有数据？

**A**: 使用导出功能：

```python
from knowledge_agent.core.data_import_export import DataExporter
from knowledge_agent.storage.sqlite_storage import SQLiteStorage

# 从数据库读取所有数据
storage = SQLiteStorage("knowledge_agent.db")
items = storage.get_all_items()
categories = storage.get_all_categories()
tags = storage.get_all_tags()
relationships = storage.get_all_relationships()

# 导出
exporter = DataExporter()
exporter.export_full_database(
    items, categories, tags, relationships,
    output_path="backup.json"
)
```

### Q4: 导入数据会覆盖现有数据吗？

**A**: 导入功能只是将数据加载到内存中，不会自动覆盖数据库。你需要手动决定如何处理导入的数据（合并、替换等）。

### Q5: 如何处理导入验证失败？

**A**: 有两个选择：

1. 修复数据文件中的错误
2. 使用 `validate=False` 跳过验证（不推荐）

```python
# 查看具体错误
errors = importer.validate_import_data(data)
for error in errors:
    print(error)

# 或跳过验证
data = importer.import_full_database(path, validate=False)
```

### Q6: 配置更改后需要重启系统吗？

**A**: 不需要。使用 `reload_if_changed()` 方法可以热重载配置：

```python
if manager.reload_if_changed():
    print("配置已更新")
```

### Q7: 如何添加多个自定义分类规则？

**A**: 可以在配置文件中定义，或通过代码批量添加：

```python
rules = [
    ClassificationRule("Python", ["python", "def"], "编程", 10),
    ClassificationRule("Java", ["java", "class"], "编程", 9),
    ClassificationRule("ML", ["machine learning"], "AI", 8),
]

for rule in rules:
    manager.add_classification_rule(rule)

manager.save()
```

### Q8: 导出的JSON文件可以手动编辑吗？

**A**: 可以，但要确保：
- 保持JSON格式有效
- 不要删除必需字段（id, title, content等）
- 保持数据类型正确（字符串、数字、布尔值）

### Q9: 如何迁移数据到另一个系统？

**A**: 
1. 在源系统导出数据：`exporter.export_full_database(...)`
2. 将JSON文件复制到目标系统
3. 在目标系统导入数据：`importer.import_full_database(...)`
4. 将导入的数据保存到目标系统的数据库

### Q10: 配置文件的优先级是什么？

**A**: 
1. 代码中直接设置的值（最高优先级）
2. 配置文件中的值
3. 默认值（最低优先级）

---

## 最佳实践

### 1. 定期备份

建议设置定期备份任务：

```python
import schedule
import time
from datetime import datetime

def backup_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.json"
    # 执行导出...
    print(f"备份完成: {filename}")

# 每天凌晨2点备份
schedule.every().day.at("02:00").do(backup_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. 版本控制配置文件

将配置文件加入版本控制（Git），但排除敏感信息：

```bash
# .gitignore
config.local.yaml
*.db
backup_*.json
```

### 3. 环境特定配置

为不同环境使用不同配置：

```python
import os

env = os.getenv("ENV", "development")
config_file = f"config.{env}.yaml"
manager = ConfigManager(config_file)
```

### 4. 配置验证

在应用启动时验证配置：

```python
manager = ConfigManager("config.yaml")
errors = manager.validate()

if errors:
    print("配置错误，无法启动:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
```

### 5. 导入前验证

始终在导入前验证数据：

```python
try:
    data = importer.import_full_database(path, validate=True)
except DataImportError as e:
    print(f"导入失败: {e}")
    # 处理错误...
```

---

## 相关文档

- [README.md](README.md) - 任务9完整文档
- [example_config.yaml](example_config.yaml) - 配置文件示例
- [example_knowledge_data.json](example_knowledge_data.json) - 数据文件示例

## 技术支持

如有问题，请查看：
1. 单元测试：`knowledge_agent/tests/test_config_manager.py`
2. 单元测试：`knowledge_agent/tests/test_data_import_export.py`
3. 源代码：`knowledge_agent/core/config_manager.py`
4. 源代码：`knowledge_agent/core/data_import_export.py`
