// Você na Tribuna — API do Centro Político (Cloudflare Worker + D1 + Turnstile).
// Público: GET /perguntas?dep=ID, GET /resumo, POST /perguntar
// Admin (cabeçalho X-Senha): GET /admin, GET /admin/api/fila, POST /admin/api/decidir,
//                            POST /admin/api/enviadas, POST /admin/api/resposta
import REE from './reeleitos.json';

const TEMAS = ['Saúde', 'Educação', 'Segurança', 'Economia e impostos', 'Emprego e renda', 'Meio ambiente',
  'Transporte e cidades', 'Direitos e costumes', 'Corrupção e transparência', 'Agro e campo', 'Gastos do mandato', 'Outro'];
const UFS = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ');
const ORIGENS = ['https://centropolitico.com.br', 'https://www.centropolitico.com.br', 'https://luanmachado3501.github.io'];
const DIA = 86400000, PRAZO_DIAS = 14;
const PUBLICOS = ['enviada', 'respondida'];
// 1ª camada (instantânea): palavrões, xingamentos e ameaças -> recusa automática, nem chega à moderação
const sem = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const OFENSA = /\b(porra|caralho|c[a@]r[a@]lh|merd[a@]|put[a@]|putinh|fdp|filh[oa] d[a@] put|vagabund|arrombad|desgracad|cuzao|cuz[aã]o|babac|otari[oa]|imbecil|idiota|retardad|escroto|canalh|safad|verme|lixo humano|vai se f|vai tomar no|tomar no cu|vtnc|vsf|pqp|viad[oa]|bicha\b|sapatao|traveco|vou te matar|te matar|vai morrer|morra|merece morrer|vou te pegar|te pegar na|bala nele|tiro na)/;
// sinais que só avisam o moderador
const SINAIS = [/https?:\/\//i, /www\./i];
// 2ª camada: IA da Cloudflare (Workers AI) para ofensas que a lista não pega. Se a IA falhar, segue só com a lista.
async function ofensivaIA(env, texto) {
  if (!env.AI) return false;
  try {
    const r = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', { max_tokens: 20, temperature: 0, messages: [
      { role: 'system', content: 'Você modera perguntas de eleitores para deputados federais no Brasil. Responda só OFENSIVA ou OK. ' +
        'OFENSIVA = xingamento, insulto pessoal, palavrão, ameaça, incitação à violência, discurso de ódio (raça, religião, gênero, orientação sexual, origem, deficiência) ou conteúdo sexual. ' +
        'OK = qualquer pergunta respeitosa, inclusive crítica dura a votos, gastos, projetos ou posições, e perguntas sobre investigações públicas.' },
      { role: 'user', content: texto }] });
    return /OFENSIV/i.test(String(r?.response || ''));
  } catch { return false; }
}

const cors = (req) => {
  const o = req.headers.get('Origin') || '';
  return { 'Access-Control-Allow-Origin': ORIGENS.includes(o) || o.startsWith('http://localhost') ? o : ORIGENS[0],
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-Senha', 'Vary': 'Origin' };
};
const json = (req, data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(req) } });

