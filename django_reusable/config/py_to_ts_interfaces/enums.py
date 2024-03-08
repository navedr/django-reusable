from typing import List


class EnumElement:
    """Represent one element of an enum."""
    name: str
    value: str

    @staticmethod
    def has_tab(line: str):
        return line.lstrip(" ") != line


    def __init__(self, line: str):
        name_and_value = line.strip().split(" = ")
        self.name = name_and_value[0]
        self.value = name_and_value[1].strip("\"")

    def get_typescript(self) -> str:
        """Return the element in typescript syntax (including indentation)."""
        return "    {0} = \'{1}\',".format(self.name, self.value.replace("'", ""))


class EnumDefinition:
    """Represent a python/typescript enum."""
    name: str
    elements: List[EnumElement]

    def __init__(self, definition: List[str]):
        definition = [line for line in definition if
                      not line.startswith("    def") and
                      not line.startswith("        ")
                      ]

        self.name = definition[0].lstrip("class ").rstrip("(Enum):")
        self.elements = []
        for line in definition[1:]:
            if not EnumElement.has_tab(line):
                break
            self.elements.append(EnumElement(line))

    def get_typescript(self) -> str:
        """Return the enum in typescript syntax (including indentation)."""
        typescript_string = "export enum {0} {{\n".format(self.name)
        for element in self.elements:
            typescript_string += "{}\n".format(element.get_typescript())
        typescript_string += "}"
        return typescript_string
