# >>> ARQUIVO PRONTO: motor V1.5 GRAVANDO (uso diário depois da etapa 5a aprovada). Cole inteiro, sem editar nada. <<<
# =========================================================================================
# TÍTULO: MOTOR MESTRE OPERACIONAL SAB V1.5 - SCRIPT 1 (CONTA CLIMA)
# RESUMO DA FUNÇÃO: Autenticação, processamento e tarefas isoladas para clima-492922
# MUDANÇAS V4 (20/10/2026) - motor V1.5 (sobre a V1.4). Trechos marcados com [V4 <item>]:
#   - [V4 B1/M05-08] Rodadas GFS: só 00Z (creation_time múltiplo de 86.400.000 ms). Completa =
#     as 208 saídas de 1 a 384 h (120 horárias + 40 de 3 h até 240 h + 48 de 3 h até 384 h), sem a
#     hora 0, contadas numa só consulta para todas as rodadas da janela. Referência = a 00Z completa
#     mais recente; sem nenhuma completa, os dias GFS não são processados nesta execução. Dias
#     passados usam a rodada 00Z do próprio dia (ou, se ela estiver incompleta, a 00Z completa
#     anterior mais recente, M05-09).
#   - [V4 B1-horizonte/M05-28] Fim da cadeia = min(hoje + 15, dia da referência + 15). O último
#     dia é o prazo 16 (horas 361-384), completo com a rodada 00Z e calibrado com a faixa L11a15.
#   - [V4 B6/M05-10/M05-11] Dia incompleto: chuva, radiação, ETo, ET real e transpiração mascaradas;
#     o balde usa a chuva escalada por 4/n blocos (0 sem blocos); fim da média simples da radiação;
#     saídas duplicadas descartadas (distinct) e contagem exata (eq). [V4 M05-09] dias incompletos
#     ou com falha são refeitos quando a rodada certa está completa.
#   - [V4 B3/M05-07] Matriz GFS: um só getInfo confere as 48 bandas de média e versao_matriz = 'V2.1'.
#   - [V4 B4/M05-05] CRIT_SOLO_BRASIL = 2.0 (±2%, como o roteiro e o D13).
#   - [V4 B5/M05-04] CONVERTER_EM_DEFINITIVO = False: dias depois de DATA_LIMITE_PROTECAO não viram
#     'definitiva' sozinhos quando o BR-DWGD passar a cobri-los; aviso no início.
#   - [V4 C1/M05-01/M05-02] Rota definitiva: BR-DWGD primeiro e ERA5 só onde ele falta; máscara que
#     exclui -32768 e o dummy -99999; ETo, radiação e vento do BR-DWGD limitados a >= 0.
#   - [V4 C2/M05-03] Máscara canônica: todos os dias novos com a cobertura de SAB_2025_12_31 (pr_mm),
#     por updateMask em finalizar(), no lugar do .clip(poligonoBrasil) (a máscara já contém o recorte).
#   - [V4 C4/M03-15] Calibração só da rota GFS: chuva (m_sicsb + 0,1)/(m_gfs + 0,1) com teto FATOR_MAX;
#     vento com fator entre 0,5 e 2,0 (a radiação também, até a revisão K9A; ver abaixo). A rota ERA5 não muda.
#   - [V4 B8/M05-17] Propriedades novas: Confianca_Prazo, fonte, janela_chuva_utc, matriz_gfs.
#   - [V4 M05-22] VERSAO_ALGORITMO = 'V1.5' e aceita nos definitivos; aviso de opções inertes com a trava.
#   - [V4 B2/M05-06] PRÉVIA 6: rota GFS calculada em memória no modo simulação (sem exportar nada).
#   - [V4.1 K7] Tmax e Tmin dos dias GFS: constante METODO_TEMP_GFS ('variancia', o padrão desde a revisão de
#     20/10/2026 validada pela auditoria K8, ou 'aditivo'; escala de variância com os desvios da matriz V2.1). A PRÉVIA 6 calcula os dois e diz qual passa no recorde
#     do INMET e na emenda com o ERA5; o motor confere também as 16 bandas de desvio da Tmax e da Tmin.
#     Propriedade nova nos dias GFS: metodo_temp_gfs.
#   - [V4.1 revisão] A PRÉVIA 6 inclui o dia de prazo 8 (faixa L6a10); o cálculo do outro método não derruba
#     o critério obrigatório; sem a emenda testada, a decisão manda rodar de novo; um dia gravado com outro
#     método é refeito na próxima execução (precisa_refazer_gfs lê metodo_temp_gfs).
#   - [K9A, 20/10/2026] Umidade relativa e radiação dos dias GFS pela escala de variância (constante
#     METODO_UR_RS_GFS = 'variancia'; 'original' volta à UR aditiva e à radiação com fator [0,5; 2]).
#     Validação K9A (GFS v16, treino 2021-2024, teste em 2025 inteiro, 300 pontos, 438 mil previsões; IC 95%
#     por bootstrap de dias): MAE da UR 6,65 -> 4,98 (-25%), da radiação 3,51 -> 3,03 MJ/m²/dia (-14%) e da
#     ETo 0,704 -> 0,611 mm/dia (-13%); a variância também ganhou em cada um dos 5 anos do v16 (cada ano
#     testado com o treino nos outros). O motor confere as 16 bandas de desvio da UR e da radiação na
#     matriz; propriedade nova nos dias GFS: metodo_ur_rs_gfs; um dia gravado com outro método é refeito.
#   - [K11, 22/10/2026] Teto da razão dos desvios da Tmax e da Tmin nos prazos de 6 dias em diante
#     (faixas L6a10 e L11a15): RAZAO_DESVIO_MAX_LONGO = 1.0 (nos prazos 1 a 5 continua RAZAO_DESVIO_MAX = 2.0;
#     a UR e a radiação não mudam). Motivo: em 22/10 a previsão de 26/10 em Casa Nova-BA (prazo 6) saiu
#     com Tmax 45,24 °C (GFS bruto 35,41 °C; razão 1,98). Validação K11 (GFS v16, teste 2025 e cada ano de
#     2021 a 2025; regra fixada antes de rodar): nos prazos 8 e 13, MAE da Tmax 1,891 -> 1,879 (-0,6%) e da
#     Tmin 1,272 -> 1,205 (-5,3%), menos previsões além do limite físico do ponto (Tmax 0,171% -> 0,163%;
#     Tmin 0,303% -> 0,151%) e geada prevista mais perto da observada (0,131% -> 0,088%; obs 0,108%); ganhou
#     nos 5 anos. Propriedade nova nos dias GFS: teto_razao_temp_gfs (dia sem ela conta como 2.0); um dia
#     gravado com outro teto é refeito.
#   - [V4 M05-19] Promoção do TMP só se a versão do algoritmo for a atual; trava também em exportar().
#   - Prévia gravada em previa_v15.csv (antes previa_v14.csv).
#   - Fora do escopo V1.5 (não feitos): interpolação mensal (M05-12), janela 12-12 UTC (M05-16/V3),
#     ERA5 horário, constantes FAO-56 na equação de Magnus (M05-23) e qualquer outra mudança na rota ERA5.
# ATUALIZAÇÃO V1.4 (sobre a V1.3):
#   - Umidade do solo do ERA5 (0-7 cm e 0-100 cm) com reamostragem bilinear, igual à matriz
#     SICSB_SOLO_2015_2025 que calcula o fator SMAP/ERA5. Antes o dia usava vizinho mais
#     próximo e a matriz usava bilinear: o fator era aplicado sobre um campo diferente do que
#     o gerou. Dias definitivos (até 2025) não mudam; a partir dos provisórios há uma pequena
#     descontinuidade conhecida nas duas bandas de umidade.
#   - GFS: reamostragem bilinear em cada imagem ANTES de compor. O .resample() sobre a
#     composição (V1.3) não vale para composições no Earth Engine. Reprojeção final sem resample.
#   - GFS calibrado pela matriz SICSB_MATRIZ_GFS_V2, com faixas de prazo (1, 2-5, 6-10 e
#     11-15 dias de antecedência). Antes a calibração do 1º dia valia para os 15 dias.
#   - Prévia ajustada à V1.4: nos dias provisórios, só as duas bandas de umidade devem mudar.
#   - Radiação do GFS pela média dos blocos de 6 h (horas múltiplas de 6), como a chuva. Auditoria
#     de 20/10/2026 (item F4): o fluxo de onda curta do GFS é a média acumulada desde o início do
#     bloco de 6 h, e a média simples das saídas superestimava a radiação diária em 3% a 11%.
# ATUALIZAÇÃO V1.3 (sobre a V1.2):
#   - ETo dos dias provisórios (rota ERA5) calculada por Penman-Monteith FAO-56 com a
#     meteorologia calibrada, pela mesma função que a rota GFS já usava. Antes era a evaporação
#     potencial do ECMWF calibrada, que no teste E4 (953 pontos, 2016-2025) errou 12,7% ao ano
#     contra 4,0% do Penman-Monteith. O BR-DWGD, base dos dias definitivos, também é FAO-56.
#   - Dias provisórios gravados por versões anteriores do algoritmo são recalculados
#   - A janela operacional cobre todos os dias provisórios (desde o dia seguinte ao último BR-DWGD).
#     Como a fila do Earth Engine atende por ordem de envio, só os 15 dias ERA5 que servem de base
#     à previsão entram antes da cadeia GFS; os demais provisórios são enviados depois dela
#   - Modo simulação com prévia: compara as 16 bandas e a coerência física (ET real <= ETo etc.)
#     do que o painel mostra hoje com o que a V1.3 gravaria, por região, e avalia o resultado
#     contra critérios definidos antes de rodar. As médias
#     regionais saem de uma só passada sobre a grade (estados pintados, sem unir polígonos) e,
#     se o Earth Engine recusar por memória ou tempo, o Brasil é dividido em 4 e depois 16 partes
#   - Dias definitivos (até o último dia do BR-DWGD) não são alterados
# ATUALIZAÇÃO V1.2 (sobre a V1.1):
#   - Calibração multiplicativa volta à fórmula da V1.0 (alvo / max(modelo, 1e-3)), agora com
#     teto no fator: onde o fator original já era menor que o teto, o resultado é idêntico à V1.0
#   - Umidade do solo limitada ao teto físico (média SMAP + 3 desvios, no máximo 0.9 m³/m³)
#   - Patch do acervo V1.0: corrige SÓ umidade do solo e escoamento; demais bandas são copiadas
#     do asset existente, sem recálculo
#   - GFS: Tmax/Tmin pela temperatura horária (mesma variável da matriz GFS), amplitude térmica
#     mínima, ET real ancorada no comportamento ERA5 recente de cada pixel, balde com capacidade
#     por pixel
#   - Recorte volta ao polígono exato do GAUL (igual à V1.0)
# ATUALIZAÇÃO V1.1:
#   - Janela diária do GFS corrigida para (00Z, 24Z] (acumulados terminam no forecast_time)
#   - Rodada GFS escolhida no cliente, gravada no asset e usada para decidir atualização
#   - Banda de transpiração mantida (troca conhecida de bandas do ERA5-Land documentada)
#   - Calibração multiplicativa com piso físico e fator limitado
#   - Escrita atômica (exporta em coleção temporária e promove após conclusão)
#   - Janela operacional (recente + previsão) processada antes do passivo histórico
#   - Sem ano fixo no código; falhas de inventário interrompem a execução
#   - Ordem de bandas canônica em todas as rotas
# =========================================================================================

import ee
import math
import re
import time
from datetime import datetime, timezone, timedelta

import pandas as pd

# =========================================================================
# 1. CONFIGURAÇÃO
# =========================================================================
PROJECT_ID_ATIVO = 'clima-492922'
ASSET_DESTINO = f'projects/{PROJECT_ID_ATIVO}/assets/SAB_V1'
ASSET_TEMP = f'projects/{PROJECT_ID_ATIVO}/assets/SAB_V1_TMP'
SUFIXO_TASK = 'C1'

ASSET_CLIMATOLOGIA = 'projects/clima-492922/assets/SICSB_1986_2025'
ASSET_DESTINO_MATRIZ_GFS = 'projects/clima-492922/assets/SICSB_MATRIZ_GFS_V2'
ASSET_SOLO = 'projects/clima-492922/assets/SICSB_SOLO_2015_2025'

VERSAO_ALGORITMO = 'V1.5'        # [V4] antes 'V1.4'
VERSAO_PATCH = 'V1.0-P12'        # dia da V1.0 com umidade do solo e escoamento corrigidos
# True: modo simulação. Lê o acervo e informa o que seria feito, sem exportar,
# apagar, renomear ou criar nenhum asset. Rode assim antes da primeira execução real.
SIMULAR = False
# True (só vale no modo simulação): calcula, sem gravar nada, uma prévia que compara o que o
# painel mostra hoje nos dias provisórios com o que a V1.5 gravaria, e diz se o resultado
# atende aos critérios de aprovação da seção 7. [V4 B2] Inclui a PRÉVIA 6 (rota GFS em memória).
PREVIA = True
PREVIA_DIAS_DO_MES = (15,)       # dias de cada mês provisório usados na prévia, ex.: (5, 15, 25)
# True: umidade do solo do ERA5 com reamostragem bilinear, igual à matriz SICSB_SOLO_2015_2025.
# False: vizinho mais próximo, como todo o histórico 1961-2025 foi gravado. Decida pela prévia.
SOLO_BILINEAR = True
# Algoritmos aceitos nos dias definitivos: esses dias nunca são recalculados por mudança de versão
ALGORITMOS_DEFINITIVOS_VALIDOS = ('V1.0', VERSAO_PATCH, 'V1.2', 'V1.3', 'V1.4', 'V1.5')   # [V4 M05-22]
# [V4 M05-22] Sem a versão atual na tupla, os definitivos dela seriam reexportados a cada execução.
assert VERSAO_ALGORITMO in ALGORITMOS_DEFINITIVOS_VALIDOS, "Inclua VERSAO_ALGORITMO em ALGORITMOS_DEFINITIVOS_VALIDOS."
# False (decisão atual): o histórico V1.0 NÃO é regravado; a correção de umidade do solo e
# escoamento desses dias é feita na leitura, pelo Painel SAB (corrigirSoloEscoamentoV10).
# True: aplica o patch no próprio banco (várias execuções, respeitando a fila).
APLICAR_PATCH_SOLO = False
# True: recalcula do zero os dias de versões anteriores (não necessário; mantenha False).
REPROCESSAR_VERSAO_ANTIGA = False
# TRAVA DO HISTÓRICO. True: nenhum dia até DATA_LIMITE_PROTECAO é exportado, recalculado, criado
# ou substituído, em nenhuma hipótese (nem por versão antiga, nem por dia ausente, nem por sobra
# na coleção temporária). Dias históricos que precisariam de alguma ação são apenas listados no
# relatório "PROTEGIDOS". Só mude para False por decisão explícita de reprocessar o histórico.
PROTEGER_HISTORICO = True
DATA_LIMITE_PROTECAO = '2025-12-31'
# [V4 B5/M05-04] False (decisão atual): quando o BR-DWGD passar a cobrir dias depois de
# DATA_LIMITE_PROTECAO, esses dias continuam provisórios (rota ERA5) e NUNCA viram 'definitiva'
# sozinhos; o início da execução avisa quantos aguardam decisão. True: converte pela rota definitiva.
CONVERTER_EM_DEFINITIVO = False

# [V4 M05-28] Hoje + 15 dias = prazo 16 (horas 361-384 da rodada 00Z de hoje). Com rodada 00Z esse
# dia fica completo (8 saídas e 4 blocos de chuva). A matriz GFS não tem faixa para o prazo 16:
# ele usa a calibração da faixa L11a15 (extrapolação). O fim efetivo da cadeia é
# min(hoje + 15, dia da rodada de referência + 15): ver fim_horizonte().
HORIZONTE_DIAS = 15
JANELA_OPERACIONAL_DIAS = 90     # dias recentes processados com prioridade
DIAS_BUSCA_RODADAS = 12          # quantos dias de rodadas GFS considerar
# [V4 B1] Rodada GFS completa: todas as saídas de 1 a 384 h (a hora 0 não conta): 120 horárias
# (1-120 h), 40 de 3 em 3 h (123-240 h) e 48 de 3 em 3 h (243-384 h) = 208. Com a hora 0, o acervo
# tem 209 imagens por rodada (auditoria F2). A V1.4 aceitava >= 198 imagens contando a hora 0.
MS_DIA = 86400000
PRAZO_MAX_GFS = 16               # 384 h / 24
HORAS_RODADA_COMPLETA = [h for h in range(1, 24 * PRAZO_MAX_GFS + 1) if h <= 120 or h % 3 == 0]
N_SAIDAS_RODADA = len(HORAS_RODADA_COMPLETA)
assert N_SAIDAS_RODADA == 208
LIMITE_TAREFAS_MAX = 3000
RESERVA_OPERACIONAL = 100        # vagas que o histórico nunca consome
INTERVALO_POLL_S = 30
TIMEOUT_TAREFA_MIN = 120

DATA_INICIO_P1 = '1991-01-01'
DATA_INICIO_P2 = '1961-01-01'
DATA_FIM_P2 = '1990-12-31'

