# -*- coding: utf-8 -*-

# https://github.com/linyuxuanlin/Auto-i18n

import os
import openai
import sys
# import env

# 设置 OpenAI API Key 和 API Base 参数，通过 env.py 传入
openai.api_key = os.environ.get("CHATGPT_API_KEY")
openai.api_base = os.environ.get("CHATGPT_API_BASE")

# 设置翻译的路径
dir_to_translate = "./"
dir_translated = {
    "en": "docs/en",
    "ja": "docs/ja",
}

exclude_list = ["index.md", "Contact-and-Subscribe.md", "WeChat.md"]  # 不进行翻译的文件列表
processed_list = "processed_list.txt"  # 已处理的 Markdown 文件名的列表，会自动生成

# 设置最大输入字段，超出会拆分输入，防止超出输入字数限制
max_length = 4000

# 文章使用英文撰写的提示，避免本身为英文的文章被重复翻译为英文
marker_written_in_en = "\n> This post was originally written in English.\n"
# 即使在已处理的列表中，仍需要重新翻译的标记
marker_force_translate = "\n[translate]\n"


# 定义翻译函数
def translate_text(text, lang):
    target_lang = {
        "en": "English",
        "ja": "Japanese",
    }[lang]

    # 使用OpenAI API进行翻译
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text into {target_lang}, maintain the original markdown format.\n\n{text}\n\n{target_lang}:",
            }
        ],
    )

    # 获取翻译结果
    output_text = completion.choices[0].message.content
    return output_text


# 定义文章拆分函数
def split_text(text, max_length):
    # 根据段落拆分文章
    paragraphs = text.split("\n\n")
    output_paragraphs = []
    current_paragraph = ""

    for paragraph in paragraphs:
        if len(current_paragraph) + len(paragraph) + 2 <= max_length:
            # 如果当前段落加上新段落的长度不超过最大长度，就将它们合并
            if current_paragraph:
                current_paragraph += "\n\n"
            current_paragraph += paragraph
        else:
            # 否则将当前段落添加到输出列表中，并重新开始一个新段落
            output_paragraphs.append(current_paragraph)
            current_paragraph = paragraph

    # 将最后一个段落添加到输出列表中
    if current_paragraph:
        output_paragraphs.append(current_paragraph)

    # 将输出段落合并为字符串
    output_text = "\n\n".join(output_paragraphs)

    return output_text


# 定义翻译文件函数
def translate_file(input_file, filename, lang):
    print(f"Translating into {lang}: {filename}")
    sys.stdout.flush()

    # 定义输出文件
    if lang in dir_translated:
        output_dir = dir_translated[lang]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, filename)

    # 读取输入文件内容
    with open(input_file, "r", encoding="utf-8") as f:
        input_text = f.read()

    # 创建一个字典来存储占位词和对应的替换文本
    placeholder_dict = {}

    # print(input_text) # debug 用，看看输入的是什么

    # 拆分文章
    paragraphs = input_text.split("\n\n")
    input_text = ""
    output_paragraphs = []
    current_paragraph = ""

    for paragraph in paragraphs:
        if len(current_paragraph) + len(paragraph) + 2 <= max_length:
            # 如果当前段落加上新段落的长度不超过最大长度，就将它们合并
            if current_paragraph:
                current_paragraph += "\n\n"
            current_paragraph += paragraph
        else:
            # 否则翻译当前段落，并将翻译结果添加到输出列表中
            output_paragraphs.append(translate_text(current_paragraph, lang))
            current_paragraph = paragraph

    # 处理最后一个段落
    if current_paragraph:
        if len(current_paragraph) + len(input_text) <= max_length:
            # 如果当前段落加上之前的文本长度不超过最大长度，就将它们合并
            input_text += "\n\n" + current_paragraph
        else:
            # 否则翻译当前段落，并将翻译结果添加到输出列表中
            output_paragraphs.append(translate_text(current_paragraph, lang))

    # 如果还有未翻译的文本，就将它们添加到输出列表中
    if input_text:
        output_paragraphs.append(translate_text(input_text, lang))

    # 将输出段落合并为字符串
    output_text = "\n\n".join(output_paragraphs)

    # 最后，将占位词替换为对应的替换文本
    for placeholder, replacement in placeholder_dict.items():
        output_text = output_text.replace(placeholder, replacement)

    # 写入输出文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

# 按文件名称顺序排序
file_list = os.listdir(dir_to_translate)
sorted_file_list = sorted(file_list)
# print(sorted_file_list)

try:
    # 创建一个外部列表文件，存放已处理的 Markdown 文件名列表
    if not os.path.exists(processed_list):
        with open(processed_list, "w", encoding="utf-8") as f:
            print("processed_list created")
            sys.stdout.flush()
    
    # 遍历目录下的所有.md文件，并进行翻译
    for filename in sorted_file_list:
        if filename.endswith(".md"):
            input_file = os.path.join(dir_to_translate, filename)

            # 读取 Markdown 文件的内容
            with open(input_file, "r", encoding="utf-8") as f:
                md_content = f.read()

            # 读取processed_list内容
            with open(processed_list, "r", encoding="utf-8") as f:
                processed_list_content = f.read()

            if marker_force_translate in md_content:  # 如果有强制翻译的标识，则执行这部分的代码
                # 删除这个提示字段
                md_content = md_content.replace(marker_force_translate, "")
                # 将删除marker_force_translate后的内容写回原文件
                # with open(filename, "w", encoding="utf-8") as f:
                #    f.write(md_content)
                if marker_written_in_en in md_content:  # 翻译为除英文之外的语言
                    print("Pass the en-en translation: ", filename)
                    sys.stdout.flush()
                    md_content = md_content.replace(marker_written_in_en, "")  # 删除这个字段
                    translate_file(input_file, filename, "ja")
                else:  # 翻译为所有语言
                    translate_file(input_file, filename, "en")
                    translate_file(input_file, filename, "ja")
            elif filename in exclude_list:  # 不进行翻译
                print(f"Pass the post in exclude_list: {filename}")
                sys.stdout.flush()
            elif filename in processed_list_content:  # 不进行翻译
                print(f"Pass the post in processed_list: {filename}")
                sys.stdout.flush()
            elif marker_written_in_en in md_content:  # 翻译为除英文之外的语言
                print(f"Pass the en-en translation: {filename}")
                sys.stdout.flush()
                md_content = md_content.replace(marker_written_in_en, "")  # 删除这个字段
                for lang in ["ja"]:
                    translate_file(input_file, filename, lang)
            else:  # 翻译为所有语言
                for lang in ["en", "ja"]:
                    translate_file(input_file, filename, lang)

            # 将处理完成的文件名加到列表，下次跳过不处理
            if filename not in processed_list_content:
                print(f"Added into processed_list: {filename}")
                with open(processed_list, "a", encoding="utf-8") as f:
                    f.write("\n")
                    f.write(filename)

            # 强制将缓冲区中的数据刷新到终端中，使用 GitHub Action 时方便实时查看过程
            sys.stdout.flush()

except Exception as e:
    # 捕获异常并输出错误信息
    print(f"An error has occurred: {e}")
    sys.stdout.flush()
    raise SystemExit(1)  # 1 表示非正常退出，可以根据需要更改退出码
    # os.remove(input_file)  # 删除源文件