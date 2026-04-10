import json
import torch

from sqlalchemy.orm import Session
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from models import Service, ServiceChunk, get_db

splitter = SentenceSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

MODELS = [
    {"name": "qwen3", "path": "Qwen/Qwen3-Embedding-0.6B"},
    {"name": "gemma", "path": "google/embeddinggemma-300m"},
    {"name": "bge", "path": "BAAI/bge-m3"}
]

LOADED_MODELS = {
    m["name"]: SentenceTransformer(m["path"], device="cuda" if torch.cuda.is_available() else "cpu")
    for m in MODELS
}

def service_to_markdown(service: dict) -> str:
    nome = service.get("nome", "Serviço sem nome")
    descricao = service.get("descricao", "Sem descrição.")

    nomes_populares = service.get("nomesPopulares", {}).get("item", [])
    nomes_str = ", ".join([n.get("item", "") for n in nomes_populares if n.get("item")])

    orgao = service.get("orgao", {}).get("nomeOrgao", "Não informado")
    gratuito = service.get("gratuito")
    custo = "Gratuito" if gratuito in ("true", True) else "Pago"

    tempo_str = extract_tempo(service)

    solicitantes = service.get("solicitantes", {}).get("solicitante", [])
    etapas = service.get("etapas", [])

    title = f"# Serviço: {nome}"
    nomes_populares_md = f"**Nomes Populares:** {nomes_str}\n" if nomes_str else ""

    md = [title, nomes_populares_md, "## Sobre", descricao, "", f"**Órgão Responsável:** {orgao}", ""]

    if solicitantes:
        md.append("## Quem pode usar:")
        for s in solicitantes:
            tipo = s.get("tipo", "Não especificado")
            req = s.get("requisitos", "")
            md.append(f"- **{tipo}**: {req}" if req else f"- **{tipo}**")
        md.append("")

    md.extend(["## Detalhes", f"- **Custo:** {custo}", f"- **Prazo:** {tempo_str}", ""])

    if etapas:
        md.append("## Passo a Passo:")
        for i, e in enumerate(etapas, 1):
            titulo = e.get("titulo", "Etapa")
            desc = e.get("descricao", "")
            md.append(f"{i}. **{titulo}**: {desc}" if desc else f"{i}. **{titulo}**")
        md.append("")

    link = service.get("linkServicoDigital")
    if link:
        md.extend(["## Canal de Acesso", link, ""])

    return "\n".join(md)

def extract_tempo(service: dict) -> str:
    tempo = service.get("tempoTotalEstimado", {}) or {}

    imediato = tempo.get("atendimentoImediato")
    nao_estimado = tempo.get("naoEstimadoAinda")

    ate = tempo.get("ate")
    em_media = tempo.get("emMedia")
    entre = tempo.get("entre")

    if imediato is not None:
        return "Atendimento imediato"
    if nao_estimado is not None:
        return "Tempo total estimado ainda não foi definido"
    
    if ate and ate.get("max"):
        return f"Até {ate['max']} {ate.get('unidade', '')}"
    elif em_media and em_media.get("max"):
        return f"Em média {em_media['max']} {em_media.get('unidade', '')}"
    elif entre and entre.get("min") and entre.get("max"):
        return f"Entre {entre['min']} e {entre['max']} {entre.get('unidade', '')}"
    else:
        return "Não informado"

def chunk_text(text: str):
    doc = Document(text=text) 
    nodes = splitter.get_nodes_from_documents([doc])
    return [node.text for node in nodes]

def ingest_services(db: Session, json_path: str):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    
    services_data = data.get("resposta", [])
    existing = {name for (name,) in db.query(Service.nome).all()}
    
    created = 0
    pbar = tqdm(services_data, desc="Ingesting services", unit="svc")
    
    for svc in pbar:
        nome = svc.get("nome", "")
        if not nome or nome in existing:
            continue
        
        pbar.set_postfix({"serviço": nome[:20]})
        markdown = service_to_markdown(svc)
        orgao = svc.get("orgao", {}).get("nomeOrgao")
        
        service = Service(nome=nome, orgao=orgao, markdown_content=markdown)
        db.add(service)
        db.flush()

        chunks = chunk_text(markdown)
        
        # Contextual Retrieval: Add service name to chunks that don't have it already
        content_with_context = []
        for i, chunk in enumerate(chunks):
            string_to_insert = f"# Serviço: {nome}"
            if string_to_insert not in chunk:
                content_with_context.append(f"{string_to_insert}\n\n{chunk}")
            else:
                content_with_context.append(chunk)


        all_vectors = {}
        for m_name, m_instance in LOADED_MODELS.items():
            all_vectors[m_name] = m_instance.encode(content_with_context)

        for i, text_content in enumerate(content_with_context):
            chunk = ServiceChunk(
                service_id=service.id,
                content=text_content,
                chunk_index=i,
                embedding_qwen=all_vectors["qwen3"][i].tolist(),
                embedding_gemma=all_vectors["gemma"][i].tolist(),
                embedding_bge=all_vectors["bge"][i].tolist()
            )
            db.add(chunk)
        
        existing.add(nome)
        created += 1
        
        if created % 50 == 0:
            db.commit()
    
    db.commit()


if __name__ == "__main__":
    result = ingest_services(next(get_db()), "./servicos.json")
