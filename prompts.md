## Passo 1: Descoberta

Você: "Oi, estou criando um e-commerce e preciso integrar um fluxo onde os clientes possam tentar pechinchar o preço.
Quais APIs de vocês eu devo usar para isso?"
(O agente buscará no RAG, recomendará listar o catálogo primeiro e depois usar a rota /negotiate, gerando um exemplo).

## Passo 2: Setup

Você: "Legal, me gera as credenciais pra eu testar isso no meu app chamado 'Loja do Futuro'."
(O agente usará a ferramenta de setup e devolverá o Bearer token na tela).

## Passo 3: Prevenção de Erros

Você: "Vou mandar esse JSON aqui no POST do /negotiate: {"product_id": 1, "proposed_price": "850.00"}. Tá certo?"
(O agente usará a ferramenta de revisão, detectará a string decimal e avisará que vai dar Erro 400, ensinando a mandar
85000 em centavos).