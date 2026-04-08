# Paper ICI - RAG

Este repositório documenta a estrutura e o pipeline de dados para a criação de um sistema RAG (Retrieval-Augmented Generation) focado nos **Serviços Públicos Prestados pelo Governo Federal**.

## Fonte dos Dados

Os dados são provenientes do Portal de Dados Abertos do Governo Federal, disponibilizados em formato JSON contendo as informações completas de todos os serviços.

🔗 [Acessar a base de dados oficial](https://dados.gov.br/dados/conjuntos-dados/informacoes-dos-servicos-publicos-prestados-pelo-governo-federal)


## Modelo de Indexação

Para que o Modelo de Linguagem interprete com precisão as minúcias de cada entidade e retenha a estrutura da informação de forma mais eficaz, aconselha-se estruturar as properties textuais em um formato **Markdown (.md)** legível na hora de gerar os *Chunks* e enviá-los para o banco vetorial.

### JSON Original
Abaixo está o exemplo completo e bruto de como o serviço chega na API original. Nele você pode ver a infinidade de campos metadados que **não são** relevantes para o RAG, além dos campos-chave que precisamos extrair:

```json
{
  "id": "[URL API do serviço]",
  "nome": "[Nome do Serviço]",
  "sigla": "[Sigla do serviço]",
  "descricao": "[Descrição detalhada do serviço]",
  "flagPortalLogado": "[S/N]",
  "contato": "[Informações de contato (telefones, e-mail)]",
  "gratuito": "[true/false]",
  "porcentagemDigital": "[Valor numérico: 0 a 100]",
  "servicoDigital": "[true/false]",
  "linkServicoDigital": "[URL alvo do serviço digital]",
  "nomesPopulares": {
    "item": [
      {
        "item": "[Nome Popular 1]",
        "id": "[Id interno]"
      }
    ]
  },
  "solicitantes": {
    "solicitante": [
      {
        "id": "[Id interno]",
        "tipo": "[Tipo de usuário, ex: Cidadão, Empresa]",
        "requisitos": "[Requisitos para este solicitante agir]"
      }
    ]
  },
  "tempoTotalEstimado": {
    "atendimentoImediato": {}, 
    "ate": {
      "max": "10",
      "unidade": "dias"
    },
    "emMedia": {
      "max": "15",
      "unidade": "dias"
    },
    "entre": {
      "min": "1",
      "max": "5",
      "unidade": "dias-uteis"
    },
    "naoEstimadoAinda": {}
  }
  "validadeDocumento": {
    "tipo": "[Ex: Sem validade, Validade estipulada]",
    "quantidade": "[Quantidade numérico]",
    "unidade": "[Unidade tempo]",
    "descricao": "[Descrição]"
  },
  "orgao": {
    "id": "[URL Estrutura Orgao]",
    "dbId": "[ID numérico]",
    "nomeOrgao": "[Nome institucional completo]",
    "porcentagemDigital": null,
    "tempoMedioEspera": null,
    "porcentagemAvaliacoesPositivas": null,
    "qtdTotal": null,
    "qtdTotalSolicitacoes": null,
    "qtdDenuncias": null,
    "qtdReclamacao": null
  },
  "segmentosDaSociedade": {
    "item": [
      {
        "item": "[Segmentos ex: Cidadãos, Empresas]",
        "idSegmento": "[...]",
        "idServicoSegmento": "[...]"
      }
    ]
  },
  "areasDeInteresse": {
    "item": [
      "[Área temática principal]"
    ]
  },
  "palavrasChave": {
    "item": [
      {
        "item": "[Palavra-chave 1]",
        "id": "[...]"
      }
    ]
  },
  "legislacoes": {
    "item": [
      {
        "item": "[Link markdown para legislação que embasa o serviço]",
        "id": "[...]"
      }
    ]
  },
  "avaliacoes": {
    "positivas": "[Contagem inteira]",
    "negativas": "[Contagem inteira]"
  },
  "condicoesAcessibilidade": "[Instruções logísticas e de direitos de acessibilidade]",
  "tratamentoPrioritario": "[Condições do tratamento de prioridades pautado em lei]",
  "tratamentoDispensadoAtendimento": "[Normativas e Diretrizes de comportamento do serviço]",
  "etapas": [
    {
      "id": "[Id de etapa]",
      "titulo": "[Título sumarizado desta etapa de execução]",
      "descricao": "[Descrição aprofundada de requisitos ou onde ir e o que fazer]",
      "documentos": {
        "documentos": "[Opcional: Listagem de Documentos exigidos]",
        "casos": []
      },
      "custos": {
        "custos": "[Opcional: Listagem de taxas/emoliumentos]",
        "casos": []
      },
      "canaisDePrestacao": {
        "canaisDePrestacao": [
          {
            "id": "[Id]",
            "tipo": "[Ex: web, presencial]",
            "descricao": "[Endereço do balcão ou URL do balcão digital]",
            "procedimentoSistemaIndisponivel": null,
            "tempoEstimadoPeriodo": null,
            "tempoEstimadoEspera": null,
            "tempoEstimadoPeriodoService": null
          }
        ],
        "casos": []
      },
      "tempoTotalEstimado": {
        "ate": null,
        "entre": null,
        "emMedia": null,
        "atendimentoImediato": null,
        "naoEstimadoAinda": {},
        "descricao": null,
        "min": null,
        "max": null
      },
      "digitalizavel": "[true/false]"
    }
  ],
  "tempoMediaEspera": "[Valor máximo numérico de espera]",
  "percentualAvaliacoesPositivas": "[Percentual]",
  "url": "[URL pública web - gov.br]",
  "flagPagTesouro": "[S/N]"
}
```

### Documento .MD
Este é o formato Markdown sugerido para ser ingerido pelo banco de dados de Embeddings, gerado a partir do JSON acima:

```markdown
# Serviço: [nome] 
**Nomes populares:** ([nomesPopulares])

## Sobre
[descricao]

**Órgão Responsável:** [nomeOrgao]

## Quem pode usar e exigências:
- **[solicitantes.tipo]**: [solicitantes.requisitos]

## Detalhes
- **Custo:** [gratuito ? 'Gratuito' : 'Pago']
- **Prazo estimado:** [tempoTotalEstimado.max] [unidade]

## Passo a Passo (Como Solicitar):
1. **[etapa1.titulo]**: [etapa1.descricao]
2. **[etapa2.titulo]**: [etapa2.descricao]

## Canal de Acesso
[linkServicoDigital]
```

## Modelos de Dados (SQLAlchemy)

O sistema utiliza SQLAlchemy com PostgreSQL e a extensão `pgvector` para armazenamento de embeddings. A estrutura de modelos está organizada em `app/models/`:

### Service

Modelo principal que armazena os serviços públicos.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `UUID` | Identificador único (PK) |
| `nome` | `str` | Nome do serviço |
| `orgao` | `str \| None` | Órgão responsável |
| `markdown_content` | `str` | Conteúdo do serviço em formato Markdown |
| `metadata` | `JSONB` | Metadados adicionais em formato JSON |
| `created_at` | `datetime` | Data de criação |
| `updated_at` | `datetime` | Data de atualização |
| `chunks` | `list[ServiceChunk]` | Relacionamento com os chunks do serviço |

### ServiceChunk

Modelo que armazena os chunks (fragmentos) de cada serviço junto com seus embeddings vetoriais.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `UUID` | Identificador único (PK) |
| `service_id` | `UUID` | FK para o serviço pai |
| `content` | `str` | Conteúdo textual do chunk |
| `chunk_index` | `int` | Índice do chunk dentro do serviço |
| `embedding` | `Vector(2048)` | Vetor de embedding (dimensão 2048) |
| `created_at` | `datetime` | Data de criação |
| `updated_at` | `datetime` | Data de atualização |
| `service` | `Service` | Relacionamento com o serviço pai |

### Diagrama de Relacionamento

```
┌─────────────────────┐       ┌─────────────────────────┐
│      Service        │       │     ServiceChunk        │
├─────────────────────┤       ├─────────────────────────┤
│ id (PK)             │───┐   │ id (PK)                 │
│ nome                │   └──►│ service_id (FK)         │
│ orgao               │       │ content                 │
│ markdown_content    │       │ chunk_index             │
│ metadata (JSONB)    │       │ embedding (Vector 2048) │
│ created_at          │       │ created_at              │
│ updated_at          │       │ updated_at              │
└─────────────────────┘       └─────────────────────────┘
        1                              N
```
