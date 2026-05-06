from pathlib import Path
import re

path = Path("frontend/src/main.jsx")
text = path.read_text()

# 1. Eliminar cualquier <CategorySpendingPie /> mal colocado
text = re.sub(r"\n\s*<CategorySpendingPie\s*/>\s*", "\n", text)

# 2. Insertarlo correctamente dentro del Dashboard,
# justo antes del cierre del fragmento principal del Dashboard.
start = text.find("function Dashboard()")
end = text.find("function CategorySpendingPie")

if start == -1:
    raise SystemExit("No encontré function Dashboard().")

if end == -1:
    raise SystemExit("No encontré function CategorySpendingPie().")

dashboard = text[start:end]

target = "\n    </>\n  );"
insert = "\n\n      <CategorySpendingPie />"

if target not in dashboard:
    raise SystemExit("No encontré el cierre esperado del Dashboard: </>.")

dashboard = dashboard.replace(target, insert + target, 1)

text = text[:start] + dashboard + text[end:]

path.write_text(text)

print("Listo: CategorySpendingPie fue movido al Dashboard correctamente.")
