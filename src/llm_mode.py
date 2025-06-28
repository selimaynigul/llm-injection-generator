from src.context_extractor import extract_context_from_url 
from src.llm_util import generate_payload 
import pandas as pd 
import os 
import csv 
import re  

# Path to the gene list CSV file
GENE_FILE = os.path.join("src", "gene", "gene_list.csv")

def load_gene_list():
    """
    Loads the gene list from the CSV file.
    Returns a list of genes if the file exists, otherwise returns an empty list.
    """
    if not os.path.exists(GENE_FILE):
        return []
    with open(GENE_FILE, newline='', encoding='utf-8') as csvfile:
        return [row[0] for row in csv.reader(csvfile)]

def save_gene_list(gene_list):
    """
    Saves the provided gene list to the CSV file.
    Ensures the result directory exists before saving.
    """
    os.makedirs("result", exist_ok=True)
    with open(GENE_FILE, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for gene in gene_list:
            writer.writerow([gene])

def update_gene_list(new_genes):
    """
    Updates the gene list with new genes if they are not already present.
    Returns a list of indices representing the position of each new gene in the updated gene list.
    """
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
    """
    Splits a payload string into its generic components (tags, event handlers, JS functions, URIs, attributes).
    Returns a list of extracted parts for further processing.
    """
    parts = []

    # Extract HTML tags (e.g., <script>, </div>)
    tags = re.findall(r'</?\w+[^>]*>', payload)
    for tag in tags:
        parts.append(tag)
        payload = payload.replace(tag, '', 1)

    # Extract event handler attributes (e.g., onclick=)
    handlers = re.findall(r'\bon\w+=', payload)
    for handler in handlers:
        parts.append(handler)
        payload = payload.replace(handler, '', 1)

    # Extract JavaScript function calls (alert, prompt, confirm)
    functions = re.findall(r'\b(alert|prompt|confirm)\s*\(.*?\)', payload)
    for func in functions:
        parts.append(f'{func}()')
        payload = re.sub(r'\b' + func + r'\s*\(.*?\)', '', payload, count=1)

    # Extract javascript: URIs
    js_uris = re.findall(r'javascript:[^"\'>\s]+', payload)
    for js in js_uris:
        parts.append(js)
        payload = payload.replace(js, '', 1)

    # Extract remaining attribute-like patterns (e.g., src="...", id="...")
    leftovers = re.findall(r'[\w-]+="?.+?"?', payload)
    parts.extend(leftovers)

    # Return cleaned and non-empty parts
    return [p.strip() for p in parts if p.strip()]

def main():
    """
    Main function to extract context, generate payloads, process them, and save results.
    Steps:
    1. Extract context from a given URL or file.
    2. Generate payloads using LLM based on the extracted context.
    3. Split each payload into generic components and update the gene list.
    4. Save the results in a CSV file for further analysis.
    """
    # URL or local file to be tested
    url = "file://../tests/test.html"

    # Extract context from the target
    context = extract_context_from_url(url)
    print("[+] Context extracted.")

    # Generate payloads using LLM
    payload_raw = generate_payload(context)
    print(f"[+] Suggested Payload:\n\n{payload_raw}")

    # Split payloads by line (each line is a separate payload)
    payload_list = payload_raw.strip().split('\n')

    results = []

    for payload in payload_list:
        # Split payload into generic components (genes)
        genes = split_payload_into_generics(payload)
        # Update gene list and get signature vector (indices)
        sig_vector = update_gene_list(genes)
        # Store the result: evaluation place, signature vector, and original payload
        results.append(["body_tag", str(sig_vector), payload])

    # Ensure result directory exists
    os.makedirs("result", exist_ok=True)

    # Save results in GA format to a CSV file
    browser_name = "chrome"  # or dynamically detect
    result_path = os.path.join("result", f"ga_result_{browser_name}.csv")
    df = pd.DataFrame(results, columns=["eval_place", "sig_vector", "sig_string"])
    df.to_csv(result_path, index=False)

    print(f"[+] {len(results)} payload processed and saved to: {result_path}")

if __name__ == "__main__":
    main()
