import os

def print_directory_tree(directory_path, indent=""):
    """Recursively prints a text tree of the directory structure."""
    print(f"{indent}{os.path.basename(directory_path)}")
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            print_directory_tree(item_path, indent + "    ")  # Increase indentation for subdirectories
        else:
            print(f"{indent}    {item}")

# Example usage:
# Replace '.' with the path to the directory you want to list
print_directory_tree('"C:\Users\zacha\OneDrive\Desktop\Moore AI"')