#!/usr/bin/env python3
"""Behavioral checks in temporary vaults, never in the source user's data."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SKILL=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SKILL/'scripts'))
import vault
import extract_resume

class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'求职仓库'
        with contextlib.redirect_stdout(io.StringIO()): vault.initialize(self.root,2028)
    def tearDown(self): self.temp.cleanup()
    def record(self,**kwargs):
        return dict(id='test-001',company='示例/公司',position='分析[实习]:岗',type='private',date='2026-09-14',stages=[],offer=False,terminated=False,**kwargs)
    def test_empty_and_repeat_init(self):
        _,_,records=vault.read_records(self.root);self.assertEqual(records,[])
        self.assertEqual((self.root/'公考时间.md').read_bytes(),(vault.TEMPLATE/'公考时间.md').read_bytes())
        self.assertIn('2028',(self.root/'投递进度.md').read_text())
        path=self.root/'CLAUDE.md';path.write_text('用户自己的规则')
        with contextlib.redirect_stdout(io.StringIO()): vault.initialize(self.root,2029)
        self.assertEqual(path.read_text(),'用户自己的规则')
        self.assertIn('2028',(self.root/'投递进度.md').read_text())
    def test_job_sync_preserves_material_and_number(self):
        rec=self.record();path=vault.job_workspace(self.root,rec)
        self.assertEqual(path,'已投递岗位/01-示例-公司 分析-实习--岗.md')
        note=self.root/path;note.write_text(note.read_text()+'\n用户资料\n')
        material=self.root/rec['folderPath']/'面试.md';material.write_text('不可覆盖')
        vault.job_workspace(self.root,rec)
        self.assertIn('用户资料',note.read_text());self.assertEqual(material.read_text(),'不可覆盖')
        recovered=self.record();vault.job_workspace(self.root,recovered);self.assertEqual(recovered['notePath'],path)
        (self.root/'已投递岗位/07-遗留资料').mkdir()
        other=self.record();other['id']='test-002';vault.job_workspace(self.root,other)
        self.assertIn('/08-',other['notePath'])
        self.assertEqual(other['folderPath'],other['notePath'][:-3])
    def test_saved_data_preserves_surrounding_and_dollar(self):
        path,original,records=vault.read_records(self.root)
        path.write_text(original+'\n用户的备注\n');original=path.read_text()
        record=self.record();record['company']='公司 $& $`';vault.job_workspace(self.root,record)
        vault.save_records(path,original,[record])
        self.assertTrue(path.read_text().endswith('用户的备注\n'))
        self.assertEqual(vault.read_records(self.root)[2][0]['company'],record['company'])
        self.assertTrue(list(path.parent.glob('投递记录数据-备份-*.md')))
    def test_corruption_and_path_escape(self):
        path=self.root/vault.DATA;path.write_text('用户内容，没有合法区块')
        with self.assertRaises(ValueError): vault.read_records(self.root)
        self.assertEqual(path.read_text(),'用户内容，没有合法区块')
        rec=self.record(notePath='../外部.md')
        with self.assertRaises(ValueError): vault.job_workspace(self.root,rec)
        external=Path(self.temp.name)/'外部';external.mkdir()
        (self.root/'外链').symlink_to(external,target_is_directory=True)
        with self.assertRaises(ValueError): vault.inside(self.root,'外链/危险.md')
    def test_different_owner_rejected(self):
        rec=self.record();vault.job_workspace(self.root,rec)
        other=dict(rec,id='test-999')
        with self.assertRaises(ValueError): vault.job_workspace(self.root,other)
    def test_decomposition_idempotent(self):
        profile=Path(self.temp.name)/'profile.json'
        profile.write_text(json.dumps({'modules':[{'id':'edu','title':'示例大学-专业','category':'教育','source':'教育经历','excerpt':'示例大学本科'},{'id':'intern','title':'公司-实践','category':'实践','source':'实践经历','excerpt':'协助整理台账'}]}))
        with contextlib.redirect_stdout(io.StringIO()): vault.decompose(self.root,profile)
        mapping=json.loads((self.root/'Resource/简历分解映射.json').read_text())
        overview=self.root/mapping['intern']/'00-经历概览.md';overview.write_text('用户补充的概览')
        with contextlib.redirect_stdout(io.StringIO()): vault.decompose(self.root,profile)
        self.assertEqual(overview.read_text(),'用户补充的概览')
        self.assertEqual(len(list((self.root/'简历分解').glob('*/00-经历概览.md'))),2)
    def test_docx_and_markdown_extraction(self):
        doc=Path(self.temp.name)/'简历.docx'
        with zipfile.ZipFile(doc,'w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>教育经历</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>实习公司 2025.01-2025.03</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
        result=extract_resume.extract(doc)
        self.assertIn('教育经历',result);self.assertIn('实习公司 2025.01-2025.03',result)
        md=Path(self.temp.name)/'简历.md';md.write_text('# 简历\n\n原文内容')
        self.assertEqual(extract_resume.extract(md),md.read_text())
    def test_incomplete_not_claimed_done(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(vault.check(self.root));self.assertFalse(vault.check(self.root,True))

if __name__=='__main__':unittest.main(verbosity=2)