# Calibração multiplicativa: fator = alvo / max(modelo, 1e-3) (fórmula da V1.0), limitado
# a FATOR_MAX. Só os pixels cujo fator original passava do teto mudam.
FATOR_MAX = 5.0
# [V4 C4/M03-15] Calibração SÓ da rota GFS (a rota ERA5 continua com calib_multiplicativa acima).
# Chuva: fator = (m_sicsb + K_CHUVA_MM)/(m_gfs + K_CHUVA_MM), com teto FATOR_MAX. Na seca a média do
# GFS fica perto de zero e o fator explodia: na matriz GFS V1, julho, p95 = 13,3 e p99 = 59,2
# (auditoria J4). Vento e radiação: fator limitado a [FATOR_MIN_UV_RS, FATOR_MAX_UV_RS]
# (fator 5 é fisicamente impossível nessas variáveis). Muda só os dias GFS.
K_CHUVA_MM = 0.1                 # mm/dia
FATOR_MIN_UV_RS = 0.5
FATOR_MAX_UV_RS = 2.0
# [V4.1 K7] Correção da Tmax e da Tmin SÓ nos dias GFS:
#   'aditivo'   (V1.5 original): x + (m_sicsb - m_gfs), a mesma correção de média da V1.0.
#   'variancia' (escala de variância; PADRÃO desde a revisão de 20/10/2026, auditoria K8): m_sicsb +
#               (x - m_gfs) x (s_sicsb / s_gfs), com a razão dos desvios limitada a [RAZAO_DESVIO_MIN,
#               RAZAO_DESVIO_MAX]. Corrige a média e também a amplitude das anomalias.
#   K7 (set-nov/2025): a correção aditiva deixa o máximo diário nacional de 2,6 a 3,5 °C acima do BR-DWGD.
#   K8 (validação fora da amostra: treino 2021-2024, teste 2025, 300 pontos, 146.400 previsões), refeita na
#   revisão final com as estatísticas de treino mês a mês, como a matriz V2.1 calcula:
#     Tmax: MAE 1,58 °C (variância) x 1,99 °C (aditiva), diferença -0,41 °C (IC 95% -0,45 a -0,37; 122 dias);
#           dias acima de 35 °C 12,4% x 17,8% (observado 11,6%); acima de 40 °C 0,08% x 0,28% (observado 0,10%).
#     Tmin: empate prático, MAE 1,085 x 1,070 °C (+0,015 °C); noites abaixo do P10 9,2% x 9,1% (observado 9,3%).
# A PRÉVIA 6 continua mostrando os dois métodos lado a lado (só informação).
METODO_TEMP_GFS = 'variancia'
RAZAO_DESVIO_MIN = 0.5
RAZAO_DESVIO_MAX = 2.0
# [K11, 22/10/2026] Nos prazos de 6 dias em diante a Tmax e a Tmin usam a razão dos desvios limitada a
# [RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX_LONGO]: o GFS varia pouco de um dia para outro nesses prazos porque perde
# habilidade, e inflar a anomalia criava extremos (Casa Nova-BA, 26/10/2026: 45,24 °C com o GFS em 35,41 °C).
# Validação K11 aprovada na Tmax e na Tmin (ver o cabeçalho). Só a Tmax e a Tmin; UR e radiação não mudam.
RAZAO_DESVIO_MAX_LONGO = 1.0
FAIXAS_LONGAS = ('L6a10', 'L11a15')
assert METODO_TEMP_GFS in ('aditivo', 'variancia'), "METODO_TEMP_GFS deve ser 'aditivo' ou 'variancia'"
# [K9A] Correção da umidade relativa e da radiação SÓ nos dias GFS:
#   'original'  (V1.5 até a revisão K9A): UR aditiva, x + (m_sicsb - m_gfs), limitada a [0, 100]; radiação com
#               o fator m_sicsb / m_gfs limitado a [FATOR_MIN_UV_RS, FATOR_MAX_UV_RS].
#   'variancia' (PADRÃO desde a revisão K9A, 20/10/2026): m_sicsb + (x - m_gfs) x (s_sicsb / s_gfs), com a
#               razão dos desvios limitada a [RAZAO_DESVIO_MIN, RAZAO_DESVIO_MAX]; UR limitada a [0, 100] e
#               radiação >= 0. Usa as bandas de desvio que a matriz V2.1 já tem (contrato de 100 bandas).
#   K9A (2025, fora do treino): MAE da UR 6,65 -> 4,98 (-25%), da radiação 3,51 -> 3,03 (-14%), da ETo
#   0,704 -> 0,611 mm/dia (-13%). Limitação registrada: a variância prevê menos dias muito secos (UR < 30%:
#   0,09% x 0,18% observado) e menos dias de ETo > 6 mm (3,3% x 4,3% observado). O vento continua com o fator.
METODO_UR_RS_GFS = 'variancia'
assert METODO_UR_RS_GFS in ('original', 'variancia'), "METODO_UR_RS_GFS deve ser 'original' ou 'variancia'"
# Teto físico da umidade do solo: média SMAP + SIGMAS desvios do mês, nunca acima de 0.9
UMIDADE_MAX_FISICA = 0.9
SIGMAS_TETO_UMIDADE = 3.0

# Balde de solo do GFS. A capacidade efetiva de cada pixel é o maior valor entre estas
# constantes e a umidade do último dia ERA5 (evita corte artificial na transição).
SW100_MAX_MM = 400.0
SW100_CC_MM = 330.0
SW5_MAX_MM = 25.0
DIAS_REF_ET = 15          # dias ERA5 usados para ancorar ET real e transpiração no GFS
AMPLITUDE_MIN_C = 1.0     # amplitude térmica mínima nos dias GFS

ORDEM_BANDAS = [
    'pr_mm', 'tmax_C', 'tmin_C', 'RH', 'et_potencial', 'et_real', 'vpd',
    'rs', 'u2', 'tsolo_C', 'tfolha_C', 'transpiracao_mm',
    'runoff_sup_mm', 'runoff_sub_mm',
    'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3',
]
VERSOES_GFS = ('provisoria_gfs', 'provisoria_gfs_incompleta', 'falha_latencia_gfs')
# [V4 B6/M05-10] Bandas mascaradas no dia 'provisoria_gfs_incompleta' (dependem da chuva ou da radiação)
BANDAS_MASCARADAS_INCOMPLETO = ['pr_mm', 'rs', 'et_potencial', 'et_real', 'transpiracao_mm']
# [V4 B3/M05-07] Matriz GFS exigida pelo motor (contrato SPEC_V4)
VERSAO_MATRIZ_GFS = 'V2.1'
VARS_MATRIZ_GFS = ('pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs')
# [V4 B8/M05-17] Propriedades gravadas (contrato SPEC_V4)
FONTE_GFS = 'NOAA/GFS0P25 (rodada 00Z)'
FONTE_ERA5 = 'ECMWF/ERA5_LAND/DAILY_AGGR'
FONTE_DEFINITIVA = 'BR-DWGD (ERA5 só onde falta)'
JANELA_CHUVA_00_24 = '00-24'
JANELA_CHUVA_12_12 = '12-12 (12 UTC D-1 a 12 UTC D)'
MATRIZ_GFS_ROTULO = f'SICSB_MATRIZ_GFS_V2 {VERSAO_MATRIZ_GFS}'
# [V4 C2/M05-03] Dia do histórico cuja máscara (banda pr_mm) é a cobertura canônica de todos os dias novos
DIA_MASCARA_CANONICA = '2025-12-31'
ARQUIVO_PREVIA = 'previa_v15.csv'   # [V4] antes previa_v14.csv
ESTADOS_ATIVOS = ('READY', 'RUNNING', 'SUBMITTED', 'PENDING')
ESTADOS_FINAIS = ('COMPLETED', 'FAILED', 'CANCELLED')

fuso_br = timezone(timedelta(hours=-3))
data_extracao_local = datetime.now(fuso_br).strftime('%Y-%m-%d %H:%M:%S')
data_hoje_dt = datetime.now(timezone.utc)
data_hoje_str = data_hoje_dt.strftime('%Y-%m-%d')
data_fim_processo = (data_hoje_dt + timedelta(days=HORIZONTE_DIAS)).strftime('%Y-%m-%d')
# [V4 B1-horizonte] executar_cadeia_gfs() reduz data_fim_processo para min(hoje + 15, referência + 15)

print(f"🔄 Iniciando SAB {VERSAO_ALGORITMO} no projeto: {PROJECT_ID_ATIVO}...")
print(f"🕒 Timestamp de Operação (Local/BRT): {data_extracao_local}\n")

try:
    ee.Initialize(project=PROJECT_ID_ATIVO)
except Exception:
    print("🔗 Autenticação necessária:")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID_ATIVO)

# [Correção 20/10/2026, 23h30] Trava de somente leitura herdada de outro script na MESMA sessão do Colab: os scripts
# de simulação e de auditoria (01a, 07, 08 e as validações) bloqueiam as funções de escrita do Earth Engine, e o
# bloqueio continua valendo nas células seguintes da sessão. Um script que grava precisa de uma sessão nova.
def _escrita_bloqueada_na_sessao():
    _funcs = [getattr(ee.batch.Task, 'start', None)] + [getattr(ee.data, _n, None) for _n in (
        'createAsset', 'deleteAsset', 'renameAsset', 'copyAsset', 'setAssetAcl', 'startProcessing', 'exportImage')]
    return any(getattr(_f, '__name__', '') in ('_bloqueado', '_bloq') for _f in _funcs)


MSG_SESSAO_TRAVADA = ('Esta sessão do Colab ainda tem a trava de somente leitura de um script rodado antes nela '
                      '(por exemplo, o 01a, o 07 ou o 08). Nada foi gravado. No menu do Colab, clique em '
                      '"Ambiente de execução" e depois em "Reiniciar sessão" (confirme), e rode este arquivo de novo.')

if not SIMULAR and _escrita_bloqueada_na_sessao():
    raise RuntimeError('❌ ' + MSG_SESSAO_TRAVADA)

# =========================================================================
# 2. OBJETOS GLOBAIS
# =========================================================================
_gaul_br = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
limitesRegiao = _gaul_br.geometry().bounds()
poligonoBrasil = _gaul_br.geometry()   # polígono exato, igual à V1.0 (garante bordas idênticas)
# [V4 C2/M05-03] finalizar() não recorta mais por poligonoBrasil: usa MASCARA_SAB, que já contém esse
# recorte (o dia de referência foi gravado com .clip(poligonoBrasil)). A variável fica para consulta.
crsNativo = 'EPSG:4326'
transformNativo = [0.09999847412109375, 0, -73.9000015258789, 0, -0.09999847412109375, 5.400000095367432]
elevacao_br = ee.Image('USGS/SRTMGL1_003').clip(limitesRegiao)
colChuvaGeral = ee.ImageCollection('projects/ee-alexandrexavier/assets/BR-DWGD')
colecao_era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
COL_GFS = 'NOAA/GFS0P25'

def ms_para_data(ms):
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime('%Y-%m-%d')

