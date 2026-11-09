# sab-motor

Atualização automática do **SAB – Banco de Dados Agrometeorológicos Diários do Brasil** (Google Earth Engine,
projeto `clima-492922`). Este repositório roda o motor (`05b_motor_sab_v1_6_GRAVACAO.py`; até a etapa 2, o V1.5)
**uma vez por dia, às 23h07 de Brasília**, pelo GitHub Actions (o GitHub costuma começar uns 40 min depois). O motor
não foi alterado: é o mesmo arquivo validado do pacote (impressão digital em `SHA256_MOTOR.txt`, conferida antes de
cada execução). V1.6 revista em 08/11/2026 depois da K21: UR pelo EQM, vento dos dias ERA5 pela correção na média.

| Arquivo | O que é |
|---|---|
| `05b_motor_sab_v1_6_GRAVACAO.py` | Motor V1.6 gravando (dias de 2026 do `SAB_V1`; histórico até 2025-12-31 travado) |
| `05a_motor_sab_v1_6_SIMULACAO.py` | O mesmo motor em simulação (não grava nada) |
| `05b_motor_sab_v1_5_GRAVACAO.py`, `05a_motor_sab_v1_5_SIMULACAO.py` | Versão anterior, só para voltar atrás |
| `rodar_motor.py` | Lançador: confere o SHA-256 e as travas, liga o Earth Engine, espera os pedidos por e-mail em andamento e roda o motor |
| `.github/workflows/motor_05b.yml` | Agendamento (23h07, uma vez por dia) e execução manual |
| `testes/teste_rodar_motor.py` | Testes do lançador (rodam antes de cada execução) |
| `ATIVIDADE.md` | Registro mensal automático (o GitHub desliga agendamentos de repositório público parado há 60 dias) |

**Segurança.** O repositório é público para usar os minutos gratuitos do GitHub Actions. A credencial do Earth Engine
fica só no segredo `EE_CREDENCIAL` (Settings → Secrets and variables → Actions), que nunca aparece no código, nos
registros nem em execuções de forks. Só quem tem acesso de escrita pode rodar o workflow à mão.

**Regra.** Mudou o motor? Rode antes o 05a (simulação) no Colab, como sempre, e atualize aqui os dois arquivos e o
`SHA256_MOTOR.txt` juntos. Sem o SHA-256 certo, o lançador para sem rodar nada.

Dados históricos: Xavier, A. C. et al. (2022). New improved Brazilian daily weather gridded data (1961–2020).
*International Journal of Climatology*, 42(16), 8390–8404. https://doi.org/10.1002/joc.7731
