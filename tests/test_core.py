import unittest
import fitz
from rag.pdf_loader import parse_pdf_bytes
from rag.text_splitter import split_text_by_page
from rag.simple_search import SearchIndex, search_chunks


class SplitTests(unittest.TestCase):
    def test_overlap_and_source_pages(self):
        chunks = split_text_by_page([{'page': 7, 'text': 'abcdefghij'}], 6, 2)
        self.assertEqual(chunks, [{'page':7,'text':'abcdef'},{'page':7,'text':'efghij'}])

    def test_short_and_blank_pages(self):
        self.assertEqual(split_text_by_page([{'page':1,'text':'abc'}]), [{'page':1,'text':'abc'}])
        self.assertEqual(split_text_by_page([{'page':2,'text':'  '}]), [])

    def test_invalid_parameters_cannot_loop(self):
        for size, overlap in [(0,0),(5,5),(5,6),(5,-1),(True,0),(5,1.5)]:
            with self.subTest(size=size, overlap=overlap), self.assertRaises(ValueError):
                split_text_by_page([],size,overlap)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.docs=[{'page':2,'text':'死锁的必要条件包括互斥、请求与保持、不可剥夺和循环等待'},
                   {'page':8,'text':'计算机网络分为物理层、数据链路层和网络层'}]
        self.index=SearchIndex(self.docs)

    def test_chinese_question_finds_relevant_page(self):
        self.assertEqual(self.index.search('死锁的必要条件是什么')[0]['page'],2)

    def test_empty_or_unmatched_queries(self):
        self.assertEqual(self.index.search('  '),[])
        self.assertEqual(self.index.search('ZZZ999'),[])

    def test_empty_index(self):
        self.assertEqual(SearchIndex([]).search('问题'),[])
        self.assertEqual(SearchIndex([{'page':1,'text':' '}]).search('问题'),[])

    def test_top_k_and_stable_ties(self):
        index=SearchIndex([{'page':5,'text':'同一段文字'},{'page':6,'text':'同一段文字'}])
        self.assertEqual([r['page'] for r in index.search('同一段文字',2)],[5,6])
        self.assertEqual(len(self.index.search('死锁网络',1)),1)

    def test_invalid_search_options(self):
        for count in [0,-1,1.5,True]:
            with self.assertRaises(ValueError): self.index.search('死锁',count)
        with self.assertRaises(ValueError): self.index.search('死锁',min_score=-.1)

    def test_index_is_reused(self):
        matrix=self.index.matrix
        self.index.search('死锁')
        self.index.search('网络')
        self.assertIs(self.index.matrix,matrix)

    def test_compatibility_function(self):
        self.assertEqual(search_chunks('死锁',self.docs)[0]['page'],2)


class PdfTests(unittest.TestCase):
    def test_original_page_number_survives_blank_page(self):
        with fitz.open() as d:
            d.new_page()
            page=d.new_page()
            page.insert_text((72,72),'Operating systems and deadlock')
            data=d.tobytes()
        pages=parse_pdf_bytes(data)
        self.assertEqual(len(pages),1)
        self.assertEqual(pages[0]['page'],2)

    def test_bad_pdf(self):
        for data in [b'',b'not a pdf']:
            with self.assertRaises(ValueError): parse_pdf_bytes(data)

    def test_blank_pdf(self):
        with fitz.open() as d:
            d.new_page(); data=d.tobytes()
        self.assertEqual(parse_pdf_bytes(data),[])


if __name__=='__main__':
    unittest.main()
