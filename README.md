# Sirchmunk 图片检索扩展版

这是基于 [Sirchmunk 原项目](https://github.com/modelscope/sirchmunk) 修改并打包的 Python wheel。原版已支持对多个文件进行文本检索；本扩展重点补上**文档图片识别、图片检索和图片结果返回**。调用者传入一个或多个文件及问题，得到文字回答和相关图片的缓存路径。仓库只提供交付文件，不包含业务文档或网页。

## 相比原版新增了什么

| 功能 | 本扩展的行为 |
| --- | --- |
| 自动判断文件是否含图 | 纯文本文件只走文本处理；有图片时才提取图片并调用视觉模型。 |
| 文档图片识别 | 提取 DOCX、PPTX、PDF 中可识别的位图，处理扫描 PDF 页面及 PNG/JPEG；为图片生成描述和 OCR 文本，供检索使用。 |
| 图文联合返回 | 检索时结合正文、图片描述及附近章节信息，返回文字回答和匹配的图片；可按需开启查询时的视觉复核。 |
| 单文件与多文件使用同一接口 | `search_file(file_path=...)` 接受一个路径或路径列表；已提交文件的 `FileSearch.search()` 接受一个 ID 或 ID 列表。图片按所属文件隔离。 |
| 原图缓存与准确定位 | 每张结果包含 `reference_id`、所属文件、原图缓存路径和 HTTP 图片地址。不同文件即使都有 `img_0001`，也不会混淆或按查询重复复制图片。 |
| 可选 HTTP API | 除 Python 函数外，还可启动带令牌的接口服务；无需部署网页。 |

处理流程：**接收文件 → 检测纯文本或含图 → 必要时提取并描述图片 → 检索正文与图片信息 → 返回回答和相关图片路径**。首次处理含图文件可能较慢；相同文件再次提交或重复提问可复用缓存。返回的是与问题匹配的图片，不保证把文档里的每张图都返回。

## 文件清单

| 文件 | 用途 |
| --- | --- |
| `sirchmunk-0.2.1+images.4-py3-none-any.whl` | 可安装的 Sirchmunk 包，一个接口检索单个或多个文件 |
| `example_usage.py` | 单次检索示例；修改文件和模型参数后可直接运行 |
| `LICENSE` | Sirchmunk 上游许可证 |
| `SHA256SUMS.txt` | 交付文件的 SHA-256 校验值 |

## 安装或更新

在本文件夹打开终端，并确保 `python` 指向准备使用的 Python 3.10+ 环境：

```powershell
python -m pip install "./sirchmunk-0.2.1+images.4-py3-none-any.whl[images]"
sirchmunk-files doctor
```

从旧版升级时安装新 wheel，然后重启 Python 程序：

```powershell
python -m pip install --upgrade "./sirchmunk-0.2.1+images.4-py3-none-any.whl[images]"
```

安装依赖需要访问 Python 包索引或已配置的软件源。`sirchmunk-files doctor` 可检查 `rg`、`rga` 等检索工具是否可用。

## 在自己的代码里调用

下面是单次查询示例。模型服务需兼容 OpenAI Chat Completions；此写法让文本和视觉使用同一模型，因此该模型需支持图片输入。

```python
import asyncio
from sirchmunk import search_file


async def main():
    result = await search_file(
        file_path="你的文档.docx",
        query="如何创建用户？",
        base_url="http://your-model-server/v1",
        model="your-model-name",
        api_key="your-api-key",
        data_dir="./sirchmunk_data",
        image_cache_dir="./sirchmunk_data/images",
        search_mode="FAST",
        image_limit=None,
        verify_images=False,
    )
    print(result.answer)
    for image in result.images:
        print(image.reference_id, image.source.file_name, image.path)


asyncio.run(main())
```

如果视觉模型与文本模型不同，另传 `vision_base_url`、`vision_model` 和 `vision_api_key`。纯文本文件不会调用视觉模型。`file_path` 传一个路径检索单文件，传路径列表检索多个文件；每次调用 `search_file()` 会打开和关闭客户端，重复提交相同文件仍可使用磁盘缓存。

## 一次检索多个文件

使用同一个 `search_file()`，把 `file_path` 设为路径列表即可：

```python
import asyncio
from sirchmunk import search_file

result = asyncio.run(search_file(
    file_path=["操作说明.docx", "补充说明.pdf"],
    query="两份文档中如何创建用户并分配权限？",
    base_url="http://your-model-server/v1",
    model="your-vision-capable-model",
    api_key="your-api-key",
    data_dir="./sirchmunk_data",
    image_cache_dir="./sirchmunk_data/images",
    search_mode="FAST",
    verify_images=False,
))
print(result.answer)
for image in result.images:
    print(image.reference_id, image.source.file_name, image.path)
```

已提交过的文件可用 `FileSearch.search(source_id_or_ids, query)` 重复检索，参数同样支持单个 ID 或 ID 列表。多文件中每张图用 `reference_id`（例如 `src_xxx:img_0001`）唯一标识；`image_limit=None` 对整次查询不设图片返回上限。

## 直接运行示例

打开 `example_usage.py`，修改文件路径和模型参数，然后执行：

```powershell
python example_usage.py
```

脚本调用一次 `search_file()`，直接输出回答和缓存图片路径。它不依赖 MES 文档，也不会把图片另复制一份。需要连续提问时，可在自己的代码中复用 `FileSearch` 客户端。

## 缓存和返回结果

- `result.answer` 是文字回答，`result.images` 是相关图片列表；没有匹配图片时为空列表。
- `image.image_id` 与缓存文件名对应，例如 `img_0003` 对应 `img_0003.png` 或 `.jpg`。`image.reference_id` 是跨文件唯一标识；`image.path` 是运行机器上的绝对路径。
- 图片保存在 `image_cache_dir/<source_id>/`。不同文件即使都含有 `img_0001`，也会位于各自的目录。同名但内容不同的文件会生成新的 `source_id`，不会混图。
- `data_dir/catalog.sqlite` 记录文件、图片和识别缓存。相同内容、文件名及识别配置再次提交时可复用处理结果；更换文件内容后需重新提交。
- `image_limit=None` 表示不设图片返回数量上限；`verify_images=False` 跳过查询时的视觉复核，首次导入含图文件仍需生成图片描述。

支持 TXT、MD、PDF、DOCX、PPTX、PNG 和 JPEG。图片识别取决于调用者配置的视觉模型；复杂 Office 绘图、SmartArt、PDF 矢量内容及外链图片可能无法完整提取，可查看 `result.warnings`。文件内容与图片会发送到调用者配置的模型服务。

## 可选 HTTP 接口

需要跨进程调用时，可以使用安装包自带的 `sirchmunk-files serve`。先在运行目录执行 `sirchmunk-files init` 生成模型配置模板，填写文本和视觉模型的六项配置，然后启动：

```powershell
sirchmunk-files serve --host 127.0.0.1 --port 8585 --service-token "your-service-token" --data-dir "./sirchmunk_data" --image-cache-dir "./sirchmunk_data/images" --search-mode FAST
```

HTTP 请求需带 `Authorization: Bearer <service-token>`。上传文件用 `POST /v1/files`，等待 `GET /v1/jobs/{job_id}` 返回 `completed` 后，用 `POST /v1/search` 检索。请求体的 `source_id` 可以是单个 ID 或 ID 列表。跨机器读取图片时使用返回的 `images[].url` 请求图片内容；`images[].path` 是服务端本地路径。完整接口契约可在认证后访问 `/openapi.json`。
