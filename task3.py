import os
import json
import zipfile
import tempfile
import subprocess
import pandas as pd
from datetime import datetime

# Task 3.1
def load_task2_files(file1_path, file2_path):
    def read_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return read_file(file1_path), read_file(file2_path)

# 3.2 Map KDE differences → Kubescape controls
def map_differences_to_controls(lines1, lines2, output_file):
    
    # region Check for NO DIFFERENCES first
    no_name_diff = (
        len(lines1) == 1 and 
        lines1[0].strip() == "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
    )

    no_req_diff = (
        len(lines2) == 1 and 
        lines2[0].strip() == "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"
    )

    if no_name_diff and no_req_diff:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("NO DIFFERENCES FOUND")
        return output_file
    # endregion


    CONTROL_MAP = [
        # ==================================================
        # COMMAND / EXECUTION
        # ==================================================
        ("command execution", "C-0002"),
        ("exec container", "C-0002"),
        ("container execution", "C-0002"),

        # ==================================================
        # RBAC / ROLES / PERMISSIONS
        # ==================================================
        ("roles delete", "C-0007"),
        ("role delete", "C-0007"),
        ("admin roles", "C-0035"),
        ("administrative roles", "C-0035"),
        ("rbac admin", "C-0035"),
        ("rbac configuration", "C-0035"),

        # ==================================================
        # SECRETS / CREDENTIALS
        # ==================================================
        ("credentials in config", "C-0012"),
        ("config credentials", "C-0012"),
        ("applications credentials", "C-0012"),

        ("list secrets", "C-0015"),
        ("secrets access", "C-0015"),
        ("kubernetes secrets", "C-0015"),

        ("secrets as files", "C-0207"),
        ("env secrets", "C-0207"),
        ("secret env var", "C-0207"),

        # ==================================================
        # CONTAINER SECURITY
        # ==================================================
        ("non root", "C-0013"),
        ("root container", "C-0013"),
        ("non-root containers", "C-0013"),

        ("privilege escalation", "C-0016"),
        ("allow privilege escalation", "C-0016"),

        ("immutable filesystem", "C-0017"),
        ("read only filesystem", "C-0017"),

        ("privileged container", "C-0057"),
        ("sudo entrypoint", "C-0062"),
        ("naked pods", "C-0073"),

        # ==================================================
        # PROBES / HEALTH CHECKS
        # ==================================================
        ("readiness probe", "C-0018"),
        ("configured readiness probe", "C-0018"),
        ("liveness probe", "C-0056"),
        ("configured liveness probe", "C-0056"),

        # ==================================================
        # SERVICE ACCOUNTS / IDENTITY
        # ==================================================
        ("service principal", "C-0020"),
        ("service account", "C-0053"),
        ("service account access", "C-0053"),
        ("automatic service account", "C-0034"),
        ("auto service account", "C-0034"),
        ("service account mapping", "C-0034"),

        ("no impersonation", "C-0065"),
        ("impersonation", "C-0065"),

        # ==================================================
        # NETWORK SECURITY
        # ==================================================
        ("ingress egress blocked", "C-0030"),
        ("network blocked", "C-0030"),

        ("missing network policy", "C-0260"),
        ("network policy missing", "C-0260"),
        ("no network policy", "C-0260"),
        ("network policies", "C-0260"),

        ("cluster internal networking", "C-0054"),
        ("hostnetwork access", "C-0041"),
        ("host network", "C-0041"),

        # ==================================================
        # PORT / EXPOSURE
        # ==================================================
        ("container hostport", "C-0044"),
        ("host port", "C-0044"),
        ("portforwarding", "C-0063"),
        ("port forward", "C-0063"),

        # ==================================================
        # HOST SECURITY
        # ==================================================
        ("host pid", "C-0038"),
        ("host ipc", "C-0038"),
        ("hostpath mount", "C-0048"),
        ("writable hostpath", "C-0045"),
        ("insecure capabilities", "C-0046"),

        # ==================================================
        # FILE / CONFIG SECURITY
        # ==================================================
        ("kubeconfig", "C-0012"),
        ("kubeconfig permissions", "C-0012"),
        ("file permissions", "C-0012"),
        ("configuration management", "C-0012"),

        # ==================================================
        # TLS / CERTIFICATES
        # ==================================================
        ("tls configuration", "C-0012"),
        ("tls enforcement", "C-0012"),
        ("certificate rotation", "C-0020"),

        # ==================================================
        # API / DASHBOARD ACCESS
        # ==================================================
        ("kubernetes dashboard", "C-0014"),
        ("dashboard access", "C-0014"),

        # ==================================================
        # EVENTS / AUDITING
        # ==================================================
        ("delete events", "C-0031"),
        ("kubernetes events", "C-0031"),

        # ==================================================
        # POD / CLUSTER POLICY
        # ==================================================
        ("psp enabled", "C-0068"),
        ("pod security policy", "C-0068"),
        ("pods default namespace", "C-0061"),
        ("pod security standards", "C-0068"),

        # ==================================================
        # IMAGES / SUPPLY CHAIN
        # ==================================================
        ("image pull policy", "C-0075"),
        ("latest tag", "C-0075"),
        ("allowed registry", "C-0078"),
        ("trusted registry", "C-0078"),
        ("container image security", "C-0078"),

        # ==================================================
        # LABELS / METADATA
        # ==================================================
        ("resource labels", "C-0076"),
        ("k8s labels", "C-0077"),

        # ==================================================
        # VULNERABILITIES / CVEs
        # ==================================================
        ("nginx ingress", "C-0059"),
        ("argocd", "C-0081"),
        ("grafana", "C-0090"),
        ("kyverno", "C-0091"),

        # ==================================================
        # RESOURCES / LIMITS
        # ==================================================
        ("cpu limits", "C-0270"),
        ("memory limits", "C-0271"),

        # ==================================================
        # STORAGE / PVC
        # ==================================================
        ("pvc access", "C-0257"),
        ("workload pvc", "C-0257"),

        # ==================================================
        # NETWORK POLICY (CATCH DUPES INCLUDED FOR MATCHING)
        # ==================================================
        ("network policy", "C-0260"),

        # ==================================================
        # ANONYMOUS ACCESS
        # ==================================================
        ("anonymous access enabled", "C-0262"),
        ("anonymous access", "C-0262"),

        # ==================================================
        # HARDENING / GENERAL
        # ==================================================
        ("linux hardening", "C-0055"),
        ("container hardening", "C-0055"),
        ("security hardening", "C-0055"),

        # ==================================================
        # AUDIT LOGGING / CONTROL PLANE LOGGING (EXPANDED)
        # ==================================================
        ("api server auditing", "C-0031"),
        ("audit logging process", "C-0031"),
        ("control plane logging", "C-0031"),
        ("enable detailed logging", "C-0031"),
        ("detailed audit logging", "C-0031"),
        ("audit logs configuration", "C-0031"),
        ("api server audit logs", "C-0031"),
        ("enable audit logs", "C-0031"),
        ("activate audit logging", "C-0031"),

        # ==================================================
        # ANONYMOUS AUTHENTICATION (EXPANDED)
        # ==================================================
        ("anonymousauth", "C-0262"),
        ("anonymous-auth", "C-0262"),
        ("anonymous authentication", "C-0262"),
        ("anonymous auth", "C-0262"),
        ("disable anonymous auth", "C-0262"),
        ("anonymous requests", "C-0262"),

        # ==================================================
        # ENCRYPTION / TLS / SECRETS ENCRYPTION (EXPANDED)
        # ==================================================
        ("encrypt sensitive data at rest", "C-0015"),
        ("encrypted sensitive data at rest", "C-0015"),
        ("secrets encryption", "C-0015"),
        ("encrypt traffic in transit", "C-0015"),
        ("encryption traffic", "C-0015"),
        ("kms encryption", "C-0015"),
        ("aws kms", "C-0015"),
        ("tls certificates", "C-0015"),
        ("tls encryption", "C-0015"),

        # ==================================================
        # API SERVER / ENDPOINT SECURITY (NEW COVERAGE)
        # ==================================================
        ("api endpoint configuration", "C-0030"),
        ("api server endpoint", "C-0030"),
        ("endpoint private access", "C-0030"),
        ("endpoint public access", "C-0030"),
        ("private endpoint access", "C-0030"),
        ("restrict api server access", "C-0030"),
        ("control plane endpoint", "C-0030"),

        # ==================================================
        # IAM / AUTHENTICATOR / ESCALATION (EXPANDED)
        # ==================================================
        ("aws iam authenticator", "C-0035"),
        ("iam authenticator for kubernetes", "C-0035"),
        ("cluster-admin usage", "C-0035"),
        ("system:masters", "C-0035"),
        ("escalation permission", "C-0016"),
        ("privilege escalation rights", "C-0016"),
        ("rbac escalation", "C-0035"),

        # ==================================================
        # ECR / IMAGE SCANNING / REGISTRY SECURITY (EXPANDED)
        # ==================================================
        ("amazon ecr access controls", "C-0078"),
        ("ecr permissions", "C-0078"),
        ("create repository", "C-0078"),
        ("vulnerability scanning tool", "C-0078"),
        ("image scanning", "C-0078"),
        ("image vulnerability scanning", "C-0078"),
        ("registry scanning", "C-0078"),

        # ==================================================
        # KUBELET / NODE HARDENING (EXPANDED)
        # ==================================================
        ("read-only port disabled", "C-0055"),
        ("read only port", "C-0055"),
        ("streaming connection idle timeout", "C-0055"),
        ("rotate certificates", "C-0020"),
        ("kubelet rotate certificates", "C-0020"),
        ("protect kernel defaults", "C-0055"),
        ("kubelet flags", "C-0055"),
        ("event record qps", "C-0055"),

        # ==================================================
        # NETWORK POLICY VARIANTS (EXPANDED COVERAGE)
        # ==================================================
        ("networkpolicy", "C-0260"),
        ("networkpolicies", "C-0260"),
        ("network-policy", "C-0260"),
        ("networkpolicyenabled", "C-0260"),
        ("network restrictions", "C-0260"),
        ("network isolation", "C-0260"),

        # ==================================================
        # KUBECONFIG / FILE SECURITY EXPANSION
        # ==================================================
        ("kubeconfig ownership", "C-0012"),
        ("kubeconfig file ownership", "C-0012"),
        ("root:root kubelet", "C-0012"),
        ("644 permissions", "C-0012"),
        ("file ownership root", "C-0012"),

        # ==================================================
        # GENERAL SECURITY HARDENING EXPANSION
        # ==================================================
        ("secure network management", "C-0055"),
        ("secure networking", "C-0055"),
        ("capability restriction", "C-0055"),
        ("default capability policy", "C-0055"),
        ("container hardening policies", "C-0055"),
    ]

    differences = []
    for line in lines2:
        parts = line.strip().split(",", 3)
        kde = parts[0]
        req = parts[3]

        if req == "NA":
            differences.append(kde)
        else:
            differences.append(kde + " " + req)

    # for line in differences:
    #     print(line)

    matched = set()
    for item in differences:
        item_lower = item.lower()
        for key, control in CONTROL_MAP:
            if key in item_lower:
                matched.add(control)

    with open(output_file, "w", encoding="utf-8") as f:
        for c in sorted(matched):
            f.write(c + "\n")

    return output_file

