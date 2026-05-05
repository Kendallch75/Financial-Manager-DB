import React, { useEffect, useState } from 'react';
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
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import api from './services/api';
import './styles.css';

const resources = {
  categories: {
    label: 'Categorías',
    icon: Tags,
    endpoint: '/categories/',
    pk: 'id_category',
    fields: ['name', 'type', 'description', 'color'],
  },
  accounts: {
    label: 'Cuentas',
    icon: Landmark,
    endpoint: '/accounts/',
    pk: 'id_account',
    fields: ['account_name', 'account_type', 'currency', 'id_main_category'],
    softDeleteField: 'deleted_at',
  },
  services: {
    label: 'Servicios',
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
  movements: {
    label: 'Movimientos',
    icon: Repeat,
    endpoint: '/movements/',
    pk: 'id_movement',
    fields: [
      'id_account',
      'id_destination_account',
      'id_category',
      'id_service',
      'id_exchange_rate',
      'amount',
      'original_currency',
      'description',
      'movement_date',
    ],
  },
  exchangeRates: {
    label: 'Tipos de cambio',
    icon: BarChart3,
    endpoint: '/exchange-rates/',
    pk: 'id_exchange_rate',
    fields: ['from_currency', 'to_currency', 'rate', 'rate_date'],
  },
  accountLimits: {
    label: 'Límites',
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
  id_account: 'Cuenta origen',
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
  type: 'EXPENSE o INCOME',
  account_type: 'ACTIVO, PASIVO, CAPITAL, INGRESO o GASTO',
  currency: 'CRC',
  original_currency: 'CRC',
  color: '#22c55e',
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
    label: (item) => item.account_name,
    allowBlank: false,
  },
  id_destination_account: {
    endpoint: '/accounts/',
    pk: 'id_account',
    label: (item) => item.account_name,
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
  const [active, setActive] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

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
    setActive('dashboard');
  }

  if (checking) {
    return <div className="loading">Cargando Financial Manager...</div>;
  }

  if (!user) {
    return <AuthScreen onLogin={setUser} />;
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <Wallet size={34} />
          <div>
            <strong>Financial Manager</strong>
            <span>Finanzas personales</span>
          </div>
        </div>

        <div className="session-box">
          <span>Sesión activa</span>
          <strong>{user.first_name} {user.last_name_1}</strong>
          <small>{user.email}</small>
        </div>

        <button
          className={active === 'dashboard' ? 'active' : ''}
          onClick={() => setActive('dashboard')}
        >
          <Gauge size={18} /> Dashboard
        </button>

        {Object.entries(resources).map(([key, item]) => {
          const Icon = item.icon;
          return (
            <button
              key={key}
              className={active === key ? 'active' : ''}
              onClick={() => setActive(key)}
            >
              <Icon size={18} /> {item.label}
            </button>
          );
        })}

        <button className="logout-btn" onClick={logout}>
          <LogOut size={18} /> Cerrar sesión
        </button>
      </aside>

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
      setForm((prev) => ({ ...prev, email: 'demo@flujex.local', password: 'demo1234' }));
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
    <div className="auth-page">
      <section className="auth-card">
        <div className="brand auth-brand">
          <Wallet size={38} />
          <div>
            <strong>Financial Manager</strong>
            <span>Finanzas personales independientes por usuario</span>
          </div>
        </div>

        <div className="auth-tabs">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>
            <LogIn size={17} /> Iniciar sesión
          </button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>
            <UserPlus size={17} /> Crear cuenta
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <>
              <label>
                Nombre
                <input value={form.first_name} onChange={(e) => update('first_name', e.target.value)} />
              </label>
              <label>
                Primer apellido
                <input value={form.last_name_1} onChange={(e) => update('last_name_1', e.target.value)} />
              </label>
              <label>
                Segundo apellido
                <input value={form.last_name_2} onChange={(e) => update('last_name_2', e.target.value)} />
              </label>
            </>
          )}

          <label>
            Email
            <input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
          </label>
          <label>
            Contraseña
            <input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'Procesando...' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
          </button>
        </form>

        {mode === 'login' && (
          <p className="muted auth-note">
            Cuenta demo: <strong>demo@flujex.local</strong> / <strong>demo1234</strong>
          </p>
        )}
      </section>
    </div>
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

  return (
    <>
      <h1>Dashboard</h1>
      <p className="muted">Resumen general de tu cuenta.</p>
      {error && <div className="error">{error}</div>}
      <div className="cards">
        <Card title="Usuarios" value={stats.total_users} />
        <Card title="Cuentas" value={stats.total_accounts} />
        <Card title="Ingresos" value={stats.income} />
        <Card title="Gastos" value={stats.expenses} />
        <Card title="Balance" value={stats.balance} />
      </div>
      <div className="panel chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="total" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

function Card({ title, value }) {
  return (
    <div className="card">
      <span>{title}</span>
      <strong>{String(value)}</strong>
    </div>
  );
}

function CrudPage({ config }) {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(emptyForm(config.fields));
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState('');
  const [lookups, setLookups] = useState({});

  const load = () => {
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
    setForm(emptyForm(config.fields));
    setEditing(null);
    setError('');
    load();
    loadLookups();
  }, [config.endpoint]);

  function cleanPayload() {
    const payload = { ...form };
    Object.keys(payload).forEach((k) => {
      if (payload[k] === '') payload[k] = null;
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
      config.fields.map((f) => [f, row[f] ?? ''])
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
        const today = new Date().toISOString();
        await api.patch(`${config.endpoint}${id}/`, {
          [config.softDeleteField]: today,
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
      return (
        <span className="color-dot" style={{ background: row[field] || '#e2e8f0' }} />
      );
    }
    if (relationConfig[field]) {
      return relationLabel(field, row[field]);
    }
    return String(row[field] ?? '');
  }

  function renderField(field) {
    if (selectOptions[field]) {
      return (
        <select
          value={form[field] ?? ''}
          onChange={(e) => setForm({ ...form, [field]: e.target.value })}
        >
          <option value="">Seleccione...</option>
          {selectOptions[field].map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (relationConfig[field]) {
      const relation = relationConfig[field];
      const options = lookups[relation.endpoint] || [];
      return (
        <select
          value={form[field] ?? ''}
          onChange={(e) => setForm({ ...form, [field]: e.target.value })}
        >
          {relation.allowBlank && <option value="">Sin asignar</option>}
          {!relation.allowBlank && <option value="">Seleccione...</option>}
          {options.map((option) => (
            <option key={option[relation.pk]} value={option[relation.pk]}>
              {relation.label(option)}
            </option>
          ))}
        </select>
      );
    }

    const inputType = field.includes('date') ? 'date' : field.includes('amount') || field === 'rate' || field === 'due_day' ? 'number' : 'text';
    return (
      <input
        type={inputType}
        value={form[field] ?? ''}
        placeholder={placeholders[field] || ''}
        step={field.includes('amount') || field === 'rate' ? '0.01' : undefined}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
      />
    );
  }

  return (
    <>
      <h1>{config.label}</h1>
      <p className="muted">Crear, editar, listar y eliminar registros de tu cuenta.</p>
      {error && <div className="error">{error}</div>}

      <form className="panel form" onSubmit={submit}>
        {config.fields.map((field) => (
          <label key={field}>
            {fieldLabels[field] || field}
            {renderField(field)}
          </label>
        ))}
        <div className="actions">
          <button>{editing ? 'Actualizar' : 'Guardar'}</button>
          {editing && (
            <button
              type="button"
              className="secondary"
              onClick={() => {
                setEditing(null);
                setForm(emptyForm(config.fields));
              }}
            >
              Cancelar edición
            </button>
          )}
        </div>
      </form>

      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              {config.fields.slice(0, 5).map((f) => (
                <th key={f}>{fieldLabels[f] || f}</th>
              ))}
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row[config.pk]}>
                <td>{row[config.pk]}</td>
                {config.fields.slice(0, 5).map((f) => (
                  <td key={f}>{renderCell(row, f)}</td>
                ))}
                <td>
                  <button className="small" onClick={() => edit(row)}>
                    Editar
                  </button>
                  <button className="small danger" onClick={() => remove(row[config.pk])}>
                    {config.softDeleteField ? 'Cancelar' : 'Eliminar'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

createRoot(document.getElementById('root')).render(<App />);
