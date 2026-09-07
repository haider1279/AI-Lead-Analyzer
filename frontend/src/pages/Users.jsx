import React, { useState, useEffect, useCallback } from 'react';
import {
  Users2,
  Plus,
  Trash2,
  UserMinus,
  UserPlus,
  ShieldCheck,
  Briefcase,
  AlertCircle,
  X,
  Edit2,
  Search,
  ChevronDown,
  Crown,
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Modal } from '../components/common/Modal';
import { getInitials } from '../utils/formatters';

// ─── Role Badge ───────────────────────────────────────────────────────────────

function RoleBadge({ role }) {
  if (role === 'admin') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
        <Crown className="w-2.5 h-2.5" />
        Admin
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30">
      <Briefcase className="w-2.5 h-2.5" />
      Employee
    </span>
  );
}

// ─── User Avatar ──────────────────────────────────────────────────────────────

function UserAvatar({ user, size = 'md' }) {
  const sizes = { sm: 'w-7 h-7 text-[10px]', md: 'w-9 h-9 text-xs' };
  return (
    <div
      className={`${sizes[size]} rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center font-bold text-white shrink-0`}
    >
      {getInitials(user?.name)}
    </div>
  );
}

// ─── Add Team Member Modal ────────────────────────────────────────────────────

function AddMemberModal({ isOpen, onClose, team, allUsers, onAdded }) {
  const [search, setSearch] = useState('');
  const [adding, setAdding] = useState(null);

  const memberIds = new Set((team?.members || []).map((m) => m.id));
  const available = allUsers.filter(
    (u) =>
      !memberIds.has(u.id) &&
      (u.name?.toLowerCase().includes(search.toLowerCase()) ||
        u.email?.toLowerCase().includes(search.toLowerCase()))
  );

  const handleAdd = async (user) => {
    setAdding(user.id);
    try {
      await api.teams.addMember(team.id, user.id);
      onAdded(user);
    } catch (err) {
      alert(err.message || 'Failed to add member.');
    } finally {
      setAdding(null);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Add Member to "${team?.name}"`}
      maxWidth="max-w-md"
    >
      <div className="space-y-4">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search users..."
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none"
          />
        </div>

        {available.length === 0 ? (
          <p className="text-center text-xs text-slate-500 py-4">
            {allUsers.length === 0 ? 'No users found.' : 'All users are already members.'}
          </p>
        ) : (
          <div className="space-y-1.5 max-h-72 overflow-y-auto">
            {available.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-800/60 transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <UserAvatar user={user} size="sm" />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-white truncate">{user.name}</p>
                    <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
                  </div>
                  <RoleBadge role={user.role} />
                </div>
                <Button
                  variant="emerald"
                  size="xs"
                  icon={UserPlus}
                  loading={adding === user.id}
                  onClick={() => handleAdd(user)}
                >
                  Add
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

// ─── Create / Edit Team Modal ─────────────────────────────────────────────────

function TeamFormModal({ isOpen, onClose, team, onSaved }) {
  const [name, setName] = useState(team?.name || '');
  const [description, setDescription] = useState(team?.description || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setName(team?.name || '');
      setDescription(team?.description || '');
      setError(null);
    }
  }, [isOpen, team]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Team name is required.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      let result;
      if (team) {
        result = await api.teams.update(team.id, { name: name.trim(), description: description.trim() || null });
      } else {
        result = await api.teams.create({ name: name.trim(), description: description.trim() || null });
      }
      onSaved(result);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save team.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={team ? `Edit Team: ${team.name}` : 'Create New Team'}
      maxWidth="max-w-md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
            {error}
          </div>
        )}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Team Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Sales A Team"
            required
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none transition-colors"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description..."
            rows={2}
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none resize-none transition-colors"
          />
        </div>
        <div className="flex gap-2 pt-1">
          <Button type="button" variant="ghost" size="sm" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm" loading={saving} className="flex-1">
            {team ? 'Save Changes' : 'Create Team'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

// ─── Team Card ────────────────────────────────────────────────────────────────

function TeamCard({ team, allUsers, isAdmin, onUpdate, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [localMembers, setLocalMembers] = useState(team.members || []);

  useEffect(() => {
    setLocalMembers(team.members || []);
  }, [team.members]);

  const handleRemoveMember = async (userId) => {
    if (!window.confirm('Remove this member from the team?')) return;
    setRemovingId(userId);
    try {
      await api.teams.removeMember(team.id, userId);
      setLocalMembers((prev) => prev.filter((m) => m.id !== userId));
      onUpdate({ ...team, members: localMembers.filter((m) => m.id !== userId) });
    } catch (err) {
      alert(err.message || 'Failed to remove member.');
    } finally {
      setRemovingId(null);
    }
  };

  const handleMemberAdded = (user) => {
    const updated = [...localMembers, user];
    setLocalMembers(updated);
    onUpdate({ ...team, members: updated });
    setShowAddMember(false);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete team "${team.name}"? This cannot be undone.`)) return;
    onDelete(team.id);
  };

  return (
    <>
      <div className="glass-card rounded-2xl border border-slate-800 hover:border-indigo-500/25 transition-all overflow-hidden">
        {/* Card Header */}
        <div className="p-5 flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shrink-0">
                <Users2 className="w-4 h-4 text-white" />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-white truncate">{team.name}</h3>
                {team.description && (
                  <p className="text-[10px] text-slate-400 truncate">{team.description}</p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 mt-3">
              <span className="text-[11px] text-slate-400">
                <span className="font-bold text-slate-200">{localMembers.length}</span>{' '}
                {localMembers.length === 1 ? 'member' : 'members'}
              </span>
              {/* Member avatars preview */}
              <div className="flex -space-x-1.5">
                {localMembers.slice(0, 5).map((m) => (
                  <div
                    key={m.id}
                    title={m.name}
                    className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-[8px] font-bold text-white border-2 border-[#0b0f19] shrink-0"
                  >
                    {getInitials(m.name)}
                  </div>
                ))}
                {localMembers.length > 5 && (
                  <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-[8px] font-bold text-slate-300 border-2 border-[#0b0f19]">
                    +{localMembers.length - 5}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5 shrink-0">
            {isAdmin && (
              <>
                <Button
                  variant="outline"
                  size="xs"
                  icon={Edit2}
                  onClick={() => setShowEdit(true)}
                  title="Edit team"
                />
                <Button
                  variant="outline"
                  size="xs"
                  icon={UserPlus}
                  onClick={() => { setShowAddMember(true); setExpanded(true); }}
                  title="Add member"
                />
                <Button
                  variant="outline"
                  size="xs"
                  icon={Trash2}
                  onClick={handleDelete}
                  title="Delete team"
                  className="hover:text-rose-400 hover:border-rose-500/50"
                />
              </>
            )}
            <button
              onClick={() => setExpanded((x) => !x)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title={expanded ? 'Collapse' : 'Expand'}
            >
              <ChevronDown
                className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
              />
            </button>
          </div>
        </div>

        {/* Expanded member list */}
        {expanded && (
          <div className="border-t border-slate-800/80 px-5 py-3 space-y-1.5">
            {localMembers.length === 0 ? (
              <p className="text-xs text-slate-500 py-2 text-center">
                No members yet.{isAdmin ? ' Click + to add members.' : ''}
              </p>
            ) : (
              localMembers.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between py-2 border-b border-slate-800/50 last:border-0"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <UserAvatar user={member} size="sm" />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{member.name}</p>
                      <p className="text-[10px] text-slate-400 truncate">{member.email}</p>
                    </div>
                    <RoleBadge role={member.role} />
                  </div>
                  {isAdmin && (
                    <Button
                      variant="ghost"
                      size="xs"
                      icon={UserMinus}
                      loading={removingId === member.id}
                      onClick={() => handleRemoveMember(member.id)}
                      title="Remove from team"
                      className="text-slate-500 hover:text-rose-400"
                    />
                  )}
                </div>
              ))
            )}
            {isAdmin && (
              <button
                onClick={() => setShowAddMember(true)}
                className="w-full mt-1 py-2 rounded-xl border border-dashed border-slate-700 text-xs text-slate-500 hover:text-slate-300 hover:border-slate-600 transition-colors flex items-center justify-center gap-1.5"
              >
                <UserPlus className="w-3.5 h-3.5" />
                Add member
              </button>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {isAdmin && (
        <>
          <AddMemberModal
            isOpen={showAddMember}
            onClose={() => setShowAddMember(false)}
            team={{ ...team, members: localMembers }}
            allUsers={allUsers}
            onAdded={handleMemberAdded}
          />
          <TeamFormModal
            isOpen={showEdit}
            onClose={() => setShowEdit(false)}
            team={team}
            onSaved={(updated) => {
              onUpdate({ ...team, ...updated, members: localMembers });
              setShowEdit(false);
            }}
          />
        </>
      )}
    </>
  );
}

// ─── All Users Panel ──────────────────────────────────────────────────────────

function AllUsersPanel({ users }) {
  const [search, setSearch] = useState('');
  const filtered = users.filter(
    (u) =>
      u.name?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="glass-card rounded-2xl border border-slate-800 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-white">All Users</h2>
        <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
          {users.length} total
        </span>
      </div>

      <div className="relative">
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter users..."
          className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none"
        />
      </div>

      <div className="space-y-1.5 max-h-[calc(100vh-26rem)] overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-4">No users found.</p>
        ) : (
          filtered.map((user) => (
            <div
              key={user.id}
              className="flex items-center gap-2.5 p-2.5 rounded-xl hover:bg-slate-800/60 transition-colors"
            >
              <UserAvatar user={user} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-white truncate">{user.name}</p>
                <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
              </div>
              <RoleBadge role={user.role} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function Users() {
  const { isAdmin } = useAuth();
  const [teams, setTeams] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [deletingTeamId, setDeletingTeamId] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [teamsData, usersData] = await Promise.all([
        api.teams.list(),
        api.auth.getUsers().catch(() => []),
      ]);
      setTeams(teamsData || []);
      setAllUsers(usersData || []);
    } catch (err) {
      setError(err.message || 'Failed to load team data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTeamCreated = (newTeam) => {
    setTeams((prev) => [{ ...newTeam, members: [] }, ...prev]);
    setShowCreateTeam(false);
  };

  const handleTeamUpdated = (updatedTeam) => {
    setTeams((prev) => prev.map((t) => (t.id === updatedTeam.id ? updatedTeam : t)));
  };

  const handleTeamDeleted = async (teamId) => {
    setDeletingTeamId(teamId);
    try {
      await api.teams.delete(teamId);
      setTeams((prev) => prev.filter((t) => t.id !== teamId));
    } catch (err) {
      alert(err.message || 'Failed to delete team.');
    } finally {
      setDeletingTeamId(null);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading teams & members..." size="lg" />;
  }

  if (error) {
    return (
      <div className="glass-card rounded-2xl border border-rose-500/30 p-8 text-center">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-white mb-1">Failed to load team data</h3>
        <p className="text-xs text-slate-400 mb-4">{error}</p>
        <Button variant="primary" size="sm" onClick={fetchData}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Team Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage teams and assign members. Roles are system-managed and cannot be changed here.
          </p>
        </div>
        {isAdmin && (
          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={() => setShowCreateTeam(true)}
          >
            New Team
          </Button>
        )}
      </div>

      {/* ── Info strip for employees ── */}
      {!isAdmin && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>You can view teams and members. Contact your admin to modify team assignments.</span>
        </div>
      )}

      {/* ── Main Layout: Teams + Users Sidebar ── */}
      <div className="flex gap-6 items-start">
        {/* Teams section */}
        <div className="flex-1 min-w-0 space-y-4">
          {teams.length === 0 ? (
            <EmptyState
              icon={Users2}
              title="No teams yet"
              description={
                isAdmin
                  ? 'Create your first team to start organizing your sales force.'
                  : 'No teams have been created yet.'
              }
              action={
                isAdmin ? (
                  <Button variant="primary" size="md" icon={Plus} onClick={() => setShowCreateTeam(true)}>
                    Create First Team
                  </Button>
                ) : null
              }
            />
          ) : (
            teams.map((team) => (
              <TeamCard
                key={team.id}
                team={team}
                allUsers={allUsers}
                isAdmin={isAdmin}
                onUpdate={handleTeamUpdated}
                onDelete={handleTeamDeleted}
              />
            ))
          )}
        </div>

        {/* Users sidebar */}
        <div className="w-72 shrink-0 sticky top-24">
          <AllUsersPanel users={allUsers} />
        </div>
      </div>

      {/* ── Create Team Modal ── */}
      {isAdmin && (
        <TeamFormModal
          isOpen={showCreateTeam}
          onClose={() => setShowCreateTeam(false)}
          team={null}
          onSaved={handleTeamCreated}
        />
      )}
    </div>
  );
}