def data_para_ms(d_str):
    return int(datetime.strptime(d_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp() * 1000)

def somar_dias(d_str, n):
    return (datetime.strptime(d_str, '%Y-%m-%d') + timedelta(days=n)).strftime('%Y-%m-%d')

def intervalo_datas(ini, fim):
    if ini > fim:
        return []
    return pd.date_range(start=ini, end=fim).strftime('%Y-%m-%d').tolist()

def id_dia(d_str):
    return 'SAB_' + d_str.replace('-', '_')

def desc_dia(d_str):
    return 'SAB_M_' + d_str.replace('-', '_') + '_' + SUFIXO_TASK

def desc_de_nome(nome):
    return nome.replace('SAB_', 'SAB_M_', 1) + '_' + SUFIXO_TASK

# [V4 C2/M05-03] Máscara canônica, lida uma vez: a cobertura da banda pr_mm do último dia do histórico.
# Todas as rotas passam a gravar exatamente essa cobertura (D10). A existência do asset é conferida
# no início da orquestração.
MASCARA_SAB = ee.Image(f'{ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}').select('pr_mm').mask()

def ultimo_dia_continuo(datas):
    """[Correção 21/10/2026, 18h] datas: conjunto de dias 'AAAA-MM-DD' com imagem ERA5-Land. Devolve (último dia
    sem lacuna desde o primeiro dia do conjunto, lista dos dias que faltam entre o primeiro e o último publicado)."""
    ordenadas = sorted(datas)
    faltando = [x for x in intervalo_datas(ordenadas[0], ordenadas[-1]) if x not in datas]
    if not faltando:
        return ordenadas[-1], []
    return somar_dias(faltando[0], -1), faltando

def limite_definitivo(ultima_brd, converter, data_limite):
    """[V4 B5/M05-04] Último dia que pode ser gravado (ou convertido) como 'definitiva'.
    Com converter=False, nenhum dia depois de data_limite vira definitivo, mesmo coberto pelo BR-DWGD."""
    return ultima_brd if converter else min(ultima_brd, data_limite)

def dias_aguardando_decisao(ultima_brd, data_limite):
    """[V4 B5/M05-04] Quantos dias depois de data_limite o BR-DWGD já cobre."""
    if ultima_brd <= data_limite:
        return 0
    return (datetime.strptime(ultima_brd, '%Y-%m-%d') - datetime.strptime(data_limite, '%Y-%m-%d')).days

# Últimas datas disponíveis (falha aqui interrompe: decidir rota sem essa informação é inseguro)
_ini_busca = ee.Date(data_hoje_dt.strftime('%Y-%m-%d')).advance(-150, 'day')
# [Correção 21/10/2026, 18h] O ERA5-Land DAILY_AGGR do Earth Engine pode publicar um dia antes dos anteriores
# (em 21/10/2026 havia 2026-10-11 sem 2026-10-09 e 2026-10-10). Com a data MÁXIMA, os dias da lacuna iam para a
# rota ERA5 sem imagem e a tarefa falhava ("Image.select: Parameter 'input' is required and may not be null").
# Agora a rota ERA5 vai só até o último dia CONTÍNUO (sem lacuna); da lacuna em diante, os dias seguem pela
# previsão GFS (rodada 00Z do próprio dia) até o ERA5 preencher a lacuna, quando a execução seguinte os refaz
# como ERA5 (o mesmo caminho que já transforma dias de previsão em dias ERA5).
_lista_era5 = colecao_era5.filterDate(_ini_busca, ee.Date(data_hoje_str).advance(1, 'day')) \
    .aggregate_array('system:time_start').getInfo()
if not _lista_era5:
    raise RuntimeError("Não foi possível determinar a última data do ERA5-Land.")
ultima_data_era5_publicada = ms_para_data(max(_lista_era5))
ultima_data_era5, dias_faltando_era5 = ultimo_dia_continuo({ms_para_data(t) for t in _lista_era5})
if dias_faltando_era5:
    print(f"⚠️ ERA5-Land sem {len(dias_faltando_era5)} dia(s) no Earth Engine antes do último publicado "
          f"({ultima_data_era5_publicada}): {dias_faltando_era5[:10]}. Os dias ERA5 vão até {ultima_data_era5} "
          f"(último sem lacuna); os seguintes seguem pela previsão GFS até a lacuna ser preenchida.")

_ms_brd = colChuvaGeral.aggregate_max('system:time_start').getInfo()
if _ms_brd is None:
    raise RuntimeError("Não foi possível determinar a última data do BR-DWGD.")
ultima_data_brd = ms_para_data(_ms_brd)

print(f"📡 Última data ERA5-Land: {ultima_data_era5}"
      + (f" (contínua; publicada até {ultima_data_era5_publicada})" if dias_faltando_era5 else "")
      + f" | Última data BR-DWGD: {ultima_data_brd}")

# [V4 B5/M05-04] Limite da rota definitiva, usado em status_dia(), na escolha da rota e na janela
limite_def = limite_definitivo(ultima_data_brd, CONVERTER_EM_DEFINITIVO, DATA_LIMITE_PROTECAO)
_n_aguardando = dias_aguardando_decisao(ultima_data_brd, DATA_LIMITE_PROTECAO)
if _n_aguardando and not CONVERTER_EM_DEFINITIVO:
    print(f"⏸️ BR-DWGD já cobre até {ultima_data_brd}: {_n_aguardando} dias aguardam decisão "
          f"(CONVERTER_EM_DEFINITIVO = False: seguem provisórios, rota ERA5).")
elif _n_aguardando:
    print(f"🔁 CONVERTER_EM_DEFINITIVO = True: {_n_aguardando} dias depois de {DATA_LIMITE_PROTECAO} "
          f"serão gravados como definitivos (BR-DWGD até {ultima_data_brd}).")

# =========================================================================
# 3. UTILITÁRIOS DE ASSET E TAREFA
# =========================================================================
def asset_existe(path):
    try:
        ee.data.getAsset(path)
        return True
    except ee.EEException:
        return False

def propriedades_asset(path):
    try:
        return ee.data.getAsset(path).get('properties', {}) or {}
    except ee.EEException:
        return None

def info_de_propriedades(p):
    if p is None:
        return None
    rodada = p.get('rodada_gfs_ms', 0)
    return {
        'versao': p.get('versao', 'definitiva'),
        'alg': p.get('versao_algoritmo', 'V1.0'),
        'rodada': int(float(rodada)) if rodada is not None else 0,
        'metodo': p.get('metodo_temp_gfs', 'aditivo'),          # [V4.1 revisão V41-08]
        'metodo_ur_rs': p.get('metodo_ur_rs_gfs', 'original'),  # [K9A]
        'teto_razao': float(p.get('teto_razao_temp_gfs', 2.0)),  # [K11] dia sem a propriedade: 2.0
    }

def garantir_colecao(path):
    if not asset_existe(path):
        if SIMULAR:
            print(f"🧪 [SIMULAÇÃO] Criaria a coleção: {path}")
            return
        ee.data.createAsset({'type': 'IMAGE_COLLECTION'}, path)
        print(f"📁 Coleção criada: {path}")

def listar_nomes(parent):
    nomes, token = [], None
    while True:
        params = {'parent': parent, 'pageSize': 1000}
        if token:
            params['pageToken'] = token
        resp = ee.data.listAssets(params)
        for a in resp.get('assets', []):
            caminho = a.get('id') or a.get('name')
            nomes.append(caminho.split('/')[-1])
        token = resp.get('nextPageToken')
        if not token:
            break
    return nomes

def listar_tarefas_ativas():
    """Retorna {descricao: id} de TODAS as tarefas ativas (a fila de 3000 é por usuário)."""
    ativas = {}
    for t in ee.data.getTaskList():
        if t.get('state') in ESTADOS_ATIVOS:
            ativas[t.get('description', '')] = t.get('id')
    return ativas

def versao_tmp_aceita(alg):
    """[V4 M05-19] Versões que podem ser promovidas da coleção temporária: a atual e a do patch."""
    return alg in (VERSAO_ALGORITMO, VERSAO_PATCH)

def promover_tmp(nome):
    """Substitui o asset definitivo pelo temporário já concluído.
    [V4 M05-19] Não é atômico (apaga e renomeia). Antes de promover: respeita a trava do histórico e
    confere a versão do algoritmo do TMP; uma sobra de versão antiga é apagada e o dia é refeito
    pelo fluxo normal (o asset final continua com a versão antiga ou ausente)."""
    tmp = f'{ASSET_TEMP}/{nome}'
    final = f'{ASSET_DESTINO}/{nome}'
    if dia_protegido(nome):                                    # [V4 M05-19]
        return False
    p = propriedades_asset(tmp)                                # [V4 M05-19] None = não existe
    if p is None:
        return False
    if not versao_tmp_aceita(p.get('versao_algoritmo')):       # [V4 M05-19]
        print(f"🧹 {nome}: sobra na coleção temporária com versão {p.get('versao_algoritmo')} "
              f"(atual {VERSAO_ALGORITMO}); apagada sem promover, o dia será refeito.")
        ee.data.deleteAsset(tmp)
        return False
    if asset_existe(final):
        ee.data.deleteAsset(final)
    ee.data.renameAsset(tmp, final)
    return True

_NOME_DIA = re.compile(r'^SAB_\d{4}_\d{2}_\d{2}$')

def data_de_nome(nome):
    """'SAB_2026_01_05' -> '2026-01-05'."""
    return nome[4:].replace('_', '-')

def dia_protegido(nome):
    """Com a trava ligada, protege todo dia até DATA_LIMITE_PROTECAO e todo nome fora do padrão."""
    if not PROTEGER_HISTORICO:
        return False
    return not (_NOME_DIA.match(nome) and data_de_nome(nome) > DATA_LIMITE_PROTECAO)

def finalizar_trocas_pendentes(tarefas_ativas):
    if not asset_existe(ASSET_TEMP):
        return
    promovidos, bloqueados, seriam, seriam_apagados = 0, [], [], []   # [V4 M05-19]
    for nome in listar_nomes(ASSET_TEMP):
        if desc_de_nome(nome) in tarefas_ativas:
            continue
        if dia_protegido(nome):
            bloqueados.append(nome)
            continue
        if SIMULAR:
            # [V4 M05-19] na simulação, separa as sobras de versão antiga (seriam apagadas, não promovidas)
            p = propriedades_asset(f'{ASSET_TEMP}/{nome}') or {}
            (seriam if versao_tmp_aceita(p.get('versao_algoritmo')) else seriam_apagados).append(nome)
            continue
        if promover_tmp(nome):
            promovidos += 1
    if bloqueados:
        print(f"🛡️ {len(bloqueados)} item(ns) na coleção temporária NÃO foram promovidos (trava do histórico): "
              f"{bloqueados[:10]}{' ...' if len(bloqueados) > 10 else ''}")
    if seriam:
        print(f"🧪 [SIMULAÇÃO] Seriam promovidos da coleção temporária: {len(seriam)} dia(s), "
              f"de {min(seriam)} a {max(seriam)}.")
    if seriam_apagados:   # [V4 M05-19]
        print(f"🧪 [SIMULAÇÃO] Seriam apagados da coleção temporária (versão diferente de {VERSAO_ALGORITMO}): "
              f"{len(seriam_apagados)} dia(s), de {min(seriam_apagados)} a {max(seriam_apagados)}.")
    if promovidos:
        print(f"🔁 {promovidos} dia(s) promovido(s) da coleção temporária para {ASSET_DESTINO}.")

def mapear_colecao():
    if not asset_existe(ASSET_DESTINO):
        return {}
    col = ee.ImageCollection(ASSET_DESTINO)

    def para_feature(img):
        d = img.toDictionary()
        return ee.Feature(None, {
            'id': img.get('system:index'),
            'versao': d.get('versao', 'definitiva'),
            'alg': d.get('versao_algoritmo', 'V1.0'),
            'rodada': d.get('rodada_gfs_ms', 0),
            'metodo': d.get('metodo_temp_gfs', 'aditivo'),          # [V4.1 revisão V41-08]
            'metodo_ur_rs': d.get('metodo_ur_rs_gfs', 'original'),  # [K9A]
            'teto_razao': d.get('teto_razao_temp_gfs', 2.0),          # [K11]
        })

    try:
        lista = col.map(para_feature) \
            .reduceColumns(ee.Reducer.toList().repeat(7), ['id', 'versao', 'alg', 'rodada', 'metodo',
                                                          'metodo_ur_rs', 'teto_razao']) \
            .get('list').getInfo()
    except Exception as e:
        raise RuntimeError(f"Falha ao inventariar {ASSET_DESTINO}; execução interrompida para evitar reenvio em massa. Detalhe: {e}")

    inventario = {}
    for idx, versao, alg, rodada, metodo, metodo_ur_rs, teto_razao in zip(*lista):
        inventario[str(idx).split('/')[-1]] = {
            'versao': versao, 'alg': alg,
            'rodada': int(float(rodada)) if rodada is not None else 0,
            'metodo': metodo,
            'metodo_ur_rs': metodo_ur_rs,                           # [K9A]
            'teto_razao': float(teto_razao) if teto_razao is not None else 2.0,   # [K11]
        }
    return inventario

# =========================================================================
# 4. FUNÇÕES DE CALIBRAÇÃO E MONTAGEM
# =========================================================================
def expandir_borda(img):
    return img.unmask(img.reproject(crs=crsNativo, crsTransform=transformNativo)
                      .focalMean(1, 'square', 'pixels'))

def calib_aditiva(img, m_alvo, m_modelo):
    return img.add(expandir_borda(m_alvo).subtract(expandir_borda(m_modelo)))

def fator_v10(m_alvo, m_modelo):
    """Fator exatamente como na V1.0 (sem teto)."""
    return expandir_borda(m_alvo).divide(expandir_borda(m_modelo).max(1e-3))

def calib_multiplicativa(img, m_alvo, m_modelo):
    # Onde o fator da V1.0 já era <= FATOR_MAX, min() devolve o mesmo valor: resultado idêntico
    return img.multiply(fator_v10(m_alvo, m_modelo).min(FATOR_MAX))

def calib_chuva_gfs(img, m_alvo, m_modelo):
    """[V4 C4/M03-15] Só rota GFS: fator = (m_sicsb + K)/(m_gfs + K), K = K_CHUVA_MM, teto FATOR_MAX.
    A constante K estabiliza o fator nos pixels e meses secos (médias perto de zero)."""
    fator = expandir_borda(m_alvo).add(K_CHUVA_MM).divide(expandir_borda(m_modelo).add(K_CHUVA_MM))
    return img.multiply(fator.min(FATOR_MAX))

def calib_limitada_gfs(img, m_alvo, m_modelo):
    """[V4 C4/M03-15] Só rota GFS (vento e radiação): fator da V1.0 limitado a [0,5; 2,0]."""
    return img.multiply(fator_v10(m_alvo, m_modelo).clamp(FATOR_MIN_UV_RS, FATOR_MAX_UV_RS))

def razao_desvios(s_alvo, s_modelo, teto=None):
    """[V4.1 K7] s_sicsb / s_gfs limitada a [RAZAO_DESVIO_MIN, teto]; teto padrão RAZAO_DESVIO_MAX.
    [K11] A Tmax e a Tmin dos prazos de 6 dias em diante usam teto = RAZAO_DESVIO_MAX_LONGO."""
    teto = RAZAO_DESVIO_MAX if teto is None else teto
    return (expandir_borda(s_alvo).divide(expandir_borda(s_modelo).max(1e-3))
            .clamp(RAZAO_DESVIO_MIN, teto))

def teto_razao_temp(faixa):
    """[K11] Teto da razão dos desvios da Tmax e da Tmin na faixa de prazo do dia."""
    return RAZAO_DESVIO_MAX_LONGO if faixa in FAIXAS_LONGAS else RAZAO_DESVIO_MAX

def calib_variancia(img, m_alvo, m_modelo, s_alvo, s_modelo, teto=None):
    """[V4.1 K7] Escala de variância (só rota GFS): m_alvo + (x - m_modelo) x razão dos desvios."""
    return expandir_borda(m_alvo).add(img.subtract(expandir_borda(m_modelo))
                                      .multiply(razao_desvios(s_alvo, s_modelo, teto)))

def teto_umidade(solo, camada):
    m = expandir_borda(solo.select(f'{camada}_m_smap'))
    s = expandir_borda(solo.select(f'{camada}_s_smap'))
    return m.add(s.multiply(SIGMAS_TETO_UMIDADE)).min(UMIDADE_MAX_FISICA).unmask(UMIDADE_MAX_FISICA)

def es_de(T):
    return T.expression('0.6108 * exp(17.625 * T / (T + 243.04))', {'T': T})

def vpd_e_ea(tmax, tmin, rh):
    es = es_de(tmax).add(es_de(tmin)).divide(2)
    ea = es.multiply(rh).divide(100)
    return es.subtract(ea).max(0).rename('vpd'), ea

def eto_penman_monteith(tmax, tmin, rh, u2, rs, data_str):
    """ETo diária FAO-56 Penman-Monteith (mm/dia), a mesma conta que a rota GFS faz desde a V1.0.
    Entradas por pixel: Tmax e Tmin (°C), UR (%), vento a 2 m (m/s) e radiação solar (MJ/m²/dia).
    Usada pelas rotas GFS e provisória (ERA5); nos dias definitivos a ETo vem do BR-DWGD."""
    data_atual = ee.Date(data_str)
    lat_rad = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180.0)
    pressao_atm = elevacao_br.multiply(-0.0065).add(293.0).divide(293.0).pow(5.26).multiply(101.3)
    gamma_dinamico = pressao_atm.multiply(0.000665)
    tmedia = tmax.add(tmin).divide(2)
    vpd, ea = vpd_e_ea(tmax, tmin, rh)
    J = ee.Number(data_atual.getRelative('day', 'year')).add(1)
    dr = J.multiply(2.0 * math.pi / 365.0).cos().multiply(0.033).add(1.0)
    delta_sol = J.multiply(2.0 * math.pi / 365.0).subtract(1.39).sin().multiply(0.409)
    ws = lat_rad.tan().multiply(delta_sol.tan()).multiply(-1.0).clamp(-1.0, 1.0).acos()
    termo1 = ws.multiply(lat_rad.sin()).multiply(delta_sol.sin())
    termo2 = lat_rad.cos().multiply(delta_sol.cos()).multiply(ws.sin())
    Ra = termo1.add(termo2).multiply(dr).multiply((24.0 * 60.0 / math.pi) * 0.0820)
    Rso = elevacao_br.multiply(0.00002).add(0.75).multiply(Ra)
    Rs_Rso = rs.divide(Rso).clamp(0.0, 1.0)
    Rns = rs.multiply(0.77)
    tmax_k = tmax.add(273.16)
    tmin_k = tmin.add(273.16)
    rad_term = tmax_k.pow(4).add(tmin_k.pow(4)).divide(2.0).multiply(4.903e-9)
    umid_term = ea.sqrt().multiply(-0.14).add(0.34)
    nuvem_term = Rs_Rso.multiply(1.35).subtract(0.35)
    Rn = Rns.subtract(rad_term.multiply(umid_term).multiply(nuvem_term).max(0))
    delta_press = tmedia.expression(
        '4283.58 * (0.6108 * exp(17.625 * T / (T + 243.04))) / ((T + 243.04) ** 2)', {'T': tmedia})
    num_1 = delta_press.multiply(Rn).multiply(0.408)
    num_2 = gamma_dinamico.multiply(ee.Image(900).divide(tmedia.add(273))).multiply(u2).multiply(vpd)
    den = delta_press.add(gamma_dinamico.multiply(ee.Image(1).add(u2.multiply(0.34))))
    return num_1.add(num_2).divide(den).max(0).rename('et_potencial')

def finalizar(img, propriedades):
    et_pot = img.select('et_potencial')
    et_real = img.select('et_real')
    transp = img.select('transpiracao_mm')
    et_real_l = et_real.min(et_pot.unmask(et_real)).rename('et_real')
    transp_l = transp.min(et_real_l).rename('transpiracao_mm')
    # [V4 C2/M05-03] Máscara canônica no lugar do .clip(poligonoBrasil): todas as rotas gravam a
    # cobertura do histórico (SAB_2025_12_31, banda pr_mm), que já traz o recorte pelo polígono GAUL.
    # O clip não é necessário para a pegada: a exportação usa region=limitesRegiao, e fora da máscara
    # tudo fica mascarado. Manter os dois poderia aplicar duas vezes a fração de borda (A CONFIRMAR:
    # como updateMask combina máscaras fracionárias; com a máscara própria da imagem = 1, o resultado é
    # a máscara de referência em qualquer regra). Efeito: os dias GFS perdem os ~4 pixels extras do
    # D10; as bandas de solo do GFS deixam de crescer 1 pixel por dia; a cobertura dos dias ERA5 e
    # definitivos fica a mesma de hoje. [V4 A-03] O updateMask só RESTRINGE: nos dias GFS a cobertura
    # fica CONTIDA na canônica (a calibração vem da pegada do BR-DWGD dilatada 2 pixels), e pixels
    # isolados preenchidos pelo ERA5 no histórico (ilhas, por exemplo) podem ficar sem valor. O D10
    # da auditoria 08 v4 confere isso separando os dias GFS dos dias ERA5.
    saida = (img.addBands(ee.Image.cat([et_real_l, transp_l]), overwrite=True)
             .select(ORDEM_BANDAS).toFloat().updateMask(MASCARA_SAB))
    return saida.set(propriedades)

def _componentes_era5(data_str):
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')
    mes = data_str[5:7]
    clima = ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{mes}')
    solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{mes}')
    era = ee.Image(colecao_era5.filterDate(dStart, dEnd).first())

    def mc(p):
        return clima.select(f'{p}_m_br'), clima.select(f'{p}_m_era')

    def ms(p):
        return solo.select(f'{p}_m_smap'), solo.select(f'{p}_m_era5')

    pr_raw = era.select('total_precipitation_sum').multiply(1000).max(0)
    tmax_raw = era.select('temperature_2m_max').subtract(273.15).resample('bilinear')
    tmin_raw = era.select('temperature_2m_min').subtract(273.15).resample('bilinear')
    # Limitação conhecida: o DAILY_AGGR só traz componentes médias; a velocidade derivada
    # delas subestima o vento em dias de direção variável. Corrigir exige ERA5_LAND/HOURLY.
    u2_raw = era.select('u_component_of_wind_10m').hypot(era.select('v_component_of_wind_10m')) \
        .multiply(0.748).resample('bilinear')
    rs_raw = era.select('surface_solar_radiation_downwards_sum').divide(1e6).resample('bilinear')
    t2m = era.select('temperature_2m').subtract(273.15).resample('bilinear')
    tdew = era.select('dewpoint_temperature_2m').subtract(273.15).resample('bilinear')
    rh_raw = t2m.expression(
        '100 * (exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T)))',
        {'T': t2m, 'Td': tdew})
    # V1.3: a evaporação potencial do ECMWF (potential_evaporation_sum) deixou de ser usada;
    # a ETo é calculada por Penman-Monteith logo abaixo, com a meteorologia já calibrada.

    c = {}
    c['pr_mm'] = calib_multiplicativa(pr_raw, *mc('pr')).max(0).rename('pr_mm')
    c['u2'] = calib_multiplicativa(u2_raw, *mc('u2')).max(0).rename('u2')
    c['rs'] = calib_multiplicativa(rs_raw, *mc('Rs')).max(0).rename('rs')
    c['tmax_C'] = calib_aditiva(tmax_raw, *mc('Tmax')).rename('tmax_C')
    c['tmin_C'] = calib_aditiva(tmin_raw, *mc('Tmin')).rename('tmin_C')
    c['RH'] = calib_aditiva(rh_raw, *mc('RH')).clamp(0, 100).rename('RH')
    c['et_potencial'] = eto_penman_monteith(c['tmax_C'], c['tmin_C'], c['RH'], c['u2'], c['rs'], data_str)
    c['vpd'], _ = vpd_e_ea(c['tmax_C'], c['tmin_C'], c['RH'])

    c['et_real'] = era.select('total_evaporation_sum').multiply(-1000).max(0) \
        .rename('et_real').resample('bilinear')
    # ATENÇÃO: problema conhecido do ERA5-Land (ver catálogo GEE). As bandas estão trocadas:
    # evaporation_from_bare_soil_sum CONTÉM os valores de transpiração da vegetação.
    # evaporation_from_vegetation_transpiration_sum contém evaporação de águas abertas. Não trocar.
    c['transpiracao_mm'] = era.select('evaporation_from_bare_soil_sum').multiply(-1000).max(0) \
        .rename('transpiracao_mm').resample('bilinear')
    c['tsolo_C'] = era.select('soil_temperature_level_1').subtract(273.15).rename('tsolo_C').resample('bilinear')
    c['tfolha_C'] = era.select('skin_temperature').subtract(273.15).rename('tfolha_C').resample('bilinear')

    ssur_era = era.select('volumetric_soil_water_layer_1')
    swat_era = era.expression('(l1*7 + l2*21 + l3*72) / 100', {
        'l1': era.select('volumetric_soil_water_layer_1'),
        'l2': era.select('volumetric_soil_water_layer_2'),
        'l3': era.select('volumetric_soil_water_layer_3'),
    })
    if SOLO_BILINEAR:   # V1.4: igual à matriz SICSB_SOLO_2015_2025 (que gera o fator SMAP/ERA5)
        ssur_era = ssur_era.resample('bilinear')
        swat_era = swat_era.resample('bilinear')
    rsup_era = era.select('surface_runoff_sum').multiply(1000).max(0)
    rsub_era = era.select('sub_surface_runoff_sum').multiply(1000).max(0)

    c['soil_moisture_0_5cm_m3_m3'] = calib_multiplicativa(ssur_era, *ms('ssur')).max(0) \
        .min(teto_umidade(solo, 'ssur')).rename('soil_moisture_0_5cm_m3_m3')
    c['soil_moisture_0_100cm_m3_m3'] = calib_multiplicativa(swat_era, *ms('swat')).max(0) \
        .min(teto_umidade(solo, 'swat')).rename('soil_moisture_0_100cm_m3_m3')
    c['runoff_sup_mm'] = calib_multiplicativa(rsup_era, *ms('rsup')).max(0).rename('runoff_sup_mm')
    c['runoff_sub_mm'] = calib_multiplicativa(rsub_era, *ms('rsub')).max(0).rename('runoff_sub_mm')
    return c

# =========================================================================
# 5. ROTAS DE PROCESSAMENTO
# =========================================================================
def processarDia_Definitivo(data_str):
    c = _componentes_era5(data_str)
    dStart = ee.Date(data_str)
    dEnd = dStart.advance(1, 'day')

    dummyBR = ee.Image.constant([-99999] * 7).rename(['pr', 'Tmax', 'Tmin', 'RH', 'u2', 'Rs', 'ET'])
    imgBR = ee.Image(colChuvaGeral.filterDate(dStart, dEnd).merge(ee.ImageCollection([dummyBR])).first())
    # [V4 C1/M05-02] Pixel válido do BR-DWGD: exclui o valor de ausência -32768 (viraria Tmax/Tmin
    # = -20 °C e chuva 0) e o dummy -99999 (dia sem BR-DWGD), em pr, Tmax e Tmin, como no 03.
    valido_br = (imgBR.select('pr').gt(-32768)
                 .And(imgBR.select('Tmax').gt(-32768))
                 .And(imgBR.select('Tmin').gt(-32768)))

    tmax_br = imgBR.select('Tmax').multiply(0.00106815).add(15.0)
    tmin_br = imgBR.select('Tmin').multiply(0.00106815).add(15.0)
    rh_br = imgBR.select('RH').multiply(0.39370079).add(-0.393701).clamp(0, 100)
    vpd_br, _ = vpd_e_ea(tmax_br, tmin_br, rh_br)

    br = {
        'pr_mm': imgBR.select('pr').multiply(0.00686666).add(225.0).max(0),
        'tmax_C': tmax_br,
        'tmin_C': tmin_br,
        'RH': rh_br,
        'vpd': vpd_br,
        # [V4 C1/M05-02] .max(0): o bruto 0 viraria ETo -0,051 mm, radiação -0,057 MJ e vento -0,059 m/s
        'et_potencial': imgBR.select('ET').multiply(0.05118110).add(-0.0511811).max(0),
        'rs': imgBR.select('Rs').multiply(0.15708661).add(-0.057087).max(0),
        'u2': imgBR.select('u2').multiply(0.05905512).add(-0.059055).max(0),
    }

    # [V4 C1/M05-01] BR-DWGD primeiro e ERA5 só onde ele falta. Na V1.0-V1.4 era
    # c[b].where(has_real_br, br[b]) seguido de unmask(fallback): onde o ERA5 calibrado é máscara
    # (litoral, lagoas, estuários), o where não faz nada e o valor do BR-DWGD era descartado, ficando
    # a média focal do ERA5. O histórico V1.0 tem 204 pixels assim (classe B da auditoria J1, valor
    # que não vem do BR-DWGD). O histórico NÃO é regravado (trava): esse defeito é tratado na leitura
    # pela máscara de qualidade SAB_MASCARA_QUALIDADE (classe 2). Só os definitivos novos mudam.
    # sameFootprint=False: a pegada da saída é a união das duas. Com o padrão (True) ficaria só a
    # pegada do BR-DWGD (grade a partir de -73,9°, sem as ilhas oceânicas), e pixels de borda que hoje
    # vêm do ERA5 sumiriam dos definitivos novos.
    era_cheia = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    img = ee.Image.cat([
        (br[b].updateMask(valido_br).unmask(era_cheia.select(b), sameFootprint=False) if b in br
         else era_cheia.select(b)).rename(b)
        for b in ORDEM_BANDAS
    ]).toFloat()

    return finalizar(img, {
        'system:time_start': dStart.millis(),
        'versao': 'definitiva',
        'versao_algoritmo': VERSAO_ALGORITMO,
        'fonte': FONTE_DEFINITIVA,                    # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_12_12,       # [V4 B8/M05-17]
    })

