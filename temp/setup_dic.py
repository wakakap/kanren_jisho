import os
from pathlib import Path
from jamdict import Jamdict

# --- 1. 定义和检查路径 (强制在当前目录) ---
# 获取当前脚本所在的文件夹
CWD = Path.cwd()
XML_FILE = CWD / 'JMDict.xml'
DB_FILE = CWD / 'jamdict.db'

print("--- 最终创建脚本 ---")
print(f"当前工作目录: {CWD}")
print(f"将要读取的XML: {XML_FILE}")
print(f"将要创建的DB: {DB_FILE}")
print("-" * 20)

# --- 2. 前置检查 ---
# 检查 XML 文件是否存在
if not XML_FILE.exists():
    print(f"错误：源文件 '{XML_FILE.name}' 不在当前目录中，请先将它放进来。")
# 检查 DB 文件是否已存在
elif DB_FILE.exists():
    print(f"提示：数据库文件 '{DB_FILE.name}' 已经存在，无需再次创建。")
else:
    # --- 3. 核心创建逻辑 ---
    print("前置检查通过，准备开始创建数据库...")
    print("这个过程需要几分钟，请保持耐心。")
    try:
        # 这是最关键的一步：在初始化时，将文件路径作为参数直接传递给 Jamdict
        # 这将强制它在当前目录工作，而不是去 C盘的默认路径
        jam = Jamdict(db_file=str(DB_FILE), jmd_xml_file=str(XML_FILE))
        
        print("Jamdict 初始化调用完成。")
        
        # --- 4. 最终验证 ---
        # 初始化完成后，立刻检查数据库文件是否真的被创建了
        if DB_FILE.exists():
            db_size_mb = DB_FILE.stat().st_size / (1024 * 1024)
            print("\n" + "="*30)
            print("🎉 成功！数据库创建成功！")
            print(f"数据库 '{DB_FILE.name}' 已在当前目录生成。")
            print(f"大小: {db_size_mb:.2f} MB")
            print("="*30)
        else:
            # 如果代码执行到这里，说明 Jamdict 运行没报错，但就是没创建文件
            print("\n" + "!"*30)
            print("严重错误：Jamdict 初始化过程没有报错，但数据库文件并未被创建。")
            print("这表明您使用的 Jamdict 版本存在核心功能缺陷。")
            print("建议更换 Jamdict 库的版本。")
            print("!"*30)

    except Exception as e:
        # 捕获在创建过程中可能发生的任何其他异常
        print("\n" + "!"*30)
        print("在数据库创建过程中发生未知异常！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        print("!"*30)