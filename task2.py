import os
import yaml
from datetime import datetime

def load_yamls(yaml1_path, yaml2_path):
    def load_yaml(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("Invalid YAML structure")

        cleaned = {}

        for _, item in data.items():
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            reqs = item.get("requirements", [])

            if not isinstance(name, str):
                continue

            cleaned[name] = reqs if isinstance(reqs, list) else []

        return cleaned

    yaml1 = load_yaml(yaml1_path)
    yaml2 = load_yaml(yaml2_path)

    return yaml1, yaml2

def compare_kde_names(data1, data2, file1_name, file2_name, output_file="name_diff.txt"):
    names1 = set(data1.keys())
    names2 = set(data2.keys())

    only1 = names1 - names2
    only2 = names2 - names1

    with open(output_file, "w", encoding="utf-8") as f:
        if not only1 and not only2:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT NAMES\n")
            return

        for name in sorted(only1 | only2):
            f.write(f"{name}\n")

    print(f"KDE name comparison written to {output_file}")

def compare_kde_and_requirements(data1, data2, file1_name, file2_name, output_file="full_diff.txt"):
    names1 = set(data1.keys())
    names2 = set(data2.keys())

    only1 = names1 - names2
    only2 = names2 - names1
    common = names1 & names2

    differences_found = False

    with open(output_file, "w", encoding="utf-8") as f:

        # --- KDE only differences ---
        for name in sorted(only1):
            f.write(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},NA\n")
            differences_found = True

        for name in sorted(only2):
            f.write(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},NA\n")
            differences_found = True

        # --- Requirement differences ---
        for name in sorted(common):
            reqs1 = set(data1[name])
            reqs2 = set(data2[name])

            only_req1 = reqs1 - reqs2
            only_req2 = reqs2 - reqs1

            for r in only_req1:
                f.write(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},{r}\n")
                differences_found = True

            for r in only_req2:
                f.write(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},{r}\n")
                differences_found = True

        if not differences_found:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS\n")

    print(f"Full comparison written to {output_file}")

def run_task2(yaml1_path, yaml2_path):
    yaml1, yaml2 = load_yamls(yaml1_path, yaml2_path)

    base1 = os.path.basename(yaml1_path).split("-kdes-")[0]
    base2 = os.path.basename(yaml2_path).split("-kdes-")[0]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    name_output = f"{base1}-{base2}-name_diff-{timestamp}.txt"
    full_output = f"{base1}-{base2}-full_diff-{timestamp}.txt"

    compare_kde_names(yaml1, yaml2, base1, base2, name_output)
    compare_kde_and_requirements(yaml1, yaml2, base1, base2, full_output)

    return name_output, full_output

# def main():

#     file1 = os.path.join("yaml_output", "cis-r1-kdes.yaml")
#     file2 = os.path.join("yaml_output", "cis-r2-kdes.yaml")
#     file3 = os.path.join("yaml_output", "cis-r3-kdes.yaml")
#     file4 = os.path.join("yaml_output", "cis-r4-kdes.yaml")

#     yaml1, yaml2 = load_yamls(file1, file2)

#     compare_kde_names(yaml1, yaml2, os.path.basename(file1), os.path.basename(file2))
#     compare_kde_and_requirements(yaml1, yaml2, os.path.basename(file1), os.path.basename(file2))
    

#     yaml1, yaml2 = load_yamls(file1, file1)

#     compare_kde_names(yaml1, yaml2, os.path.basename(file1), os.path.basename(file1))
#     compare_kde_and_requirements(yaml1, yaml2, os.path.basename(file1), os.path.basename(file1))


# if __name__ == "__main__":
#     main()