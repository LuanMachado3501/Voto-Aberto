import unicodedata, re
def N(s):
    s=unicodedata.normalize('NFD',str(s)).encode('ascii','ignore').decode().upper()
    s=re.sub(r'\(.*','',s); s=s.replace('.',' ')
    s=re.sub(r'\bPROF\b','PROFESSOR',s); s=re.sub(r'\bPROFA\b','PROFESSORA',s); s=re.sub(r'\bDEL\b','DELEGADO',s)
    s=re.sub(r'\bCEL\b','CORONEL',s); s=re.sub(r'\bSGT\b','SARGENTO',s); s=re.sub(r'\bCAP\b','CAPITAO',s); s=re.sub(r'\bPR\b','PASTOR',s)
    return re.sub(r'[^A-Z ]','',re.sub(r'\s+',' ',s)).strip()
