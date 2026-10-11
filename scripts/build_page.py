import os, datetime
D=os.environ.get('DATA','.'); T=os.environ.get('TEMPLATE','template.html'); O=os.environ.get('OUT','hemiciclo.html')
t=open(T).read()
for k,f in [('__HEM__','hemiciclo_data.json'),('__HIST__','historico_data.json'),('__PRES__','presidente_data.json'),('__NEWS__','noticias_data.json'),('__COTA__','cota_data.json')]:
    t=t.replace(k,open(os.path.join(D,f)).read().strip())
t=t.replace('__ATUALIZADO__',datetime.date.today().strftime('%d/%m/%Y'))
open(O,'w').write(t)
