# Leitor Bradesco CNAB 400

Leitor e validador de arquivo de retorno de cobrança Bradesco no formato fixo CNAB 400, com suporte ao registro de transação tipo 1.

## O que foi corrigido

- parser sem estado global e sem `pandas`;
- validação de 400 posições por registro, header tipo `0`, detalhe tipo `1` e trailer tipo `9`;
- leitura explícita das posições usadas pelo leiaute Bradesco;
- conversão segura de datas `DDMMAA` e valores numéricos em centavos;
- validação do total do trailer contra os detalhes lidos;
- CLI reprodutível, adequada para automação, com saída JSON e CSV;
- mock determinístico e testes unitários executáveis só com a biblioteca padrão.

## Uso

```bash
python -m cnab400 examples/mock_retorno.ret --csv retorno.csv --json retorno.json
```

Ou, depois de instalar o projeto:

```bash
pip install -e .
cnab400 examples/mock_retorno.ret --csv retorno.csv
```

O padrão de entrada é `cp1252`, comum nos arquivos bancários. Use `--encoding utf-8` quando o arquivo tiver outra codificação. Em caso de arquivo legado cujo trailer não fecha com a quantidade de linhas, use `--allow-total-mismatch` conscientemente.

## Testes

```bash
python -m unittest discover -v
```

## Posições utilizadas

Os campos de detalhe mantêm as posições do leiaute original do projeto, documentadas em índice humano (1-based): conta 33–37, nosso número 71–82, ocorrência 109–110, data da ocorrência 111–116, vencimento 147–152, valor do título 154–165, valor pago 255–266, crédito 296–301 e motivo 319–328. No trailer são lidos quantidade 58–62, valor registrado 63–74, valor liquidado 75–86, quantidade liquidada 87–91, quantidade baixada 104–108 e valor baixado 109–120.

O layout de cobrança é uma particularização do banco sobre o padrão CNAB; por isso o manual Bradesco vigente deve ser a fonte de conferência antes de usar o leitor em produção. O validador oficial do Bradesco também diferencia validação de remessa e interpretação de retorno.

## Referências consultadas

- [Layouts da FEBRABAN](https://portal.febraban.org.br/pagina/3425/33/pt-br/layout-febraban), para a distinção entre padrões padronizados e particularidades de cada serviço;
- [Manual oficial Bradesco — layout de arquivos 400 posições](https://assets.bradesco/content/dam/portal-bradesco/assets/pessoajuridica/pdf/mpo_arquivos_layout_400P.pdf), fonte das posições de cobrança usadas pelo parser;
- [Validador oficial Bradesco](https://wspf.bradesco.com.br/wsValidadorUniversal/), para conferir remessas e consultar as limitações do retorno.

O manual bancário é a autoridade operacional: versões, carteiras e campos de uso exclusivo podem mudar. O código não tenta inferir uma especificação FEBRABAN 400 universal onde o banco fornece um leiaute próprio.

## Histórico

Este repositório foi mantido como registro histórico do leitor original. O código aqui é uma refatoração compatível com o objetivo do projeto, não substitui homologação bancária nem garante que um arquivo real seja aceito pelo Bradesco sem conferência do contrato da carteira.
