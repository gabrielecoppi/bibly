import urllib
import json

key_list = ['author', 'title', 'doctype', 'eprint', 'archivePrefix', 'primaryClass', \
            'doi', 'journal', 'volume', 'number', 'pages', 'year', 'source', \
            'keytitle']

class inspire:

    def __init__(self, author_key):
        self.author_key = author_key

    def inspire_author_list(self, author=None):

        if not author:
            author = self.author_key
        request = 'https://inspirehep.net/api/literature?sort=mostrecent&size=1000&q=a%20' + author
        data = json.loads(urllib.request.urlopen(request).read())
        
        papers = []
        
        for i in range(data['hits']['total']):
            papers.append(data['hits']['hits'][i]['id'])
        
        return papers

    def create_record_from_metadata(self, bib, metadata, max_num_authors=None, \
                                    num_authors_short=None, journal_arXiv_fallback=False):

        if "authors" in metadata:
            num_authors = len(metadata["authors"])
            if max_num_authors is not None and num_authors > max_num_authors:
                short_author_list = True
                if num_authors_short is None:
                    num_authors_short = max_num_authors
            else:
                short_author_list = False
            author_list = []
            for idx, author in enumerate(metadata['authors']):
                if short_author_list and idx >= num_authors_short:
                    author_list.append("et al.")
                    break
                author_list.append(author['full_name'])
            
            bib['author'].append(author_list)

        else:
            bib['author'].append('')
            
        doctype = metadata["document_type"][0]
        
        try:
            bib['doctype'].append(doctype)
        except KeyError:
            bib['doctype'].apppen('')
        
        try:
            bib['title'].append(metadata["titles"][0]["title"])
        except KeyError:
            bib['title'].append('')

        try:
            keytitle = ''.join(e for e in metadata["titles"][0]["title"] \
                               if e.isalnum()).lower()
            bib['keytitle'].append(keytitle)
        except KeyError:
            keytitle = ''
            bib['keytitle'].append('')

        try:
            bib["eprint"].append(metadata["arxiv_eprints"][0]["value"])
            bib["archivePrefix"].append("arXiv")
            bib["primaryClass"].append(metadata["arxiv_eprints"][0]["categories"][0])
        except KeyError:
            bib["eprint"].append('')
            bib["archivePrefix"].append('')
            bib["primaryClass"].append('')

        try:
            bib["doi"].append(metadata["dois"][0]["value"])
        except KeyError:
            bib['doi'].append('')

        try:
            bib["journal"].append(metadata["publication_info"][0]["journal_title"])
        except KeyError:
            if journal_arXiv_fallback:
                bib["journal"].append("arXiv:" + metadata["arxiv_eprints"][0]["value"])
            else:
                bib['journal'].append('')

        try:
            bib["volume"].append(metadata["publication_info"][0]["journal_volume"])
        except KeyError:
            bib['volume'].append('')

        try:
            bib["number"].append(metadata["publication_info"][0]["journal_issue"])
        except KeyError:
            bib['number'].append('')
        
        try:
            bib["pages"].append(metadata["publication_info"][0]["page_start"])
        except KeyError:
            bib['pages'].append('')

        try:
            bib["year"].append(metadata["publication_info"][0]["year"])
        except KeyError:
            try:
                bib["year"].append(metadata["preprint_date"][0:4])
            except KeyError:
                bib['year'].append('')

        bib['source'].append('inspire')
                
        return bib, keytitle

    def single_entry(self, bib, key, max_num_authors=None, num_authors_short=None, journal_arXiv_fallback=False, \
                     return_citations_id=False, citations_bib=None, key_list=key_list):
        """
        Generate a single record based on the id number from inspire
        """
        
        request = 'https://inspirehep.net/api/literature?q=recid:' + key
        req = urllib.request.urlopen(request).read()
        data = json.loads(req)

        idx = None
        
        if data['hits']['total'] != 1:
            for i in range(data['hits']['total']):
                if data['hits']['hits'][i]['id'] == key:
                    idx = i
                else:
                    pass
            if idx is None:
                return None
        else:
            idx = 0
        
        metadata = data['hits']['hits'][0]['metadata']
        links = data['hits']['hits'][0]['links']
        
        bib, title = self.create_record_from_metadata(bib, metadata, max_num_authors=max_num_authors, \
                                                      num_authors_short=max_num_authors, \
                                                      journal_arXiv_fallback=journal_arXiv_fallback)

        bib['citation_count'].append(metadata['citation_count'])

        if return_citations_id:
            citations_bib[title] = dict((key, []) for key in key_list)
            
            citations = metadata['citation_count']
            if citations <= 10:
                ln = links['citations']
            else:
                index = links['citations'].find('q=refersto')
                ln = links['citations'][:index]+ 'size='+str(citations+1) + '&' + links['citations'][index:]

            data_citations = json.loads(urllib.request.urlopen(ln).read())

            for i in range(citations):
                citations_bib[title], _ = self.create_record_from_metadata(citations_bib[title], \
                                                                           data_citations['hits']['hits'][i]['metadata'], \
                                                                           max_num_authors=max_num_authors, \
                                                                           num_authors_short=max_num_authors, \
                                                                           journal_arXiv_fallback=journal_arXiv_fallback)
            return bib, citations_bib
        
        else:
            return bib, None

    def generate_full(self, max_num_authors=None, num_authors_short=None, journal_arXiv_fallback=False, \
                      return_citations_id=False, citations_bib=None):

        papers = self.inspire_author_list()

        bib = dict((key, []) for key in key_list)
        bib['citation_count'] = []
        
        if return_citations_id:
            citations_bib = {}

        for i in papers:
            bib, citations_bib = self.single_entry(bib, i, max_num_authors=max_num_authors,  \
                                                   num_authors_short=num_authors_short, \
                                                   journal_arXiv_fallback=journal_arXiv_fallback, \
                                                   return_citations_id=return_citations_id, \
                                                   citations_bib=citations_bib)

        return bib, citations_bib