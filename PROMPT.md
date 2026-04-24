# PROMPT.md

This file contains all prompts used for Task 1 KDE extraction using Gemma-3-1B.

---

## 1. ZERO-SHOT PROMPT
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

---

## 2. FEW-SHOT PROMPT
Extract security KDEs from the text below.

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

---

## 3. CHAIN-OF-THOUGHT PROMPT
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
