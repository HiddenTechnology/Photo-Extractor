#!/usr/bin/env python3
# Dependências necessárias para o Termux:
# pkg update && pkg install python -y
# pip install requests beautifulsoup4

import os
import sys

# Verificação automática de dependências para o Termux
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("\033[1;31m[!]\033[m Erro: Bibliotecas faltando.")
    print("Execute este comando no Termux e tente novamente:")
    print("\033[1;32mpip install requests beautifulsoup4\033[m")
    sys.exit()

from urllib.parse import urljoin, urlparse

def extrair_todas_imagens():
    # Suporta passar a URL direto: extrair http://site.com
    if len(sys.argv) > 1:
        url_alvo = sys.argv[1].strip()
    else:
        print("\033[1;34m[?]\033[m Digite a URL para extrair imagens:")
        url_alvo = input("> ").strip()

    if not url_alvo:
        return

    if not url_alvo.startswith('http'):
        url_alvo = 'http://' + url_alvo

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

    try:
        print(f"[*] Analisando: \033[1;36m{url_alvo}\033[m...")
        r = requests.get(url_alvo, headers=headers, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        links_vistos = set()
        contador = 0

        # 1. Busca nos METADADOS (og:image / twitter:image)
        print("\n\033[1;33m--- IMAGENS DE METADADOS ---\033[m")
        meta_tags = soup.find_all("meta", property="og:image") or \
                    soup.find_all("meta", attrs={"name": "twitter:image"})
        
        for meta in meta_tags:
            link = meta.get("content")
            if link:
                full_url = urljoin(url_alvo, link)
                if full_url not in links_vistos:
                    print(f"[META] {full_url}")
                    links_vistos.add(full_url)
                    contador += 1

        # 2. Busca imagens no corpo (tag <img>)
        print("\n\033[1;32m--- IMAGENS NO CORPO DA PÁGINA ---\033[m")
        for img in soup.find_all('img'):
            # Tenta pegar de vários atributos comuns em sites modernos
            link_bruto = img.get('src') or img.get('data-src') or img.get('srcset') or img.get('data-lazy-src')
            
            if link_bruto:
                # Limpa srcset (pega apenas a primeira imagem da lista)
                link_limpo = link_bruto.split(',')[0].split(' ')[0].strip()
                link_completo = urljoin(url_alvo, link_limpo)
                
                if link_completo not in links_vistos and not link_completo.startswith('data:image'):
                    print(link_completo)
                    links_vistos.add(link_completo)
                    contador += 1

        print(f"\n\033[1;32m[+]\033[m Total de imagens únicas encontradas: {contador}")

        # --- DOWNLOAD COM NOME ORIGINAL E VERIFICAÇÃO ---
        if contador > 0:
            opcao = input("\n\033[1;34m[?]\033[m Gostaria de baixar as imagens encontradas? (s/n): ").lower().strip()
            if opcao == 's':
                dominio = urlparse(url_alvo).netloc.replace('.', '_')
                pasta = dominio if dominio else "imagens_extraidas"
                
                if not os.path.exists(pasta):
                    os.makedirs(pasta)

                print(f"[*] Baixando em: \033[1;32m{pasta}/\033[m")
                for i, link in enumerate(links_vistos, 1):
                    try:
                        # Extrai o nome do arquivo da URL (ex: foto.jpg)
                        nome_original = os.path.basename(urlparse(link).path)
                        
                        # Se não houver nome ou for inválido, usa um padrão numerado
                        if not nome_original or "." not in nome_original:
                            nome_original = f"imagem_extraida_{i:03d}.jpg"
                        
                        caminho_final = os.path.join(pasta, nome_original)

                        # Pula se já existir
                        if os.path.exists(caminho_final):
                            print(f"  [{i}/{contador}] Ignorado (já existe): {nome_original}")
                            continue

                        img_res = requests.get(link, headers=headers, timeout=10)
                        if img_res.status_code == 200:
                            with open(caminho_final, 'wb') as f:
                                f.write(img_res.content)
                            print(f"  [{i}/{contador}] Sucesso: {nome_original}")
                    except:
                        print(f"  [{i}/{contador}] \033[1;31mFalha:\033[m {link}")
                print("\n\033[1;32m[+]\033[m Download concluído!")
            else:
                print("[*] Download cancelado.")

    except KeyboardInterrupt:
        print("\n[!] Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n\033[1;31m[!] Erro:\033[m {e}")

if __name__ == "__main__":
    extrair_todas_imagens()
