import sqlite3
import tkinter as tk
import test

def search_word(que):
    test.search_dictionary()
    conn.close()
    
    result_text.delete(1.0, tk.END)
    for row in results:
        result_text.insert(tk.END, f"单词: {row[0]}\n读音: {row[1]}\n意思: {row[2]}\词性: {row[3]}\n助词: {row[4]}\n变形: {row[5]}\n例句: {row[6]}\n级别: {row[7]}")

# 创建窗口
root = tk.Tk()
root.title("日语词典")

# 输入框
entry = tk.Entry(root, width=30)
entry.pack(pady=10)

# 搜索按钮
btn = tk.Button(root, text="搜索", command=test.search_word)
btn.pack(pady=5)

# 结果显示
result_text = tk.Text(root, height=10, width=50)
result_text.pack(pady=10)

root.mainloop()