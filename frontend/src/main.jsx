import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Wallet,
  Tags,
  Landmark,
  Repeat,
  Receipt,
  Gauge,
  BarChart3,
  LogOut,
  UserPlus,
  LogIn,
  ChevronDown,
} from 'lucide-react';
import {
  BarChart,
  Bar, Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import api from './services/api';
import './styles.css';

const resources = {
  movements: {
    label: 'Transacciones',
    title: 'Transacciones',
    description: 'Registra ingresos, gastos y transferencias entre cuentas.',
    icon: Repeat,
    endpoint: '/movements/',
    pk: 'id_movement',
    fields: [
      'id_account',
      'id_destination_account',
      'id_service',
      'id_exchange_rate',
      'amount',
      'original_currency',
      'description',
      'movement_date',
    ],
  },
  categories: {
    label: 'Categorías',
    title: 'Categorías',
    description: 'Clasifica tus ingresos y gastos con categorías personalizadas.',
    icon: Tags,
    endpoint: '/categories/',
    pk: 'id_category',
    fields: ['name', 'type', 'description', 'color'],
  },
  accounts: {
    label: 'Cuentas',
    title: 'Cuentas',
    description: 'Administra las cuentas o rubros donde se registran movimientos.',
    icon: Landmark,
    endpoint: '/accounts/',
    pk: 'id_account',
    fields: ['account_name', 'account_type', 'currency', 'id_main_category'],
    softDeleteField: 'deleted_at',
  },
  services: {
    label: 'Servicios',
    title: 'Servicios',
    description: 'Controla pagos recurrentes y servicios por vencer.',
    icon: Receipt,
    endpoint: '/services/',
    pk: 'id_service',
    fields: [
      'service_name',
      'provider_name',
      'reference_number',
      'due_day',
      'typical_amount',
      'currency',
    ],
    softDeleteField: 'cancellation_date',
  },
  exchangeRates: {
    label: 'Tipos de cambio',
    title: 'Tipos de cambio',
    description: 'Registra tasas de conversión entre monedas.',
    icon: BarChart3,
    endpoint: '/exchange-rates/',
    pk: 'id_exchange_rate',
    fields: ['from_currency', 'to_currency', 'rate', 'rate_date'],
  },
  accountLimits: {
    label: 'Límites',
    title: 'Límites de cuenta',
    description: 'Define límites de gasto por cuenta y período.',
    icon: Gauge,
    endpoint: '/account-limits/',
    pk: 'id_limit',
    fields: ['id_account', 'start_date', 'end_date', 'max_amount'],
  },
};

const fieldLabels = {
  first_name: 'Nombre',
  last_name_1: 'Primer apellido',
  last_name_2: 'Segundo apellido',
  email: 'Email',
  password: 'Contraseña',
  name: 'Nombre',
  type: 'Tipo',
  description: 'Descripción',
  color: 'Color',
  account_name: 'Nombre cuenta',
  account_type: 'Tipo cuenta',
  currency: 'Moneda',
  id_main_category: 'Categoría principal',
  service_name: 'Servicio',
  provider_name: 'Proveedor',
  reference_number: 'Referencia',
  due_day: 'Día de pago',
  typical_amount: 'Monto típico',
  id_account: 'Cuenta afectada',
  id_destination_account: 'Cuenta destino',
  id_category: 'Categoría',
  id_service: 'Servicio',
  id_exchange_rate: 'Tipo de cambio',
  amount: 'Monto',
  original_currency: 'Moneda original',
  movement_date: 'Fecha',
  from_currency: 'Desde',
  to_currency: 'Hacia',
  rate: 'Tasa',
  rate_date: 'Fecha tasa',
  start_date: 'Inicio',
  end_date: 'Fin',
  max_amount: 'Monto máximo',
};

const placeholders = {
  password: 'Ingrese una contraseña',
  color: '#22c55e',
  currency: 'CRC',
  original_currency: 'CRC',
  movement_date: '2026-04-27',
  rate_date: '2026-04-27T00:00:00',
};

const selectOptions = {
  type: [
    { value: 'EXPENSE', label: 'Gasto' },
    { value: 'INCOME', label: 'Ingreso' },
  ],
  account_type: [
    { value: 'ACTIVO', label: 'Activo' },
    { value: 'PASIVO', label: 'Pasivo' },
    { value: 'CAPITAL', label: 'Capital' },
    { value: 'INGRESO', label: 'Ingreso' },
    { value: 'GASTO', label: 'Gasto' },
  ],
  currency: [
    { value: 'CRC', label: 'CRC' },
    { value: 'USD', label: 'USD' },
    { value: 'EUR', label: 'EUR' },
  ],
  original_currency: [
    { value: 'CRC', label: 'CRC' },
    { value: 'USD', label: 'USD' },
    { value: 'EUR', label: 'EUR' },
  ],
};

const relationConfig = {
  id_main_category: {
    endpoint: '/categories/',
    pk: 'id_category',
    label: (item) => `${item.name} (${item.type})`,
    allowBlank: true,
  },
  id_category: {
    endpoint: '/categories/',
    pk: 'id_category',
    label: (item) => `${item.name} (${item.type})`,
    allowBlank: false,
  },
  id_account: {
    endpoint: '/accounts/',
    pk: 'id_account',
    label: (item) => `${item.account_name} (${item.account_type})`,
    allowBlank: false,
  },
  id_destination_account: {
    endpoint: '/accounts/',
    pk: 'id_account',
    label: (item) => `${item.account_name} (${item.account_type})`,
    allowBlank: true,
  },
  id_service: {
    endpoint: '/services/',
    pk: 'id_service',
    label: (item) => item.service_name,
    allowBlank: true,
  },
  id_exchange_rate: {
    endpoint: '/exchange-rates/',
    pk: 'id_exchange_rate',
    label: (item) => `${item.from_currency} → ${item.to_currency} (${item.rate})`,
    allowBlank: true,
  },
};

function emptyForm(fields) {
  return Object.fromEntries(
    fields.map((field) => [field, field === 'color' ? '#22c55e' : ''])
  );
}

function App() {
  const [active, setActive] = useState('movements');
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  const navItems = useMemo(
    () => [
      { key: 'movements', label: 'Transacciones', icon: Repeat },
      { key: 'dashboard', label: 'Dashboard', icon: Wallet },
      ...Object.entries(resources)
        .filter(([key]) => key !== 'movements')
        .map(([key, item]) => ({ key, label: item.label, icon: item.icon })),
    ],
    []
  );

  const activeItem = navItems.find((item) => item.key === active) || navItems[0];

  useEffect(() => {
    api
      .get('/auth/me/')
      .then((r) => setUser(r.data.user))
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  async function logout() {
    await api.post('/auth/logout/');
    setUser(null);
    setActive('movements');
    setMenuOpen(false);
  }

  function navigate(key) {
    setActive(key);
    setMenuOpen(false);
  }

  if (checking) {
    return <div className="loading">Cargando Financial Manager...</div>;
  }

  if (!user) {
    return <AuthScreen onLogin={setUser} />;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-icon"><Wallet size={22} /></div>
          <div>
            <strong>Financial Manager</strong>
            <span>Finanzas personales</span>
          </div>
        </div>

        <div className="nav-dropdown">
          <button
            type="button"
            className="nav-trigger"
            onClick={() => setMenuOpen((value) => !value)}
            aria-expanded={menuOpen}
          >
            <span>Vista: {activeItem.label}</span>
            <ChevronDown size={18} />
          </button>

          {menuOpen && (
            <div className="nav-menu">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.key}
                    type="button"
                    className={active === item.key ? 'active' : ''}
                    onClick={() => navigate(item.key)}
                  >
                    <Icon size={18} />
                    {item.label}
                  </button>
                );
              })}
              <button type="button" className="logout-menu-btn" onClick={logout}>
                <LogOut size={18} />
                Cerrar sesión
              </button>
            </div>
          )}
        </div>

        <div className="session-pill">
          <span>Sesión activa</span>
          <strong>{user.first_name} {user.last_name_1}</strong>
          <small>{user.email}</small>
        </div>
      </header>

      <main className="content">
        {active === 'dashboard' ? (
          <Dashboard />
        ) : (
          <CrudPage config={resources[active]} />
        )}
      </main>
    </div>
  );
}

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    first_name: '',
    last_name_1: '',
    last_name_2: '',
    email: 'demo@flujex.local',
    password: 'demo1234',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const endpoint = mode === 'login' ? '/auth/login/' : '/auth/register/';
      const payload = mode === 'login'
        ? { email: form.email, password: form.password }
        : form;
      const response = await api.post(endpoint, payload);
      onLogin(response.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo iniciar sesión.');
    } finally {
      setLoading(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError('');
    if (nextMode === 'login') {
      setForm((prev) => ({
        ...prev,
        email: 'demo@flujex.local',
        password: 'demo1234',
      }));
    } else {
      setForm({
        first_name: '',
        last_name_1: '',
        last_name_2: '',
        email: '',
        password: '',
      });
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <h1>Financial Manager</h1>
          <span>Finanzas personales independientes por usuario</span>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={mode === 'login' ? 'active' : ''}
            onClick={() => switchMode('login')}
          >
            <LogIn size={18} /> Iniciar sesión
          </button>
          <button
            type="button"
            className={mode === 'register' ? 'active' : ''}
            onClick={() => switchMode('register')}
          >
            <UserPlus size={18} /> Crear cuenta
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <>
              <label>Nombre
                <input value={form.first_name} onChange={(e) => update('first_name', e.target.value)} />
              </label>
              <label>Primer apellido
                <input value={form.last_name_1} onChange={(e) => update('last_name_1', e.target.value)} />
              </label>
              <label>Segundo apellido
                <input value={form.last_name_2} onChange={(e) => update('last_name_2', e.target.value)} />
              </label>
            </>
          )}
          <label>Email
            <input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
          </label>
          <label>Contraseña
            <input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Procesando...' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
          </button>
        </form>

        {mode === 'login' && (
          <p className="auth-note">Cuenta demo: demo@flujex.local / demo1234</p>
        )}
      </div>
    </section>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_accounts: 0,
    income: 0,
    expenses: 0,
    balance: 0,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/dashboard/')
      .then((r) => setStats(r.data))
      .catch(() => setError('No se pudo conectar con el backend.'));
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

  return (
    <>
      <section className="page-heading">
        <h1>Dashboard</h1>
        <p className="muted">Resumen general de tu cuenta.</p>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="cards">
        <Card title="Cuentas" value={stats.total_accounts} />
        <Card title="Ingresos" value={stats.income} />
        <Card title="Gastos" value={stats.expenses} />
        <Card title="Balance" value={stats.balance} />
      </section>

      <section className="panel">
        <h2>Resumen gráfico</h2>
        <div className="chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total" radius={[10, 10, 0, 0]}>{chart.map((entry) => (<Cell key={entry.name} fill={chartColors[entry.name] || '#64748b'} />))}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </>
  );
}

