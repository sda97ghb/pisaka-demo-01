# Этот модуль должен быть импортирован не в момент инициализации приложения,
# а в момент выполнения CLI команды, так что скорость импортов нам здесь
# уже не важна
from rich.table import Table

from pisaka.app.authors import Author


def repr_author_as_table(author: Author, title: str) -> Table:
    table = Table("Property", "Value", title=title)
    table.add_section()
    table.add_row("ID", str(author.id))
    table.add_section()
    table.add_row("Name", author.name)
    table.add_row("Is real person?", str(author.is_real_person))
    return table
