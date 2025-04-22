# llm_mode.py
from context_extractor import extract_context_from_url
from llm_util import generate_payload
import pandas as pd
import os
import csv
import re


GENE_FILE = "gene/gene_list.csv"

def load_gene_list():
    if not os.path.exists(GENE_FILE):
        return []
    with open(GENE_FILE, newline='', encoding='utf-8') as csvfile:
        return [row[0] for row in csv.reader(csvfile)]

def save_gene_list(gene_list):
    os.makedirs("result", exist_ok=True)
    with open(GENE_FILE, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for gene in gene_list:
            writer.writerow([gene])

def update_gene_list(new_genes):
    existing_genes = load_gene_list()
    updated = False

    for gene in new_genes:
        if gene not in existing_genes:
            existing_genes.append(gene)
            updated = True

    if updated:
        save_gene_list(existing_genes)

    return [existing_genes.index(gene) for gene in new_genes]



def split_payload_into_generics(payload):
    parts = []

    tags = re.findall(r'</?\w+[^>]*>', payload)
    for tag in tags:
        parts.append(tag)
        payload = payload.replace(tag, '', 1)

    handlers = re.findall(r'\bon\w+=', payload)
    for handler in handlers:
        parts.append(handler)
        payload = payload.replace(handler, '', 1)

    functions = re.findall(r'\b(alert|prompt|confirm)\s*\(.*?\)', payload)
    for func in functions:
        parts.append(f'{func}()')
        payload = re.sub(r'\b' + func + r'\s*\(.*?\)', '', payload, count=1)

    js_uris = re.findall(r'javascript:[^"\'>\s]+', payload)
    for js in js_uris:
        parts.append(js)
        payload = payload.replace(js, '', 1)

    leftovers = re.findall(r'[\w-]+="?.+?"?', payload)
    parts.extend(leftovers)

    return [p.strip() for p in parts if p.strip()]

def main():
    # Test edilecek URL veya lokal dosya
    url = "file:///C:/Users/Selim/OneDrive%20-%20Gebze%20Teknik%20%C3%9Cniversitesi/Masa%C3%BCst%C3%BC/okul/injection-generator/my_generator/test.html"

    # İçeriği al
    context = extract_context_from_url(url)
    print("[+] Context extracted.")

    # LLM'den payload üret
    payload_raw = generate_payload(context)
    print(f"[+] Suggested Payload:\n\n{payload_raw}")

    # Payload'ları tek tek ele al (her satır bir payload olacak şekilde)
    payload_list = payload_raw.strip().split('\n')

    results = []

    for payload in payload_list:
        genes = split_payload_into_generics(payload)
        sig_vector = update_gene_list(genes)
        results.append(["body_tag", str(sig_vector), payload])

    # Kayıt klasörü oluştur
    os.makedirs("result", exist_ok=True)

    # Sonuçları GA formatında yaz
    result_path = os.path.join("result", "ga_result_llm.csv")
    df = pd.DataFrame(results, columns=["eval_place", "sig_vector", "sig_string"])
    df.to_csv(result_path, index=False)

    print(f"[+] {len(results)} payload processed and saved to: {result_path}")


if __name__ == "__main__":
    main()
