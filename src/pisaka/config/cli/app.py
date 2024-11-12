# Старайтесь делать здесь как можно меньше импортов, чтобы приложение
# запускалось быстрее. В идеале должно быть всего два следующие импорта
from typer import Typer

from pisaka.config.cli import authors, dev

app = Typer(no_args_is_help=True)
app.add_typer(authors.cli, name="authors")
app.add_typer(dev.cli, name="dev")
