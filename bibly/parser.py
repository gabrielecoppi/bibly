import pandas as pd
import copy
import re

key_list = ['author', 'title', 'doctype', 'eprint', 'archivePrefix', 'primaryClass', \
            'doi', 'journal', 'volume', 'number', 'pages', 'year', 'source', 'keytitle']

bib_fields = ['author', 'title', 'doi', 'journal', 'volume', 'number', 'pages', 'year', 'source']

class parser:

    def __init__(self, bibs=None):

        if bibs is not None:
            self.bibs = copy.deepcopy(bibs)
        else:
            self.bibs = bibs

    def clean_names(self, x):

        l = len(x)
        for i in range(l):
            if i < l-1:
                x.insert(2*i+1, ' and ')

        return ''.join(x)
        
    def merge(self, bibs=None, remove_duplicate=True, main_source=None, cycle_remove=True, \
              remove_keys=None):

        if bibs is None:
            if self.bibs is None:
                return
            else:
                bibs = self.bibs

        if isinstance(bibs, list):
            d = {}
            
            for i in bibs:
                try:
                    source = i['source'][0]
                    d[source] = copy.deepcopy(i)
                except IndexError:
                    return None
        
        elif isinstance(bibs, dict):
            
            keys = list(bibs.keys())

            if keys[0] in key_list:
                d = {}
                d[bibs['source'][0]] = bibs
            else:
                d = bibs

        keys = d.keys()

        if not main_source:
            main_source = str(list(keys)[0])

        df = pd.DataFrame(columns=key_list)

        for k in keys:
            if k == main_source:
                priority = 1
            else:
                priority = 0

            if isinstance(d[k], dict):
                temp = pd.DataFrame.from_dict(d[k].copy())
            elif isinstance(d[k], pd.DataFrame):
                temp = copy.copy(d[k])

            if k.lower() == 'google_scholar':
                columns = list(temp.columns)

                diff = list(set(key_list)^set(columns))

                for i in diff:
                    temp[i] = ''

            temp['priority'] = priority
            temp['author'] = temp['author'].apply(self.clean_names)
            df = pd.concat([df, temp])

        if remove_duplicate:
            df = df.sort_values('priority', ascending=False)

            if remove_keys is None:
                if cycle_remove:
                    remove_keys = [['doi', 'keytitle'], 'author']
                else:
                    remove_keys = ['doi', 'keytitle']

            if cycle_remove:
                for i in remove_keys:
                    df = df.drop_duplicates(subset=i)
            else:
                df = df.drop_duplicates(subset=remove_keys)

        return df

    def merge_citations(self, df, citations, remove_duplicate=True, main_source=None, cycle_remove=True, \
                        remove_keys=None, savefile=False, savepath=None):

        if isinstance(citations, dict):
            cits = [citations]
        else:
            cits = citations

        keytitles = df['keytitle'].tolist()

        cits_merge = {}

        for i in keytitles:
            temp = []
            for j in cits:
                if i in cits.keys():
                    temp.append(j)

            df_temp = self.merge(temp, remove_duplicate=remove_duplicate, main_source=main_source, \
                                 cycle_remove=cycle_remove, remove_keys=remove_keys)
            cits_merge[i] = df_temp

            if savefile:
                if savepath is None:
                    path = i+'.bib'
                else:
                    path = savepath+i+'.bib'
                _ = self.create_bib_file(df_temp, savefile=savefile, savepath=path)

        return cits_merge

    def create_bib_file(self, df, savefile=False, savepath=None):

        if df is None:
            return None

        s = ''
        for index, row in df.iterrows():
            if len(row['author']) > 0:
                key = row['author'].split()[0][:-1].lower()+str(row['year'])

                ### Handle LTD proceedings that are refeered, so 
                ### should be cited as articles
                jrl = ''.join(e for e in row['journal'] if e.isalnum()).lower()

                if jrl == 'journaloflowtemperaturephysics':
                    dc = 'article'
                else:
                    if row['doctype'] == 'conference paper':
                        dc = 'inproceedings'
                    else:
                        dc = row['doctype']

                s += '@{}{{{}'.format(dc, key)
                for field in df.columns:
                    if field in bib_fields:
                        if field == 'author':
                            val = re.sub('\s\s+', " ", row[field])
                        elif field == 'journal':
                            val = '{'+row[field]+'}'
                        else:
                            val = row[field]
                            
                        s += ",\n    {} = \"{}\"".format(field, val)
                s += "\n}"
                s += "\n"

        if savefile:

            if not savepath:
                savepath = 'biblio.bib'

            with open(savepath, 'w', encoding='utf-8') as f:
                f.write(s)

        return s   