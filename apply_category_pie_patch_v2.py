from pathlib import Path
import re

ROOT = Path.cwd()
FRONTEND = ROOT / 'frontend' / 'src' / 'main.jsx'
VIEWS = ROOT / 'backend' / 'core' / 'views.py'
URLS = ROOT / 'backend' / 'core' / 'urls.py'

if not FRONTEND.exists() or not VIEWS.exists() or not URLS.exists():
    raise SystemExit('Ejecuta este script desde la raíz del proyecto: financial_manager_login_clean')

# ---------- frontend/src/main.jsx ----------
text = FRONTEND.read_text(encoding='utf-8')

# Add Pie imports to recharts import block.
match = re.search(r"import\s*\{(?P<body>.*?)\}\s*from\s*['\"]recharts['\"];", text, flags=re.S)
if not match:
    raise SystemExit('No encontré el import de recharts en frontend/src/main.jsx')
body = match.group('body')
names = [n.strip() for n in body.replace('\n', ' ').split(',') if n.strip()]
for name in ['PieChart', 'Pie', 'Legend']:
    if name not in names:
        names.append(name)
new_import = "import {\n  " + ",\n  ".join(names) + ",\n} from 'recharts';"
text = text[:match.start()] + new_import + text[match.end():]

# Add CategorySpendingPie component if missing.
if 'function CategorySpendingPie()' not in text:
    component = r'''

function CategorySpendingPie() {
  const [filters, setFilters] = useState({ start_date: '', end_date: '' });
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');

  const pieColors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'];

  function buildQuery() {
    const params = new URLSearchParams();
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    const query = params.toString();
    return query ? `/reports/category-spending/?${query}` : '/reports/category-spending/';
  }

  function loadReport() {
    setError('');
    api
      .get(buildQuery())
      .then((r) => {
        setData(r.data.items || []);
        setTotal(Number(r.data.total || 0));
      })
      .catch(() => setError('No se pudo cargar el reporte por categoría.'));
  }

  useEffect(() => {
    loadReport();
  }, []);

  return (
    <section className="panel">
      <div className="panel-title-row">
        <div>
          <h2>Gastos por categoría</h2>
          <p className="muted">Porcentaje del gasto total agrupado por categoría.</p>
        </div>
      </div>

      <div className="filter-row">
        <label>
          Desde
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
          />
        </label>
        <button type="button" onClick={loadReport}>Aplicar filtro</button>
        <button
          type="button"
          className="secondary"
          onClick={() => {
            setFilters({ start_date: '', end_date: '' });
            setTimeout(loadReport, 0);
          }}
        >
          Todo el tiempo
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {data.length === 0 ? (
        <p className="muted">Aún no hay gastos registrados para mostrar.</p>
      ) : (
        <div className="pie-report-grid">
          <div className="chart pie-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={95}
                  label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
                >
                  {data.map((entry, index) => (
                    <Cell key={entry.category} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => Number(value).toFixed(2)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Total</th>
                  <th>Porcentaje</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.category}>
                    <td>{item.category}</td>
                    <td>{Number(item.total).toFixed(2)}</td>
                    <td>{Number(item.percentage).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">Total gastado: {total.toFixed(2)}</p>
          </div>
        </div>
      )}
    </section>
  );
}
'''
    insert_at = text.find('\nfunction Card(')
    if insert_at == -1:
        insert_at = text.find('function Card(')
    if insert_at == -1:
        raise SystemExit('No encontré function Card para insertar CategorySpendingPie.')
    text = text[:insert_at] + component + text[insert_at:]

# Insert CategorySpendingPie in Dashboard return if not used.
if '<CategorySpendingPie />' not in text:
    dash_start = text.find('function Dashboard()')
    card_start = text.find('function Card(', dash_start)
    if dash_start == -1 or card_start == -1:
        raise SystemExit('No encontré el bloque Dashboard completo.')
    dash = text[dash_start:card_start]
    last_section = dash.rfind('</section>')
    if last_section == -1:
        raise SystemExit('No encontré el cierre de sección del gráfico del Dashboard.')
    dash = dash[:last_section + len('</section>')] + "\n\n      <CategorySpendingPie />" + dash[last_section + len('</section>'):]
    text = text[:dash_start] + dash + text[card_start:]

# Add minimal CSS by injecting class names into styles.css separately if available.
FRONTEND.write_text(text, encoding='utf-8')

styles_path = ROOT / 'frontend' / 'src' / 'styles.css'
if styles_path.exists():
    css = styles_path.read_text(encoding='utf-8')
    extra_css = r'''

.pie-report-grid {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(280px, 1fr);
  gap: 1rem;
  align-items: stretch;
}

.pie-chart-box {
  min-height: 320px;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  align-items: end;
  margin-bottom: 1rem;
}

@media (max-width: 760px) {
  .pie-report-grid {
    grid-template-columns: 1fr;
  }
}
'''
    if '.pie-report-grid' not in css:
        styles_path.write_text(css + extra_css, encoding='utf-8')

# ---------- backend/core/views.py ----------
views = VIEWS.read_text(encoding='utf-8')
if 'from django.db import connection, transaction' not in views:
    views = views.replace('from django.db import transaction', 'from django.db import connection, transaction')

if 'def category_spending_report' not in views:
    report_view = r'''

@api_view(["GET"])
def category_spending_report(request):
    user, error = require_login(request)
    if error:
        return error

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    params = [user.id_user]
    date_filter = ""

    if start_date:
        date_filter += " AND m.movement_date >= %s"
        params.append(start_date)

    if end_date:
        date_filter += " AND m.movement_date <= %s"
        params.append(end_date)

    query = f"""
        SELECT
            c.name AS category,
            SUM(ABS(m.amount)) AS total
        FROM MOVEMENT m
        JOIN ACCOUNT a ON m.id_account = a.id_account
        JOIN CATEGORY c ON m.id_category = c.id_category
        WHERE a.id_user = %s
          AND c.type = 'EXPENSE'
          AND m.amount < 0
          {date_filter}
        GROUP BY c.id_category, c.name
        ORDER BY total DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total_spent = sum(float(row[1] or 0) for row in rows)
    items = []

    for category, total in rows:
        value = float(total or 0)
        percentage = (value / total_spent * 100) if total_spent else 0
        items.append(
            {
                "category": category,
                "total": value,
                "percentage": percentage,
            }
        )

    return Response(
        {
            "total": total_spent,
            "items": items,
        }
    )
'''
    marker = '@api_view(["GET"])\ndef dashboard(request):'
    if marker not in views:
        marker = '@api_view(["GET"]) def dashboard(request):'
    idx = views.find(marker)
    if idx == -1:
        raise SystemExit('No encontré la vista dashboard para insertar category_spending_report.')
    views = views[:idx] + report_view + '\n' + views[idx:]

VIEWS.write_text(views, encoding='utf-8')

# ---------- backend/core/urls.py ----------
urls = URLS.read_text(encoding='utf-8')
if 'category_spending_report' not in urls:
    urls = urls.replace('me_view,', 'me_view,\n    category_spending_report,')
if 'reports/category-spending/' not in urls:
    urls = urls.replace('path("dashboard/", dashboard),', 'path("dashboard/", dashboard),\n    path("reports/category-spending/", category_spending_report),')
URLS.write_text(urls, encoding='utf-8')

print('Parche aplicado: gráfico pie de gastos por categoría agregado al Dashboard.')
