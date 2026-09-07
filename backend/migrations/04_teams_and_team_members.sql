-- ==============================================================================
-- MIGRATION 04: TEAMS & TEAM MEMBERSHIP SCHEMA
-- Execute this script in your Supabase SQL Editor
-- ==============================================================================

-- 1. Create TEAMS table
CREATE TABLE IF NOT EXISTS public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Create TEAM_MEMBERS junction table
CREATE TABLE IF NOT EXISTS public.team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_team_member UNIQUE (team_id, user_id)
);

-- 3. Indexes for high-performance membership lookups
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON public.team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON public.team_members(user_id);

-- 4. Trigger for automatic updated_at on teams
DROP TRIGGER IF EXISTS update_teams_updated_at ON public.teams;
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON public.teams
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Seed default organizational teams (idempotent)
INSERT INTO public.teams (name, description) VALUES
    ('Sales Team', 'Direct outbound sales and deal closing'),
    ('Management Team', 'Executive leadership and operations'),
    ('Lead Research Team', 'Prospecting, intelligence gathering, and qualification')
ON CONFLICT (name) DO NOTHING;

-- 6. Enable Row Level Security (RLS)
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

-- 7. RLS Policies for TEAMS
DROP POLICY IF EXISTS "Teams viewable by authenticated users" ON public.teams;
CREATE POLICY "Teams viewable by authenticated users"
    ON public.teams FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Admins can insert teams" ON public.teams;
CREATE POLICY "Admins can insert teams"
    ON public.teams FOR INSERT TO authenticated WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS "Admins can update teams" ON public.teams;
CREATE POLICY "Admins can update teams"
    ON public.teams FOR UPDATE TO authenticated USING (public.is_admin());

DROP POLICY IF EXISTS "Admins can delete teams" ON public.teams;
CREATE POLICY "Admins can delete teams"
    ON public.teams FOR DELETE TO authenticated USING (public.is_admin());

-- 8. RLS Policies for TEAM_MEMBERS
DROP POLICY IF EXISTS "Team members viewable by authenticated users" ON public.team_members;
CREATE POLICY "Team members viewable by authenticated users"
    ON public.team_members FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Admins can insert team members" ON public.team_members;
CREATE POLICY "Admins can insert team members"
    ON public.team_members FOR INSERT TO authenticated WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS "Admins can delete team members" ON public.team_members;
CREATE POLICY "Admins can delete team members"
    ON public.team_members FOR DELETE TO authenticated USING (public.is_admin());