def processarDia_Rota1(data_str):
    c = _componentes_era5(data_str)
    img = expandir_borda(ee.Image.cat([c[b] for b in ORDEM_BANDAS]).toFloat())
    return finalizar(img, {
        'system:time_start': ee.Date(data_str).millis(),
        'versao': 'provisoria_era5',
        'versao_algoritmo': VERSAO_ALGORITMO,
        'fonte': FONTE_ERA5,                          # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_00_24,       # [V4 B8/M05-17]
    })

def aplicarPatch_Solo(data_str):
    """Corrige SÓ umidade do solo e escoamento de um dia gravado pela V1.0.
    As outras 12 bandas e todas as propriedades são copiadas do asset existente.
    Valor V1.0 = bruto x fator_v10, então o valor com teto = valor V1.0 x (FATOR_MAX / fator_v10)
    nos pixels onde fator_v10 > FATOR_MAX; nos demais, o valor não muda."""
    solo = ee.Image(f'{ASSET_SOLO}/Matriz_Solo_{data_str[5:7]}')
    antigo = ee.Image(f'{ASSET_DESTINO}/{id_dia(data_str)}')

    def correcao(p):
        f = fator_v10(solo.select(f'{p}_m_smap'), solo.select(f'{p}_m_era5'))
        acima = f.gt(FATOR_MAX).unmask(0)
        return ee.Image.constant(1).where(acima, ee.Image.constant(FATOR_MAX).divide(f))

    novas = []
    for banda, p in [('runoff_sup_mm', 'rsup'), ('runoff_sub_mm', 'rsub'),
                     ('soil_moisture_0_5cm_m3_m3', 'ssur'), ('soil_moisture_0_100cm_m3_m3', 'swat')]:
        b = antigo.select(banda).multiply(correcao(p))
        if p in ('ssur', 'swat'):
            b = b.min(teto_umidade(solo, p))
        novas.append(b.toFloat().rename(banda))

    return (antigo.addBands(ee.Image.cat(novas), overwrite=True)
            .select(ORDEM_BANDAS)
            .set('versao_algoritmo', VERSAO_PATCH))

_cache_bandas_gfs = {}

def bandas_matriz_gfs(mes):
    if mes not in _cache_bandas_gfs:
        _cache_bandas_gfs[mes] = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mes}').bandNames().getInfo()
    return _cache_bandas_gfs[mes]

def colecao_gfs_rodada(creation_ms):
    # Pressupõe system:time_start == creation_time no NOAA/GFS0P25 (filtro indexado, rápido).
    return (ee.ImageCollection(COL_GFS)
            .filterDate(creation_ms, creation_ms + 3600 * 1000)
            .filter(ee.Filter.eq('creation_time', creation_ms)))

def contagem_esperada(dia_ms, creation_ms):
    """Horas de previsão esperadas na janela (início, fim] do dia, e blocos de chuva de 6 h."""
    h0 = int(round((dia_ms - creation_ms) / 3600000.0))
    horas = [h for h in range(h0 + 1, h0 + 25) if 0 < h <= 384 and (h <= 120 or h % 3 == 0)]
    # [V4 A-02] Horas inteiras, como o 03 e o F3 da auditoria (inList com inteiros comprovado no acervo).
    horas_chuva = [h for h in horas if h % 6 == 0]
    return len(horas), horas_chuva

