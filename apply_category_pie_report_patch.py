from pathlib import Path
import re

ROOT = Path.cwd()
views_path = ROOT / 'backend' / 'core' / 'views.py'
urls_path = ROOT / 'backend' / 'core' / 'urls.py'
main_path = ROOT / 'frontend' / 'src' / 'main.jsx'
styles_path = ROOT / 'frontend' / 'src' / 'styles.css'
queries_path = ROOT / 'backend' / 'db' / 'queries.sql'

missing = [p for p in [views_path, urls_path, main_path, styles_path] if not p.exists()]
if missing:
    raise SystemExit('No se encontraron archivos esperados:\n' + '\n'.join(str(p) for p in missing))

# ---------- backend/core/views.py ----------
views = views_path.read_text(encoding='utf-8')

if 'from django.db import transaction, connection' not in views:
    views = views.replace('from django.db import transaction', 'from django.db import transaction, connection')

report_func = r'''

@api_view(["GET"])
def category_spending_report(request):
    user, error = require_login(request)
    if error:
        return error

    start_date = request.GET.get("start_date") or None
    end_date = request.GET.get("end_date") or None

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
            c.id_category,
            c.name AS category,
            c.color AS color,
            COUNT(m.id_movement) AS quantity,
            COALESCE(SUM(ABS(m.amount)), 0) AS total
        FROM MOVEMENT m
        JOIN ACCOUNT a ON m.id_account = a.id_account
        JOIN CATEGORY c ON m.id_category = c.id_category
        WHERE a.id_user = %s
          AND m.amount < 0
          {date_filter}
        GROUP BY c.id_category, c.name, c.color
        HAVING total > 0
        ORDER BY total DESC;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total_spent = sum(Decimal(str(row[4])) for row in rows)
    results = []

    for row in rows:
        amount = Decimal(str(row[4]))
        percentage = Decimal("0.00")
        if total_spent > 0:
            percentage = (amount / total_spent * Decimal("100")).quantize(Decimal("0.01"))

        results.append(
            {
                "id_category": row[0],
                "category": row[1],
                "color": row[2] or "#64748b",
                "quantity": row[3],
                "total": float(amount),
                "percentage": float(percentage),
            }
        )

    return Response(
        {
            "start_date": start_date,
            "end_date": end_date,
            "total_spent": float(total_spent),
            "results": results,
        }
    )
'''

if 'def category_spending_report(request):' not in views:
    m = re.search(r'\n@api_view\(\["GET"\]\)\ndef dashboard\(request\):', views)
    if m:
        views = views[:m.start()] + report_func + views[m.start():]
    else:
        views += report_func

views_path.write_text(views, encoding='utf-8')

# ---------- backend/core/urls.py ----------
urls = urls_path.read_text(encoding='utf-8')
if 'category-spending' not in urls:
    # Most project versions import views as module or import dashboard directly. Handle both.
    if 'from . import views' in urls:
        route = '    path("reports/category-spending/", views.category_spending_report, name="category-spending-report"),\n'
    else:
        # Add function import if urls imports individual views.
        urls = re.sub(
            r'from \.views import \((.*?)\)',
            lambda m: 'from .views import (' + m.group(1).rstrip() + ', category_spending_report)',
            urls,
            flags=re.DOTALL,
        )
        if 'category_spending_report' not in urls:
            urls = urls.replace('from .views import ', 'from .views import category_spending_report, ')
        route = '    path("reports/category-spending/", category_spending_report, name="category-spending-report"),\n'

    # Insert after dashboard route if possible, otherwise at start of urlpatterns.
    inserted = False
    patterns = [
        r'(path\([\'\"]dashboard/[\'\"].*?\),\s*)',
        r'(path\([\'\"]api/dashboard/[\'\"].*?\),\s*)',
    ]
    for pat in patterns:
        new_urls, n = re.subn(pat, lambda m: m.group(1) + '\n' + route, urls, count=1, flags=re.DOTALL)
        if n:
            urls = new_urls
            inserted = True
            break
    if not inserted:
        urls = urls.replace('urlpatterns = [', 'urlpatterns = [\n' + route, 1)

