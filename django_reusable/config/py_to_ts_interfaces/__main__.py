import os
import traceback
from typing import Union

from django_reusable.logging.loggers import PrintLogger
from .enums import EnumDefinition
from .file_io import write_file, read_file
from .interfaces import InterfaceDefinition
from .strings import StringDefinition
from .utils import is_class_definition, is_string_definition


def python_to_typescript_file(python_code: str) -> str:
    logger = PrintLogger("python_to_typescript_file")
    """
    Convert python enum and dataclass definitions to equivalent typescript code.

    :param python_code: Python code containing only enums and dataclasses.
    :return: Equivalent typescript code.
    """
    # initial processing (remove superfluous lines)
    lines = python_code.splitlines()
    lines = [line for line in lines if line and not line.isspace() and not line.startswith(("from ", "#", "@"))]

    # group the lines for each enum/class definition together
    definition_groups: list[list[str]] = []
    for line in lines:
        if is_class_definition(line) or is_string_definition(line):
            definition_groups.append([])
        definition_groups[-1].append(line)

    # convert each group into either an EnumDefinition or InterfaceDefinition object
    processed_definitions: list[Union[EnumDefinition, InterfaceDefinition, StringDefinition]] = []
    for definition in definition_groups:
        try:
            if definition[0].endswith("(Enum):"):
                processed_definitions.append(EnumDefinition(definition))
            elif definition[0].endswith("\""):
                processed_definitions.append(StringDefinition(definition))
            else:
                processed_definitions.append(InterfaceDefinition(definition))
        except:
            logger.error("error while processing definition")
            traceback.print_exc()

    # construct final output
    typescript_output = ""
    for i, processed_definition in enumerate(processed_definitions):
        typescript_output += "{}\n".format(processed_definition.get_typescript())
        # Want consecutive string definitions to be next to each other
        if not (len(processed_definitions) >= i + 1 and
                isinstance(processed_definition, StringDefinition) and
                isinstance(processed_definitions[i + 1], StringDefinition)):
            typescript_output += "\n"
    typescript_output = typescript_output.strip("\n")
    # add just one newline at the end
    typescript_output += "\n"

    return typescript_output


def python_to_typescript_folder(input_path: str, output_path: str) -> None:
    """
    Convert all python files in input directory to typescript files in output directory. Each output file has the
    same name as its python source (with the file extension changed to 'ts').

    :param input_path: A full or relative path to a folder containing .py files.
    :param output_path: A full or relative path to a folder which may not exist.
    """
    for file in os.listdir(input_path):
        if file.endswith(".py") and file != "__init__.py":
            file_contents = read_file(os.path.join(input_path, file))

            typescript_output = python_to_typescript_file(file_contents)

            write_file(typescript_output, os.path.join(output_path, file[:-3] + ".ts"))