async function sha(s) {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
}
function senhaOk(req, env) {
  const a = req.headers.get('X-Senha') || '', b = env.ADMIN_SENHA || '';
  if (!b || a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
// status mostrado ao público: "enviada" vira "sem_resposta" depois do prazo
const publico = (r, agora) => ({ id: r.id, dep: r.dep, tema: r.tema, texto: r.texto, uf: r.uf, enviada: r.enviada, prazo: r.prazo,
  resposta: r.resposta, respondida: r.respondida,
  status: r.status === 'respondida' ? 'respondida' : (r.prazo && agora > r.prazo ? 'sem_resposta' : 'aguardando') });

async function perguntar(req, env) {
  let b; try { b = await req.json(); } catch { return json(req, { erro: 'Pedido inválido.' }, 400); }
  const dep = String(b.dep || ''), texto = String(b.texto || '').replace(/\s+/g, ' ').trim(), tema = String(b.tema || ''), uf = String(b.uf || '');
  if (!Object.prototype.hasOwnProperty.call(REE, dep)) return json(req, { erro: 'A Tribuna aceita perguntas só para deputados reeleitos.' }, 400);
  if (!TEMAS.includes(tema)) return json(req, { erro: 'Escolha um tema.' }, 400);
  if (uf && !UFS.includes(uf)) return json(req, { erro: 'Estado inválido.' }, 400);
  if (texto.length < 15 || texto.length > 300) return json(req, { erro: 'A pergunta precisa ter entre 15 e 300 caracteres.' }, 400);
  const ip = req.headers.get('CF-Connecting-IP') || '';
  // 1) não sou robô
  const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.token || '')); if (ip) fd.append('remoteip', ip);
  let v = { success: env.TESTE_SEM_TURNSTILE === '1' };   // só em teste local
  if (!v.success) {
    try { v = await (await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd })).json(); }
    catch { return json(req, { erro: 'Não conseguimos verificar agora. Tente de novo em instantes.' }, 503); }
  }
  if (!v.success) return json(req, { erro: 'Não conseguimos confirmar que você não é um robô. Tente de novo.' }, 400);
  // 2) anti-flood sem guardar quem é: código embaralhado com um segredo, apagado em 7 dias
  const agora = Date.now(), h = await sha(ip + '|' + env.TURNSTILE_SECRET);
  const lim = await env.DB.prepare('SELECT SUM(dep=?1 AND criada>?2) AS semana, SUM(criada>?3) AS dia FROM limites WHERE h=?4')
    .bind(dep, agora - 7 * DIA, agora - DIA, h).first();
  if ((lim?.semana || 0) >= 1) return json(req, { erro: 'Você já fez uma pergunta para este deputado nesta semana.' }, 429);
  if ((lim?.dia || 0) >= 3) return json(req, { erro: 'Limite de 3 perguntas por dia. Volte amanhã.' }, 429);
  // recusa automática: não vai para a moderação; conta só no limite diário (a pessoa pode reescrever para o mesmo deputado)
  if (OFENSA.test(sem(texto)) || await ofensivaIA(env, texto)) {
    await env.DB.batch([
      env.DB.prepare("INSERT INTO perguntas (dep,tema,texto,uf,status,motivo,criada,decidida) VALUES (?1,?2,?3,?4,'recusada','ofensa (automático)',?5,?5)").bind(dep, tema, texto, uf || null, agora),
      env.DB.prepare('INSERT INTO limites (h,dep,criada) VALUES (?1,?2,?3)').bind(h, '-', agora),
    ]);
    return json(req, { erro: 'Sua pergunta foi recusada automaticamente porque tem ofensa, palavrão ou ameaça. Reescreva de forma respeitosa: crítica ao mandato é bem-vinda.' }, 422);
  }
  const aviso = SINAIS.some(r => r.test(texto)) ? 'contém link' : (texto === texto.toUpperCase() && /[A-Z]/.test(texto) ? 'tudo em maiúsculas' : null);
  await env.DB.batch([
    env.DB.prepare('INSERT INTO perguntas (dep,tema,texto,uf,aviso,criada) VALUES (?1,?2,?3,?4,?5,?6)').bind(dep, tema, texto, uf || null, aviso, agora),
    env.DB.prepare('INSERT INTO limites (h,dep,criada) VALUES (?1,?2,?3)').bind(h, dep, agora),
  ]);
  return json(req, { ok: true });
}

