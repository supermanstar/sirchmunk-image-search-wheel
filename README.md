# Sirchmunk 文件与图片检索：使用说明

本文件夹用于交付 Python 包。安装 wheel 后，调用者传入自己的文件、问题、模型和缓存目录，即可获得文字回答及相关图片的缓存路径。无需网页，也无需本项目的源码、测试文档或 `.env`。

## 文件清单

| 文件 | 用途 |
| --- | --- |
| `sirchmunk-0.2.1+images.1-py3-none-any.whl` | 可安装的 Sirchmunk 包，包含文件与图片检索接口 |
| `example_usage.py` | 单次检索示例；修改文件和模型参数后可直接运行 |
| `LICENSE` | Sirchmunk 上游许可证 |
| `SHA256SUMS.txt` | 交付文件的 SHA-256 校验值 |

## 安装或更新

在本文件夹打开终端，并确保 `python` 指向准备使用的 Python 3.10+ 环境：

```powershell
python -m pip install "./sirchmunk-0.2.1+images.1-py3-none-any.whl[images]"
sirchmunk-files doctor
```

如果已装过**同版本号**的旧 wheel，用新文件覆盖安装，然后重启 Python 程序：

```powershell
python -m pip install --force-reinstall --no-deps "./sirchmunk-0.2.1+images.1-py3-none-any.whl"
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
        print(image.image_id, image.path)


asyncio.run(main())
```

如果视觉模型与文本模型不同，另传 `vision_base_url`、`vision_model` 和 `vision_api_key`。纯文本文件不会调用视觉模型。每次调用 `search_file()` 会打开和关闭客户端，重复提交相同文件仍可使用磁盘缓存；同一文件连续提问推荐复用一个客户端。

## 直接运行示例

打开 `example_usage.py`，修改文件路径和模型参数，然后执行：

```powershell
python example_usage.py
```

脚本调用一次 `search_file()`，直接输出回答和缓存图片路径。它不依赖 MES 文档，也不会把图片另复制一份。需要连续提问时，可在自己的代码中复用 `FileSearch` 客户端。

## 缓存和返回结果

- `result.answer` 是文字回答，`result.images` 是相关图片列表；没有匹配图片时为空列表。
- `image.image_id` 与缓存文件名对应，例如 `img_0003` 对应 `img_0003.png` 或 `.jpg`。`image.path` 是运行机器上的绝对路径。
- 图片保存在 `image_cache_dir/<source_id>/`。不同文件即使都含有 `img_0001`，也会位于各自的目录。同名但内容不同的文件会生成新的 `source_id`，不会混图。
- `data_dir/catalog.sqlite` 记录文件、图片和识别缓存。相同内容、文件名及识别配置再次提交时可复用处理结果；更换文件内容后需重新提交。
- `image_limit=None` 表示不设图片返回数量上限；`verify_images=False` 跳过查询时的视觉复核，首次导入含图文件仍需生成图片描述。

支持 TXT、MD、PDF、DOCX、PPTX、PNG 和 JPEG。复杂 Office 绘图、SmartArt、PDF 矢量内容及外链图片可能无法完整提取；可查看 `result.warnings`。程序会把文档内容发送到调用者配置的模型服务。

## 可选 HTTP 接口

需要跨进程调用时，可以使用安装包自带的 `sirchmunk-files serve`。先在运行目录执行 `sirchmunk-files init` 生成模型配置模板，填写文本和视觉模型的六项配置，然后启动：

```powershell
sirchmunk-files serve --host 127.0.0.1 --port 8585 --service-token "your-service-token" --data-dir "./sirchmunk_data" --image-cache-dir "./sirchmunk_data/images" --search-mode FAST
```

HTTP 请求需带 `Authorization: Bearer <service-token>`。上传文件用 `POST /v1/files`，等待 `GET /v1/jobs/{job_id}` 返回 `completed` 后，用 `POST /v1/search` 检索。跨机器读取图片时使用返回的 `images[].url` 请求图片内容；`images[].path` 是服务端本地路径。完整接口契约可在认证后访问 `/openapi.json`。
