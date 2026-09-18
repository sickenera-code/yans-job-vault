#!/usr/bin/env python3
"""Extract local PDF/DOCX/MD/TXT resumes without uploading them."""
import argparse
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def extract(source):
    suffix=source.suffix.lower()
    if suffix in ('.md','.txt'):
        return source.read_text(encoding='utf-8-sig')
    if suffix=='.docx':
        with zipfile.ZipFile(source) as archive:
            # Include text boxes (w:t descendants) and table cells in document order.
            root=ET.fromstring(archive.read('word/document.xml'))
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs=[]
            for paragraph in root.findall('.//w:p',ns):
                text=''.join(node.text or '' for node in paragraph.findall('.//w:t',ns))
                if text.strip(): paragraphs.append(text)
            return '\n\n'.join(paragraphs)
    if suffix=='.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            if shutil.which('pdftotext'):
                return subprocess.run(['pdftotext','-layout',str(source),'-'],check=True,capture_output=True,text=True).stdout
            raise ValueError('PDF 读取需要 pypdf 或 pdftotext；可用 python3 -m pip install pypdf，或使用当前 Agent 的 PDF 工具。')
        reader=PdfReader(source)
        if reader.is_encrypted and not reader.decrypt(''):
            raise ValueError('PDF 有密码，请使用用户提供的密码解锁副本后读取')
        return '\n\n'.join(f'<!-- 原件第 {i} 页 -->\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages,1))
    if suffix=='.doc':
        if shutil.which('antiword'):
            return subprocess.run(['antiword',str(source)],check=True,capture_output=True,text=True).stdout
        raise ValueError('旧版 .doc 需要 antiword，或用本地 Word/LibreOffice 转为 .docx 后重新读取；不要改扩展名冒充转换。')
    raise ValueError('支持 PDF、DOCX、DOC、Markdown、TXT；其他格式使用当前环境的文档读取能力。')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    text=extract(args.source.expanduser().resolve())
    meaningful=''.join(line for line in text.splitlines() if not line.startswith('<!--'))
    if len(meaningful.strip())<30:
        raise ValueError('未提取到足够文本，可能是扫描件。使用本地 OCR 或 Agent 视觉读取逐页识别并核对，不要交付空白简历。')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as handle: handle.write(text.rstrip()+'\n')
    print(f'已提取到 {args.output}；请对照原件核对顺序、表格、日期和数值。')

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,zipfile.BadZipFile,ET.ParseError,subprocess.CalledProcessError) as exc:
        print(f'错误：{exc}',file=sys.stderr);sys.exit(1)
