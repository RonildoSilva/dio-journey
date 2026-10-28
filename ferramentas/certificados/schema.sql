-- Banco local de certificados da DIO (dados/certificados.db, fora do git).
-- Reconstruído do zero pelo banco.py a partir dos dados locais (sem rede).
--
-- Um certificado = um curso concluído. Um mesmo curso pode estar em várias formações
-- (ex.: "Versionamento de Código com Git e GitHub"), por isso o vínculo é muitos-para-muitos.

CREATE TABLE IF NOT EXISTS formacoes (
    slug   TEXT PRIMARY KEY,           -- igual à pasta em formacoes/ (ex.: flutter-specialist)
    nome   TEXT NOT NULL,
    url    TEXT
);

CREATE TABLE IF NOT EXISTS atividades (
    formacao_slug  TEXT NOT NULL REFERENCES formacoes(slug),
    modulo         TEXT NOT NULL,
    titulo         TEXT NOT NULL,
    tipo           TEXT NOT NULL,      -- curso, desafio, desafio-codigo, complementar, avaliacao
    nivel          TEXT,
    horas          INTEGER,
    status         TEXT NOT NULL,      -- concluido | pendente (status da página da DIO)
    PRIMARY KEY (formacao_slug, modulo, titulo)
);

CREATE TABLE IF NOT EXISTS certificados (
    codigo          TEXT PRIMARY KEY,  -- código do PDF, ex.: HCXSQUZE
    curso           TEXT NOT NULL,     -- título do curso (API da DIO)
    nome_aluno      TEXT,              -- lido do PDF (OCR)
    data_conclusao  TEXT NOT NULL,     -- AAAA-MM-DD
    carga_horaria   TEXT,              -- ex.: "2 horas" (OCR)
    horas           INTEGER,           -- carga horária em número
    tipo_catalogo   TEXT,              -- course, lab_projects, bootcamp... (NULL se não está no catálogo)
    url_pdf         TEXT NOT NULL,     -- https://hermes.dio.me/certificates/<codigo>.pdf
    arquivo         TEXT NOT NULL,     -- caminho local relativo a dados/
    baixado_em      TEXT NOT NULL      -- data do arquivo PDF local (AAAA-MM-DD HH:MM)
);

CREATE TABLE IF NOT EXISTS certificado_formacao (
    codigo         TEXT NOT NULL REFERENCES certificados(codigo),
    formacao_slug  TEXT NOT NULL REFERENCES formacoes(slug),
    modulo         TEXT NOT NULL,
    PRIMARY KEY (codigo, formacao_slug, modulo)
);

CREATE INDEX IF NOT EXISTS idx_vinculo_formacao ON certificado_formacao(formacao_slug);
