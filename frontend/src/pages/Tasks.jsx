import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Clock,
  Plus,
  Trash2,
  Edit2,
  Building,
} from 'lucide-react';
import { api } from '../services/api';
import { formatDate, getInitials } from '../utils/formatters';
import { PriorityBadge } from '../components/leads/PriorityBadge';
import { TaskModal } from '../components/tasks/TaskModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';

export function Tasks({ onSelectLead }) {
  const [tasks, setTasks] = useState([]);
  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [statusFilter, setStatusFilter] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (assigneeFilter) params.assigned_to = assigneeFilter;

      const [tasksData, leadsData, usersData] = await Promise.all([
        api.tasks.list(params),
        api.leads.list().catch(() => []),
        api.auth.getUsers().catch(() => []),
      ]);

      setTasks(tasksData);
      setLeads(leadsData);
      setUsers(usersData);
    } catch (err) {
      alert(err.message || 'Failed to load tasks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [statusFilter, assigneeFilter]);

  const handleToggleStatus = async (task) => {
    const nextStatus = task.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await api.tasks.update(task.id, { status: nextStatus });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: nextStatus } : t))
      );
    } catch (err) {
      alert(err.message || 'Failed to update task.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this task?')) return;
    try {
      await api.tasks.delete(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      alert(err.message || 'Failed to delete task.');
    }
  };

  const pendingCount = tasks.filter((t) => t.status !== 'COMPLETED').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Task Center</h2>
          <p className="text-xs text-slate-400">
            {pendingCount} open action items • {tasks.length - pendingCount} completed
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            setEditingTask(null);
            setModalOpen(true);
          }}
          icon={Plus}
        >
          Add Task
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3 glass-card p-3 rounded-2xl border border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-2.5 py-1.5 outline-none"
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Assignee:</span>
          <select
            value={assigneeFilter}
            onChange={(e) => setAssigneeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-2.5 py-1.5 outline-none"
          >
            <option value="">All Employees</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text="Loading task records..." size="md" />
      ) : tasks.length === 0 ? (
        <EmptyState
          title="No tasks found"
          description="You have no tasks matching your filters. Create a new task or adjust your status filter."
          actionLabel="Create Task"
          onAction={() => {
            setEditingTask(null);
            setModalOpen(true);
          }}
        />
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`glass-card p-4 rounded-2xl border flex flex-wrap items-center justify-between gap-4 transition-all ${
                task.status === 'COMPLETED'
                  ? 'border-slate-800/60 bg-slate-900/30 opacity-60'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-900/70'
              }`}
            >
              <div className="flex items-start gap-3 min-w-0 max-w-xl">
                <button
                  onClick={() => handleToggleStatus(task)}
                  className={`w-6 h-6 rounded-lg border flex items-center justify-center transition-colors shrink-0 mt-0.5 ${
                    task.status === 'COMPLETED'
                      ? 'bg-emerald-600 border-emerald-500 text-white'
                      : 'border-slate-700 hover:border-slate-500 text-transparent'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                </button>

                <div className="min-w-0">
                  <p
                    className={`text-xs font-bold ${
                      task.status === 'COMPLETED' ? 'line-through text-slate-400' : 'text-white'
                    }`}
                  >
                    {task.title}
                  </p>

                  {task.description && (
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                      {task.description}
                    </p>
                  )}

                  {task.lead_company_name && (
                    <button
                      onClick={() => onSelectLead(task.lead_id)}
                      className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:underline mt-1 font-medium"
                    >
                      <Building className="w-3 h-3" />
                      <span>{task.lead_company_name}</span>
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs shrink-0">
                <PriorityBadge priority={task.priority} />

                {task.due_date && (
                  <span className="text-slate-400 text-[11px] flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>Due {formatDate(task.due_date)}</span>
                  </span>
                )}

                {task.assigned_user && (
                  <div className="flex items-center gap-1.5 text-slate-300 text-[11px]">
                    <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-bold">
                      {getInitials(task.assigned_user.name)}
                    </div>
                    <span className="hidden sm:inline">{task.assigned_user.name}</span>
                  </div>
                )}

                <div className="flex items-center gap-1 border-l border-slate-800 pl-3">
                  <button
                    onClick={() => {
                      setEditingTask(task);
                      setModalOpen(true);
                    }}
                    className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => handleDelete(task.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <TaskModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditingTask(null);
        }}
        initialData={editingTask}
        leads={leads}
        users={users}
        onSuccess={() => fetchTasks()}
      />
    </div>
  );
}
