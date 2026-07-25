from langgraph.graph import StateGraph, END
from vivia.graph.state import ViviaState
from vivia.graph.nodes import (
    node_acordar, node_cafe_manha, node_meio_manha,
    node_almoco, node_meio_tarde, node_jantar, node_antes_dormir,
)

NODE_MAP = {
    "acordar": node_acordar,
    "cafe_manha": node_cafe_manha,
    "meio_manha": node_meio_manha,
    "almoco": node_almoco,
    "meio_tarde": node_meio_tarde,
    "jantar": node_jantar,
    "antes_dormir": node_antes_dormir,
}


def _select_moment(state: ViviaState) -> str:
    """
    Decide qual nó processar nesta chamada do grafo.

    O momento do dia já vem calculado no estado inicial (router.get_current_moment(),
    chamado em main.py antes do primeiro invoke). Aqui só direcionamos a entrada
    para o nó correspondente — nunca percorremos os outros momentos na mesma
    chamada.
    """
    moment = state.get("current_moment", "acordar")
    return moment if moment in NODE_MAP else "acordar"


def build_graph():
    graph = StateGraph(ViviaState)

    for name, node_fn in NODE_MAP.items():
        graph.add_node(name, node_fn)

    # Entrada condicional: cada invoke() processa APENAS o momento atual do
    # estado — não a sequência inteira do dia. Passar de um momento para o
    # outro acontece ENTRE invocações (nova hora do dia, novo gatilho
    # externo), nunca dentro de uma mesma chamada.
    graph.set_conditional_entry_point(_select_moment, {m: m for m in NODE_MAP})

    # Cada nó encerra o turno diretamente — sem encadeamento automático
    # para o próximo momento. Isso é o que faltava: antes, todo nó tinha
    # uma aresta fixa para o próximo momento, fazendo o grafo atravessar
    # os 7 momentos numa única chamada.
    for name in NODE_MAP:
        graph.add_edge(name, END)

    return graph.compile()