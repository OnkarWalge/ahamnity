import { createClient } from '@supabase/supabase-js'

// The anon key is safe to expose in the browser — Row Level Security
// policies on the `cases` table (set up in Step 9) control what it can
// actually read/write. Never put the service_role key here.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_KEY — create frontend/.env (see .env.example)'
  )
}

export const supabase = createClient(supabaseUrl, supabaseKey)