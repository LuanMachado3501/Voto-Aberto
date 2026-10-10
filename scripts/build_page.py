t=open('template.html').read()
for k,f in [('__HEM__','hemiciclo_data.json'),('__HIST__','historico_data.json'),('__PRES__','presidente_data.json'),('__NEWS__','noticias_data.json')]: t=t.replace(k,open(f).read().strip())
open('hemiciclo.html','w').write(t)
