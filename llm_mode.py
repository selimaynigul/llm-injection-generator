# llm_mode.py
from context_extractor import extract_context_from_url
from llm_util import generate_payload
import pandas as pd
import os

def main():
    # Test edilecek URL veya lokal dosya
    url = "file:///C:/Users/Selim/OneDrive%20-%20Gebze%20Teknik%20%C3%9Cniversitesi/Masa%C3%BCst%C3%BC/okul/injection-generator/my_generator/test.html"

    # İçeriği al
    context = extract_context_from_url(url)
    print("[+] Context extracted.")

    # LLM'den payload üret
    payload = generate_payload(context)
    print(f"[+] Suggested Payload:\n\n{payload}")

    # GA formatında kayıt
    result_path = os.path.join("result", "ga_result_llm.csv")
    os.makedirs("result", exist_ok=True)  # klasör yoksa oluştur

    df = pd.DataFrame([["body_tag", "", payload]], columns=["eval_place", "sig_vector", "sig_string"])
    df.to_csv(result_path, index=False)
    print(f"[+] Payload saved to: {result_path}")

if __name__ == "__main__":
    main()
