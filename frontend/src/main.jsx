import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Wallet, Users, Tags, Landmark, Repeat, Receipt, Gauge, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from './services/api';
import './styles.css';

const resources = {
  users: {
    label: 'Usuarios',
    icon: Users,
    endpoint: '/users/',
    pk: 'id_user',
    fields: ['first_name', 'last_name_1', 'last_name_2', 'email', 'password'],
    softDeleteField: 'cancellation_date',
  },
  categories: {
    label: 'Categorías',
    icon: Tags,
    endpoint: '/categories/',
    pk: 'id_category',
    fields: ['id_user', 'name', 'type', 'description', 'color'],
  },
  accounts: {
    label: 'Cuentas',
    icon: Landmark,
    endpoint: '/accounts/',
    pk: 'id_account',
    fields: ['id_user', 'account_name', 'account_type', 'currency', 'id_main_category'],
    softDeleteField: 'deleted_at',
  },
  services: {
    label: 'Servicios',
    icon: Receipt,
    endpoint: '/services/',
    pk: 'id_service',
    fields: ['id_user', 'service_name', 'provider_name', 'reference_number', 'due_day', 'typical_amount', 'currency'],
    softDeleteField: 'cancellation_date',
  },
  movements: {
    label: 'Movimientos',
    icon: Repeat,
    endpoint: '/movements/',
    pk: 'id_movement',
    fields: ['id_account', 'id_destination_account', 'id_category', 'id_service', 'id_exchange_rate', 'amount', 'original_currency', 'description', 'movement_date'],
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
  }
};

const fieldLabels = {
  first_name: 'Nombre',
  last_name_1: 'Primer apellido',
  last_name_2: 'Segundo apellido',
  email: 'Email',
  password: 'Contraseña',

  id_user: 'Usuario',
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
  max_amount: 'Monto máximo'
};

const placeholders = {
  password: 'Ingrese una contraseña',
  type: 'EXPENSE o INCOME',
  account_type: 'ACTIVO, PASIVO, CAPITAL, INGRESO o GASTO',
  currency: 'CRC',
  original_currency: 'CRC',
  color: '#22c55e',
  movement_date: '2026-04-27',
  rate_date: '2026-04-27T00:00:00'
};

function emptyForm(fields) {
  return Object.fromEntries(
    fields.map((field) => [
      field,
      field === 'color' ? '#22c55e' : ''
    ])
  );
}

function App() {
  const [active, setActive] = useState('dashboard');

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <Wallet size={28} />
          <div>
            <strong>Financial Manager</strong>
            <span>Finanzas personales</span>
          </div>
        </div>

        <button
          className={active === 'dashboard' ? 'active' : ''}
          onClick={() => setActive('dashboard')}
        >
          <BarChart3 size={18} />Dashboard
        </button>

        {Object.entries(resources).map(([key, item]) => {
          const Icon = item.icon;

          return (
            <button
              key={key}
              className={active === key ? 'active' : ''}
              onClick={() => setActive(key)}
            >
              <Icon size={18} />{item.label}
            </button>
          );
        })}
      </aside>

      <main className="content">
        {active === 'dashboard' ? <Dashboard /> : <CrudPage config={resources[active]} />}
      </main>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_accounts: 0,
    income: 0,
    expenses: 0,
    balance: 0
  });

  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/dashboard/')
      .then(r => setStats(r.data))
      .catch(() => setError('No se pudo conectar con el backend.'));
  }, []);

  const chart = [
    { name: 'Ingresos', total: Number(stats.income) },
    { name: 'Gastos', total: Number(stats.expenses) },
    { name: 'Balance', total: Number(stats.balance) }
  ];

  return (
    <section>
      <h1>Dashboard</h1>
      <p className="muted">Resumen general de la aplicación.</p>

      {error && <p className="error">{error}</p>}

      <div className="cards">
        <Card title="Usuarios" value={stats.total_users} />
        <Card title="Cuentas" value={stats.total_accounts} />
        <Card title="Ingresos" value={stats.income} />
        <Card title="Gastos" value={stats.expenses} />
        <Card title="Balance" value={stats.balance} />
      </div>

      <div className="panel chart">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chart}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="total" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
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

  const load = () => {
    api.get(config.endpoint)
      .then(r => {
        const now = new Date();

        const activeRows = r.data.filter(row => {
          if (config.softDeleteField && row[config.softDeleteField]) {
            return new Date(row[config.softDeleteField]) > now;
          }

          return true;
        });

        setRows(activeRows);
      })
      .catch(() => setError('No se pudo cargar la información.'));
  };

  useEffect(() => {
    setForm(emptyForm(config.fields));
    setEditing(null);
    setError('');
    load();
  }, [config.endpoint]);

  function cleanPayload() {
    const payload = { ...form };

    Object.keys(payload).forEach(k => {
      if (payload[k] === '') payload[k] = null;
    });

    if (editing && payload.password === null) {
      delete payload.password;
    }

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
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error guardando datos'));
    }
  }

  function edit(row) {
    setEditing(row[config.pk]);

    const nextForm = Object.fromEntries(
      config.fields.map(f => [f, f === 'password' ? '' : row[f] ?? ''])
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
          [config.softDeleteField]: today
        });
      } else {
        await api.delete(`${config.endpoint}${id}/`);
      }

      load();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error eliminando registro'));
    }
  }

  function renderCell(row, field) {
    if (field === 'password') {
      return '********';
    }

    if (field === 'color') {
      return (
        <div
          style={{
            width: '28px',
            height: '20px',
            borderRadius: '6px',
            backgroundColor: row[field] || '#ffffff',
            border: '1px solid #ccc'
          }}
          title={row[field]}
        />
      );
    }

    return String(row[field] ?? '');
  }

  return (
    <section>
      <h1>{config.label}</h1>
      <p className="muted">Crear, editar, listar y eliminar registros.</p>

      {error && <p className="error">{error}</p>}

      <form className="panel form" onSubmit={submit}>
        {config.fields.map(field => (
          <label key={field}>
            {fieldLabels[field] || field}

            <input
              type={
                field === 'password'
                  ? 'password'
                  : field === 'color'
                  ? 'color'
                  : 'text'
              }
              value={form[field] || (field === 'color' ? '#22c55e' : '')}
              placeholder={placeholders[field] || ''}
              onChange={e => setForm({ ...form, [field]: e.target.value })}
            />
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

              {config.fields.slice(0, 5).map(f => (
                <th key={f}>{fieldLabels[f] || f}</th>
              ))}

              <th>Acciones</th>
            </tr>
          </thead>

          <tbody>
            {rows.map(row => (
              <tr key={row[config.pk]}>
                <td>{row[config.pk]}</td>

                {config.fields.slice(0, 5).map(f => (
                  <td key={f}>
                    {renderCell(row, f)}
                  </td>
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
    </section>
  );
}

createRoot(document.getElementById('root')).render(<App />);