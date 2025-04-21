import pandas as pd
import csv

# Yolları ayarla
gene_file = "gene/gene_list.csv"
llm_output_file = "llm_output.txt"  # LLM'den gelen payloadlar satır satır burada olsun
output_file = "result/ga_result_llm.csv"

# Gene list'i yükle
df_genes = pd.read_csv(gene_file, header=None)
gene_list = df_genes[0].tolist()

# LLM çıktılarını yükle
with open(llm_output_file, "r", encoding="utf-8") as f:
    llm_lines = [line.strip() for line in f if line.strip()]

def match_sig_string_to_genes(sig_string):
    matched_indices = []
    remaining = sig_string

    while remaining:
        match_found = False
        for i, gene in enumerate(gene_list):
            if remaining.startswith(gene):
                matched_indices.append(i)
                remaining = remaining[len(gene):]
                match_found = True
                break
        if not match_found:
            # Hiçbir parça eşleşmiyor, dur.
            return None
    return matched_indices

rows = []
for sig in llm_lines:
    sig_vector = match_sig_string_to_genes(sig)
    if sig_vector is not None:
        rows.append(["body_tag", str(sig_vector), sig])
    else:
        print(f"[!] Skipped unmatched payload: {sig}")

# Sonucu yaz
with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["eval_place", "sig_vector", "sig_string"])
    writer.writerows(rows)

print(f"[+] {len(rows)} payloads converted and saved to {output_file}")
