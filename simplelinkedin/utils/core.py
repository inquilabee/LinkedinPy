import os
from pathlib import Path


def get_preferences(file_name_or_list: list | os.PathLike | str) -> list[str]:
    if file_name_or_list and not isinstance(file_name_or_list, list):
        if not Path(file_name_or_list).exists():
            raise FileNotFoundError(f"File not found: {Path(file_name_or_list).absolute()}")

        with open(file_name_or_list) as f:
            users_preferred = f.readlines()
    elif file_name_or_list:
        users_preferred = file_name_or_list
    else:
        users_preferred = []

    return [line.strip().lower() for line in users_preferred if line.strip()]


def find_in_text(text: str, search_words: list[str]) -> bool:
    """

    :param text: Where to search
    :param search_words: What to search
    :return: Boolean indicating the search result
    """

    # TODO: Improve matching algorithm

    if not search_words:
        return True

    if not text:
        return False

    return any(search_word in text for search_word in search_words)