FAIXAS_GFS = ('L1', 'L2a5', 'L6a10', 'L11a15')
# [V4 B3/M05-07] As 48 bandas de média que o motor usa: {v}_m_{sicsb|gfs}_{faixa}
BANDAS_MEDIA_GFS = [f'{v}_m_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                    for v in VARS_MATRIZ_GFS]
# [V4.1 K7] As 16 bandas de desvio da Tmax e da Tmin, usadas pela escala de variância (contrato V2.1: 100 bandas)
BANDAS_DESVIO_TEMP = [f'{v}_s_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                      for v in ('Tmax', 'Tmin')]
# [K9A] As 16 bandas de desvio da UR e da radiação, usadas pela escala de variância (METODO_UR_RS_GFS)
BANDAS_DESVIO_UR_RS = [f'{v}_s_{fonte}_{fx}' for fx in FAIXAS_GFS for fonte in ('sicsb', 'gfs')
                       for v in ('RH', 'Rs')]

def colecao_gfs_dia(data_str, creation_ms):
    """[V4] Saídas da rodada válidas na janela (00Z, 24Z] do dia, cada uma reamostrada (bilinear).
    Extraída de processarDia_GFS para a PRÉVIA 6 usar a mesma seleção (GFS bruto)."""
    data_atual = ee.Date(data_str)
    t0 = data_atual.millis()
    t1 = data_atual.advance(1, 'day').millis()
    # CORRIGIDO: janela (00Z, 24Z]. Acumulados e extremos do GFS referem-se ao período
    # que TERMINA no forecast_time.
    saidas = (colecao_gfs_rodada(creation_ms)
              .filter(ee.Filter.gt('forecast_time', t0))
              .filter(ee.Filter.lte('forecast_time', t1))
              .filter(ee.Filter.gt('forecast_hours', 0)))
    # [V4 M05-11] Uma imagem por hora de previsão: uma duplicata no acervo dobraria o bloco de chuva.
    # Collection.distinct devolve, no cliente Python, um FeatureCollection; o ee.ImageCollection()
    # só refaz o tipo para o map com resample (os elementos continuam imagens no servidor).
    saidas = ee.ImageCollection(saidas.distinct('forecast_hours'))
    # V1.4: bilinear em cada imagem antes de compor (resample não vale em composições)
    return saidas.map(lambda i: i.resample('bilinear'))

def eh_rodada_00z(creation_ms):
    """[V4 B1] Rodada das 00Z: creation_time múltiplo de 86.400.000 ms."""
    return int(creation_ms) % MS_DIA == 0

def selecionar_rodadas(rodadas_ms, contagens):
    """[V4 B1/M05-08] rodadas_ms: creation_time de cada rodada; contagens: nº de horas distintas de
    HORAS_RODADA_COMPLETA presentes em cada uma (mesma ordem). Devolve (rodadas_00z, completas,
    referencia): só rodadas 00Z, completas = com as 208 saídas, referência = a completa mais recente
    (None se nenhuma estiver completa)."""
    contagem = {}
    for r, n in zip(rodadas_ms, contagens):
        contagem[int(float(r))] = int(n or 0)
    rodadas_00z = sorted(r for r in contagem if eh_rodada_00z(r))
    completas = [r for r in rodadas_00z if contagem[r] >= N_SAIDAS_RODADA]
    return rodadas_00z, completas, (completas[-1] if completas else None)

def prazo_L(dia_ms, creation_ms):
    """[V4] Prazo do dia em relação à rodada: o dia L termina 24*L horas depois da criação."""
    horas_fim = (dia_ms + MS_DIA - creation_ms) / 3600000.0
    return math.ceil(horas_fim / 24.0 - 1e-9)

def faixa_prazo(dia_ms, creation_ms):
    """Faixa de antecedência do dia em relação à rodada: L1 (1º dia), L2a5, L6a10, L11a15.
    O dia L termina 24*L horas depois da criação da rodada.
    [V4 M05-28] O prazo 16 (horas 361-384) entra em L11a15: calibração extrapolada."""
    L = prazo_L(dia_ms, creation_ms)
    if L <= 1:
        return 'L1'
    if L <= 5:
        return 'L2a5'
    if L <= 10:
        return 'L6a10'
    return 'L11a15'

def confianca_prazo(L):
    """[V4 B8] Confianca_Prazo: 'alta' (prazo 1 a 5), 'media' (6 a 10), 'baixa' (11 em diante)."""
    if L <= 5:
        return 'alta'
    if L <= 10:
        return 'media'
    return 'baixa'

def fim_horizonte(hoje_str, referencia_ms):
    """[V4 B1-horizonte] Último dia da cadeia GFS: min(hoje + 15, dia da referência + 15).
    O dia da referência + 15 é o prazo 16 (horas 361-384), o último que a rodada 00Z cobre."""
    return min(somar_dias(hoje_str, HORIZONTE_DIAS),
               somar_dias(ms_para_data(referencia_ms), HORIZONTE_DIAS))

def rodada_para_dia(d_str, completas, referencia):
    """[V4 B1/M05-09] Rodada 00Z usada no dia. Dias a partir do dia da referência: a referência.
    Dias passados: a rodada 00Z do próprio dia, se completa; se não, a 00Z completa anterior mais
    recente que ainda cubra o dia (prazo <= 16). None se nenhuma rodada completa cobrir o dia."""
    t0 = data_para_ms(d_str)
    if t0 >= referencia:
        return referencia
    candidatas = [r for r in completas if r <= t0 and prazo_L(t0, r) <= PRAZO_MAX_GFS]
    return max(candidatas) if candidatas else None

def precisa_refazer_gfs(info, rodada, forcar, n_blocos, faixa=None):
    """Decide se um dia da cadeia GFS precisa ser (re)calculado.
    [V4 M05-09] Também refaz dias gravados como incompletos ou com falha quando a rodada do dia
    tem os 4 blocos de chuva (antes, com a mesma rodada, nunca eram refeitos)."""
    if forcar or info is None:
        return True
    if info['rodada'] != rodada or info['alg'] != VERSAO_ALGORITMO:
        return True
    if info.get('metodo', 'aditivo') != METODO_TEMP_GFS:     # [V4.1 revisão V41-08] troca de método refaz o dia
        return True
    if info.get('metodo_ur_rs', 'original') != METODO_UR_RS_GFS:   # [K9A] troca de método da UR/radiação refaz o dia
        return True
    if faixa is not None and abs(float(info.get('teto_razao', 2.0)) - teto_razao_temp(faixa)) > 1e-9:
        return True                                               # [K11] gravado com outro teto da razão
    return info['versao'] != 'provisoria_gfs' and n_blocos >= 4

def processarDia_GFS(data_str, estado_anterior, ref, creation_ms, n_img_esperado, horas_chuva, faixa,
                     prazo, metodo_temp=None):   # [V4 B8] prazo L do dia; [V4.1 K7] metodo_temp (PRÉVIA 6)
    data_atual = ee.Date(data_str)
    mes = data_str[5:7]

    # Janela (00Z, 24Z] do dia; [V4 M05-11] sem saídas duplicadas (ver colecao_gfs_dia)
    gfs_dia = colecao_gfs_dia(data_str, creation_ms)
    chuva_blocos = gfs_dia.filter(ee.Filter.inList('forecast_hours', horas_chuva))

    qtd_img = gfs_dia.size()
    qtd_chuva = chuva_blocos.size()

    if len(horas_chuva) >= 4:
        # [V4 M05-11] contagem exata (eq), como no 03: todas as saídas esperadas e os 4 blocos
        completo = qtd_img.eq(n_img_esperado).And(qtd_chuva.eq(len(horas_chuva)))
    else:
        completo = ee.Number(0)                   # dia além do horizonte da rodada
    versao_ok = ee.Algorithms.If(completo, 'provisoria_gfs', 'provisoria_gfs_incompleta')

    nomes = ['total_precipitation_surface', 'maximum_temperature_2m_above_ground',
             'minimum_temperature_2m_above_ground', 'downward_shortwave_radiation_flux',
             'relative_humidity_2m_above_ground', 'wind_speed_10m_above_ground']

    def vel_vento(img):
        return img.select('u_component_of_wind_10m_above_ground') \
            .hypot(img.select('v_component_of_wind_10m_above_ground')) \
            .rename('wind_speed_10m_above_ground')

    img_chuva = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('total_precipitation_surface').sum(),
        ee.Image.constant(0).rename('total_precipitation_surface')))
    # [V4 B6/M05-10] Chuva do balde de solo: a soma dos n blocos escalada por 4/n, ou seja, a média
    # dos blocos x 4 (0 sem blocos). Em dia completo o balde usa a própria chuva do dia (abaixo).
    img_chuva_balde = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('total_precipitation_surface').mean().multiply(4),
        ee.Image.constant(0).rename('total_precipitation_surface')))

    # V1.4: o fluxo de onda curta do GFS é a média desde o início do bloco de 6 h (auditoria F4).
    # Nas horas múltiplas de 6 ele vale a média do bloco inteiro; a média desses blocos é a média
    # do dia. [V4 B6/M05-10] Sem nenhum bloco no dia, a radiação fica mascarada (acabou a média
    # simples das saídas, que o F4 condenou); o balde usa a radiação média do BR-DWGD (abaixo).
    img_rad = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0),
        chuva_blocos.select('downward_shortwave_radiation_flux').mean(),
        ee.Image.constant(0).rename('downward_shortwave_radiation_flux').updateMask(0)))
    img_dia = ee.Image(ee.Algorithms.If(
        qtd_img.gt(0),
        ee.Image.cat([
            img_chuva,
            # Mesma variável usada na matriz SICSB_MATRIZ_GFS (temperatura horária instantânea)
            gfs_dia.select('temperature_2m_above_ground').max().rename('maximum_temperature_2m_above_ground'),
            gfs_dia.select('temperature_2m_above_ground').min().rename('minimum_temperature_2m_above_ground'),
            img_rad.rename('downward_shortwave_radiation_flux'),
            gfs_dia.select('relative_humidity_2m_above_ground').mean(),
            gfs_dia.map(vel_vento).mean(),
        ]),
        ee.Image.constant([0] * 6).rename(nomes)))

    pr_raw = img_dia.select('total_precipitation_surface').max(0)
    tmax_raw = img_dia.select('maximum_temperature_2m_above_ground')
    tmin_raw = img_dia.select('minimum_temperature_2m_above_ground')
    rs_raw = img_dia.select('downward_shortwave_radiation_flux').multiply(0.0864).max(0)
    rh_raw = img_dia.select('relative_humidity_2m_above_ground').clamp(0, 100)
    u2_raw = img_dia.select('wind_speed_10m_above_ground').multiply(0.748)

    cache_gfs = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mes}')
    bandas_cache = bandas_matriz_gfs(mes)

    def medias(banda):
        # V1.4: média do GFS da mesma faixa de prazo do dia (matriz V2)
        alvo, modelo = f'{banda}_m_sicsb_{faixa}', f'{banda}_m_gfs_{faixa}'
        faltam = [b for b in (alvo, modelo) if b not in bandas_cache]
        if faltam:
            raise RuntimeError(f"Matriz GFS do mês {mes} sem as bandas {faltam}; gere a SICSB_MATRIZ_GFS_V2.")
        return cache_gfs.select(alvo), cache_gfs.select(modelo)

    def desvios(banda):
        # [V4.1 K7] desvios-padrão diários do BR-DWGD e do GFS na mesma faixa (bandas s da matriz V2.1);
        # [K9A] usados na Tmax, na Tmin e, com METODO_UR_RS_GFS = 'variancia', na UR e na radiação
        alvo, modelo = f'{banda}_s_sicsb_{faixa}', f'{banda}_s_gfs_{faixa}'
        faltam = [b for b in (alvo, modelo) if b not in bandas_cache]
        if faltam:
            raise RuntimeError(f"Matriz GFS do mês {mes} sem as bandas {faltam}; gere a SICSB_MATRIZ_GFS_V2 (V2.1).")
        return cache_gfs.select(alvo), cache_gfs.select(modelo)

    # [V4 C4/M03-15] chuva com fator suavizado (K_CHUVA_MM); vento com fator em [0,5; 2,0];
    # [K9A] UR e radiação pela escala de variância (METODO_UR_RS_GFS)
    pr = calib_chuva_gfs(pr_raw, *medias('pr')).max(0).rename('pr_mm')
    metodo = metodo_temp or METODO_TEMP_GFS                                   # [V4.1 K7]
    if metodo == 'variancia':
        teto_temp = teto_razao_temp(faixa)                                            # [K11]
        tmax_c = calib_variancia(tmax_raw, *medias('Tmax'), *desvios('Tmax'), teto=teto_temp)
        tmin_c = calib_variancia(tmin_raw, *medias('Tmin'), *desvios('Tmin'), teto=teto_temp)
    else:
        tmax_c = calib_aditiva(tmax_raw, *medias('Tmax'))
        tmin_c = calib_aditiva(tmin_raw, *medias('Tmin'))
    # Amplitude mínima: preserva a média e só altera pixels com amplitude < AMPLITUDE_MIN_C
    t_med = tmax_c.add(tmin_c).divide(2)
    meia_amp = tmax_c.subtract(tmin_c).max(AMPLITUDE_MIN_C).divide(2)
    tmax = t_med.add(meia_amp).rename('tmax_C')
    tmin = t_med.subtract(meia_amp).rename('tmin_C')
    u2 = calib_limitada_gfs(u2_raw, *medias('u2')).max(0).rename('u2')            # [V4 C4]
    if METODO_UR_RS_GFS == 'variancia':                                           # [K9A]
        rh = calib_variancia(rh_raw, *medias('RH'), *desvios('RH')).clamp(0, 100).rename('RH')
        rs = calib_variancia(rs_raw, *medias('Rs'), *desvios('Rs')).max(0).rename('rs')
    else:
        rh = calib_aditiva(rh_raw, *medias('RH')).clamp(0, 100).rename('RH')
        rs = calib_limitada_gfs(rs_raw, *medias('Rs')).max(0).rename('rs')        # [V4 C4]

    # [V4 B6/M05-10] Entradas do balde. Em dia completo são a própria chuva e a própria radiação do
    # dia. Em dia incompleto: chuva escalada para 4 blocos e radiação dos blocos disponíveis; sem
    # nenhum bloco, a radiação média do BR-DWGD (Rs_m_sicsb da faixa) só para a ETo do balde.
    # Nesses dias, a saída grava chuva, radiação, ETo, ET real e transpiração mascaradas.
    pr_balde = ee.Image(ee.Algorithms.If(
        completo, pr,
        calib_chuva_gfs(img_chuva_balde.max(0), *medias('pr')).max(0).rename('pr_mm')))
    rs_balde = ee.Image(ee.Algorithms.If(
        qtd_chuva.gt(0), rs, expandir_borda(medias('Rs')[0]).rename('rs')))

    vpd, _ = vpd_e_ea(tmax, tmin, rh)
    # Penman-Monteith FAO-56: a mesma função usada pela rota provisória (ERA5) a partir da V1.3
    # [V4 B6] com rs_balde (= rs nos dias completos)
    et_potencial = eto_penman_monteith(tmax, tmin, rh, u2, rs_balde, data_str)

    # Balde de solo ancorado no último período ERA5 de cada pixel (ref):
    #  - capacidade e início da drenagem nunca abaixo da umidade do último dia ERA5
    #  - ET real = ETp x razão ET real/ETp do ERA5 recente x variação relativa da umidade
    #  - transpiração = mesma fração da ET real observada no ERA5 recente
    k_et = ref.select('k_et')
    f_transp = ref.select('f_transp')
    sw_ref = ref.select('sw_ref_100')
    cap100 = sw_ref.max(SW100_MAX_MM)
    cc100 = sw_ref.max(SW100_CC_MM).min(cap100)
    cap5 = ref.select('sw_ref_5').max(SW5_MAX_MM)

    sw100 = estado_anterior.select('sw_100').min(cap100)
    sw5 = estado_anterior.select('sw_5').min(cap5)
    saturacao = sw100.divide(cap100)
    cn = ee.Image.constant(60).add(saturacao.multiply(35))
    s_ret = ee.Image.constant(25400).divide(cn).subtract(254)
    p_ia = pr_balde.subtract(s_ret.multiply(0.2)).max(0)                     # [V4 B6] pr_balde
    runoff_sup = p_ia.pow(2).divide(p_ia.add(s_ret)).rename('runoff_sup_mm')
    infiltracao = pr_balde.subtract(runoff_sup).max(0)                       # [V4 B6] pr_balde

    g_umidade = sw100.divide(sw_ref.max(1.0)).clamp(0.5, 1.5)
    et_real = et_potencial.multiply(k_et).multiply(g_umidade).min(et_potencial).rename('et_real')
    transp_b = et_real.multiply(f_transp).rename('transpiracao_mm')
    evaporacao = et_real.subtract(transp_b)

    sw100_tmp = sw100.add(infiltracao).subtract(et_real)
    excesso = sw100_tmp.subtract(cap100).max(0)
    drenagem = sw100_tmp.min(cap100).subtract(cc100).max(0).multiply(0.04)
    runoff_sub = excesso.add(drenagem).rename('runoff_sub_mm')
    # clamp() só aceita números; com limite por pixel (imagem) usa-se max/min
    novo_sw100 = sw100_tmp.subtract(runoff_sub).max(0).min(cap100)
    novo_sw5 = sw5.add(infiltracao).subtract(evaporacao).max(0).min(cap5)

    # tsolo/tfolha mascarados: o GFS não tem equivalente direto às bandas do ERA5,
    # e usar Tmédia/Tmin criava degrau artificial na transição ERA5 -> GFS.
    mascarado = ee.Image.constant(0).updateMask(0)

    bandas_ok = {
        'pr_mm': pr, 'tmax_C': tmax, 'tmin_C': tmin, 'RH': rh,
        'et_potencial': et_potencial, 'et_real': et_real, 'vpd': vpd,
        'rs': rs, 'u2': u2,
        'tsolo_C': mascarado.rename('tsolo_C'), 'tfolha_C': mascarado.rename('tfolha_C'),
        'transpiracao_mm': transp_b, 'runoff_sup_mm': runoff_sup, 'runoff_sub_mm': runoff_sub,
        'soil_moisture_0_5cm_m3_m3': novo_sw5.divide(50).rename('soil_moisture_0_5cm_m3_m3'),
        'soil_moisture_0_100cm_m3_m3': novo_sw100.divide(1000).rename('soil_moisture_0_100cm_m3_m3'),
    }
    img_ok = ee.Image.cat([bandas_ok[b] for b in ORDEM_BANDAS]).toFloat() \
        .reproject(crs=crsNativo, crsTransform=transformNativo)   # V1.4: sem resample na composição
    img_ok = expandir_borda(img_ok)
    # [V4 B6/M05-10] Dia incompleto: chuva, radiação, ETo, ET real e transpiração mascaradas (o painel
    # mostra "Parcial"); temperatura, UR, vento, VPD, escoamento e umidade do solo continuam gravados.
    img_ok = ee.Image(ee.Algorithms.If(
        completo, img_ok,
        img_ok.addBands(img_ok.select(BANDAS_MASCARADAS_INCOMPLETO).updateMask(0), overwrite=True)))

    bandas_falha = {b: mascarado.rename(b) for b in ORDEM_BANDAS}
    bandas_falha['soil_moisture_0_5cm_m3_m3'] = sw5.divide(50).rename('soil_moisture_0_5cm_m3_m3')
    bandas_falha['soil_moisture_0_100cm_m3_m3'] = sw100.divide(1000).rename('soil_moisture_0_100cm_m3_m3')
    img_falha = ee.Image.cat([bandas_falha[b] for b in ORDEM_BANDAS]).toFloat()

    registro_gee = ee.Algorithms.If(
        qtd_img.gt(0),
        ee.Date(ee.Number(gfs_dia.aggregate_max('system:version')).divide(1000)).format('YYYY-MM-dd HH:mm:ss'),
        'N/A')

    comuns = {
        'system:time_start': data_atual.millis(),
        'versao_algoritmo': VERSAO_ALGORITMO,
        'rodada_gfs_ms': creation_ms,
        'Rodada_Utilizada_NOAA': datetime.fromtimestamp(creation_ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'Imagens_Esperadas_GFS': n_img_esperado,
        'Faixa_Prazo_GFS': faixa,
        'Momento_Extracao_Local': data_extracao_local,
        'Confianca_Prazo': confianca_prazo(prazo),    # [V4 B8/M05-17]
        'fonte': FONTE_GFS,                           # [V4 B8/M05-17]
        'janela_chuva_utc': JANELA_CHUVA_00_24,       # [V4 B8/M05-17]
        'matriz_gfs': MATRIZ_GFS_ROTULO,              # [V4 B8/M05-17]
        'metodo_temp_gfs': metodo,                    # [V4.1 K7] 'aditivo' ou 'variancia'
        'metodo_ur_rs_gfs': METODO_UR_RS_GFS,         # [K9A] 'original' ou 'variancia'
        'teto_razao_temp_gfs': float(teto_razao_temp(faixa)),   # [K11] 2.0 nos prazos 1-5; 1.0 do 6 em diante
    }
    final_ok = finalizar(img_ok, dict(comuns, versao=versao_ok, Imagens_Validas_GFS=qtd_img,
                                      Registro_Servidor_GEE=registro_gee))
    final_falha = finalizar(img_falha, dict(comuns, versao='falha_latencia_gfs', Imagens_Validas_GFS=0,
                                            Registro_Servidor_GEE='N/A'))
    return ee.Image(ee.Algorithms.If(qtd_img.gt(0), final_ok, final_falha))

# =========================================================================
# 6. ORQUESTRAÇÃO
# =========================================================================
print("==========================================================")
print(f"🕹️ CENTRO OPERACIONAL SAB {VERSAO_ALGORITMO} - TASK MANAGER {PROJECT_ID_ATIVO}")
print("==========================================================")

faltam_matriz = [m for m in range(1, 13)
                 if not asset_existe(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{m:02d}')]
if faltam_matriz:
    raise RuntimeError(f"❌ A matriz {ASSET_DESTINO_MATRIZ_GFS} não tem os meses {faltam_matriz}. "
                       "Rode o script da matriz GFS V2 e espere as 12 tarefas terminarem.")

# [V4 B3/M05-07] Um só getInfo com bandas e propriedades dos 12 meses. Exige as 48 bandas de média
# {v}_m_{sicsb|gfs}_{faixa} e versao_matriz = 'V2.1'. Uma matriz deixada por um 03 antigo seria usada
# sem aviso (o pacote v1 tinha a radiação antiga). As bandas ficam no cache de bandas_matriz_gfs().
_meses_matriz = [f'{m:02d}' for m in range(1, 13)]
_info_matriz = ee.List([
    ee.List([ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mm}').bandNames(),
             ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{mm}').toDictionary()])
    for mm in _meses_matriz]).getInfo()
_problemas_matriz = []
for _mm, (_bandas, _props) in zip(_meses_matriz, _info_matriz):
    _cache_bandas_gfs[_mm] = _bandas
    _exigidas = BANDAS_MEDIA_GFS + BANDAS_DESVIO_TEMP + BANDAS_DESVIO_UR_RS             # [V4.1 K7] + [K9A] desvios
    _faltam = [b for b in _exigidas if b not in _bandas]
    if _faltam:
        _problemas_matriz.append(f"mês {_mm} sem {len(_faltam)} das {len(_exigidas)} "
                                 f"bandas de média e de desvio (ex.: {_faltam[:3]})")
    if (_props or {}).get('versao_matriz') != VERSAO_MATRIZ_GFS:
        _problemas_matriz.append(f"mês {_mm} com versao_matriz = {(_props or {}).get('versao_matriz')!r} "
                                 f"(esperado '{VERSAO_MATRIZ_GFS}')")
if _problemas_matriz:
    raise RuntimeError(f"❌ A matriz {ASSET_DESTINO_MATRIZ_GFS} não é a {VERSAO_MATRIZ_GFS} que o motor "
                       f"{VERSAO_ALGORITMO} exige: " + '; '.join(_problemas_matriz)
                       + ". Apague os meses antigos, rode o 03 (matriz V2.1) e espere as 12 tarefas terminarem.")
_p01 = _info_matriz[0][1] or {}
print(f"✅ Matriz GFS {VERSAO_MATRIZ_GFS}: 12 meses com as {len(BANDAS_MEDIA_GFS)} bandas de média e as "
      f"{len(BANDAS_DESVIO_TEMP) + len(BANDAS_DESVIO_UR_RS)} de desvio da Tmax, da Tmin, da UR e da radiação "
      f"(modelo {_p01.get('modelo_gfs', '?')}, rodadas desde {_p01.get('inicio_rodadas', '?')}, "
      f"dias até {_p01.get('fim_dias', '?')}).")
print(f"   Correção da Tmax/Tmin nos dias GFS: {METODO_TEMP_GFS} (METODO_TEMP_GFS; a PRÉVIA 6 compara com a outra).")
print(f"   Correção da UR e da radiação nos dias GFS: {METODO_UR_RS_GFS} (METODO_UR_RS_GFS; auditoria K9A).")
print(f"   Teto da razão dos desvios da Tmax/Tmin: {RAZAO_DESVIO_MAX} nos prazos 1 a 5 e {RAZAO_DESVIO_MAX_LONGO} "
      f"do 6 em diante (RAZAO_DESVIO_MAX_LONGO; validação K11).")

# [V4 C2/M05-03] A máscara canônica vem de um dia do histórico; sem ele, toda exportação falharia.
if not asset_existe(f'{ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}'):
    raise RuntimeError(f"❌ Não encontrei {ASSET_DESTINO}/{id_dia(DIA_MASCARA_CANONICA)}, de onde vem a máscara "
                       "canônica (cobertura do histórico) aplicada a todos os dias novos.")

garantir_colecao(ASSET_DESTINO)
garantir_colecao(ASSET_TEMP)

tarefas = listar_tarefas_ativas()
finalizar_trocas_pendentes(tarefas)

print(f"🔍 Mapeando inventário de {ASSET_DESTINO}...")
inventario = mapear_colecao()
capacidade = max(0, LIMITE_TAREFAS_MAX - len(tarefas))
print(f"📊 Fila: {len(tarefas):,} tarefas ativas | {capacidade:,} vagas | {len(inventario):,} dias no acervo.\n")

def status_dia(d_str, info):
    if info is None:
        return 'ausente'
    v, alg = info['versao'], info['alg']
    if v in VERSOES_GFS:
        return 'precisa_upgrade' if d_str <= ultima_data_era5 else 'gravado'
    if v == 'provisoria_era5':
        # [V4 B5/M05-04] limite_def, não ultima_data_brd: sem CONVERTER_EM_DEFINITIVO, um dia depois
        # de DATA_LIMITE_PROTECAO nunca vira definitivo, mesmo que o BR-DWGD já o cubra
        if d_str <= limite_def:
            return 'precisa_upgrade'      # o BR-DWGD já cobre o dia: vira definitivo
        if alg != VERSAO_ALGORITMO:
            return 'precisa_upgrade'      # provisórios acompanham sempre a versão atual
        return 'gravado'
    # Dias definitivos: só mudam por decisão explícita (REPROCESSAR_VERSAO_ANTIGA ou patch)
    if REPROCESSAR_VERSAO_ANTIGA and alg != VERSAO_ALGORITMO:
        return 'precisa_upgrade'
    if alg not in ALGORITMOS_DEFINITIVOS_VALIDOS:
        return 'precisa_upgrade'          # dias da V1.1 (fórmula de calibração diferente)
    if alg == 'V1.0' and APLICAR_PATCH_SOLO:
        return 'precisa_patch'
    return 'gravado'

def exportar(img, d_str, usar_tmp):
    global capacidade
    nome = id_dia(d_str)
    desc = desc_dia(d_str)
    if dia_protegido(nome):   # [V4 M05-19] última barreira: os chamadores já conferem a trava
        raise RuntimeError(f"❌ Trava do histórico: exportação de {nome} bloqueada (dia até "
                           f"{DATA_LIMITE_PROTECAO} ou nome fora do padrão).")
    destino = f'{ASSET_TEMP if usar_tmp else ASSET_DESTINO}/{nome}'
    task = ee.batch.Export.image.toAsset(
        image=img, description=desc, assetId=destino,
        region=limitesRegiao, crs=crsNativo, crsTransform=transformNativo, maxPixels=1e13)
    task.start()
    tarefas[desc] = task.id
    capacidade -= 1
    return task

def aguardar_tarefa(desc):
    global capacidade
    task_id = tarefas.get(desc)
    if task_id is None:
        return 'COMPLETED'
    limite = time.time() + TIMEOUT_TAREFA_MIN * 60
    while True:
        estado = ee.data.getTaskStatus(task_id)[0].get('state')
        if estado in ESTADOS_FINAIS:
            tarefas.pop(desc, None)
            capacidade += 1
            return estado
        if time.time() > limite:
            raise TimeoutError(f"Tarefa {desc} excedeu {TIMEOUT_TAREFA_MIN} min (estado: {estado}).")
        time.sleep(INTERVALO_POLL_S)

def aguardar_dia_pronto(d_str):
    nome, desc = id_dia(d_str), desc_dia(d_str)
    if desc in tarefas:
        print(f"    ⏳ Aguardando tarefa do dia base {d_str}...")
        estado = aguardar_tarefa(desc)
        if estado != 'COMPLETED':
            raise RuntimeError(f"Dia base {d_str} terminou com estado {estado}; cadeia GFS interrompida.")
    promover_tmp(nome)
    if not asset_existe(f'{ASSET_DESTINO}/{nome}'):
        raise RuntimeError(f"Dia base {d_str} não existe no acervo e não há tarefa ativa para ele.")

def despachar_assincrono(datas, rotulo, reserva):
    global capacidade
    print(f"🔎 {rotulo}: {len(datas):,} dias avaliados.")
    enviados, por_ano = [], {}
    for d in datas:
        st_ano = por_ano.setdefault(d[:4], {'gravado': 0, 'fila': 0, 'enviado': 0, 'adiado': 0, 'protegido': 0})
        nome, desc = id_dia(d), desc_dia(d)
        if desc in tarefas:
            st_ano['fila'] += 1
            continue
        status = status_dia(d, inventario.get(nome))
        if status == 'gravado':
            st_ano['gravado'] += 1
            continue
        if PROTEGER_HISTORICO and d <= DATA_LIMITE_PROTECAO:
            st_ano['protegido'] += 1
            info = inventario.get(nome)
            situacao = 'ausente no SAB_V1' if info is None else f"{info['versao']} {info['alg']}"
            motivo = f"{status} ({situacao})"
            relatorio_protegidos[motivo] = relatorio_protegidos.get(motivo, 0) + 1
            continue
        if capacidade <= reserva:
            st_ano['adiado'] += 1
            continue
        if SIMULAR:
            info = inventario.get(nome)
            rota = 'definitiva' if d <= limite_def else 'provisoria_era5'   # [V4 B5/M05-04]
            if status == 'precisa_patch':
                motivo = f"patch solo/escoamento ({info['versao']}, V1.0 -> {VERSAO_PATCH})"
            elif info is None:
                motivo = f"criar ({rota})"
            else:
                motivo = f"recalcular {info['versao']} {info['alg']} -> {rota} {VERSAO_ALGORITMO}"
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            capacidade -= 1
            st_ano['enviado'] += 1
            enviados.append(d)
            continue
        if status == 'precisa_patch':
            img = aplicarPatch_Solo(d)
        else:
            img = processarDia_Definitivo(d) if d <= limite_def else processarDia_Rota1(d)   # [V4 B5/M05-04]
        exportar(img, d, usar_tmp=(status != 'ausente'))
        st_ano['enviado'] += 1
        enviados.append(d)
    for ano, s in sorted(por_ano.items()):
        if s['enviado'] or s['adiado'] or s['fila'] or s['protegido']:
            print(f"  📅 [{ano}] gravados {s['gravado']:,} | na fila {s['fila']:,} | "
                  f"enviados {s['enviado']:,} | adiados por capacidade {s['adiado']:,} | "
                  f"protegidos {s['protegido']:,}")
    return enviados

def descobrir_rodadas_gfs():
    # A busca precisa cobrir todo o intervalo sem ERA5, senão dias passados ficam sem rodada
    lacuna = (data_hoje_dt.date() - datetime.strptime(ultima_data_era5, '%Y-%m-%d').date()).days
    dias_busca = max(DIAS_BUSCA_RODADAS, lacuna + 3)
    ini = (data_hoje_dt - timedelta(days=dias_busca)).strftime('%Y-%m-%d')
    fim = (data_hoje_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    col = ee.ImageCollection(COL_GFS).filterDate(ini, fim)
    rodadas = col.aggregate_array('creation_time').distinct().getInfo()
    # [V4 B1/M05-08] Só rodadas 00Z, como na matriz (03). A V1.4 aceitava 06/12/18Z: com 12Z, o 1º dia
    # previsto tinha 12 h e 2 blocos, e o prazo não batia com as faixas da matriz.
    rodadas_00z = sorted({int(float(r)) for r in (rodadas or []) if eh_rodada_00z(int(float(r)))})
    if not rodadas_00z:
        print("  ⚠️ Nenhuma rodada GFS 00Z no período de busca: os dias GFS não serão processados "
              "nesta execução (os existentes ficam como estão).")
        return [], [], None

    # [V4 B1/M05-08] Uma só consulta conta, em cada rodada 00Z, as horas distintas de 1 a 384 h
    # esperadas (HORAS_RODADA_COMPLETA, 208). A V1.4 contava as imagens com a hora 0 e aceitava >= 198,
    # olhando só as 4 últimas rodadas (um getInfo por rodada). Padrões: filtro inList com horas
    # inteiras (como o 03) e aggregate_array(...).distinct().
    # [V4 A-02] Horas inteiras (inList com inteiros comprovado no 03 e no F3 da auditoria).
    col_saidas = col.filter(ee.Filter.inList('forecast_hours', HORAS_RODADA_COMPLETA))
    contagens = ee.List(rodadas_00z).map(
        lambda r: col_saidas.filter(ee.Filter.eq('creation_time', r))
        .aggregate_array('forecast_hours').distinct().size()).getInfo()
    rodadas_00z, completas, referencia = selecionar_rodadas(rodadas_00z, contagens)

    incompletas = [f"{ms_para_data(r)} ({n}/{N_SAIDAS_RODADA})"
                   for r, n in zip(rodadas_00z, contagens) if r not in completas]
    print(f"  🛰️ Rodadas 00Z na janela ({ini} a {fim}): {len(rodadas_00z)} | completas "
          f"({N_SAIDAS_RODADA} saídas de 1 a 384 h): {len(completas)}"
          + (f" | incompletas: {', '.join(incompletas)}" if incompletas else ""))
    if referencia is None:
        print("  ⚠️ Nenhuma rodada 00Z completa na janela: os dias GFS não serão processados nesta "
              "execução (os existentes ficam como estão). Rode de novo mais tarde.")
        return rodadas_00z, completas, None
    print(f"  🛰️ Rodada GFS de referência: "
          f"{datetime.fromtimestamp(referencia / 1000, tz=timezone.utc).strftime('%Y-%m-%d %HZ')}")
    return rodadas_00z, completas, referencia

def referencia_balde(ultima_era5):
    """Razões ET real/ETp e transpiração/ET real dos últimos DIAS_REF_ET dias ERA5,
    e a umidade do último dia ERA5, por pixel."""
    ini = somar_dias(ultima_era5, -(DIAS_REF_ET - 1))
    col = ee.ImageCollection(ASSET_DESTINO).filterDate(ini, somar_dias(ultima_era5, 1))
    et_r = col.select('et_real').mean()
    et_p = col.select('et_potencial').mean()
    tr = col.select('transpiracao_mm').mean()
    base = ee.Image(f'{ASSET_DESTINO}/{id_dia(ultima_era5)}')
    return ee.Image.cat([
        et_r.divide(et_p.max(0.1)).clamp(0.05, 1.0).rename('k_et'),
        tr.divide(et_r.max(0.05)).clamp(0.0, 1.0).rename('f_transp'),
        base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_ref_100'),
        base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_ref_5'),
    ])

# [V4 B2] Rodadas completas, referência e fim do horizonte da cadeia, guardados para a PRÉVIA 6
contexto_gfs = {}

def executar_cadeia_gfs(enviados_operacionais):
    global data_fim_processo
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    if not dias:
        return
    print("\n⚙ Cadeia GFS sequencial (só rodadas 00Z completas):")
    _, completas, referencia = descobrir_rodadas_gfs()
    if referencia is None:   # [V4 B1] sem rodada 00Z completa: nenhum dia GFS nesta execução
        contexto_gfs.update(completas=completas, referencia=None, fim=None)
        if SIMULAR:
            motivo = 'GFS não processado (nenhuma rodada 00Z completa)'
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
        return
    # [V4 B1-horizonte] fim = min(hoje + 15, dia da referência + 15): o prazo 16 da referência
    data_fim_processo = fim_horizonte(data_hoje_str, referencia)
    dias = intervalo_datas(somar_dias(ultima_data_era5, 1), data_fim_processo)
    contexto_gfs.update(completas=completas, referencia=referencia, fim=data_fim_processo)
    if not dias:
        return
    print(f"  📆 Dias GFS: {dias[0]} a {dias[-1]} ({len(dias)} dias; o último é o prazo "
          f"L{prazo_L(data_para_ms(dias[-1]), referencia)} da referência).")

    dias_ref = intervalo_datas(somar_dias(ultima_data_era5, -(DIAS_REF_ET - 1)), ultima_data_era5)
    ref = None
    if not SIMULAR:
        for d_ref in dias_ref:            # a referência precisa estar com as versões finais
            aguardar_dia_pronto(d_ref)
        ref = referencia_balde(ultima_data_era5)
    forcar = any(d_ref in enviados_operacionais for d_ref in dias_ref)

    for d in dias:
        nome, desc = id_dia(d), desc_dia(d)
        caminho = f'{ASSET_DESTINO}/{nome}'
        if desc in tarefas and not SIMULAR:
            aguardar_tarefa(desc)
            promover_tmp(nome)

        rodada = rodada_para_dia(d, completas, referencia)          # [V4 B1/M05-09]
        if rodada is None:
            # [V4 B1] Nenhuma rodada 00Z completa cobre o dia: a cadeia do balde não pode pular um dia
            print(f"    ⚠️ {d}: nenhuma rodada 00Z completa cobre o dia; cadeia GFS interrompida aqui "
                  f"(os dias seguintes ficam como estão).")
            if SIMULAR:
                motivo = 'GFS interrompido (dia sem rodada 00Z completa)'
                relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            break
        dia_ms = data_para_ms(d)
        n_img, horas_chuva = contagem_esperada(dia_ms, rodada)
        prazo = prazo_L(dia_ms, rodada)
        faixa = faixa_prazo(dia_ms, rodada)
        info = info_de_propriedades(propriedades_asset(caminho))
        precisa = precisa_refazer_gfs(info, rodada, forcar, len(horas_chuva), faixa)   # [V4 M05-09] [K11]
        if not precisa:
            print(f"    ✔️ {d}: atualizado com a rodada esperada.")
            continue
        forcar = True   # estado do solo mudou: todos os dias seguintes precisam ser refeitos
        if SIMULAR:
            motivo = 'criar (GFS)' if info is None else f"refazer {info['versao']} -> GFS"
            relatorio_sim[motivo] = relatorio_sim.get(motivo, 0) + 1
            continue

        d_ant = somar_dias(d, -1)
        aguardar_dia_pronto(d_ant)
        base = ee.Image(f'{ASSET_DESTINO}/{id_dia(d_ant)}')
        estado = ee.Image.cat([
            base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_100'),
            base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_5'),
        ])

        img = processarDia_GFS(d, estado, ref, rodada, n_img, horas_chuva, faixa, prazo)   # [V4 B8] prazo
        usar_tmp = info is not None
        exportar(img, d, usar_tmp)
        estado_final = aguardar_tarefa(desc)
        if estado_final != 'COMPLETED':
            raise RuntimeError(f"Falha na cadeia GFS: {desc} terminou com {estado_final}.")
        if usar_tmp:
            promover_tmp(nome)
        print(f"    ✔️ {d}: exportado (rodada {ms_para_data(rodada)} 00Z, prazo L{prazo}, faixa {faixa}, "
              f"confiança {confianca_prazo(prazo)}, {n_img} imagens esperadas, {len(horas_chuva)} blocos de chuva).")

# =========================================================================
# 7. PRÉVIA DA V1.5 (só no modo simulação; nada é gravado)
# [V4] Nos dias provisórios ERA5, a V1.5 grava o mesmo que a V1.4 (só a umidade muda em relação aos
# dias V1.3 do acervo); os rótulos passam a usar VERSAO_ALGORITMO. [V4 B2] PRÉVIA 6: rota GFS.
# =========================================================================
# Estados de cada região com os nomes usados pelo FAO/GAUL 2015 (sem acentos)
UFS_REGIAO = {
    'Norte': ['Acre', 'Amapa', 'Amazonas', 'Para', 'Rondonia', 'Roraima', 'Tocantins'],
    'Nordeste': ['Alagoas', 'Bahia', 'Ceara', 'Maranhao', 'Paraiba', 'Pernambuco', 'Piaui',
                 'Rio Grande Do Norte', 'Sergipe'],
    'Centro-Oeste': ['Distrito Federal', 'Goias', 'Mato Grosso', 'Mato Grosso Do Sul'],
    'Sudeste': ['Espirito Santo', 'Minas Gerais', 'Rio De Janeiro', 'Sao Paulo'],
    'Sul': ['Parana', 'Rio Grande Do Sul', 'Santa Catarina'],
}
CODIGO_REGIAO = {reg: k for k, reg in enumerate(UFS_REGIAO, start=1)}   # 0 = pixel fora das UFs listadas
BANDAS_PREVIA = list(ORDEM_BANDAS)   # as 16 bandas do SAB
# O que a V1.4 faz com cada banda dos dias provisórios gravados pela V1.4:
BANDAS_MUDAM = ('soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3')   # ERA5 agora bilinear
BANDAS_SOLO = BANDAS_MUDAM   # usadas na marca f_solo (pixel com umidade alterada)
BANDAS_IGUAIS = tuple(b for b in BANDAS_PREVIA if b not in BANDAS_MUDAM)       # mesma conta, mesmos dados
assert sorted(BANDAS_MUDAM + BANDAS_IGUAIS) == sorted(BANDAS_PREVIA)
GRUPO_BANDA = {**{b: f'muda na {VERSAO_ALGORITMO}' for b in BANDAS_MUDAM},   # [V4] rótulo da versão
               **{b: 'deve ficar igual' for b in BANDAS_IGUAIS}}
UNIDADE_BANDA = {'pr_mm': 'mm', 'tmax_C': '°C', 'tmin_C': '°C', 'RH': '%', 'et_potencial': 'mm',
                 'et_real': 'mm', 'vpd': 'kPa', 'rs': 'MJ/m²', 'u2': 'm/s', 'tsolo_C': '°C',
                 'tfolha_C': '°C', 'transpiracao_mm': 'mm', 'runoff_sup_mm': 'mm', 'runoff_sub_mm': 'mm',
                 'soil_moisture_0_5cm_m3_m3': 'm³/m³', 'soil_moisture_0_100cm_m3_m3': 'm³/m³'}
# Diferença mínima, na unidade da banda, para um pixel contar como alterado
TOLERANCIA_PREVIA = {b: 0.01 for b in BANDAS_PREVIA}
TOLERANCIA_PREVIA.update({'RH': 0.1, 'vpd': 0.001, 'soil_moisture_0_5cm_m3_m3': 0.001,
                          'soil_moisture_0_100cm_m3_m3': 0.001})
# Coerência física de cada imagem (fração de pixels com o problema)
COERENCIA = {
    'etr_acima_eto': 'ET real acima da ETo',
    'transp_acima_etr': 'transpiração acima da ET real',
    'tmax_abaixo_tmin': 'Tmax abaixo da Tmin',
    'ur_fora': 'UR fora de 0 a 100%',
    'umid_acima_teto': f'umidade do solo acima de {UMIDADE_MAX_FISICA}',
}
# Bandas somadas pela prévia, na ordem do redutor: a_ = como o painel mostra hoje, n_ = V1.4,
# d_ = |V1.4 - hoje|, f_ = 1 se o pixel mudou mais que a tolerância. n_pix vale 1 em cada pixel
# válido: a soma dele é a contagem de pixels, e média = soma da banda / soma de n_pix.
NOMES_SOMA = ([f'{p}_{b}' for p in ('a', 'n', 'd', 'f') for b in BANDAS_PREVIA]
              + ['a_deficit', 'n_deficit', 'clim_eto', 'f_solo']
              + [f'{p}_{c}' for p in ('a', 'n') for c in COERENCIA] + ['n_pix'])
# Tentativas de cálculo de cada dia: (n, tileScale) = retângulo do Brasil cortado em n x n partes.
# Se o Earth Engine recusar por memória ou tempo, passa para a tentativa seguinte, com partes
# menores; as somas das partes fecham exatamente com a do retângulo inteiro.
NIVEIS_PREVIA = ((1, 4), (2, 16), (4, 16))

# Critérios de aprovação, definidos antes de rodar. A V1.4 só troca a reamostragem da umidade
# do solo (vizinho mais próximo -> bilinear) no mesmo campo do ERA5: a média regional quase não
# deve mudar; mudança grande indica erro. As outras 14 bandas devem sair idênticas.
CRIT_SOLO_BRASIL = 2.0               # |variação| máxima da umidade média do Brasil (%) [V4 B4/M05-05: era 5.0]
CRIT_SOLO_REGIAO = 10.0              # |variação| máxima da umidade média de cada região (%)
CRIT_MAX_PIXELS_IGUAIS = 0.5         # % máxima de pixels alterados nas bandas que devem ficar iguais
CRIT_MAX_INCOERENCIA = 0.01          # % máxima de pixels incoerentes na V1.4 (pelo código, deve ser 0)
CRIT_MIN_DIAS = 2 / 3                # fração mínima dos dias amostrados que precisa ser calculada
CRIT_MIN_COBERTURA = 0.95            # as cinco regiões juntas precisam ter 95% dos pixels do Brasil

def _imagem_como_no_painel(d):
    """O dia gravado como o painel o mostra hoje: nos dias da V1.0 o painel aplica, na leitura,
    a correção de umidade e escoamento, que é a mesma do aplicarPatch_Solo."""
    info = inventario.get(id_dia(d))
    if info is not None and info['alg'] == 'V1.0':
        return aplicarPatch_Solo(d)
    return ee.Image(f'{ASSET_DESTINO}/{id_dia(d)}')

def _rotulo_regioes():
    """Imagem com o código da região de cada pixel (1 a 5, na ordem de UFS_REGIAO; 0 = pixel fora
    das UFs listadas). Os estados são pintados na grade, sem unir polígonos: a união
    (FeatureCollection.geometry) é a operação que o Earth Engine desaconselha por consumir muita
    memória, e era feita a cada dia na versão anterior da prévia. Usa a versão do GAUL 2015
    simplificada a 500 m (mesmos nomes e atributos), mais leve e suficiente para pixels de 11 km;
    o recorte do Brasil continua vindo das próprias imagens do SAB."""
    estados = (ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level1')
               .filter(ee.Filter.eq('ADM0_NAME', 'Brazil')))
    nomes_gaul = set(estados.aggregate_array('ADM1_NAME').getInfo())
    rotulo = ee.Image.constant(0).toByte()
    for reg, ufs in UFS_REGIAO.items():
        faltam = [u for u in ufs if u not in nomes_gaul]
        if faltam:
            print(f"   ⚠️ {reg}: estados não encontrados no GAUL, fora da prévia: {faltam}")
        rotulo = rotulo.paint(estados.filter(ee.Filter.inList('ADM1_NAME', ufs)), CODIGO_REGIAO[reg])
    return rotulo.rename('cod_regiao')

def _retangulos_previa(limites, n):
    """Retângulo do Brasil cortado em n x n partes, com os cortes sobre as linhas da grade de 0,1°
    do SAB: cada pixel cai em uma única parte. limites = (oeste, sul, leste, norte), em graus."""
    oeste, sul, leste, norte = limites
    dx, x0 = transformNativo[0], transformNativo[2]
    dy, y0 = -transformNativo[4], transformNativo[5]
    c0, c1 = math.floor((oeste - x0) / dx), math.ceil((leste - x0) / dx)
    l0, l1 = math.floor((y0 - norte) / dy), math.ceil((y0 - sul) / dy)
    cols = [c0 + round(i * (c1 - c0) / n) for i in range(n + 1)]
    lins = [l0 + round(i * (l1 - l0) / n) for i in range(n + 1)]
    return [[x0 + ca * dx, y0 - lb * dy, x0 + cb * dx, y0 - la * dy]
            for la, lb in zip(lins, lins[1:]) for ca, cb in zip(cols, cols[1:])]

def _coerencia(img):
    """Marca, pixel a pixel, os problemas físicos listados em COERENCIA (1 = problema)."""
    teto = UMIDADE_MAX_FISICA + 1e-4
    return ee.Image.cat([
        img.select('et_real').gt(img.select('et_potencial').add(0.001)),
        img.select('transpiracao_mm').gt(img.select('et_real').add(0.001)),
        img.select('tmax_C').lt(img.select('tmin_C')),
        img.select('RH').lt(0).Or(img.select('RH').gt(100)),
        img.select('soil_moisture_0_100cm_m3_m3').gt(teto).Or(img.select('soil_moisture_0_5cm_m3_m3').gt(teto)),
    ]).rename(list(COERENCIA))

def _pilha_previa(d, rotulo):
    """As 16 bandas do dia como estão hoje (a_*) e como a V1.4 gravaria (n_*), a diferença (d_*),
    a marca de pixel alterado (f_*), déficits, ETo climatológica do mês, coerência física, n_pix e,
    por último, o código da região."""
    antigo = _imagem_como_no_painel(d).select(BANDAS_PREVIA)
    novo = processarDia_Rota1(d).select(BANDAS_PREVIA)
    clima_eto = expandir_borda(ee.Image(f'{ASSET_CLIMATOLOGIA}/Matriz_Clima_{d[5:7]}').select('ET_m_br'))

    def deficit(img):
        return img.select('et_potencial').subtract(img.select('et_real'))

    dif = novo.subtract(antigo).abs().rename(BANDAS_PREVIA)      # banda a banda, na mesma ordem
    mudou = dif.gt(ee.Image.constant([TOLERANCIA_PREVIA[b] for b in BANDAS_PREVIA])).rename(BANDAS_PREVIA)

    pilha = ee.Image.cat([
        antigo.rename([f'a_{b}' for b in BANDAS_PREVIA]),
        novo.rename([f'n_{b}' for b in BANDAS_PREVIA]),
        dif.rename([f'd_{b}' for b in BANDAS_PREVIA]),
        mudou.rename([f'f_{b}' for b in BANDAS_PREVIA]),
        deficit(antigo).rename('a_deficit'),
        deficit(novo).rename('n_deficit'),
        clima_eto.rename('clim_eto'),
        mudou.select(list(BANDAS_SOLO)).reduce(ee.Reducer.max()).rename('f_solo'),
        _coerencia(antigo).rename([f'a_{c}' for c in COERENCIA]),
        _coerencia(novo).rename([f'n_{c}' for c in COERENCIA]),
        ee.Image.constant(1).rename('n_pix'),
        rotulo,
    ]).select(NOMES_SOMA + ['cod_regiao'])
    # Uma só máscara para todas as bandas: hoje e V1.4 são comparados exatamente nos mesmos pixels.
    # Fora do Brasil as imagens do SAB são mascaradas, então o retângulo não soma oceano nem vizinhos.
    return pilha.updateMask(pilha.mask().reduce(ee.Reducer.min()))

class _PedidoGrande(Exception):
    """O Earth Engine recusou o pedido por memória ou por tempo."""

def _pedido_grande_demais(erro):
    msg = str(erro).lower()
    return 'memory' in msg or 'timed out' in msg

def _somas_regiao(pilha, retangulos, tile_scale):
    """Soma de cada banda de NOMES_SOMA por código de região, parte por parte (um pedido por parte)."""
    n = len(NOMES_SOMA)
    redutor = ee.Reducer.sum().repeat(n).group(groupField=n, groupName='cod_regiao')
    total = {}
    for ret in retangulos:
        geometria = ee.Geometry.Rectangle(ret, proj=crsNativo, geodesic=False)
        for tentativa in range(3):
            try:
                r = pilha.reduceRegion(reducer=redutor, geometry=geometria, crs=crsNativo,
                                       crsTransform=transformNativo, tileScale=tile_scale,
                                       maxPixels=1e10).getInfo()
                break
            except Exception as e:
                if _pedido_grande_demais(e):
                    raise _PedidoGrande(str(e)) from None
                if tentativa == 2:
                    raise
                time.sleep(15)   # falha passageira do servidor (ex.: 503 ou excesso de pedidos)
        for grupo in r.get('groups', []):
            cod = int(grupo['cod_regiao'])
            anterior = total.get(cod, [0.0] * n)
            total[cod] = [a + (s or 0.0) for a, s in zip(anterior, grupo['sum'])]
    return total

def _medias_previa(somas):
    """Converte as somas por código em médias por região; o Brasil soma todos os códigos, inclusive
    o 0. Região sem pixel nenhum fica de fora (e o resumo acusa a ausência)."""
    i_pix = NOMES_SOMA.index('n_pix')
    nome = {k: reg for reg, k in CODIGO_REGIAO.items()}

    def medias(v):
        saida = {b: v[i] / v[i_pix] for i, b in enumerate(NOMES_SOMA) if b != 'n_pix'}
        saida['n_pix'] = v[i_pix]
        return saida

    resultado = {nome[k]: medias(v) for k, v in somas.items() if k in nome and v[i_pix] > 0}
    brasil = [sum(col) for col in zip(*somas.values())]
    if brasil and brasil[i_pix] > 0:
        resultado['Brasil'] = medias(brasil)
    return resultado

def _previa_dia(d, rotulo, limites):
    """Médias regionais do dia como está hoje (a_*) e como a V1.5 gravaria (n_*). Se o Earth Engine
    recusar por memória ou tempo, refaz o mesmo cálculo em partes menores (NIVEIS_PREVIA)."""
    pilha = _pilha_previa(d, rotulo)
    for k, (n, tile_scale) in enumerate(NIVEIS_PREVIA):
        try:
            resultado = _medias_previa(_somas_regiao(pilha, _retangulos_previa(limites, n), tile_scale))
            if 'Brasil' not in resultado:
                raise RuntimeError(f"nenhum pixel válido em comum entre o dia gravado e a {VERSAO_ALGORITMO}")   # [V4]
            return resultado
        except _PedidoGrande as e:
            if k == len(NIVEIS_PREVIA) - 1:
                raise RuntimeError(f"{e} Recusado mesmo em {n * n} partes.") from None
            prox = NIVEIS_PREVIA[k + 1][0] ** 2
            print(f"   {d}: o Earth Engine recusou por memória ou tempo; refazendo em {prox} partes...")

def _resumir_previa(df, motivos_simulacao, dias_previstos=None):
    """Monta as tabelas da prévia e aplica os critérios da V1.5. Não usa o Earth Engine."""
    nv = VERSAO_ALGORITMO   # [V4] rótulo da versão nova nas tabelas (antes 'V1.4' fixo)
    ordem = [r for r in ['Brasil', *UFS_REGIAO] if r in set(df['regiao'])]
    br = df[df['regiao'] == 'Brasil'].set_index('data').sort_index()
    u5, u100 = 'soil_moisture_0_5cm_m3_m3', 'soil_moisture_0_100cm_m3_m3'
    por_data = pd.DataFrame({
        'Umid 0-5 hoje': br[f'a_{u5}'], f'Umid 0-5 {nv}': br[f'n_{u5}'],
        'ΔUmid 0-5 %': 100 * (br[f'n_{u5}'] / br[f'a_{u5}'] - 1),
        'Umid 0-100 hoje': br[f'a_{u100}'], f'Umid 0-100 {nv}': br[f'n_{u100}'],
        'ΔUmid 0-100 %': 100 * (br[f'n_{u100}'] / br[f'a_{u100}'] - 1),
        'ETo hoje': br['a_et_potencial'], f'ETo {nv}': br['n_et_potencial'],
    }).astype(float).round(4)

    g = df.groupby('regiao')
    soma = lambda col: g[col].sum()
    variacao = lambda a, n: 100 * (soma(n) / soma(a) - 1)
    por_regiao = pd.DataFrame({
        'ΔUmid 0-5 %': variacao(f'a_{u5}', f'n_{u5}'),
        'ΔUmid 0-100 %': variacao(f'a_{u100}', f'n_{u100}'),
        '% pixels solo alterado': 100 * g['f_solo'].mean(),
        'ΔETo %': variacao('a_et_potencial', 'n_et_potencial'),
        'ΔChuva %': variacao('a_pr_mm', 'n_pr_mm'),
    }).reindex(ordem).astype(float).round(3)

    # As 16 bandas no Brasil: média dos dias amostrados, hoje x versão nova
    hoje = pd.Series({b: br[f'a_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    v14 = pd.Series({b: br[f'n_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float)
    n_alterados = pd.Series({b: br[f'f_{b}'].sum() for b in BANDAS_PREVIA}, dtype=float)
    todas = pd.DataFrame({
        'grupo': [GRUPO_BANDA[b] for b in BANDAS_PREVIA],
        'unid.': [UNIDADE_BANDA[b] for b in BANDAS_PREVIA],
        'hoje': hoje, nv: v14, 'Δ': v14 - hoje,                                  # [V4] rótulo nv
        'Δ %': 100 * (v14 / hoje.where(hoje.abs() > 1e-9) - 1),
        '% pixels alterados': pd.Series({b: 100 * br[f'f_{b}'].mean() for b in BANDAS_PREVIA}, dtype=float),
        '|Δ| onde mudou': pd.Series({b: br[f'd_{b}'].sum() / n_alterados[b] if n_alterados[b] > 0 else 0.0
                                     for b in BANDAS_PREVIA}, dtype=float),
    }, index=pd.Index(BANDAS_PREVIA, name='banda'))
    num = todas.columns[2:]
    todas[num] = todas[num].astype(float).round(4)

    coerencia = pd.DataFrame({
        'hoje (% pixels)': [100 * br[f'a_{c}'].mean() for c in COERENCIA],
        f'{nv} (% pixels)': [100 * br[f'n_{c}'].mean() for c in COERENCIA],   # [V4] rótulo nv
    }, index=pd.Index(list(COERENCIA.values()), name='verificação')).astype(float).round(3)

    falhas = []
    definitivos = [m for m in motivos_simulacao
                   if m.startswith('recalcular definitiva') or m.startswith('patch')]
    if definitivos:
        falhas.append(f"a execução mexeria em dias definitivos: {definitivos}")
    if 'Brasil' in por_regiao.index:
        b = por_regiao.loc['Brasil']
        for col in ('ΔUmid 0-5 %', 'ΔUmid 0-100 %'):
            if abs(b[col]) > CRIT_SOLO_BRASIL:
                falhas.append(f"{col} no Brasil = {b[col]:+.2f}% (limite ±{CRIT_SOLO_BRASIL:.0f}%)")
        for banda in BANDAS_IGUAIS:
            p = todas.loc[banda, '% pixels alterados']
            if p > CRIT_MAX_PIXELS_IGUAIS:
                falhas.append(f"{banda} mudou em {p:.2f}% dos pixels, mas a conta é a mesma da {nv} "
                              f"(limite {CRIT_MAX_PIXELS_IGUAIS}%)")                    # [V4] rótulo nv
        for chave, texto in COERENCIA.items():
            agora, novo = coerencia.loc[texto, 'hoje (% pixels)'], coerencia.loc[texto, f'{nv} (% pixels)']
            # Tmax < Tmin vem da calibração aditiva, igual nas duas versões: a nova só não pode piorar
            limite = agora + CRIT_MAX_INCOERENCIA if chave == 'tmax_abaixo_tmin' else CRIT_MAX_INCOERENCIA
            if novo > limite:
                falhas.append(f"{nv} com {texto} em {novo:.3f}% dos pixels (limite {limite:.3f}%)")   # [V4]
    else:
        falhas.append("a prévia não conseguiu calcular a média do Brasil")
    for r in UFS_REGIAO:
        if r not in por_regiao.index:
            falhas.append(f"a prévia não conseguiu calcular a região {r}")
            continue
        for col in ('ΔUmid 0-5 %', 'ΔUmid 0-100 %'):
            v = por_regiao.loc[r, col]
            if abs(v) > CRIT_SOLO_REGIAO:
                falhas.append(f"{col} no {r} = {v:+.2f}% (limite ±{CRIT_SOLO_REGIAO:.0f}%)")
    # Controles da própria prévia: dias suficientes e regiões cobrindo o país
    n_dias = df['data'].nunique()
    if dias_previstos and n_dias < math.ceil(CRIT_MIN_DIAS * dias_previstos):
        falhas.append(f"só {n_dias} de {dias_previstos} dias foram calculados "
                      f"(mínimo {math.ceil(CRIT_MIN_DIAS * dias_previstos)})")
    if 'n_pix' in df.columns and 'Brasil' in set(df['regiao']):
        pix = df.pivot_table(index='data', columns='regiao', values='n_pix', aggfunc='sum')
        regs = [r for r in UFS_REGIAO if r in pix.columns]
        cobertura = (pix[regs].sum(axis=1) / pix['Brasil']).min() if regs else 0.0
        if cobertura < CRIT_MIN_COBERTURA:
            falhas.append(f"as regiões cobrem só {100 * cobertura:.0f}% dos pixels do Brasil "
                          f"(mínimo {100 * CRIT_MIN_COBERTURA:.0f}%)")
    return por_data, por_regiao, todas, coerencia, falhas

# [V4 B2/M05-06] PRÉVIA 6: a rota GFS calculada em memória (nada é exportado). Até a V1.4, a simulação
# saía da cadeia GFS antes de chamar processarDia_GFS, e a etapa 5a nunca exercitava a matriz, os
# blocos de 6 h nem a calibração do GFS.
TMAX_RECORDE_BR = 44.8      # °C: recorde nacional de temperatura máxima do INMET
SALTO_MAX_TMAX = 2.0        # °C: |Tmax máx nacional do 1º dia GFS - a do último dia ERA5| (J5: +2,4)
BANDAS_PREVIA_GFS = ('tmax_C', 'pr_mm', 'rs', 'et_potencial')
COLUNAS_PREVIA_GFS = {('tmax_C', 'mean'): 'Tmax média °C', ('tmax_C', 'max'): 'Tmax máx °C',
                      ('pr_mm', 'mean'): 'Chuva média mm', ('rs', 'mean'): 'Rs média MJ/m²',
                      ('et_potencial', 'mean'): 'ETo média mm'}

def dias_previa_gfs(primeiro_dia, referencia_ms, fim):
    """1º dia GFS e os dias de prazo L2, L8 e L11 da rodada de referência, sem repetir, dentro da cadeia.
    [V4.1 revisão V41-09] O L8 cobre a faixa L6a10, onde a K7 mediu o máximo +2,9 °C acima do BR-DWGD."""
    ref_dia = ms_para_data(referencia_ms)
    saida = []
    for d in (primeiro_dia, somar_dias(ref_dia, 1), somar_dias(ref_dia, 7), somar_dias(ref_dia, 10)):
        if primeiro_dia <= d <= fim and d not in saida:
            saida.append(d)
    return saida

def _estado_previa_gfs(base):
    """Estado do solo e referência do balde montados em memória a partir do último dia ERA5. Encadear
    o balde por 10 dias em memória seria pesado; chuva, Tmax, radiação e ETo, que a PRÉVIA 6 compara,
    não dependem do balde, então todos os dias da prévia partem deste mesmo estado."""
    estado = ee.Image.cat([
        base.select('soil_moisture_0_100cm_m3_m3').multiply(1000).rename('sw_100'),
        base.select('soil_moisture_0_5cm_m3_m3').multiply(50).rename('sw_5'),
    ])
    ref = ee.Image.cat([
        ee.Image.constant(0.5).rename('k_et'), ee.Image.constant(0.5).rename('f_transp'),
        estado.select('sw_100').rename('sw_ref_100'), estado.select('sw_5').rename('sw_ref_5'),
    ])
    return estado, ref

def _nacional_gfs(partes, extras):
    """Média e máximo nacionais de cada banda de cada parte (prefixo, imagem, bandas) num só pedido.
    Cada banda reduz com a sua própria máscara. extras: valores do servidor lidos no mesmo pedido."""
    pilha = ee.Image.cat([img.select(list(bandas)).rename([f'{p}__{b}' for b in bandas])
                          for p, img, bandas in partes])
    redutor = ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True)
    for tile_scale in (4, 16):
        try:
            r = ee.Dictionary(dict(extras, est=pilha.reduceRegion(
                reducer=redutor, geometry=limitesRegiao, crs=crsNativo, crsTransform=transformNativo,
                tileScale=tile_scale, maxPixels=1e10))).getInfo()
            break
        except Exception as e:
            if tile_scale == 16 or not _pedido_grande_demais(e):
                raise
            print("   o Earth Engine recusou por memória ou tempo; refazendo com tileScale 16...")
    est = r.pop('est', None) or {}
    valores = {}
    for p, _, bandas in partes:
        for b in bandas:
            for estat in ('mean', 'max'):
                valores[(p, b, estat)] = est.get(f'{p}__{b}_{estat}')
    return valores, r

def executar_previa_gfs():
    """[V4 B2/M05-06] Calcula em memória o 1º dia GFS e os dias de prazo L2, L8 e L11 da referência.
    Devolve {'tabela', 'linhas', 'falhas'}: as falhas entram no veredito da PRÉVIA 5."""
    nv = VERSAO_ALGORITMO
    res = {'tabela': None, 'linhas': [], 'falhas': []}

    def criterio(ok, texto):
        res['linhas'].append(f"{'✅' if ok else '⚠️'} {texto}")
        if not ok:
            res['falhas'].append(texto)

    def problema(obrigatorio, texto):
        # o 1º dia é obrigatório (entra no veredito); os outros são tolerados, como na prévia ERA5
        if obrigatorio:
            criterio(False, texto)
        else:
            res['linhas'].append(f"⚠️ {texto} (dia opcional; não entra no veredito)")

    if not contexto_gfs:
        res['linhas'].append("ℹ️ Nenhum dia GFS nesta execução: a rota GFS não foi testada.")
        return res
    referencia = contexto_gfs.get('referencia')
    if referencia is None:
        criterio(False, "nenhuma rodada 00Z completa: a rota GFS não pôde ser testada (rode de novo mais tarde)")
        return res
    dias = dias_previa_gfs(somar_dias(ultima_data_era5, 1), referencia, contexto_gfs['fim'])
    if not dias:
        res['linhas'].append("ℹ️ Nenhum dia GFS dentro do horizonte: a rota GFS não foi testada.")
        return res
    # [V4.1 K7] O outro método da Tmax/Tmin, calculado em memória ao lado do escolhido (só informação)
    alt = 'variancia' if METODO_TEMP_GFS == 'aditivo' else 'aditivo'
    tmax_ok = {METODO_TEMP_GFS: True, alt: True}
    emenda_testada = {METODO_TEMP_GFS: False, alt: False}                              # [V4.1 revisão V41-03]
    n_calculados = 0
    print(f"\n🔎 PRÉVIA GFS {nv}: {len(dias)} dia(s) calculado(s) em memória ({', '.join(dias)}), "
          f"sem exportar nada; conte de 1 a 3 minutos por dia.")
    base = processarDia_Rota1(ultima_data_era5)
    estado, ref_balde = _estado_previa_gfs(base)
    tabela = {}

    def linha_tabela(rotulo, valores, prefixo):
        tabela[rotulo] = {col: valores.get((prefixo, b, estat)) for (b, estat), col in COLUNAS_PREVIA_GFS.items()}

    for i, d in enumerate(dias):
        rodada = rodada_para_dia(d, contexto_gfs['completas'], referencia)
        if rodada is None:
            problema(i == 0, f"{d}: nenhuma rodada 00Z completa cobre o dia")
            continue
        dia_ms = data_para_ms(d)
        n_img, horas_chuva = contagem_esperada(dia_ms, rodada)
        prazo, faixa = prazo_L(dia_ms, rodada), faixa_prazo(dia_ms, rodada)
        novo = processarDia_GFS(d, estado, ref_balde, rodada, n_img, horas_chuva, faixa, prazo)
        novo_alt = processarDia_GFS(d, estado, ref_balde, rodada, n_img, horas_chuva, faixa, prazo,
                                    metodo_temp=alt)                                  # [V4.1 K7]
        partes = [('novo', novo, BANDAS_PREVIA_GFS)]
        # [V4.1 K7] Partes só informativas (o outro método e a razão dos desvios): se o pedido com elas falhar,
        # o dia é refeito sem elas, para o informativo nunca derrubar o critério obrigatório (revisão V41-02)
        partes_info = [('alt', novo_alt, ('tmax_C',))]
        if i == 0:
            mat = ee.Image(f'{ASSET_DESTINO_MATRIZ_GFS}/Matriz_GFS_{d[5:7]}')
            razao = razao_desvios(mat.select(f'Tmax_s_sicsb_{faixa}'), mat.select(f'Tmax_s_gfs_{faixa}'))
            partes_info.append(('razao', ee.Image.cat([razao.rename('razao_tmax'),
                                                       razao.lt(1).rename('frac_menor_1')]).updateMask(MASCARA_SAB),
                                ('razao_tmax', 'frac_menor_1')))
        info = inventario.get(id_dia(d))
        if info is not None:
            partes.append(('gravado', ee.Image(f'{ASSET_DESTINO}/{id_dia(d)}'), BANDAS_PREVIA_GFS))
        if i == 0:
            partes.append(('era5', base, BANDAS_PREVIA_GFS))
            # J6: Tmax do GFS BRUTO (antes da calibração), para separar viés do modelo de efeito da calibração
            bruto = (colecao_gfs_dia(d, rodada).select('temperature_2m_above_ground').max()
                     .rename('tmax_C').updateMask(MASCARA_SAB))
            partes.append(('bruto', bruto, ('tmax_C',)))
        inicio = time.time()
        extras_req = {'versao': novo.get('versao'), 'n_img': novo.get('Imagens_Validas_GFS')}
        try:
            try:
                v, extras = _nacional_gfs(partes + partes_info, extras_req)
            except Exception as e_info:                                                # [V4.1 revisão V41-02]
                res['linhas'].append(f"ℹ️ {d}: Tmax pelo outro método ({alt}) não calculada "
                                     f"({str(e_info)[:120]}); refeito só o método em uso")
                tmax_ok[alt] = False
                v, extras = _nacional_gfs(partes, extras_req)
        except Exception as e:
            print(f"   ⚠️ {d} (prazo L{prazo}): prévia GFS não calculada ({e})")
            problema(i == 0, f"{d} (prazo L{prazo}): prévia GFS não calculada")
            continue
        n_calculados += 1                                                                 # [V4.1 K7]
        print(f"   {d}: ok em {(time.time() - inicio) / 60:.1f} min (rodada {ms_para_data(rodada)} 00Z, "
              f"prazo L{prazo}, faixa {faixa})")
        if i == 0:
            linha_tabela(f"{ultima_data_era5} último ERA5 ({nv})", v, 'era5')
        linha_tabela(f"{d} L{prazo} {nv} ({extras.get('versao')})", v, 'novo')
        if info is not None:
            linha_tabela(f"{d} gravado ({info['versao']} {info['alg']})", v, 'gravado')
        linha_tabela(f"{d} L{prazo} Tmax pelo outro método ({alt})", v, 'alt')     # [V4.1 K7]
        if i == 0:
            linha_tabela(f"{d} GFS bruto (sem calibração)", v, 'bruto')

        criterio(extras.get('versao') == 'provisoria_gfs',
                 f"{d} (L{prazo}): {extras.get('versao')}, {extras.get('n_img')} de {n_img} saídas "
                 f"(esperado provisoria_gfs, dia completo)")
        tmax_max = v.get(('novo', 'tmax_C', 'max'))
        tmax_alt = v.get(('alt', 'tmax_C', 'max'))                                       # [V4.1 K7]
        criterio(tmax_max is not None and tmax_max <= TMAX_RECORDE_BR,
                 f"{d} (L{prazo}): Tmax máxima nacional "
                 f"{'não calculada' if tmax_max is None else f'{tmax_max:.1f} °C'} "
                 f"(recorde do INMET {TMAX_RECORDE_BR} °C; método {METODO_TEMP_GFS})")
        tmax_ok[METODO_TEMP_GFS] &= tmax_max is not None and tmax_max <= TMAX_RECORDE_BR
        tmax_ok[alt] &= tmax_alt is not None and tmax_alt <= TMAX_RECORDE_BR
        res['linhas'].append(
            f"ℹ️ {d} (L{prazo}): Tmax máxima nacional {METODO_TEMP_GFS} "
            f"{'?' if tmax_max is None else f'{tmax_max:.1f}'} °C x {alt} "
            f"{'?' if tmax_alt is None else f'{tmax_alt:.1f}'} °C (recorde {TMAX_RECORDE_BR} °C)")
        if i == 0:
            tmax_era5, tmax_bruto = v.get(('era5', 'tmax_C', 'max')), v.get(('bruto', 'tmax_C', 'max'))
            if tmax_max is not None and tmax_era5 is not None:
                salto = tmax_max - tmax_era5
                criterio(abs(salto) <= SALTO_MAX_TMAX,
                         f"salto da Tmax máxima nacional na emenda ERA5 -> GFS ({ultima_data_era5} -> {d}): "
                         f"{tmax_era5:.1f} -> {tmax_max:.1f} °C ({salto:+.1f} °C; limite ±{SALTO_MAX_TMAX:.0f} °C)")
                tmax_ok[METODO_TEMP_GFS] &= abs(salto) <= SALTO_MAX_TMAX
                emenda_testada[METODO_TEMP_GFS] = True
            if tmax_alt is not None and tmax_era5 is not None:
                tmax_ok[alt] &= abs(tmax_alt - tmax_era5) <= SALTO_MAX_TMAX
                emenda_testada[alt] = True
                res['linhas'].append(f"ℹ️ salto na emenda pelo outro método ({alt}): "
                                     f"{tmax_alt - tmax_era5:+.1f} °C (limite ±{SALTO_MAX_TMAX:.0f} °C)")
            rz, fr = v.get(('razao', 'razao_tmax', 'mean')), v.get(('razao', 'frac_menor_1', 'mean'))
            if rz is not None and fr is not None:
                res['linhas'].append(
                    f"ℹ️ razão dos desvios da Tmax BR-DWGD/GFS (mês {d[5:7]}, faixa {faixa}): média {rz:.2f}; "
                    f"{100 * fr:.0f}% dos pixels abaixo de 1 (abaixo de 1, a escala de variância encolhe as "
                    f"anomalias do GFS e reduz os extremos)")
            if tmax_bruto is not None and tmax_max is not None and tmax_era5 is not None:
                res['linhas'].append(
                    f"ℹ️ {d}: Tmax máxima nacional do GFS bruto {tmax_bruto:.1f} °C -> calibrado {tmax_max:.1f} °C "
                    f"(efeito da calibração {tmax_max - tmax_bruto:+.1f} °C; bruto - último ERA5 "
                    f"{tmax_bruto - tmax_era5:+.1f} °C). Bruto já acima do recorde = viés do modelo; "
                    f"só o calibrado acima = efeito da calibração.")
        rs_novo, rs_grav = v.get(('novo', 'rs', 'mean')), v.get(('gravado', 'rs', 'mean'))
        if rs_novo is not None and rs_grav:
            res['linhas'].append(f"ℹ️ {d}: razão da radiação média {nv}/gravado ({info['alg']}) = "
                                 f"{rs_novo / rs_grav:.3f} (informativa)")
    if tabela:
        res['tabela'] = pd.DataFrame.from_dict(tabela, orient='index').astype(float).round(2)
    if n_calculados:
        res['linhas'].append(decisao_tmax(METODO_TEMP_GFS, alt, tmax_ok, emenda_testada))   # [V4.1 K7]
    return res

def decisao_tmax(metodo, alt, ok, emenda=None):
    """[V4.1 K7] Frase da decisão da Tmax: ok = {método: passou no recorde e na emenda em todos os dias};
    emenda = {método: a emenda ERA5 -> GFS foi testada} (revisão V41-03; None = as duas testadas)."""
    emenda = emenda if emenda is not None else {metodo: True, alt: True}
    if not emenda.get(metodo):
        return ("⚠️ Tmax: a emenda ERA5 -> GFS não foi testada nesta execução (1º dia GFS não calculado); "
                "não decida o método agora: rode o 05a de novo mais tarde.")
    if not emenda.get(alt):
        ok = dict(ok, **{alt: False})
    if ok.get(metodo):
        return (f"✅ Tmax: o método em uso ({metodo}) passa no recorde e na emenda; o outro ({alt}) "
                f"{'também passa' if ok.get(alt) else 'não passaria'}. Não é preciso mudar nada.")
    if ok.get(alt) and metodo == 'variancia':
        # [Revisão 20/10/2026] A variância foi validada fora da amostra (K8, cerca de 146 mil previsões); poucos
        # dias da PRÉVIA não bastam para voltar ao aditivo
        return (f"⚠️ Tmax: nesta execução '{alt}' passou no recorde e na emenda e '{metodo}' não. NÃO troque o "
                f"método por conta disso (a auditoria K8 validou '{metodo}' em 2025 inteiro): mande esta saída.")
    if ok.get(alt):
        return (f"➜ DECISÃO (roteiro, etapa 5a): com '{alt}' a Tmax passaria no recorde e na emenda. Para adotar, "
                f"troque METODO_TEMP_GFS = '{metodo}' por '{alt}' no 05a e no 05b e rode o 05a de novo.")
    return ("➜ DECISÃO (roteiro, etapa 5a): nenhum dos dois métodos tira a Tmax de cima do recorde ou do limite da "
            "emenda. Veja a linha do GFS bruto: se ele já passa do recorde, a cauda vem do próprio GFS.")

def _imprimir_previa_gfs(gfs):
    print("\n=== PRÉVIA 6. ROTA GFS EM MEMÓRIA (Brasil: médias e máximos nacionais; nada é gravado) ===")
    if gfs['tabela'] is not None:
        print(gfs['tabela'])
    for linha in gfs['linhas']:
        print(f"   {linha}")

def _previa_gfs_sozinha():
    """[V4 B2] Sem a prévia ERA5 (nenhum dia V1.3 para comparar), a PRÉVIA 6 roda com veredito próprio."""
    gfs = executar_previa_gfs()
    _imprimir_previa_gfs(gfs)
    if gfs['falhas']:
        print("⚠️ NÃO EXECUTE AINDA. Pontos fora do esperado na rota GFS:")
        for f in gfs['falhas']:
            print(f"   - {f}")
    else:
        print("✅ Critérios da rota GFS (PRÉVIA 6) atendidos.")

def executar_previa():
    # [V4 B5/M05-04] provisórios começam depois de limite_def (não de ultima_data_brd)
    meses = sorted({d[:7] for d in intervalo_datas(somar_dias(limite_def, 1), ultima_data_era5)})
    datas = [f'{m}-{dia:02d}' for m in meses for dia in PREVIA_DIAS_DO_MES]
    # Só dias provisórios já gravados pela V1.3: a comparação isola o que a V1.5 muda nos dias ERA5
    datas = [d for d in datas if d <= ultima_data_era5
             and (inventario.get(id_dia(d)) or {}).get('versao') == 'provisoria_era5'
             and (inventario.get(id_dia(d)) or {}).get('alg') == 'V1.3']
    if not datas:
        print("\n🔎 Prévia: não há dias provisórios gravados pela V1.3 para comparar.")
        _previa_gfs_sozinha()   # [V4 B2]
        return
    print(f"\n🔎 PRÉVIA {VERSAO_ALGORITMO}: {len(datas)} dias provisórios, do jeito que o painel mostra hoje x "
          f"como a {VERSAO_ALGORITMO} gravaria. Nada é gravado; conte de 1 a 3 minutos por dia.")   # [V4]
    rotulo = _rotulo_regioes()
    anel = limitesRegiao.coordinates().getInfo()[0]       # retângulo envolvente do Brasil
    xs, ys = [p[0] for p in anel], [p[1] for p in anel]
    limites = (min(xs), min(ys), max(xs), max(ys))
    linhas, falhas_seguidas = [], 0
    for d in datas:
        inicio = time.time()
        try:
            resultado = _previa_dia(d, rotulo, limites)
        except Exception as e:
            print(f"   ⚠️ {d}: prévia não calculada ({e})")
            falhas_seguidas += 1
            if falhas_seguidas == 3:
                print("   Três dias seguidos falharam; a prévia parou aqui para não gastar mais tempo.")
                break
            continue
        falhas_seguidas = 0
        for reg, props in resultado.items():
            linhas.append(dict(props, data=d, regiao=reg))
        # Grava a cada dia: se a execução for interrompida, os dias já calculados ficam no arquivo
        pd.DataFrame(linhas).to_csv(ARQUIVO_PREVIA, index=False, sep=';', decimal=',')   # [V4] previa_v15.csv
        br = resultado.get('Brasil')
        resumo = ''
        if br:
            u = 'soil_moisture_0_100cm_m3_m3'
            resumo = (f" | Umidade 0-100 cm Brasil {br['a_' + u]:.4f} -> {br['n_' + u]:.4f} m³/m³ "
                      f"({100 * (br['n_' + u] / br['a_' + u] - 1):+.2f}%)")
        print(f"   {d}: ok em {(time.time() - inicio) / 60:.1f} min{resumo}")
    if not linhas:
        print("   Nenhum dia calculado; a prévia não pode ser avaliada.")
        _previa_gfs_sozinha()   # [V4 B2]
        return

    df = pd.DataFrame(linhas)
    por_data, por_regiao, todas, coerencia, falhas = _resumir_previa(df, list(relatorio_sim), len(datas))
    print(f"\n   Dias calculados: {df['data'].nunique()} de {len(datas)}.")
    # [V4 B2/M05-06] Rota GFS em memória; os critérios dela entram no veredito da PRÉVIA 5
    gfs = executar_previa_gfs()
    falhas = falhas + [f"rota GFS (PRÉVIA 6): {f}" for f in gfs['falhas']]
    pd.set_option('display.width', 220)
    pd.set_option('display.max_columns', 20)
    print("\n=== PRÉVIA 1. BRASIL, DIA A DIA (umidade em m³/m³; ETo em mm/dia) ===")
    print(por_data)
    print(f"\n=== PRÉVIA 2. MÉDIA DOS DIAS AMOSTRADOS, POR REGIÃO (variações da {VERSAO_ALGORITMO} "
          f"sobre o painel atual) ===")   # [V4] rótulo da versão
    print(por_regiao)
    print(f"\n=== PRÉVIA 3. AS 16 VARIÁVEIS NO BRASIL (média dos dias; Δ = {VERSAO_ALGORITMO} - hoje; "
          "|Δ| onde mudou = mudança média nos pixels alterados) ===")   # [V4] rótulo da versão
    print(todas)
    print("\n=== PRÉVIA 4. COERÊNCIA FÍSICA (% dos pixels com o problema) ===")
    print(coerencia)
    print("\n=== PRÉVIA 5. CRITÉRIOS DE APROVAÇÃO ===")
    print("   (inclui os critérios da rota GFS, detalhados na PRÉVIA 6, logo abaixo)")   # [V4 B2]
    if falhas:
        print("⚠️ NÃO EXECUTE AINDA. Pontos fora do esperado:")
        for f in falhas:
            print(f"   - {f}")
    else:
        print("✅ Todos os critérios atendidos. Para gravar, mude SIMULAR = False e rode de novo.")
    _imprimir_previa_gfs(gfs)   # [V4 B2]
    df.to_csv(ARQUIVO_PREVIA, index=False, sep=';', decimal=',')   # [V4] previa_v15.csv
    print(f"💾 Valores completos da prévia em {ARQUIVO_PREVIA} (formato do Excel em português).")

# --- Execução ---
relatorio_sim = {}
relatorio_protegidos = {}
if PROTEGER_HISTORICO:
    print(f"🛡️ TRAVA DO HISTÓRICO LIGADA: nenhum dia até {DATA_LIMITE_PROTECAO} será alterado.\n")
    # [V4 M05-22] Com a trava, estas opções não têm efeito nos dias até DATA_LIMITE_PROTECAO
    if APLICAR_PATCH_SOLO:
        print(f"⚠️ APLICAR_PATCH_SOLO = True não tem efeito com a trava ligada: os dias V1.0 vão até "
              f"{DATA_LIMITE_PROTECAO} e só aparecem no relatório PROTEGIDOS.\n")
    if REPROCESSAR_VERSAO_ANTIGA:
        print(f"⚠️ REPROCESSAR_VERSAO_ANTIGA = True com a trava ligada: os dias até {DATA_LIMITE_PROTECAO} "
              f"não são recalculados e só aparecem no relatório PROTEGIDOS.\n")
if SIMULAR:
    print("🧪 MODO SIMULAÇÃO ATIVO: nenhum asset será criado, apagado ou exportado.\n")
# Todos os dias provisórios (desde o dia seguinte ao último dia definitivo) entram na janela
# operacional, para que um recálculo de versão tenha prioridade sobre o passivo histórico.
# [V4 B5/M05-04] limite_def no lugar de ultima_data_brd: sem conversão, os dias que o BR-DWGD já
# cobre depois de DATA_LIMITE_PROTECAO continuam provisórios e continuam na janela.
inicio_janela = min(somar_dias(data_hoje_str, -JANELA_OPERACIONAL_DIAS),
                    somar_dias(limite_def, 1), ultima_data_era5)

# A fila do Earth Engine atende por ordem de envio (com a mesma prioridade, quem chega primeiro
# roda primeiro) e roda poucas tarefas ao mesmo tempo. A cadeia GFS espera cada dia terminar,
# então antes dela só entram os dias ERA5 que ela usa como base. Se os ~270 provisórios entrassem
# antes, cada dia de previsão esperaria a fila inteira e poderia estourar TIMEOUT_TAREFA_MIN.
dias_janela = intervalo_datas(inicio_janela, ultima_data_era5)[::-1]   # do mais recente ao mais antigo

# 1) Base da previsão: os últimos DIAS_REF_ET dias do ERA5, sem reserva
enviados_op = despachar_assincrono(
    dias_janela[:DIAS_REF_ET], "📌 JANELA OPERACIONAL (base da previsão)", reserva=0)

# 2) Previsão GFS encadeada
executar_cadeia_gfs(enviados_op)

# 3) Resto da janela operacional (demais provisórios e dias recentes), sem reserva. As tarefas
#    seguem rodando no Earth Engine depois que a execução termina; a execução seguinte as promove.
despachar_assincrono(dias_janela[DIAS_REF_ET:], "📌 JANELA OPERACIONAL (restante)", reserva=0)

# 4) Passivo histórico, respeitando a reserva para as próximas execuções
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P1, somar_dias(inicio_janela, -1)),
    f"📚 HISTÓRICO PRINCIPAL ({DATA_INICIO_P1[:4]} até a janela)", reserva=RESERVA_OPERACIONAL)
despachar_assincrono(
    intervalo_datas(DATA_INICIO_P2, DATA_FIM_P2),
    f"🔍 HISTÓRICO SECUNDÁRIO ({DATA_INICIO_P2[:4]}-{DATA_FIM_P2[:4]})", reserva=RESERVA_OPERACIONAL)

# 5) Promove o que já terminou
finalizar_trocas_pendentes(listar_tarefas_ativas())

if SIMULAR:
    print("\n🧪 RESUMO DA SIMULAÇÃO (dias por ação):")
    for motivo, n in sorted(relatorio_sim.items()):
        print(f"   {motivo}: {n:,}")
    print("   Demais dias do acervo: mantidos sem alteração.")
    if PREVIA:
        executar_previa()
if relatorio_protegidos:
    print("\n🛡️ PROTEGIDOS: dias históricos que precisariam de ação e NÃO foram tocados (trava ligada):")
    for motivo, n in sorted(relatorio_protegidos.items()):
        print(f"   {motivo}: {n:,}")
else:
    print("\n🛡️ PROTEGIDOS: nenhum dia histórico precisaria de ação.")
print(f"\n✅ Execução encerrada. Vagas restantes na fila: {capacidade:,}.")

