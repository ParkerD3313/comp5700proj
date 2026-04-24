import os
import re
import json
import yaml
import torch
from pypdf import PdfReader
from datetime import datetime
from transformers import pipeline
from transformers.utils import logging as hf_logging
import logging

# Suppress warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)
hf_logging.set_verbosity_error()

# Task 1.1 - Done
def load_documents(doc1_path, doc2_path):
    def load_doc(filepath):
        
        # Check file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Check file is a PDF
        if not filepath.lower().endswith(".pdf"):
            raise ValueError(f"File must be a PDF: {filepath}")
        
        # Check file is not empty
        if os.path.getsize(filepath) == 0:
            raise ValueError(f"File is empty: {filepath}")
        
        # Check file can be opened
        try:
            reader = PdfReader(filepath)
        except Exception as e:
            raise ValueError(f"Could not open PDF: {filepath}. Error: {e}")
        
        full_text = ""
        pages = {}
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text += page_text

        # Check text was extracted
        if not full_text.strip():
          raise ValueError(f"No text could be extracted from: {filepath}")
        
        # Chunk the full text
        lines = full_text.split('\n')
        chunks = []
        chunk_size = 3000
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) > chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
              current_chunk += line + '\n'

        if current_chunk.strip():
            chunks.append(current_chunk.strip())


        # Return all file content
        return {
              "filename": os.path.basename(filepath),
              "filepath": filepath,
              "num_pages": len(reader.pages),
              "num_chunks": len(chunks),
              "pages": pages,
              "chunks": chunks,
              "full_text": full_text
        }

    # Load each doc separately
    doc1 = load_doc(doc1_path)
    doc2 = load_doc(doc2_path)

    print(f"Loaded '{doc1['filename']}': {doc1['num_pages']} pages, {doc1['num_chunks']} chunks")
    print(f"Loaded '{doc2['filename']}': {doc2['num_pages']} pages, {doc2['num_chunks']} chunks")

    return doc1, doc2


# Task 1.2 - Done
def zero_shot_prompt(input_text):
    prompt = f"""
Extract security KDEs from the text below.

A KDE is a named security setting, flag, file, role, or control that a requirement tells you to configure.

Rules:
- Only extract KDEs that are explicitly mentioned in the text
- If no KDEs are present, output an empty array: []
- Do not invent or guess KDEs
- Each object must have ONLY two fields: name and requirements. No other fields.

Output ONLY a JSON array:
[
  {{"name": "<kde name>", "requirements": ["<exact requirement text>"]}}
]

TEXT:
{input_text}
"""
    return prompt

# Task 1.3 - Done
def few_shot_prompt(input_text):
    prompt = f"""Extract security KDEs from the text below.

A KDE is a named security setting, flag, file, role, or control that a requirement tells you to configure.

EXAMPLES of correct KDE extraction:
- Text: "3.2.1 Ensure that the Anonymous Auth is Not Enabled"
  KDE: {{"name": "anonymous-auth", "requirements": ["3.2.1 Ensure that the Anonymous Auth is Not Enabled"]}}

- Text: "3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive"
        "3.1.3 Ensure that the kubelet configuration file has permissions set to 644 or more restrictive"
  KDE: {{"name": "kubeconfig file permissions", "requirements": ["3.1.1 Ensure that the kubeconfig file permissions are set to 644 or more restrictive", "3.1.3 Ensure that the kubelet configuration file has permissions set to 644 or more restrictive"]}}

- Text: "2.1.1 Enable audit Logs"
  KDE: {{"name": "audit logging", "requirements": ["2.1.1 Enable audit Logs"]}}

Rules:
- Only extract KDEs explicitly present in the text below
- Copy requirement text exactly as written
- Group requirements that refer to the same underlying setting
- If no KDEs are present, output an empty array: []
- Do not invent or guess KDEs
- Each object must have ONLY two fields: name and requirements. No other fields.

Output ONLY a JSON array:
[
  {{"name": "<kde name>", "requirements": ["<exact requirement text>"]}}
]

TEXT:
{input_text}
"""
    return prompt

# Task 1.4 - Done
def chain_of_thought_prompt(input_text):
    prompt = f"""
Extract security KDEs from the text below.

A KDE is a named security setting, flag, file, role, or control that a requirement tells you to configure.

Before outputting, think through these steps:
1. Find lines that look like requirements (e.g. "3.2.1 Ensure that...")
2. For each requirement, identify what specific setting it configures
3. Group requirements that configure the same setting
4. Name each group after the setting (e.g. "anonymous-auth", "audit logging")

Rules:
- Only extract KDEs explicitly present in the text below
- Copy requirement text exactly as written
- If no requirements are found, output an empty array: []
- Do not invent or guess KDEs
- Do not include your reasoning in the output

Output ONLY a JSON array:
[
  {{"name": "<kde name>", "requirements": ["<exact requirement text>"]}}
]

TEXT:
{input_text}
"""
    return prompt


# Load Gemma Model - LLM Functions
def load_gemma():
    return pipeline(
        "text-generation", 
        model="google/gemma-3-1b-it", 
        device=0, 
        dtype=torch.float16
    )

