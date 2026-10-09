# Quanto é

App para o celular: aponte a câmera para um preço em pesos argentinos, toque no botão e veja quanto custa em dólares ou reais.

- **Peso para dólar:** taxa Visa do dia, a mesma que a Nomad aplica nas compras em pesos. Dá para conferir com uma compra real nas configurações e aplicar um ajuste.
- **Dólar para real:** cotação comercial + spread da Nomad + IOF (padrão 2% e 3,5%, editáveis), ou o VET manual do app da Nomad.
- **Leitura:** o Claude (API da Anthropic) lê o recorte da mira. A chave fica salva só no seu celular.

## Instalar no Android

1. Abra o endereço do app no Chrome.
2. Menu ⋮ > **Adicionar à tela inicial** (ou **Instalar app**).
3. Abra pelo ícone, permita a câmera e cole a chave da API nas configurações.

## Como as cotações são atualizadas

O workflow `.github/workflows/pages.yml` roda uma vez por dia (08:47 em Buenos Aires) e a cada mudança no código: busca a taxa Visa e o dólar comercial (`scripts/update_rates.py`), gera `rates.json` e publica o site no GitHub Pages. Se uma fonte falhar, mantém o último valor publicado com a data original, e o app avisa quando a taxa estiver desatualizada.
