import requests
import json
from bs4 import BeautifulSoup
import time
import pandas as pd

# Chave fixa da loja na Yourviews
STORE_KEY = "df83d295-4802-4668-9bc5-f38cfb9b0054"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def mapear_links_perfumes():
    print("1. Iniciando varredura do catálogo...")
    base_url = "https://www.intheboxperfumes.com.br/perfumes-masculinos"
    page = 1
    links_encontrados = []

    while True:
        url = f"{base_url}?page={page}"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega TODOS os links (<a>) da página que possuem um href
        todos_links = soup.find_all('a', href=True)
        
        # Filtra apenas os que são links de produtos
        produtos_encontrados_na_pagina = 0
        for a in todos_links:
            link = a.get('href')
            # Verifica se o link começa com '/produto/'
            if link.startswith('/produto/'):
                # Transforma o link relativo em absoluto
                link_completo = f"https://www.intheboxperfumes.com.br{link}"
                
                if link_completo not in links_encontrados:
                    links_encontrados.append(link_completo)
                    produtos_encontrados_na_pagina += 1
                    
        # Se varreu a página inteira e não achou nenhum produto novo, significa que as páginas acabaram
        if produtos_encontrados_na_pagina == 0 or page > 20: 
            break
                
        print(f"   Página {page} mapeada. Encontrados até agora: {len(links_encontrados)}")
        page += 1
        time.sleep(1)

    print(f"Total de links encontrados: {len(links_encontrados)}\n")
    return links_encontrados

def descobrir_id_e_nome_do_produto(url_produto):
    if url_produto.startswith('/'):
        url_produto = f"https://www.intheboxperfumes.com.br{url_produto}"
        
    try:
        response = requests.get(url_produto, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega o nome do perfume (Geralmente no h1)
        nome = soup.find('h1').text.strip() if soup.find('h1') else "Nome Desconhecido"
        
        # ESTRATÉGIA VNDA: Extrai o número final da URL
        # Ex: "salt-crystal-100ml-262" -> divide pelo traço e pega o último item ("262")
        possivel_id = url_produto.strip('/').split('-')[-1]
        
        if possivel_id.isdigit(): # Verifica se realmente é um número
            return possivel_id, nome
            
        # Estratégia de backup caso a URL não tenha número
        div_yv = soup.find('div', class_='yv-review-quickreview')
        if div_yv and div_yv.has_attr('value'):
            return div_yv['value'], nome
            
    except Exception as e:
        print(f"Erro ao ler produto {url_produto}: {e}")
        
    return None, "Desconhecido"

def extrair_quantidade_avaliacoes(product_id):
    # Pedimos APENAS a página 1
    url = f"https://service.yourviews.com.br/review/getreview?page=1&storeKey={STORE_KEY}&productStoreId={product_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return 0
            
        texto_resposta = response.text.strip()
        if texto_resposta.startswith('(') and texto_resposta.endswith(')'):
            texto_resposta = texto_resposta[1:-1]
            
        dados_json = json.loads(texto_resposta)
        html_puro = dados_json.get('html', '')
        
        soup = BeautifulSoup(html_puro, 'html.parser')
        
        # Procura exatamente a tag que contém o número total
        elemento_total = soup.find('span', class_='yv-summary-box__average-rating__rating-box__qtde__total')
        
        if elemento_total:
            # Pega o texto (ex: "148"), transforma em número inteiro e retorna
            return int(elemento_total.text.strip())
            
    except Exception as e:
        print(f"Erro ao buscar quantidade do ID {product_id}: {e}")
        
    return 0 # Retorna 0 se o perfume não tiver nenhuma avaliação

# ==========================================
# EXECUÇÃO DO PIPELINE OTIMIZADO
# ==========================================
dados_finais = []

# Passo 1: Pega todos os links
links = mapear_links_perfumes()

# Passo 2 e 3: Roda produto por produto UMA ÚNICA VEZ
for index, link in enumerate(links, 1):
    print(f"Processando {index}/{len(links)}: {link}")
    
    produto_id, nome_produto = descobrir_id_e_nome_do_produto(link)
    
    if produto_id:
        quantidade_reviews = extrair_quantidade_avaliacoes(produto_id)
        
        # Calcula as Vendas Estimadas na hora (ex: 1 review = 25 vendas)
        FATOR_MULTIPLICADOR = 5
        vendas_estimadas = quantidade_reviews * FATOR_MULTIPLICADOR
        
        print(f"   ID: {produto_id} | Avaliações: {quantidade_reviews} | Vendas Estimadas: {vendas_estimadas}")
        
        dados_finais.append({
            'Perfume': nome_produto,
            'ID': produto_id,
            'Avaliacoes': quantidade_reviews,
            'Vendas_Estimadas': vendas_estimadas,
            'URL': link
        })
    else:
        print("   Falha ao encontrar o ID. Pulando.")
    
    time.sleep(1) # Ainda mantemos 1 segundo de pausa para segurança

# Passo 4: Salva o ranking final!
df = pd.DataFrame(dados_finais)

if not df.empty:
    # Ordena a tabela do mais vendido para o menos vendido
    df = df.sort_values(by='Avaliacoes', ascending=False)
    
    arquivo_saida = "ranking_vendas_inthebox.csv"
    df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
    print(f"\n✅ SUCESSO! Ranking gerado com {len(df)} perfumes em '{arquivo_saida}'.")