async function adminApi(req, env, path) {
  if (!senhaOk(req, env)) return json(req, { erro: 'Senha incorreta.' }, 401);
  const agora = Date.now();
  if (path === '/admin/api/fila') {
    const { results } = await env.DB.prepare("SELECT * FROM perguntas WHERE status IN ('pendente','aprovada') OR (status='enviada') ORDER BY status, criada").all();
    return json(req, { perguntas: results.map(r => ({ ...r, nome: REE[r.dep] || r.dep })) });
  }
  let b = {}; try { b = await req.json(); } catch {}
  if (path === '/admin/api/decidir') {
    const acao = b.acao === 'aprovar' ? 'aprovada' : b.acao === 'recusar' ? 'recusada' : null;
    if (!acao) return json(req, { erro: 'Ação inválida.' }, 400);
    await env.DB.prepare("UPDATE perguntas SET status=?1, decidida=?2, motivo=?3 WHERE id=?4 AND status='pendente'").bind(acao, agora, b.motivo || null, Number(b.id)).run();
    return json(req, { ok: true });
  }
  if (path === '/admin/api/enviadas') {   // depois de mandar os e-mails da semana
    const r = await env.DB.prepare("UPDATE perguntas SET status='enviada', enviada=?1, prazo=?2 WHERE status='aprovada'").bind(agora, agora + PRAZO_DIAS * DIA).run();
    return json(req, { ok: true, marcadas: r.meta?.changes ?? 0 });
  }
  if (path === '/admin/api/resposta') {
    const t = String(b.texto || '').trim(); if (!t) return json(req, { erro: 'Resposta vazia.' }, 400);
    await env.DB.prepare("UPDATE perguntas SET status='respondida', resposta=?1, respondida=?2 WHERE id=?3 AND status='enviada'").bind(t, agora, Number(b.id)).run();
    return json(req, { ok: true });
  }
  return json(req, { erro: 'Não encontrado.' }, 404);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), p = url.pathname;
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(req) });
    try {
      if (p === '/perguntar' && req.method === 'POST') return await perguntar(req, env);
      if (p === '/perguntas') {
        const agora = Date.now(), dep = url.searchParams.get('dep');
        const q = dep ? env.DB.prepare(`SELECT * FROM perguntas WHERE dep=?1 AND status IN ('enviada','respondida') ORDER BY criada DESC LIMIT 50`).bind(dep)
                      : env.DB.prepare(`SELECT * FROM perguntas WHERE status IN ('enviada','respondida','aprovada') ORDER BY criada DESC LIMIT 500`);
        const { results } = await q.all();
        // a lista geral inclui as aprovadas ainda não enviadas (é dela que sai o rascunho dos e-mails da semana)
        return json(req, { perguntas: results.map(r => r.status === 'aprovada' ? { ...publico(r, agora), status: 'a_enviar' } : publico(r, agora)) });
      }
      if (p === '/resumo') {
        const agora = Date.now();
        const { results } = await env.DB.prepare(`SELECT dep, COUNT(*) AS n, SUM(status='respondida') AS resp, SUM(status='enviada' AND prazo<?1) AS sem FROM perguntas WHERE status IN ('enviada','respondida') GROUP BY dep`).bind(agora).all();
        const tot = await env.DB.prepare(`SELECT SUM(status='pendente') AS triagem, SUM(status='recusada') AS recusadas, SUM(status IN ('aprovada','enviada','respondida')) AS publicadas FROM perguntas`).first();
        return json(req, { deps: results, totais: tot, temas: TEMAS });
      }
      if (p === '/admin') return new Response(ADMIN_HTML, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'X-Robots-Tag': 'noindex' } });
      if (p.startsWith('/admin/api/')) return await adminApi(req, env, p);
      return json(req, { ok: true, servico: 'Você na Tribuna' });
    } catch (e) {
      return json(req, { erro: 'Erro interno. Tente de novo em instantes.' }, 500);
    }
  },
  async scheduled(_ev, env) {   // limpeza diária do anti-flood
    await env.DB.prepare('DELETE FROM limites WHERE criada < ?1').bind(Date.now() - 7 * DIA).run();
  },
};