# 3.3 Execute Kubescape (FIXED JSON PARSING)
def run_kubescape(controls_file, scan_path, framework="nsa"):

    def resolve_scan_path(path):
        # Case 1: already a directory
        if os.path.isdir(path):
            return path

        # Case 2: zip exists
        zip_path = path + ".zip"
        if os.path.exists(zip_path):
            extract_dir = tempfile.mkdtemp()

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(extract_dir)

            return extract_dir

        # Case 3: nothing found
        raise FileNotFoundError(
            f"Neither folder '{path}' nor zip '{zip_path}' exists"
        )
    
    scan_path = resolve_scan_path(scan_path)
    
    with open(controls_file, "r", encoding="utf-8") as f:
        lines = [c.strip() for c in f if c.strip()]
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"kubescape_output-{timestamp}.json"

    if len(lines) == 1 and lines[0] == "NO DIFFERENCES FOUND":
        cmd = [
            "kubescape",
            "scan",
            "framework", 
            framework,
            scan_path,
            "-f", "json",
            "-o", output_file
        ]
    else:
        # join controls into comma-separated string
        controls = ",".join(lines)
        cmd = [
            "kubescape",
            "scan",
            "control",
            controls,
            scan_path,
            "-f", "json",
            "-o", output_file
        ]

    subprocess.run(cmd, text=True, check=True)

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    controls_data = data.get("summaryDetails", {}).get("controls", {})

    # -----------------------------
    # Extract meaningful results
    # (Kubescape structure varies slightly by version)
    # -----------------------------
    rows = []

    for control_id, control in controls_data.items():

        rc = control.get("ResourceCounters", {})

        rows.append({
            "control_id": control_id,
            "control_name": control.get("name"),
            "severity": control.get("severity"),
            "status": control.get("status"),

            "passed_resources": rc.get("passedResources"),
            "failed_resources": rc.get("failedResources"),
            "skipped_resources": rc.get("skippedResources"),
            "excluded_resources": rc.get("excludedResources"),

            "compliance_score": control.get("complianceScore"),
            "score": control.get("score"),
        })

    df = pd.DataFrame(rows)

    return df

