# >>> SAB: execução automática do motor V1.5 no GitHub Actions (15h e 23h de Brasília). Versão 2026.11.01 <<<
# =========================================================================================
# O QUE FAZ, NESTA ORDEM
#   1. Confere a impressão digital (SHA-256) do arquivo do motor contra SHA256_MOTOR.txt: só roda o arquivo
#      aprovado (05b_motor_sab_v1_5_GRAVACAO.py do pacote, o mesmo do Colab). Qualquer edição faz parar aqui.
#   2. Confere no texto do arquivo as travas: PROTEGER_HISTORICO = True e DATA_LIMITE_PROTECAO = '2025-12-31'
#      (e SIMULAR = False no 05b, SIMULAR = True no 05a). Sem elas, para sem rodar nada.
#   3. Liga o Earth Engine com a credencial do segredo EE_CREDENCIAL. Se falhar, para (nunca pede login).
#   4. Espera os pedidos por e-mail em andamento (tarefas SABPED_ prontas ou rodando) terminarem, até
#      ESPERA_PEDIDOS_MIN minutos: o motor troca dias da previsão no SAB_V1, e uma exportação de pedido lendo um
#      dia que está sendo trocado pode falhar. Passado o prazo, segue (a previsão não pode ficar velha).
#   5. Roda o motor sem nenhuma mudança (runpy), como no Colab: MODO=gravar roda o 05b; MODO=simular, o 05a.
# O Apps Script não despacha pedido novo enquanto esta execução estiver na fila ou rodando (consulta a API do
# GitHub) nem nas janelas de CONFIG.JANELAS_MOTOR. Os dois juntos evitam o conflito nos dois sentidos.
# =========================================================================================
import hashlib
import os
import re
import runpy
import sys
import time
from datetime import datetime, timedelta, timezone

VERSAO = '2026.11.01'
PROJETO = 'clima-492922'
ARQUIVOS = {'gravar': '05b_motor_sab_v1_5_GRAVACAO.py', 'simular': '05a_motor_sab_v1_5_SIMULACAO.py'}
ESPERA_PEDIDOS_MIN = 45
INTERVALO_S = 60
ATIVOS = ('READY', 'RUNNING', 'PENDING', 'SUBMITTED')
BRT = timezone(timedelta(hours=-3))
AQUI = os.path.dirname(os.path.abspath(__file__))


def sha256(caminho):
    with open(caminho, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def esperados(caminho_lista):
    saida = {}
    for linha in open(caminho_lista, encoding='utf-8'):
        partes = linha.split()
        if len(partes) == 2:
            saida[partes[1]] = partes[0]
    return saida


def conferir_travas(texto, modo):
    """Lista de problemas (vazia = tudo certo) nas constantes de segurança do motor."""
    problemas = []
    if not re.search(r'^PROTEGER_HISTORICO = True\b', texto, re.M):
        problemas.append('PROTEGER_HISTORICO não está True')
    if not re.search(r"^DATA_LIMITE_PROTECAO = '2025-12-31'", texto, re.M):
        problemas.append("DATA_LIMITE_PROTECAO não é '2025-12-31'")
    simular = re.search(r'^SIMULAR = (True|False)\b', texto, re.M)
    if not simular or simular.group(1) != ('False' if modo == 'gravar' else 'True'):
        problemas.append(f"SIMULAR deveria ser {'False' if modo == 'gravar' else 'True'} no arquivo do modo {modo}")
    return problemas


def pedidos_ativos(ops):
    return sorted(str(op.get('metadata', {}).get('description', '')) for op in ops or []
                  if str(op.get('metadata', {}).get('description', '')).startswith('SABPED_')
                  and op.get('metadata', {}).get('state') in ATIVOS)


def esperar_pedidos(ee, limite_min=ESPERA_PEDIDOS_MIN, intervalo_s=INTERVALO_S, dormir=time.sleep):
    t0 = time.time()
    while True:
        try:
            ativos = pedidos_ativos(ee.data.listOperations())
        except Exception as e:
            print(f'⚠️ Não consegui listar as tarefas ({str(e)[:120]}); sigo sem esperar.')
            return 0
        if not ativos:
            print('✅ Nenhum pedido por e-mail em andamento no Earth Engine.')
            return 0
        espera = (time.time() - t0) / 60
        if espera >= limite_min:
            print(f'⚠️ {len(ativos)} tarefa(s) de pedido ainda ativas depois de {limite_min} min ({ativos[:3]}...). '
                  'Sigo com o motor: a previsão não pode atrasar mais.')
            return len(ativos)
        print(f'⏳ {len(ativos)} tarefa(s) de pedido em andamento ({ativos[0]}...). Espero {intervalo_s} s '
              f'({espera:.0f} de {limite_min} min).')
        dormir(intervalo_s)


def main():
    modo = os.environ.get('MODO', 'gravar').strip().lower()
    if modo not in ARQUIVOS:
        print(f'❌ MODO deve ser gravar ou simular (veio "{modo}").')
        return 2
    arquivo = os.path.join(AQUI, ARQUIVOS[modo])
    print(f'🤖 SAB, motor automático | {datetime.now(BRT):%d/%m/%Y %H:%M} (BRT) | modo {modo} | {ARQUIVOS[modo]} | '
          f'rotina {VERSAO}')
    esperado = esperados(os.path.join(AQUI, 'SHA256_MOTOR.txt')).get(ARQUIVOS[modo])
    atual = sha256(arquivo)
    if atual != esperado:
        print(f'❌ O arquivo do motor não é o aprovado: SHA-256 {atual[:16]}... (esperado {str(esperado)[:16]}...). '
              'Nada foi rodado. Suba o arquivo do pacote sem editar, ou atualize SHA256_MOTOR.txt junto com ele.')
        return 3
    print(f'🔏 SHA-256 conferido: {atual}')
    problemas = conferir_travas(open(arquivo, encoding='utf-8').read(), modo)
    if problemas:
        print('❌ Travas de segurança erradas: ' + '; '.join(problemas) + '. Nada foi rodado.')
        return 4
    print('🛡️ Travas conferidas: PROTEGER_HISTORICO = True, limite 2025-12-31, SIMULAR certo para o modo.')
    import ee
    try:
        ee.Initialize(project=PROJETO)
        ee.Number(1).getInfo()
    except Exception as e:
        print(f'❌ O Earth Engine não aceitou a credencial do segredo EE_CREDENCIAL: {str(e)[:300]}')
        return 5
    if modo == 'gravar':
        esperar_pedidos(ee)
    ee.Authenticate = lambda *a, **k: (_ for _ in ()).throw(RuntimeError(
        'A credencial não funcionou dentro do motor: atualize o segredo EE_CREDENCIAL.'))   # nunca pede login
    print('\n' + '=' * 90)
    runpy.run_path(arquivo, run_name='__main__')
    print('=' * 90)
    print(f'✅ Motor terminou às {datetime.now(BRT):%H:%M} (BRT).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
