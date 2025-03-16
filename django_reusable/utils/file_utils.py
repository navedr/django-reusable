import os
import re
import unicodedata

# Regular expression to strip non-ASCII characters from filenames
_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")

# List of special device files on Windows systems
_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)


def secure_filename(filename: str) -> str:
    r"""
    Pass it a filename and it will return a secure version of it. This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`. The filename returned is an ASCII only string
    for maximum portability.

    On Windows systems, the function also makes sure that the file is not
    named after one of the special device files.

    Examples:
        >>> secure_filename("My cool movie.mov")
        'My_cool_movie.mov'
        >>> secure_filename("../../../etc/passwd")
        'etc_passwd'
        >>> secure_filename('i contain cool \xfcml\xe4uts.txt')
        'i_contain_cool_umlauts.txt'

    The function might return an empty filename. It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.

    Args:
        filename (str): The filename to secure.

    Returns:
        str: A secure version of the filename.
    """
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )

    # On Windows, ensure the filename is not a special device file
    if (
            os.name == "nt"
            and filename
            and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename


def generate_file_if_updated(name, path, content, logger):
    """
    Checks if file contents have changed. If so, re-generates the file.

    Args:
        name (str): The name of the file.
        path (str): The path to the file.
        content (str): The content to write to the file.
        logger (Logger): The logger to use for logging information.
    """
    try:
        with open(path, 'r') as f:
            if f.read() == content:
                return
    except FileNotFoundError:
        pass
    with open(path, 'w') as f:
        logger.info(f'{name} contents have changed. re-generating file...')
        f.write(content)
