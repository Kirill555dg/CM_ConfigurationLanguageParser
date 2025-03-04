import sys
import xml.etree.ElementTree as ET
from lark import Lark, Transformer, exceptions, LarkError

# Грамматика конфигурационного языка
grammar = """
start: (const_decl)* config

config: NAME value

const_decl: "var" NAME value
const_eval: "|" NAME "|"

value:  NUMBER | array | dict | const_eval

array: "[" [value ("," value)*] "]"
dict: "{" [pair (";" pair)*] "}"
pair: NAME ":" value

NAME: /[a-zA-Z][_a-zA-Z0-9]*/

%import common.NUMBER
%import common.WS
%ignore WS
"""

# Инициализация Lark парсера
config_parser = Lark(grammar)


class ConfigTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.constants = {}  # Хранилище для констант

    # Обработка точки старта
    def start(self, value):
        return value[-1]

    # Обработка записи константы
    def const_decl(self, tupl):
        name, value = tupl
        if name in self.constants:
            raise LarkError(f"Константа {name} уже объявлена")
        self.constants[name] = value

    # Обработка вычисления константы
    def const_eval(self, value):
        name = value[0]
        if name not in self.constants:
            raise ValueError(f"В конфигурации использована неизвестная константа по имени {name}")
        return self.constants[name]

    # Обработка корневого узла
    def config(self, value):
        name, info = value
        info = info[1]
        return f"<{name}>{info}</{name}>"

    # Обработка пары ключ-значение в словаре
    def pair(self, value):
        key, tupl = value
        typ, val = tupl
        return f"<{key} type=\"{typ}\">{val}</{key}>"

    # Обработка словаря
    def dict(self, items):
        result = ""
        # Словарь состоит из нескольких пар, каждая пара обработана через 'pair'
        for item in items:
            if item is not None:
                result += item
        return "dict", result

    # Обработка массива
    def array(self, tuples):
        # Массив обрабатывается путём обёртки каждого элемента в тег 'element'
        elements = ''.join([f"<element type=\"{typ}\">{val}</element>" for typ, val in tuples])
        return "array", elements

    # Обработка чисел
    def NUMBER(self, token):
        return "int", int(token)

    # Обработка имён
    def NAME(self, token):
        return str(token)

    # Обработка значения (которое может быть числом, массивом или словарём)
    def value(self, tupl):
        return tupl[0]

    # Функция для парсинга и обработки ошибок


def parse_config(input_text):
    try:
        # Парсинг входного текста
        tree = config_parser.parse(input_text)

        # Преобразование дерева в XML
        transformer = ConfigTransformer()
        xml_output = transformer.transform(tree)
        return xml_output
    except exceptions.UnexpectedCharacters as uc:
        return f"Unexpected Characters:\n{str(uc)}"
    except exceptions.LarkError as le:
        return f"Ошибка при обработке:\n{str(le)}"


def pretty_print_xml(xml_string):
    # Парсинг строки XML в дерево
    root = ET.fromstring(xml_string)

    # Преобразование дерева в красиво отформатированную строку
    pretty_xml = ET.tostring(root, encoding='UTF-8', method='xml')

    # Преобразование строки в отформатированную с отступами
    import xml.dom.minidom
    dom = xml.dom.minidom.parseString(pretty_xml)

    # Возвращаем красиво отформатированный текст
    return dom.toprettyxml()

# Пример использования
if __name__ == "__main__":
    input_text = sys.stdin.read()
    xml_str  = parse_config(input_text)
    output = pretty_print_xml(xml_str)
    sys.stdout.write(output)