urls_path.write_text(urls, encoding='utf-8')

# ---------- frontend/src/main.jsx ----------
main = main_path.read_text(encoding='utf-8')

# Add Pie components to recharts import.
if 'PieChart' not in main:
    main = main.replace('BarChart,', 'BarChart,\n  PieChart,\n  Pie,\n  Cell,\n  Legend,')
elif 'Legend' not in main:
    main = main.replace('ResponsiveContainer,', 'ResponsiveContainer,\n  Legend,')
if 'Cell' not in main.split("from 'recharts'")[0] and 'Cell,' not in main.split('from "recharts"')[0]:
    main = main.replace('Bar,', 'Bar,\n  Cell,')

new_dashboard = r'''function Dashboard() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_accounts: 0,
    income: 0,
    expenses: 0,
    balance: 0,
  });
  const [categoryReport, setCategoryReport] = useState({
    total_spent: 0,
    results: [],
  });
  const [reportFilters, setReportFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [error, setError] = useState('');
  const [reportError, setReportError] = useState('');

  useEffect(() => {
    api
      .get('/dashboard/')
      .then((r) => setStats(r.data))
      .catch(() => setError('No se pudo conectar con el backend.'));
  }, []);

  function loadCategoryReport(filters = reportFilters) {
    const params = {};
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;

    setReportError('');
    api
      .get('/reports/category-spending/', { params })
      .then((r) => setCategoryReport(r.data))
      .catch(() => setReportError('No se pudo cargar el reporte por categoría.'));
  }

  useEffect(() => {
    loadCategoryReport({ start_date: '', end_date: '' });
  }, []);

  const chart = [
    { name: 'Ingresos', total: Number(stats.income) },
    { name: 'Gastos', total: Number(stats.expenses) },
    { name: 'Balance', total: Number(stats.balance) },
  ];

  const chartColors = {
    Ingresos: '#22c55e',
    Gastos: '#ef4444',
    Balance: '#eab308',
  };

  const pieData = (categoryReport.results || []).map((item) => ({
    name: item.category,
    value: Number(item.total),
    percentage: Number(item.percentage),
    color: item.color || '#64748b',
  }));

  return (
    <>
      <header className="page-header">
        <h1>Dashboard</h1>
        <p>Resumen general de tu cuenta.</p>
      </header>

      {error && <div className="error-box">{error}</div>}

      <section className="summary-grid">
        <Card title="Cuentas" value={stats.total_accounts} />
        <Card title="Ingresos" value={stats.income} />
        <Card title="Gastos" value={stats.expenses} />
        <Card title="Balance" value={stats.balance} />
      </section>

      <section className="panel">
        <h2>Resumen gráfico</h2>
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chart}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total" radius={[10, 10, 0, 0]}>
                {chart.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={chartColors[entry.name] || '#64748b'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="report-header">
          <div>
            <h2>Gastos por categoría</h2>
            <p>
              Por defecto se muestra todo el historial. Puedes filtrar por un rango de fechas.
            </p>
          </div>
          <div className="report-total">
            Total gastado: {Number(categoryReport.total_spent || 0).toLocaleString()}
          </div>
        </div>

        <div className="report-filters">
          <label>
            Desde
            <input
              type="date"
              value={reportFilters.start_date}
              onChange={(e) =>
                setReportFilters({ ...reportFilters, start_date: e.target.value })
              }
            />
          </label>
          <label>
            Hasta
            <input
              type="date"
              value={reportFilters.end_date}
              onChange={(e) =>
                setReportFilters({ ...reportFilters, end_date: e.target.value })
              }
            />
          </label>
          <button type="button" onClick={() => loadCategoryReport()}>
            Aplicar filtro
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              const clean = { start_date: '', end_date: '' };
              setReportFilters(clean);
              loadCategoryReport(clean);
            }}
          >
            Todo el tiempo
          </button>
        </div>

        {reportError && <div className="error-box">{reportError}</div>}

        {pieData.length > 0 ? (
          <div className="report-layout">
            <div className="chart-box pie-chart-box">
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={110}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name, props) => [
                      `${Number(value).toLocaleString()} (${props.payload.percentage}%)`,
                      name,
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="table-wrap report-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Categoría</th>
                    <th>Total</th>
                    <th>Porcentaje</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryReport.results.map((item) => (
                    <tr key={item.id_category}>
                      <td>{item.category}</td>
                      <td>{Number(item.total).toLocaleString()}</td>
                      <td>{item.percentage}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="empty-state">No hay gastos registrados para el rango seleccionado.</p>
        )}
      </section>
    </>
  );
}
'''

