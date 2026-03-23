import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.tools import create_retriever_tool, tool
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

# 1. Configuração da API Key
os.environ["OPENAI_API_KEY"] = ""

print("Carregando a documentação e criando a base de vetores...")

# 2. RAG: Carregar a Especificação OpenAPI
loader = TextLoader("openapi.yaml")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

# --- FERRAMENTA 1: BUSCA NA DOCUMENTAÇÃO ---
tool_busca = create_retriever_tool(
    retriever,
    "buscar_documentacao_api",
    "Busca informações sobre as APIs disponíveis na api-poc, rotas, regras de negócio e payloads.",
)


# --- FERRAMENTA 2: SETUP DE CREDENCIAIS ---
@tool
def gerar_credenciais_sandbox(nome_aplicacao: str) -> str:
    """
    Gera credenciais de teste (Client ID e Token) para um desenvolvedor que deseja iniciar a integração.
    """
    print(f"\n   [⚡ AÇÃO: Provisionando credenciais de Sandbox para '{nome_aplicacao}'...]")
    # Simula a criação em um banco de dados
    return f"""
      Credenciais geradas com sucesso para a aplicação '{nome_aplicacao}':
    - Client_ID: dev_client_{nome_aplicacao.lower().replace(' ', '_')}
    - Authorization Header: Bearer sandbox-token-123
    """


# --- FERRAMENTA 3: LINTER / REVISOR DE PAYLOAD ---
@tool
def revisar_payload_integracao(endpoint: str, payload_json: str) -> str:
    """
    Simula uma validação de contrato. O desenvolvedor envia o JSON que ele pretende usar e o agente valida se causaria erro 400.
    """
    print(f"\n   [AÇÃO: Validando payload do desenvolvedor para a rota {endpoint}...]")

    # Lógica simples de simulação de linter de API
    if endpoint == "/negotiate" and ("." in payload_json or "100.00" in payload_json):
        return "CRÍTICO: Possível Erro HTTP 400. A API exige que os valores financeiros sejam inteiros em centavos (ex: 85000 para R$ 850,00). O payload atual contém decimais ou strings formatadas."

    return "SUCESSO: O payload parece estar formatado corretamente de acordo com os contratos da API."


# 3. Compilando o Agente
tools = [tool_busca, gerar_credenciais_sandbox, revisar_payload_integracao]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# System Prompt focado em DevEx
regras_devex = SystemMessage(content="""
Você é um Especialista em Integração (Developer Advocate) responsável por ajudar desenvolvedores parceiros a integrarem suas aplicações com a plataforma.

Seu papel é orientar tecnicamente qual endpoint, fluxo ou recurso da API deve ser utilizado para cada necessidade apresentada.

CONTEXTO DA DOCUMENTAÇÃO
Abaixo você receberá trechos da documentação recuperados via RAG. 
Use essas informações como fonte primária de verdade.

<context>
{context}
</context>

PERGUNTA DO DESENVOLVEDOR
{question}

REGRAS DE COMPORTAMENTO

1. Você NÃO executa transações de negócio.
   - Não faz compras
   - Não cria pedidos
   - Não altera dados de clientes
   Seu papel é apenas orientar integração.

2. Seu objetivo principal é RECOMENDAR a melhor rota ou fluxo de API para resolver o problema do desenvolvedor.

3. Sempre baseie suas respostas no contexto da documentação fornecido.
   - Se a informação não estiver no contexto, diga claramente que a documentação não contém essa informação.
   - Nunca invente endpoints, parâmetros ou comportamentos da API.

4. Quando o desenvolvedor quiser testar a integração ou começar a usar a API:
   - Sugira gerar credenciais de sandbox
   - Utilize a ferramenta apropriada se disponível.

5. Se o desenvolvedor fornecer:
   - código
   - JSON
   - payload de requisição

   então utilize a ferramenta de revisão de payload para validar a estrutura e evitar erros.

6. Sempre que possível forneça exemplos práticos de integração baseados na documentação.

FORMATOS DE EXEMPLO ACEITOS

Forneça exemplos preferencialmente em:

- curl
- Python
- Node.js

FORMATO DA RESPOSTA

Responda usando a seguinte estrutura:

1. Explicação breve da solução
2. Endpoint recomendado
3. Parâmetros importantes
4. Exemplo de requisição
5. Observações ou boas práticas de integração

IMPORTANTE

- Seja técnico e objetivo.
- O público são desenvolvedores.
- Prefira respostas claras e estruturadas.
""")

agent_executor = create_agent(llm, tools, system_prompt=regras_devex)

# 4. Loop de Chat
print("\nAssistente de Integração inicializado!")
print("-" * 50)

while True:
    user_input = input("\nDesenvolvedor Parceiro: ")
    if user_input.lower() in ['sair', 'exit', 'quit']:
        break

    print("Agente: Analisando integração...\n")

    for state in agent_executor.stream({"messages": [("user", user_input)]}, stream_mode="values"):
        ultima_mensagem = state["messages"][-1]
        if ultima_mensagem.type == "ai" and ultima_mensagem.content:
            print(f"🤖: {ultima_mensagem.content}")
        # elif ultima_mensagem.type == "tool":
        #     print(f"   [🛠️ Sistema: {ultima_mensagem.content}]")
