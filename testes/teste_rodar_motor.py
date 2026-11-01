# Testes do lançador do motor (sem Earth Engine). Rodar: python testes/teste_rodar_motor.py
import os
import sys
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import rodar_motor as rm  # noqa: E402

falhas = 0


def confere(c, m):
    global falhas
    print(('  ok   ' if c else '  FALHA ') + m)
    falhas += 0 if c else 1


RAIZ = os.path.join(AQUI, '..')
esp = rm.esperados(os.path.join(RAIZ, 'SHA256_MOTOR.txt'))
for modo, arq in rm.ARQUIVOS.items():
    confere(rm.sha256(os.path.join(RAIZ, arq)) == esp.get(arq), f'{arq}: o arquivo do repositório é o aprovado')
    confere(rm.conferir_travas(open(os.path.join(RAIZ, arq), encoding='utf-8').read(), modo) == [],
            f'{arq}: travas certas para o modo {modo}')
texto = open(os.path.join(RAIZ, rm.ARQUIVOS['gravar']), encoding='utf-8').read()
confere(rm.conferir_travas(texto.replace('PROTEGER_HISTORICO = True', 'PROTEGER_HISTORICO = False'), 'gravar') != [],
        'trava do histórico desligada: não roda')
confere(rm.conferir_travas(texto, 'simular') != [], 'arquivo de gravação no modo simular: não roda')
ops = [{'metadata': {'description': 'SABPED_P1_002', 'state': 'RUNNING'}},
       {'metadata': {'description': 'SABPED_P1_003', 'state': 'COMPLETED'}},
       {'metadata': {'description': 'SAB_2026_11_01_C1', 'state': 'RUNNING'}}]
confere(rm.pedidos_ativos(ops) == ['SABPED_P1_002'], 'só tarefas de pedido ativas contam')
chamadas = []
fila = [ops, ops, []]
ee = types.SimpleNamespace(data=types.SimpleNamespace(listOperations=lambda: fila.pop(0)))
confere(rm.esperar_pedidos(ee, limite_min=10, intervalo_s=1, dormir=chamadas.append) == 0 and len(chamadas) == 2,
        'espera os pedidos terminarem e segue')
ee2 = types.SimpleNamespace(data=types.SimpleNamespace(listOperations=lambda: ops))
confere(rm.esperar_pedidos(ee2, limite_min=0, intervalo_s=1, dormir=lambda s: None) == 1,
        'passado o prazo, segue mesmo com pedido ativo')
os.environ['MODO'] = 'apagar'
confere(rm.main() == 2, 'modo desconhecido não roda')
print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
