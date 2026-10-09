"""修改文件和模型参数后直接运行，检索一次并输出结果。"""

import asyncio
from sirchmunk import search_file


result = asyncio.run(search_file(
    "你的文档.docx", "如何创建用户？",
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
    print(image.path)