new_main, n = re.subn(r'function Dashboard\(\) \{.*?\}\s*function Card', new_dashboard + '\nfunction Card', main, count=1, flags=re.DOTALL)
if n == 0:
    # Try a more permissive pattern for formatted files.
    new_main, n = re.subn(r'function Dashboard\(\)\s*\{.*?\n\}\s*\nfunction Card', new_dashboard + '\nfunction Card', main, count=1, flags=re.DOTALL)
if n == 0:
    raise SystemExit('No se pudo localizar function Dashboard() en frontend/src/main.jsx')
main = new_main
main_path.write_text(main, encoding='utf-8')

# ---------- frontend/src/styles.css ----------
styles = styles_path.read_text(encoding='utf-8')
extra_css = r'''

.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.report-header p {
  margin: 0.25rem 0 0;
  color: #64748b;
}

.report-total {
  font-weight: 800;
  color: #0f172a;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 0.75rem 1rem;
  white-space: nowrap;
}

.report-filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, auto));
  align-items: end;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.report-filters label {
  display: grid;
  gap: 0.35rem;
  font-weight: 700;
  color: #334155;
}

.report-filters input {
  min-height: 2.5rem;
}

.secondary-button {
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #cbd5e1;
}

.report-layout {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(280px, 0.9fr);
  gap: 1rem;
  align-items: start;
}

.pie-chart-box {
  min-height: 320px;
}

.empty-state {
  padding: 1rem;
  border: 1px dashed #cbd5e1;
  border-radius: 1rem;
  color: #64748b;
  background: #f8fafc;
}

@media (max-width: 760px) {
  .report-header {
    display: grid;
  }

  .report-total {
    white-space: normal;
  }

  .report-filters {
    grid-template-columns: 1fr;
  }

  .report-layout {
    grid-template-columns: 1fr;
  }
}
'''
if '.report-filters' not in styles:
    styles += extra_css
styles_path.write_text(styles, encoding='utf-8')

# ---------- backend/db/queries.sql ----------
if queries_path.exists():
    queries = queries_path.read_text(encoding='utf-8')
    query_block = r'''

-- Reporte: porcentaje de gasto por categoría para el usuario actual y rango opcional
-- Reemplazar ? por id_usuario, fecha_inicio y fecha_fin cuando aplique.
SELECT
    c.name AS category,
    COUNT(m.id_movement) AS quantity,
    SUM(ABS(m.amount)) AS total,
    ROUND(
        SUM(ABS(m.amount)) * 100.0 /
        NULLIF((
            SELECT SUM(ABS(m2.amount))
            FROM MOVEMENT m2
            JOIN ACCOUNT a2 ON m2.id_account = a2.id_account
            WHERE a2.id_user = ?
              AND m2.amount < 0
              AND m2.movement_date BETWEEN ? AND ?
        ), 0),
        2
    ) AS percentage
FROM MOVEMENT m
JOIN ACCOUNT a ON m.id_account = a.id_account
JOIN CATEGORY c ON m.id_category = c.id_category
WHERE a.id_user = ?
  AND m.amount < 0
  AND m.movement_date BETWEEN ? AND ?
GROUP BY c.id_category, c.name
ORDER BY total DESC;
'''
    if 'porcentaje de gasto por categoría' not in queries:
        queries += query_block
    queries_path.write_text(queries, encoding='utf-8')

print('Parche aplicado correctamente: reporte de gastos por categoría con gráfico pie en Dashboard.')