function Card({ title, value }) {
  return (
    <article className="card">
      <span>{title}</span>
      <strong>{String(value)}</strong>
    </article>
  );
}

function CrudPage({ config }) {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(emptyForm(config.fields));
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState('');
  const [lookups, setLookups] = useState({});

  const visibleFields = config.fields;

  const load = () => {
    setRows([]);
    api
      .get(config.endpoint)
      .then((r) => {
        const now = new Date();
        const activeRows = r.data.filter((row) => {
          if (config.softDeleteField && row[config.softDeleteField]) {
            return new Date(row[config.softDeleteField]) > now;
          }
          return true;
        });
        setRows(activeRows);
      })
      .catch(() => setError('No se pudo cargar la información.'));
  };

  const loadLookups = async () => {
    const relationFields = config.fields.filter((field) => relationConfig[field]);
    if (relationFields.length === 0) {
      setLookups({});
      return;
    }
    const uniqueEndpoints = [...new Set(relationFields.map((field) => relationConfig[field].endpoint))];
    try {
      const responses = await Promise.all(uniqueEndpoints.map((endpoint) => api.get(endpoint)));
      const nextLookups = {};
      uniqueEndpoints.forEach((endpoint, index) => {
        nextLookups[endpoint] = responses[index].data;
      });
      setLookups(nextLookups);
    } catch {
      setError('No se pudieron cargar las listas relacionadas.');
    }
  };

  useEffect(() => {
    setRows([]);
    setLookups({});
    setForm(emptyForm(config.fields));
    setEditing(null);
    setError('');
    load();
    loadLookups();
  }, [config.endpoint]);

  function cleanPayload() {
    const payload = { ...form };
    Object.keys(payload).forEach((key) => {
      if (payload[key] === '') payload[key] = null;
      if (relationConfig[key] && payload[key] !== null) payload[key] = Number(payload[key]);
    });
    return payload;
  }

  async function submit(e) {
    e.preventDefault();
    setError('');
    try {
      if (editing) {
        await api.patch(`${config.endpoint}${editing}/`, cleanPayload());
      } else {
        await api.post(config.endpoint, cleanPayload());
      }
      setForm(emptyForm(config.fields));
      setEditing(null);
      load();
      loadLookups();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error guardando datos'));
    }
  }

  function edit(row) {
    setEditing(row[config.pk]);
    const nextForm = Object.fromEntries(
      config.fields.map((field) => [field, row[field] ?? ''])
    );
    setForm(nextForm);
  }

  async function remove(id) {
    const message = config.softDeleteField
      ? '¿Cancelar/Eliminar registro? El registro quedará guardado en la base de datos.'
      : '¿Eliminar registro definitivamente?';
    if (!confirm(message)) return;
    try {
      if (config.softDeleteField) {
        await api.patch(`${config.endpoint}${id}/`, {
          [config.softDeleteField]: new Date().toISOString(),
        });
      } else {
        await api.delete(`${config.endpoint}${id}/`);
      }
      load();
      loadLookups();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error eliminando registro'));
    }
  }

  function relationLabel(field, value) {
    if (value === null || value === undefined || value === '') return '';
    const relation = relationConfig[field];
    if (!relation) return String(value ?? '');
    const options = lookups[relation.endpoint] || [];
    const item = options.find((option) => String(option[relation.pk]) === String(value));
    return item ? relation.label(item) : String(value);
  }

  function renderCell(row, field) {
    if (field === 'color') {
      return <span className="color-dot" style={{ background: row[field] }} />;
    }
    if (relationConfig[field]) {
      return relationLabel(field, row[field]);
    }
    return String(row[field] ?? '');
  }

  function renderField(field) { if (field === 'color') { return ( <div className="color-picker-row"> <input className="color-picker" type="color" value={form[field] || '#22c55e'} onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> <input className="color-code-input" type="text" value={form[field] || '#22c55e'} placeholder="#22c55e" onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> </div> ); }
    if (selectOptions[field]) {
      return (
        <select value={form[field] ?? ''} onChange={(e) => setForm({ ...form, [field]: e.target.value })}>
          <option value="">Seleccione...</option>
          {selectOptions[field].map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      );
    }

    if (relationConfig[field]) {
      const relation = relationConfig[field];
      const options = lookups[relation.endpoint] || [];
      return (
        <select value={form[field] ?? ''} onChange={(e) => setForm({ ...form, [field]: e.target.value })}>
          {relation.allowBlank && <option value="">Sin asignar</option>}
          {!relation.allowBlank && <option value="">Seleccione...</option>}
          {options.map((option, index) => (
            <option key={`${field}-${option[relation.pk] ?? index}`} value={option[relation.pk]}>{relation.label(option)}</option>
          ))}
        </select>
      );
    }

    const inputType = field.includes('date')
      ? 'date'
      : field.includes('amount') || field === 'rate' || field === 'due_day'
        ? 'number'
        : 'text';

    return (
      <input
        type={inputType}
        value={form[field] ?? ''}
        placeholder={placeholders[field] || ''}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
      />
    );
  }

  return (
    <>
      <section className="page-heading">
        <h1>{config.title || config.label}</h1>
        <p className="muted">{config.description || 'Crear, editar, listar y eliminar registros de tu cuenta.'}</p>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="panel form-panel">
        <form className="form" onSubmit={submit}>
          {visibleFields.map((field) => (
            <label key={field}>
              {fieldLabels[field] || field}
              {renderField(field)}
            </label>
          ))}
          <div className="actions">
            <button type="submit">{editing ? 'Actualizar' : 'Guardar'}</button>
            {editing && (
              <button type="button" className="secondary" onClick={() => {
                setEditing(null);
                setForm(emptyForm(config.fields));
              }}>
                Cancelar edición
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                {config.fields.slice(0, 5).map((field) => (
                  <th key={field}>{fieldLabels[field] || field}</th>
                ))}
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${config.endpoint}-${row[config.pk] ?? index}`}>
                  <td>{row[config.pk]}</td>
                  {config.fields.slice(0, 5).map((field) => (
                    <td key={field}>{renderCell(row, field)}</td>
                  ))}
                  <td>
                    <button type="button" className="small" onClick={() => edit(row)}>Editar</button>
                    <button type="button" className="small danger" onClick={() => remove(row[config.pk])}>
                      {config.softDeleteField ? 'Cancelar' : 'Eliminar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

createRoot(document.getElementById('root')).render(<App />);
