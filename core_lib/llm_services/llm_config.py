import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取通义千问的API Key
TONGYI_API_KEY = os.getenv("TONGYI_API_KEY")