import os
import difflib
import shutil

from yoda_dbt2looker.core.converter import convert


class TestConverter:

    def test_run_convert(self):
        self.clear_folder_contents("generated_lookml")
        convert(
            target_dir="tests/resources/core/test_target",
            project_dir="tests/resources",
            output_dir="generated_lookml",
            tag="yoda_looker",
            log_level="INFO",
        )
        self.compare_folders_content("tests/resources/core/expected_lookml", "generated_lookml")

    @staticmethod
    def clear_folder_contents(folder_path: str) -> None:
        """
        Remove all contents of the specified folder but keep the folder itself.

        Args:
            folder_path (str): The path to the folder to be cleared.
        """
        # Ensure the directory exists
        if not os.path.isdir(folder_path):
            raise ValueError(f"The folder path '{folder_path}' is not a directory or does not exist.")

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove directory and its contents
            else:
                os.remove(item_path)  # Remove file

    @staticmethod
    def compare_folders_content(folder1: str, folder2: str):
        """
        Compares the content of files with the same name in two different folders.

        Args:
            folder1 (str): The path to the first folder.
            folder2 (str): The path to the second folder.

        Raises:
            AssertionError: If the content of any file is different.
        """
        for file in os.listdir(folder1):
            path1 = os.path.join(folder1, file)
            path2 = os.path.join(folder2, file)

            if os.path.isfile(path1) and os.path.isfile(path2):
                with open(path1, 'r') as f1, open(path2, 'r') as f2:
                    text1 = f1.read()
                    text2 = f2.read()

                    diff = difflib.unified_diff(text1.splitlines(), text2.splitlines())
                    if diff:
                        raise AssertionError(f"File content mismatch for {file}")