# 3.4 Export CSV
def export_kubescape_csv(df, output_file, file_path):

    # Compute "All Resources"
    df["All Resources"] = (
        df["passed_resources"].fillna(0)
        + df["failed_resources"].fillna(0)
        + df["skipped_resources"].fillna(0)
        + df["excluded_resources"].fillna(0)
    )

    # Build final dataframe with required columns
    final_df = pd.DataFrame({
        "FilePath": file_path,
        "Severity": df["severity"],
        "Control name": df["control_name"],
        "Failed resources": df["failed_resources"],
        "All Resources": df["All Resources"],
        "Compliance score": df["compliance_score"],
    })

    # Save to CSV
    final_df.to_csv(output_file, index=False)

    return output_file

def run_task3(name_diff_path, full_diff_path):

    scan_path="project-yamls"

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    controls_output = f"controls-{timestamp}.txt"

    # 1. Load Task 2 outputs
    lines1, lines2 = load_task2_files(name_diff_path, full_diff_path)

    # 2. Map differences → controls
    controls_file = map_differences_to_controls(lines1, lines2, controls_output)

    # 3. Run Kubescape scan
    df = run_kubescape(controls_file, scan_path)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kubescape_csv = f"kubescape_csv-{timestamp}.csv"
    # 4. Export results
    csv_file = export_kubescape_csv(df, kubescape_csv, scan_path)

    return csv_file




# def main():
#     file1 = "name_diff.txt"
#     file2 = "full_diff.txt"

#     lines1, lines2 = load_task2_files(file1, file2)
    
#     controls_file = map_differences_to_controls(lines1, lines2)

#     df = run_kubescape(controls_file, scan_path="project-yamls")

#     export_kubescape_csv(df)


# if __name__ == "__main__":
#     main()