const ADMIN_HTML = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Tribuna · moderação</title><style>
:root{--bg:#0F1B16;--panel:#15241D;--line:#2A3C33;--fg:#EEF0E8;--muted:#9DA9A2;--led:#FFB000}
body{margin:0;background:var(--bg);color:var(--fg);font:15px system-ui,sans-serif;padding:16px;max-width:900px;margin:auto}
h1{font-size:22px}input,textarea,button{font:inherit}input,textarea{background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:8px}
button{cursor:pointer;border-radius:6px;border:1px solid var(--line);background:none;color:var(--fg);padding:7px 12px}button.ok{background:var(--led);color:#1A1200;border:0;font-weight:700}
.c{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;margin:8px 0}.m{color:var(--muted);font-size:13px}.av{color:var(--led);font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}textarea{width:100%;min-height:70px;box-sizing:border-box}h2{font-size:17px;margin-top:26px}
</style></head><body><h1>Você na Tribuna · moderação</h1>
<div class="row" id="login"><input id="s" type="password" placeholder="Senha"><button class="ok" id="entrar">Entrar</button></div>
<div id="app"></div><script>
const API=location.origin; let S=sessionStorage.getItem('s')||'';
const call=(p,b)=>fetch(API+p,{method:b?'POST':'GET',headers:{'X-Senha':S,'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined}).then(r=>r.json());
const esc=t=>String(t??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
const dt=t=>t?new Date(t).toLocaleDateString('pt-BR'):'';
async function load(){const r=await call('/admin/api/fila'); if(r.erro){app.innerHTML='<p>'+esc(r.erro)+'</p>';return}
 document.getElementById('login').hidden=true; const P=r.perguntas, g=s=>P.filter(x=>x.status===s);
 const card=(x,btns)=>'<div class="c"><b>'+esc(x.nome||('Deputado '+x.dep))+'</b> <span class="m">· '+esc(x.tema)+(x.uf?' · eleitor de '+esc(x.uf):'')+' · '+dt(x.criada)+'</span>'+(x.aviso?'<div class="av">⚠ '+esc(x.aviso)+'</div>':'')+'<p>'+esc(x.texto)+'</p>'+btns(x)+'</div>';
 app.innerHTML='<h2>Na triagem ('+g('pendente').length+')</h2>'+g('pendente').map(x=>card(x,x=>'<div class="row"><button class="ok" onclick="dec('+x.id+',\\'aprovar\\')">Aprovar</button><button onclick="dec('+x.id+',\\'recusar\\',prompt(\\'Motivo (ofensiva, fora do mandato, repetida, não é pergunta)\\'))">Recusar</button></div>')).join('')
  +'<h2>Aprovadas, a enviar ('+g('aprovada').length+')</h2><p class="m">Depois de mandar os e-mails da semana aos deputados, clique abaixo para começar a contar o prazo de 14 dias.</p>'+g('aprovada').map(x=>card(x,()=>'')).join('')+(g('aprovada').length?'<button class="ok" onclick="env()">Marcar todas como enviadas</button>':'')
  +'<h2>Enviadas, esperando resposta ('+g('enviada').length+')</h2>'+g('enviada').map(x=>card(x,x=>'<p class="m">Prazo: '+dt(x.prazo)+'</p><textarea id="r'+x.id+'" placeholder="Cole aqui a resposta do gabinete, na íntegra"></textarea><div class="row"><button class="ok" onclick="resp('+x.id+')">Publicar resposta</button></div>')).join('');}
async function dec(id,acao,motivo){if(acao==='recusar'&&motivo===null)return; await call('/admin/api/decidir',{id,acao,motivo}); load()}
async function env(){if(!confirm('Confirmar que os e-mails desta semana foram enviados?'))return; await call('/admin/api/enviadas',{}); load()}
async function resp(id){const t=document.getElementById('r'+id).value; if(!t.trim())return; await call('/admin/api/resposta',{id,texto:t}); load()}
entrar.onclick=()=>{S=s.value; sessionStorage.setItem('s',S); load()}; if(S) load();
</script></body></html>`;
