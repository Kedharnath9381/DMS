import { useEffect, useState } from 'react'
import {
  ShieldCheck,
  Activity,
  Database,
  Clock3,
  Plus,
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Download,
  Server,
  HardDrive
} from 'lucide-react'

const API = 'http://127.0.0.1:8000/api'

const INITIAL_FORM = {
  name: '',
  dataset_size_mb: 500,
  scenario: 'NORMAL',
  target_rto_seconds: 10
}

const SCENARIOS = [
  { value: 'NORMAL', label: 'Normal' },
  { value: 'CPU_CONTENTION', label: 'CPU contention' },
  { value: 'DISK_CONTENTION', label: 'Disk contention' },
  { value: 'COMBINED', label: 'Combined contention' }
]

const DATASET_SIZES = [
  { value: 100, label: '100 MiB' },
  { value: 500, label: '500 MiB' },
  { value: 1000, label: '1000 MiB (≈ 1 GiB)' },
  { value: 2000, label: '2000 MiB (≈ 2 GiB)' }
]

export default function App() {
  const [experiments, setExperiments] = useState([])
  const [apiStatus, setApiStatus] = useState('checking')

  const [showForm, setShowForm] = useState(false)
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(false)

  const [latestResult, setLatestResult] = useState(null)
  const [error, setError] = useState('')

  const [form, setForm] = useState(INITIAL_FORM)

  // --------------------------------------------------
  // Load dashboard data
  // --------------------------------------------------

  async function load() {
    setLoading(true)

    try {
      const healthResponse = await fetch(`${API}/health`)

      setApiStatus(
        healthResponse.ok ? 'online' : 'offline'
      )

      const response = await fetch(`${API}/experiments`)

      if (!response.ok) {
        throw new Error('Failed to fetch experiments')
      }

      const data = await response.json()

      setExperiments(Array.isArray(data) ? data : [])
      setError('')
    } catch (err) {
      console.error('Dashboard loading error:', err)

      setApiStatus('offline')
      setError('Backend connection unavailable. Check whether FastAPI is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  // --------------------------------------------------
  // Run experiment
  // --------------------------------------------------

  async function runExperiment(e) {
    e.preventDefault()

    if (running) return

    setRunning(true)
    setError('')
    setLatestResult(null)

    try {
      const payload = {
        ...form,
        name:
          form.name.trim() ||
          `${form.dataset_size_mb} MiB ${form.scenario} Experiment`
      }

      const response = await fetch(`${API}/experiments/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Experiment execution failed'
        )
      }

      setLatestResult(data)
      setShowForm(false)

      setForm(INITIAL_FORM)

      await load()
    } catch (err) {
      console.error('Experiment error:', err)

      setError(
        err.message || 'Experiment execution failed.'
      )
    } finally {
      setRunning(false)
    }
  }

  // --------------------------------------------------
  // CSV export
  // --------------------------------------------------

  async function exportCSV() {
    try {
      const response = await fetch(`${API}/experiments/export/csv`)

      if (!response.ok) {
        throw new Error('CSV export failed')
      }

      const blob = await response.blob()

      const url = window.URL.createObjectURL(blob)

      const link = document.createElement('a')

      link.href = url
      link.download = 'disaster_recovery_experiments.csv'

      document.body.appendChild(link)
      link.click()

      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message || 'Unable to export CSV.')
    }
  }

  // --------------------------------------------------
  // Dashboard calculations
  // --------------------------------------------------

  const completedExperiments = experiments.filter(
    x =>
      x.status === 'COMPLETED' ||
      x.status === 'FAILED'
  )

  const pendingExperiments = experiments.filter(
    x =>
      x.status === 'CREATED' ||
      x.status === 'RUNNING'
  )

  /*
   * Important:
   * RTO statistics must not depend on experiment status.
   *
   * A restore may successfully execute but exceed the
   * configured RTO. That trial still belongs in RTO stats.
   */

  const rtoPassed = experiments.filter(
    x => x.rto_status === 'PASS'
  )

  const rtoFailed = experiments.filter(
    x => x.rto_status === 'FAIL'
  )

  const rtoEvaluated = experiments.filter(
    x =>
      x.rto_status === 'PASS' ||
      x.rto_status === 'FAIL'
  )

  const integrityPassed = experiments.filter(
    x => x.integrity_status === 'PASS'
  )

  const integrityFailed = experiments.filter(
    x => x.integrity_status === 'FAIL'
  )

  // Average restore time includes every record
  // that has an actual measured restore duration.

  const restoreMeasurements = experiments.filter(
    x =>
      x.restore_duration_seconds !== null &&
      x.restore_duration_seconds !== undefined &&
      !Number.isNaN(Number(x.restore_duration_seconds))
  )

  const avgRestoreTime = restoreMeasurements.length
    ? (
        restoreMeasurements.reduce(
          (sum, x) =>
            sum + Number(x.restore_duration_seconds),
          0
        ) / restoreMeasurements.length
      ).toFixed(2)
    : '—'

  const rtoSuccessRate = rtoEvaluated.length
    ? (
        (rtoPassed.length / rtoEvaluated.length) *
        100
      ).toFixed(1)
    : '—'

  // --------------------------------------------------
  // Main UI
  // --------------------------------------------------

  return (
    <div className="app-shell">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            <ShieldCheck size={22} />
          </div>

          <div>
            <b>RecoveryLab</b>
            <small>DR VERIFICATION</small>
          </div>

        </div>

        <div className="nav-label">
          WORKSPACE
        </div>

        <div className="nav-item active">
          <Activity size={18} />
          Overview
        </div>

        <div className="nav-item">
          <Database size={18} />
          Experiments
        </div>

        <div className="nav-item">
          <Clock3 size={18} />
          Recovery analysis
        </div>

        <div className="sidebar-bottom">

          <span className={`dot ${apiStatus}`} />

          API {apiStatus.toUpperCase()}

        </div>

      </aside>

      {/* MAIN CONTENT */}

      <main className="main">

        {/* TOP BAR */}

        <header className="topbar">

          <div>

            <span className="eyebrow">
              DISASTER RECOVERY / LAB
            </span>

            <h1>Overview</h1>

          </div>

          <button
            className="ghost"
            onClick={load}
            disabled={loading || running}
          >

            <RefreshCw
              size={16}
              className={loading ? 'spin' : ''}
            />

            {loading
              ? 'Refreshing...'
              : 'Refresh'}

          </button>

        </header>

        {/* INTRO */}

        <section className="intro">

          <div>

            <h2>
              Recovery objective verification
            </h2>

            <p>
              Measure real restore performance.
              Validate whether recovery targets are achievable.
            </p>

          </div>

          <button
            className="primary"
            onClick={() => setShowForm(!showForm)}
            disabled={running}
          >

            <Plus size={17} />

            New experiment

          </button>

        </section>

        {/* ERROR */}

        {error && (

          <div className="error-banner">

            <XCircle size={18} />

            {error}

          </div>

        )}

        {/* METRIC CARDS */}

        <section className="cards">

          <Metric
            title="Total experiments"
            value={experiments.length}
            icon={<Activity />}
            note="All recorded trials"
          />

          <Metric
            title="RTO achieved"
            value={rtoPassed.length}
            icon={<ShieldCheck />}
            note="Restore completed within target"
          />

          <Metric
            title="RTO exceeded"
            value={rtoFailed.length}
            icon={<Clock3 />}
            note="Restore time exceeded target"
          />

          <Metric
            title="Avg restore time"
            value={
              avgRestoreTime === '—'
                ? '—'
                : `${avgRestoreTime}s`
            }
            icon={<Database />}
            note="All measured restore trials"
          />

        </section>

        {/* ADDITIONAL METRICS */}

        <section className="cards">

          <Metric
            title="Integrity verified"
            value={integrityPassed.length}
            icon={<CheckCircle2 />}
            note="SHA-256 verification passed"
          />

          <Metric
            title="Integrity failures"
            value={integrityFailed.length}
            icon={<XCircle />}
            note="Data verification failed"
          />

          <Metric
            title="Pending experiments"
            value={pendingExperiments.length}
            icon={<Loader2 />}
            note="Created or running"
          />

          <Metric
            title="RTO success rate"
            value={
              rtoSuccessRate === '—'
                ? '—'
                : `${rtoSuccessRate}%`
            }
            icon={<Activity />}
            note="Based on evaluated trials"
          />

        </section>

        {/* EXPERIMENT FORM */}

        {showForm && (

          <section className="panel form-panel">

            <div className="panel-heading">

              <div>

                <h3>
                  Configure experiment
                </h3>

                <p>
                  Configure and execute a real backup and restore test
                </p>

              </div>

            </div>

            <form
              onSubmit={runExperiment}
              className="experiment-form"
            >

              {/* EXPERIMENT NAME */}

              <label>

                Experiment name

                <input
                  value={form.name}
                  onChange={e =>
                    setForm({
                      ...form,
                      name: e.target.value
                    })
                  }
                  placeholder="e.g. 500 MiB baseline recovery"
                  maxLength={120}
                />

              </label>

              {/* DATASET SIZE */}

              <label>

                Dataset size

                <select
                  value={form.dataset_size_mb}
                  onChange={e =>
                    setForm({
                      ...form,
                      dataset_size_mb: Number(
                        e.target.value
                      )
                    })
                  }
                >

                  {DATASET_SIZES.map(size => (

                    <option
                      key={size.value}
                      value={size.value}
                    >
                      {size.label}
                    </option>

                  ))}

                </select>

              </label>

              {/* SCENARIO */}

              <label>

                Scenario

                <select
                  value={form.scenario}
                  onChange={e =>
                    setForm({
                      ...form,
                      scenario: e.target.value
                    })
                  }
                >

                  {SCENARIOS.map(scenario => (

                    <option
                      key={scenario.value}
                      value={scenario.value}
                    >
                      {scenario.label}
                    </option>

                  ))}

                </select>

              </label>

              {/* TARGET RTO */}

              <label>

                Target RTO (seconds)

                <input
                  type="number"
                  min="1"
                  max="3600"
                  required
                  value={form.target_rto_seconds}
                  onChange={e =>
                    setForm({
                      ...form,
                      target_rto_seconds: Number(
                        e.target.value
                      )
                    })
                  }
                />

              </label>

              {/* FORM BUTTONS */}

              <div className="form-actions">

                <button
                  type="button"
                  className="ghost"
                  onClick={() => setShowForm(false)}
                  disabled={running}
                >
                  Cancel
                </button>

                <button
                  className="primary run-button"
                  type="submit"
                  disabled={running}
                >

                  {running ? (

                    <>
                      <Loader2
                        size={17}
                        className="spin"
                      />

                      Experiment running...

                    </>

                  ) : (

                    <>
                      <Play size={17} />

                      Run experiment

                    </>

                  )}

                </button>

              </div>

            </form>

          </section>

        )}

        {/* RUNNING STATE */}

        {running && (

          <section className="running-panel">

            <Loader2
              size={24}
              className="spin"
            />

            <div>

              <h3>
                Experiment in progress
              </h3>

              <p>
                Generating dataset, performing backup,
                restoring data and verifying integrity.
                Please do not close the application.
              </p>

            </div>

          </section>

        )}

        {/* LATEST RESULT */}

        {latestResult && (

          <section className="panel result-panel">

            <div className="panel-heading">

              <div>

                <h3>
                  Latest experiment result
                </h3>

                <p>
                  Experiment #{latestResult.experiment?.id}
                </p>

              </div>

              <StatusBadge
                value={
                  latestResult.experiment?.status ||
                  'UNKNOWN'
                }
              />

            </div>

            <div className="result-grid">

              <ResultMetric
                label="Backup duration"
                value={
                  latestResult.results?.backup_duration_seconds != null
                    ? `${Number(
                        latestResult.results.backup_duration_seconds
                      ).toFixed(2)}s`
                    : '—'
                }
              />

              <ResultMetric
                label="Restore duration"
                value={
                  latestResult.results?.restore_duration_seconds != null
                    ? `${Number(
                        latestResult.results.restore_duration_seconds
                      ).toFixed(2)}s`
                    : '—'
                }
              />

              <ResultMetric
                label="Integrity"
                value={
                  latestResult.results?.integrity_status ||
                  'UNKNOWN'
                }
                status={
                  latestResult.results?.integrity_status
                }
              />

              <ResultMetric
                label="RTO verification"
                value={
                  latestResult.results?.rto_status ||
                  'UNKNOWN'
                }
                status={
                  latestResult.results?.rto_status
                }
              />

            </div>

          </section>

        )}

        {/* EXPERIMENT HISTORY */}

        <section className="panel">

          <div className="panel-heading">

            <div>

              <h3>
                Experiment history
              </h3>

              <p>
                Recorded recovery verification experiments
              </p>

            </div>

            <div className="history-actions">

              <span className="badge">
                {experiments.length} records
              </span>

              <button
                className="ghost"
                onClick={exportCSV}
                disabled={experiments.length === 0}
              >

                <Download size={15} />

                Export CSV

              </button>

            </div>

          </div>

          {/* EMPTY STATE */}

          {experiments.length === 0 ? (

            <div className="empty">

              <div className="empty-icon">
                <Database />
              </div>

              <h3>
                No experiments yet
              </h3>

              <p>
                Run your first recovery verification experiment.
              </p>

              <button
                className="primary"
                onClick={() => setShowForm(true)}
              >

                <Plus size={16} />

                New experiment

              </button>

            </div>

          ) : (

            /* HISTORY TABLE */

            <div className="table-wrap">

              <table>

                <thead>

                  <tr>
                    <th>Experiment</th>
                    <th>Dataset</th>
                    <th>Scenario</th>
                    <th>Target RTO</th>
                    <th>Restore</th>
                    <th>Integrity</th>
                    <th>RTO</th>
                    <th>Status</th>
                  </tr>

                </thead>

                <tbody>

                  {experiments.map(x => (

                    <tr key={x.id}>

                      {/* EXPERIMENT */}

                      <td>

                        <b>
                          {x.name || `Experiment #${x.id}`}
                        </b>

                        <small>
                          #{x.id}
                        </small>

                      </td>

                      {/* DATASET */}

                      <td>
                        {x.dataset_size_mb} MiB
                      </td>

                      {/* SCENARIO */}

                      <td>

                        {x.scenario
                          ?.replaceAll('_', ' ')
                          || '—'}

                      </td>

                      {/* TARGET RTO */}

                      <td>
                        {x.target_rto_seconds}s
                      </td>

                      {/* RESTORE TIME */}

                      <td>

                        {x.restore_duration_seconds == null
                          ? '—'
                          : `${Number(
                              x.restore_duration_seconds
                            ).toFixed(2)}s`}

                      </td>

                      {/* INTEGRITY */}

                      <td>

                        <StatusBadge
                          value={x.integrity_status || 'UNKNOWN'}
                        />

                      </td>

                      {/* RTO */}

                      <td>

                        <StatusBadge
                          value={x.rto_status || 'UNKNOWN'}
                        />

                      </td>

                      {/* EXECUTION STATUS */}

                      <td>

                        <StatusBadge
                          value={x.status || 'UNKNOWN'}
                        />

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </section>

        {/* FOOTER */}

        <footer>

          RecoveryLab · Research prototype ·
          Real backup and restore verification

        </footer>

      </main>

    </div>
  )
}

// --------------------------------------------------
// METRIC CARD
// --------------------------------------------------

function Metric({
  title,
  value,
  icon,
  note
}) {

  return (

    <div className="metric">

      <div className="metric-top">

        <span>
          {title}
        </span>

        <div className="metric-icon">
          {icon}
        </div>

      </div>

      <strong>
        {value}
      </strong>

      <small>
        {note}
      </small>

    </div>

  )
}

// --------------------------------------------------
// RESULT METRIC
// --------------------------------------------------

function ResultMetric({
  label,
  value,
  status
}) {

  return (

    <div className="result-metric">

      <span>
        {label}
      </span>

      <strong
        className={
          status
            ? status.toLowerCase()
            : ''
        }
      >
        {value}
      </strong>

    </div>

  )

}

// --------------------------------------------------
// STATUS BADGE
// --------------------------------------------------

function StatusBadge({
  value
}) {

  let className = 'pending'

  if (
    value === 'PASS' ||
    value === 'COMPLETED' ||
    value === 'ONLINE'
  ) {
    className = 'success'
  }

  if (
    value === 'FAIL' ||
    value === 'FAILED' ||
    value === 'OFFLINE'
  ) {
    className = 'failure'
  }

  return (

    <span className={`status ${className}`}>

      {value}

    </span>

  )

}