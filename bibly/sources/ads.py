import ads

# key to download from NASA ADS
ads_key = ['author', 'title', 'id', 'bibcode', 'doi', 'doctype', 'volume', 'arxiv_class', \
           'identifier', 'issue', 'page', 'year', 'citation_count', 'citation', 'pub']

# key for the output dictionary
key_list = ['author', 'title', 'doctype', 'eprint', 'archivePrefix', 'primaryClass', \
            'doi', 'journal', 'volume', 'number', 'pages', 'year', 'source', 'keytitle']

class nasa_ads:

    def __init__(self, author, ads_token):

        self.author = author
        ads.config.token = ads_token

    def get_number_paper(self, aut):
    
        qry = ads.SearchQuery(q='author:"'+aut+'"')
        
        n = list(qry)
        del n

        return qry.response.numFound
    
    def create_bib_from_ads_meta(self, bib, metadata, max_num_authors=None, \
                                 num_authors_short=None, journal_arXiv_fallback=False):
    
        num_authors = len(metadata.author)
        if max_num_authors is not None and num_authors > max_num_authors:
            short_author_list = True
            if num_authors_short is None:
                num_authors_short = max_num_authors
        else:
            short_author_list = False
        author_list = []
        for idx, author in enumerate(metadata.author):
            if short_author_list and idx >= num_authors_short:
                author_list.append("et al.")
                break
            author_list.append(author)

        bib['author'].append(author_list)
        bib['citation_count'].append(metadata.citation_count)
        bib['doctype'].append(metadata.doctype)
            
        if metadata.title is not None:
            bib['title'].append(metadata.title[0])
            keytitle = ''.join(e for e in metadata.title[0] if e.isalnum()).lower()
            bib['keytitle'].append(keytitle)
        else:
            bib['title'].append('')
            keytitle = ''
            bib['keytitle'].append('')

        if metadata.identifier is not None:
            if metadata.identifier[:6] == 'arXiv:':
                bib["eprint"].append(metadata.identifier[6:])
                bib["archivePrefix"].append("arXiv")
                bib["primaryClass"].append(metadata.arxiv_class)
            else:
                bib["eprint"].append('')
                bib["archivePrefix"].append('')
                bib["primaryClass"].append('')
        else:
            bib["eprint"].append('')
            bib["archivePrefix"].append('')
            bib["primaryClass"].append('')

        if metadata.doi is not None:
            bib["doi"].append(metadata.doi[0])
        else:
            bib['doi'].append('')

        if metadata.pub is not None:
            bib["journal"].append(metadata.pub)
        else:
            if journal_arXiv_fallback:
                bib["journal"].append("arXiv:" + metadata["arxiv_eprints"][0]["value"])
            else:
                bib['journal'].append('')

        if metadata.volume is not None:
            bib["volume"].append(metadata.volume)
        else:
            bib['volume'].append('')

        if metadata.issue is not None:
            bib["number"].append(metadata.issue)
        else:
            bib['number'].append('')
        
        if metadata.page is not None:
            bib["pages"].append(metadata.page[0])
        else:
            bib['pages'].append('')

        if metadata.year is not None:
            bib["year"].append(metadata.year)
        else:
            bib['year'].append('')

        bib['source'].append('ads')

        return bib, keytitle

    def ads_bib(self, aut=None, num_paper=None, ads_key=ads_key, max_num_authors=None, \
                num_authors_short=None, journal_arXiv_fallback=False, \
                return_citations_id=False, key_list=key_list):

        if aut is None:
            aut = self.author
        if num_paper is None:
            num_paper = self.get_number_paper(aut)
    
        qry = ads.SearchQuery(q='author:"'+aut+'"', rows=num_paper, fl=ads_key)

        bib = dict((key, []) for key in key_list)
        bib['citation_count'] = []
        
        papers = list(qry)

        if return_citations_id:
            citations_bib = {}
        else:
            citations_bib = None
        
        for i in papers:
            bib, title = self.create_bib_from_ads_meta(bib, i, max_num_authors=max_num_authors, num_authors_short=num_authors_short, \
                                                       journal_arXiv_fallback=journal_arXiv_fallback)
            if return_citations_id:

                citations_bib[title] = dict((key, []) for key in key_list)
                citations_bib[title]['citation_count'] = []

                if i.citation is not None:
                    for j in i.citation:
                        temp = list(ads.SearchQuery(q='bibcode:"'+j+'"', fl=ads_key))
            
                        citations_bib[title], _ = self.create_bib_from_ads_meta(citations_bib[title], temp[0], \
                                                                                max_num_authors=max_num_authors, \
                                                                                num_authors_short=num_authors_short, \
                                                                                journal_arXiv_fallback=journal_arXiv_fallback)

        return bib, citations_bib