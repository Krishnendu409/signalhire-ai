from transformers import AutoTokenizer
import zipfile
import xml.etree.ElementTree as ET
import os

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

def main():
    print("Investigating JD Truncation for all-MiniLM-L6-v2...")
    jd_path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\job_description.docx"
    jd_text = get_docx_text(jd_path)
    
    print(f"JD Character Length: {len(jd_text)}")
    
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    tokens = tokenizer.encode(jd_text)
    
    total_tokens = len(tokens)
    model_max_length = tokenizer.model_max_length
    embedded_tokens = min(total_tokens, model_max_length)
    truncated_tokens = max(0, total_tokens - model_max_length)
    truncated_pct = (truncated_tokens / total_tokens) * 100 if total_tokens > 0 else 0
    
    print(f"Total Tokens: {total_tokens}")
    print(f"Model Max Length: {model_max_length}")
    print(f"Embedded Tokens: {embedded_tokens}")
    print(f"Truncated Tokens: {truncated_tokens}")
    print(f"Truncated Percentage: {truncated_pct:.2f}%")

if __name__ == "__main__":
    main()
