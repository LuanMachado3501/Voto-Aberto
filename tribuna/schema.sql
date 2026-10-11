-- Você na Tribuna: perguntas de eleitores aos deputados reeleitos.
-- Não guardamos nome, e-mail nem IP de quem pergunta.
CREATE TABLE IF NOT EXISTS perguntas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dep TEXT NOT NULL,            -- id do deputado na Câmara
  tema TEXT NOT NULL,
  texto TEXT NOT NULL,
  uf TEXT,                      -- estado informado (opcional)
  status TEXT NOT NULL DEFAULT 'pendente',  -- pendente | aprovada | recusada | enviada | respondida
  aviso TEXT,                   -- sinal automático para a triagem (ex.: palavrão, link)
  motivo TEXT,                  -- motivo da recusa (público só como categoria)
  criada INTEGER NOT NULL,
  decidida INTEGER,
  enviada INTEGER,
  prazo INTEGER,
  resposta TEXT,
  respondida INTEGER
);
CREATE INDEX IF NOT EXISTS idx_perg_dep ON perguntas(dep, status);
CREATE INDEX IF NOT EXISTS idx_perg_status ON perguntas(status);
-- Anti-flood: só um código embaralhado (não reversível), apagado depois de 7 dias.
CREATE TABLE IF NOT EXISTS limites (h TEXT NOT NULL, dep TEXT NOT NULL, criada INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_lim ON limites(h, criada);
