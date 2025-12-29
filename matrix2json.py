#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取 MITRE ATT&CK 矩阵 HTML 中最外层 technique-cell（含 supertechniquecell），
并把再深一层的 technique-cell 作为其子技术。
用法: python extract.py input.html > output.json
"""

import sys
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag

def is_top_level(cell: Tag) -> bool:
    """判断该 technique-cell 是否是最外层（祖先里再无同类）"""
    parent = cell.parent
    while parent:
        if parent.name == 'div':
            cls = parent.get('class', [])
            if 'subtechniques' in cls:
                return False
        parent = parent.parent
    return True



def extract_id_name(a_tag: Tag) -> tuple[str, str]:
    """
    从锚点标签中提取技术ID和名称

    Args:
        a_tag: BeautifulSoup锚点标签

    Returns:
        tuple: (技术ID, 名称) 或 (None, None)
    """
    href = a_tag.get('href', '')
    if not href:
        return None, None

    # 解析URL路径获取ID
    parts = [p for p in href.split('/') if p]
    if len(parts) < 2 or not parts[0].lower().startswith('t'):
        return None, None

    technique_id = parts[1]
    # 处理子技术ID格式：Txxxx.yyy
    if len(parts) >= 3:
        technique_id += '.' + parts[-1]

    # 清理名称文本：移除<sub>标签内容并规范化空白字符
    cleaned_tag = a_tag.__copy__()

    # 删除所有子标签（如计数标记）
    for sub_element in cleaned_tag.select('sub'):
        sub_element.decompose()

    # 规范化文本
    raw_text = cleaned_tag.get_text() or ''

    # 使用正则表达式清理空白字符
    # 换行符+空白 -> 单个空格
    cleaned_text = re.sub(r'\n\s+', ' ', raw_text)
    # 多个空白字符 -> 单个空格
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    # 移除首尾空白
    technique_name = cleaned_text.strip()

    return technique_id, technique_name

def parse_html(html: str):
    soup = BeautifulSoup(html, 'lxml')
    # 匹配所有含有technique-cell类型的元素
    top_cells = [
        div for div in soup.find_all(
            'div',
            class_=lambda x: x and 'technique-cell' in x
        )
        if is_top_level(div)
    ]

    result = []
    for top in top_cells:
        a_tag = top.find('a')
        if not a_tag:
            continue
        tid, name = extract_id_name(a_tag)
        if not tid:
            continue
        item = {tid: name}

        # 查找嵌套的子技术（包含所有层级的 technique-cell）
        sub_cells = top.find_all('div', class_=lambda x: x and 'technique-cell' in x)
        if sub_cells:
            sub_list = []
            for sub in sub_cells:
                sa = sub.find('a')
                if not sa:
                    continue
                stid, sname = extract_id_name(sa)
                if stid:
                    # sub_list.append({'id': stid, 'name': sname})
                    sub_list.append({stid, sname})
            if sub_list:
                item['sub'] = sub_list
        result.append(item)

    return result

def _extract_technique_info(container: Tag) -> dict:
    """提取单个技术信息，返回{id: name}格式字典"""
    anchor_tag = container.find('a')
    if not anchor_tag:
        return None

    technique_id, technique_name = extract_id_name(anchor_tag)
    if not technique_id:
        return None

    return {technique_id: technique_name}


def _process_simple_technique(child_element: Tag) -> dict:
    """处理无子技术的简单技术"""
    technique_info = _extract_technique_info(child_element)
    if technique_info:
        technique_info['sub'] = []
    return technique_info


def _process_composite_technique(child_element: Tag) -> dict:
    """处理包含子技术的复合技术"""
    # 提取所有技术单元格
    technique_cells = [
        div for div in child_element.find_all(
            'div',
            class_=lambda x: x and 'technique-cell' in x
        )
    ]

    if len(technique_cells) < 2:
        return None  # 复合技术应该至少有主技术+子技术

    # 提取主技术信息
    main_technique = _extract_technique_info(technique_cells[0])
    if not main_technique:
        return None

    # 提取子技术列表 - 紧凑格式，直接包含ID和名称
    sub_techniques = []
    for cell in technique_cells[1:]:
        sub_technique = _extract_technique_info(cell)
        if sub_technique:
            sub_techniques.append(sub_technique)

    if sub_techniques:
        main_technique['sub'] = sub_techniques
    else:
        main_technique['sub'] = []

    return main_technique


def parse_html2(html: str):
    """
    解析 MITRE ATT&CK HTML 矩阵，提取技术和子技术信息

    Args:
        html: HTML 字符串内容

    Returns:
        list: 包含技术信息的字典列表，格式 [{Txxxx: 名称, sub: [{Txxxx.001: 名称}]}]
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        result = []
        # 安全获取根节点
        body_element = soup.body
        if not body_element:
            raise ValueError("HTML文档缺少body元素")

        root_children = body_element.find_all(recursive=False)
        if not root_children:
            raise ValueError("HTML文档body为空")

        # 遍历第一层子元素
        for child in root_children[0].find_all(recursive=False):
            if not isinstance(child, Tag):
                continue

            technique_info = None

            if child.name == 'div':
                # 处理无子技术的简单技术
                technique_info = _process_simple_technique(child)
            else:
                # print("test\n")
                # 处理包含子技术的复合技术
                technique_info = _process_composite_technique(child)

            if technique_info:
                result.append(technique_info)

        return result

    except Exception as e:
        # 在实际应用中，可以考虑使用日志记录
        print(f"解析HTML时出错: {e}", file=sys.stderr)
        return []    


def main():
    if len(sys.argv) != 2:
        print('用法: python extract.py input.html > output.json', file=sys.stderr)
        sys.exit(1)
    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print('文件不存在', file=sys.stderr)
        sys.exit(1)
    records = parse_html2(html_path.read_text(encoding='utf-8'))
    print(json.dumps(records, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()