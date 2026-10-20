# Validação realizada

Ambiente: Linux, Python 3.12, Pillow 12.3.0, NumPy 2.3.5 e VTracer 0.6.15.

- 15 testes automatizados aprovados (`python -m unittest discover -s tests -v`).
- Os quatro logotipos enviados foram convertidos pela CLI real do aplicativo.
- As dimensões originais, as duas cores e o fundo transparente foram mantidos.
- Cada resultado contém 28 caminhos SVG e nenhum elemento de imagem embutida.
- As saídas foram renderizadas com CairoSVG e inspecionadas visualmente.

| Entrada | Dimensões | Interseção/união da silhueta |
| --- | --- | --- |
| Horizontal_Azul.png | 2048 × 201 | 0,99065 |
| Horizontal_Branco.png | 2047 × 200 | 0,99022 |
| Vertical_Azul.png | 2048 × 610 | 0,99189 |
| Vertical_Branco.png | 2048 × 610 | 0,99012 |

A comparação usa máscaras de opacidade de pelo menos 50% na resolução original.
Essa métrica avalia sobreposição de silhuetas; não mede fidelidade de fontes,
exatidão colorimétrica nem garante equivalência em qualquer outra imagem.

Os testes cobrem PNG inválido, conteúdo renomeado, pastas com extensão PNG,
transparência total, APNG, limite de pixels, cores brancas e laranja, franjas de
antialias, saída vetorial, rejeição de SVG com imagem, nomes com acentos,
sobrescrita, preservação do arquivo anterior, limpeza de temporários, timeout e
código de saída de falha na CLI.

Os arquivos de imagem usados na validação não estão incluídos neste pacote.
A interface gráfica e os arquivos `.bat` não foram executados no Windows nesta
validação. Os testes de conversão foram executados pelo Python no Linux.