def gemma_msg_gen(user_prompt):
    messages = [
        [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful security requirements document analyzer. You only respond with valid JSON. No explanations."},]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt},]
            },
        ],
    ]
    return messages

def run_gemma(pipe, prompt):
    output = pipe(
        gemma_msg_gen(prompt),
        max_new_tokens=300,
        do_sample=False,
        repetition_penalty=1.3
    )
    return output[0][0]['generated_text'][-1]['content']

# Task 1.5 - Done - Could improve KDE filtering if need be
def extract_kdes(pipe, doc1, doc2, output_filename):

    def extract_json(text):
        match = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return []
            json_str = match.group(0)

        # fix smart quotes
        json_str = json_str.replace("\u201c", '"').replace("\u201d", '"')
        # replace ALL newlines
        json_str = re.sub(r'\n', ' ', json_str)
        # fix escaped newlines \n inside strings
        json_str = json_str.replace('\\n', ' ') 
        # fix double closing quotes
        json_str = re.sub(r'([^\\])""', r'\1"', json_str)
        # fix period before closing brace
        json_str = re.sub(r'"\s*\.\s*}', '"}', json_str)
        # fix trailing commas before closing bracket
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return [parsed]
            return parsed
        except json.JSONDecodeError as e:
            print(f"BROKEN JSON ({e}):")
            print(json_str) 
            print("---")
            return None

    def process_doc(doc):
        
        all_items = {}


        for i, chunk in enumerate(doc["chunks"]):
            print(f"Processing chunk {i+1}/{len(doc['chunks'])} of {doc['filename']}")

            prompt_types = [
                ("Zero Shot", zero_shot_prompt),
                ("Few Shot", few_shot_prompt),
                ("Chain of Thought", chain_of_thought_prompt)
            ]

            for prompt_name, prompt_func in prompt_types:
                prompt = prompt_func(chunk)
                output = run_gemma(pipe, prompt)

                data = extract_json(output)

                if not isinstance(data, list):
                    continue
                elif data == []:
                    continue

                for item in data:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    reqs = item.get("requirements", [])

                    if not isinstance(name, str):
                        continue

                    name = name.lower().strip()

                    if len(name) < 4:
                        continue
                    if name.replace(".", "").isdigit():
                        continue

                    if not isinstance(reqs, list):
                        if isinstance(reqs, str):
                            reqs = [reqs]
                        else:
                            reqs = []

                    if name not in all_items:
                        all_items[name] = {
                            "name": name,
                            "requirements": set()
                        }

                    clean_reqs = []
                    for r in reqs:
                        if isinstance(r, str):
                            all_items[name]["requirements"].add(r)

                collect_llm_output(output_filename, prompt, prompt_name, output)

        kde_dict = {}
        for i, (name, value) in enumerate(all_items.items()):
            kde_dict[f"element{i+1}"] = {
                "name": value["name"],
                "requirements": sorted(list(value["requirements"]))
            }

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Build full path inside folder
        yaml_filename = f"{os.path.splitext(doc['filename'])[0]}-kdes-{timestamp}.yaml"

        with open(yaml_filename, "w", encoding="utf-8") as f:
            yaml.dump(kde_dict, f, sort_keys=False, allow_unicode=True)

        return yaml_filename

    doc1_name = process_doc(doc1)
    doc2_name = process_doc(doc2)
    return doc1_name, doc2_name

# Task 1.6 - Done
def collect_llm_output(filename, prompt_used, prompt_type, llm_output):
    
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"*LLM Name*\ngoogle/gemma-3-1b-it\n")
        f.write(f"*Prompt Used*\n{prompt_used}\n")
        f.write(f"*Prompt Type*\n{prompt_type}\n")
        f.write(f"*LLM Output*\n{llm_output}\n\n")

def run_task1(file1, file2):

    pipe = load_gemma()

    doc1, doc2 = load_documents(file1, file2)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    llm_output_file = f"{os.path.splitext(doc1['filename'])[0]}-{os.path.splitext(doc2['filename'])[0]}-output-{timestamp}.txt"

    torch.cuda.empty_cache()
    doc1_filename, doc2_filename = extract_kdes(pipe, doc1, doc2, llm_output_file)

    return doc1_filename, doc2_filename

# # Main
# def main():

#     # Load Model
#     pipe = load_gemma()

#     # Load Documents
#     document1, document2 = load_documents("cis-r1.pdf", "cis-r2.pdf")
#     document3, document4 = load_documents("cis-r3.pdf", "cis-r4.pdf")

#     def run_docs(doc1, doc2):

#         output_dir = "llm_output"
#         os.makedirs(output_dir, exist_ok=True)

#         # Prepare LLM Output File
#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         llm_output_filename = os.path.join(
#             output_dir,
#             f"{os.path.splitext(doc1['filename'])[0]}-{os.path.splitext(doc2['filename'])[0]}-output-{timestamp}.txt"
#         )

#         open(llm_output_filename, "w").close()

#         # Run KDEs Extraction
#         doc1_kdes, doc2_kdes = extract_kdes(pipe, doc1, doc2, llm_output_filename)

#     torch.cuda.empty_cache()
#     run_docs(document1, document2)
    

# if __name__ == "__main__":
#     main()